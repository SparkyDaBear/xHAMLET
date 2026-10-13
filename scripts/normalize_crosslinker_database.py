#!/usr/bin/env python3
"""Normalize extracted crosslinker reagent text spans against the curated database.

The pipeline's ad hoc crosslinker matching (exact name/alias lookup, see
``XiConfigGenerator.get_crosslinker``) is intentionally simple and frequently
fails on real-world text: isotope-labeled variants ("BS3-d4"), reordered
parenthetical abbreviations ("BS3 (bis[sulfosuccinimidyl] suberate)"), and
genuinely new reagents never catalogued in
``assets/crosslinker_definitions.json``.

This script scans every ``store/<PXD>/llm/responses.json`` for extracted
``comment[cross-linker]`` text spans (handling the schema variants seen across
different pipeline runs), resolves as many as possible deterministically, and
uses a single batched LLM pass - over only the small number of *distinct*
spans still unresolved - to either:

  1. map a span to an existing database entry (auto-applied as a new alias:
     low-risk, does not touch any chemistry-critical field XiSearch relies on
     for peptide scoring), or
  2. draft a new candidate entry for a genuinely novel reagent (written to a
     separate pending-review file - NOT auto-merged into the live database,
     since an LLM should not be trusted to silently supply authoritative
     monoisotopic mass / cleavage-site chemistry), or
  3. flag the span as not a chemical crosslinking reagent at all (reducing
     agents, proximity-labeling, enzymatic/UV-only crosslinking, etc.)

A decision cache keyed by normalized span text makes re-runs incremental:
only spans never seen before cost an LLM call, so this is safe to re-run
every time new PXDs are added to the store (as long as they made it at
least through SDRF generation).

Examples:
    python scripts/normalize_crosslinker_database.py
    python scripts/normalize_crosslinker_database.py --dry-run
    python scripts/normalize_crosslinker_database.py --data-dir store --crosslinker-db assets/crosslinker_definitions.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

DEFAULT_DATA_DIR = Path("store")
DEFAULT_DB_PATH = Path("assets/crosslinker_definitions.json")
DEFAULT_PENDING_PATH = Path("assets/crosslinker_definitions.pending.json")
DEFAULT_CACHE_PATH = Path("assets/crosslinker_normalization_cache.json")
DEFAULT_CONFIG_PATH = Path("configs/config.yaml")

ISOTOPE_SUFFIX_RE = re.compile(
    r"[\s\-]*(?:d\d+(?:/d\d+)?|h\d+/d\d+)\b\.?\s*$|^h\d+/d\d+[\s\-]*",
    re.IGNORECASE,
)
TRAILING_PAREN_ABBREV_RE = re.compile(r"\(([A-Za-z0-9\-]+)\)\s*$")
LEADING_PAREN_ABBREV_RE = re.compile(r"^([A-Za-z0-9\-]+)\s*\(")
# All-caps alphanumeric tokens (2-6 chars) look like crosslinker abbreviations
# (BS3, DSS, DSP, SDA...). Used to sanity-check accession-based matches below.
ABBREV_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b")

BATCH_SIZE = 25

CLASSIFICATION_PROMPT_TEMPLATE = """You are curating a reference database of chemical crosslinking reagents used \
in crosslinking mass spectrometry (XL-MS) experiments.

You will be given:
1. The CURRENT DATABASE (reagents already catalogued, with their aliases and XLMOD/ChEBI accessions).
2. A list of TEXT SPANS extracted from publication/metadata text by an earlier LLM pass, each of which
   named what the extracting model believed was a chemical crosslinking reagent, but which did not
   match anything in the current database via exact name/alias lookup. Some spans include a
   "(context: ...)" excerpt - the actual sentence it was extracted from. ALWAYS prefer that context
   over your own prior knowledge of the abbreviation: short acronyms are frequently ambiguous outside
   XL-MS (e.g. "PDH" is Pyruvate Dehydrogenase in general biochemistry, but in a crosslinking paper's
   context "pimelic acid dihydrazide (PDH)" it is a carboxyl-reactive crosslinking reagent; "ADH"
   similarly means Alcohol Dehydrogenase generally but "adipic acid dihydrazide" in this domain).
   When context is present and clearly describes crosslinking chemistry, trust it over the
   abbreviation's more common meaning elsewhere.

For EACH text span, decide exactly one of:
  - "map_to_existing": the span is a synonym, alternate punctuation, or isotope-labeled variant of an
    EXISTING database entry (e.g. "BS3-d4", "H12/D12 DSS", "BS3 (bis[sulfosuccinimidyl] suberate)" are
    all variants of already-catalogued reagents). Set "matched_name" to that entry's exact name as it
    appears in the CURRENT DATABASE below.
  - "new_candidate": the span names a real chemical crosslinking reagent that is genuinely absent from
    the current database. Draft as much of a new entry as you can confidently infer from the span and
    its context; leave any field you are not confident about as null rather than guessing. NEVER
    guess an exact monoisotopic mass unless it is explicitly stated in the provided context - mass is
    used directly for search-engine scoring and a wrong value is worse than a missing one.
  - "not_a_crosslinker": the span is NOT a chemical crosslinking reagent at all - e.g. a reducing/
    alkylating agent (DTT, iodoacetamide), a proximity-labeling enzyme or its substrate (TurboID,
    BioID, APEX, biotin-phenol), a coupling/activator reagent that is not itself the crosslinker
    (e.g. NHS, sulfo-NHS used only to describe chemistry), an enzymatic/natural crosslink (e.g.
    transglutaminase-catalyzed isopeptide bonds), or vague/unparseable noise.

CURRENT DATABASE:
{database_block}

TEXT SPANS TO CLASSIFY:
{spans_block}

Respond with ONLY a JSON array, one object per span, in the same order given, with this exact shape:
[
  {{
    "span": "<the exact text span as given above>",
    "verdict": "map_to_existing" | "new_candidate" | "not_a_crosslinker",
    "matched_name": "<existing database entry name, only if verdict is map_to_existing, else null>",
    "new_candidate": {{
      "name": "<short name/abbreviation as commonly used, or null>",
      "full_name": "<full chemical name, or null>",
      "aliases": ["<alternate spellings/abbreviations seen>"],
      "xlmod_accession": "<XLMOD:##### or ChEBI accession if stated/known, else null>",
      "ms_cleavable": true | false | null,
      "linked_aminoacids": "<comma-separated reactive residues e.g. 'K,nterm', or null>",
      "notes": "<brief note on chemistry/usage if known, else null>"
    }},
    "reasoning": "<one sentence>",
    "confidence": "high" | "medium" | "low"
  }},
  ...
]
Omit the "new_candidate" object (set it to null) unless verdict is "new_candidate".
"""


def normalize_key(span: str) -> str:
    """Normalize a text span into a cache/dedup key."""
    return re.sub(r"\s+", " ", span.strip().lower())


def strip_isotope_suffix(span: str) -> str:
    stripped = ISOTOPE_SUFFIX_RE.sub("", span).strip(" -")
    return stripped if stripped else span


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


class CrosslinkerDatabase:
    """In-memory view of assets/crosslinker_definitions.json with lookup helpers."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.data = load_json(db_path, {"crosslinkers": [], "validation_info": {}, "notes": "", "_xlmod_audit": {}})
        self.entries: list[dict[str, Any]] = self.data.setdefault("crosslinkers", [])
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        self.by_name: dict[str, dict[str, Any]] = {}
        self.by_accession: dict[str, dict[str, Any]] = {}
        for entry in self.entries:
            for key in self._name_keys(entry):
                self.by_name[key] = entry
            accession = entry.get("xlmod_accession")
            if accession:
                self.by_accession[accession.strip().upper()] = entry

    def _name_keys(self, entry: dict[str, Any]) -> Iterable[str]:
        yield entry["name"].lower()
        if "short_name" in entry:
            yield entry["short_name"].lower()
        for alias in entry.get("aliases", []):
            yield alias.lower()

    def match_by_name(self, span: str) -> dict[str, Any] | None:
        """Exact/alias match, with regex fallback for both abbreviation orderings
        and isotope-label stripping - a superset of XiConfigGenerator.get_crosslinker."""
        if not span:
            return None
        candidates = [span, strip_isotope_suffix(span)]
        for candidate in candidates:
            key = candidate.lower().strip()
            if key in self.by_name:
                return self.by_name[key]
            trailing = TRAILING_PAREN_ABBREV_RE.search(candidate)
            if trailing and trailing.group(1).lower() in self.by_name:
                return self.by_name[trailing.group(1).lower()]
            leading = LEADING_PAREN_ABBREV_RE.search(candidate)
            if leading and leading.group(1).lower() in self.by_name:
                return self.by_name[leading.group(1).lower()]
        return None

    def match_by_accession(self, accession: str | None) -> dict[str, Any] | None:
        if not accession:
            return None
        return self.by_accession.get(str(accession).strip().upper())

    def match_by_accession_safe(self, accession: str | None, original_span: str) -> dict[str, Any] | None:
        """Like match_by_accession, but guards against (occasionally hallucinated)
        accessions from the original extraction: if the span itself spells out an
        explicit all-caps abbreviation that names a DIFFERENT catalogued entry
        (e.g. "dithiobis (succinimidyl propionate);DSP" literally contains "DSP"),
        trust that literal text over the recorded accession. Only returns the
        accession match when there is no such conflict; returns the conflicting
        entry instead when exactly one distinct conflict is found; returns None
        (defer to the LLM tier) when the conflict is ambiguous."""
        candidate = self.match_by_accession(accession)
        if candidate is None:
            return None
        candidate_keys = set(self._name_keys(candidate))
        conflicts = {
            id(self.by_name[token.lower()]): self.by_name[token.lower()]
            for token in ABBREV_TOKEN_RE.findall(original_span)
            if token.lower() in self.by_name and token.lower() not in candidate_keys
        }
        if not conflicts:
            return candidate
        if len(conflicts) == 1:
            return next(iter(conflicts.values()))
        return None

    def add_alias(self, entry: dict[str, Any], alias: str) -> bool:
        """Add alias if not already present; returns True if the entry changed."""
        aliases = entry.setdefault("aliases", [])
        if any(a.lower() == alias.lower() for a in aliases) or alias.lower() == entry["name"].lower():
            return False
        aliases.append(alias)
        self._rebuild_indexes()
        return True

    def save(self) -> None:
        save_json(self.db_path, self.data)

    def render_reference_block(self) -> str:
        lines = []
        for entry in self.entries:
            name = entry.get("short_name") or entry["name"]
            aliases = sorted(set(entry.get("aliases", [])) - {name})
            accession = entry.get("xlmod_accession") or "null"
            alias_text = f"; aliases: {', '.join(aliases)}" if aliases else ""
            lines.append(f"- {name} (AC={accession}){alias_text}")
        return "\n".join(lines)


def extract_reagent_mentions(entry: Any) -> list[tuple[str, str | None, str | None]]:
    """Return [(NT, AC, evidence_quote), ...] from a comment[cross-linker] LLM response entry,
    handling the schema variants seen across different pipeline runs. Also
    returns a short evidence_quote per mention when available, since short
    abbreviations (PDH, ADH, SDH...) are often ambiguous without the
    surrounding sentence (e.g. "PDH" alone reads as Pyruvate Dehydrogenase to
    an LLM; "pimelic acid dihydrazide (PDH) and the coupling reagent DMTMM"
    makes the crosslinker usage unambiguous)."""
    if not isinstance(entry, dict):
        return []
    parsed = entry.get("parsed")
    if not isinstance(parsed, dict):
        return []
    value = parsed.get("value")
    nt_top = parsed.get("NT")
    quote_top = parsed.get("evidence_quote")
    mentions: list[tuple[str, str | None, str | None]] = []
    if isinstance(value, list) and value and isinstance(value[0], dict) and "NT" in value[0]:
        quote_list = quote_top if isinstance(quote_top, list) else [quote_top] * len(value)
        for i, item in enumerate(value):
            if isinstance(item, dict) and item.get("NT"):
                mentions.append((item.get("NT"), item.get("AC"), quote_list[i] if i < len(quote_list) else None))
    elif isinstance(nt_top, list):
        ac = parsed.get("AC")
        ac_list = ac if isinstance(ac, list) else [ac] * len(nt_top)
        quote_list = quote_top if isinstance(quote_top, list) else [quote_top] * len(nt_top)
        for i, name in enumerate(nt_top):
            if name:
                mentions.append((
                    name,
                    ac_list[i] if i < len(ac_list) else None,
                    quote_list[i] if i < len(quote_list) else None,
                ))
    elif nt_top:
        mentions.append((nt_top, parsed.get("AC"), quote_top if isinstance(quote_top, str) else None))
    return [
        (str(name).strip(), (str(acc).strip() if acc else None), (str(quote).strip() if quote else None))
        for name, acc, quote in mentions
        if name and str(name).strip().lower() not in ("null", "none", "")
    ]


def scan_store(data_dir: Path) -> dict[str, dict[str, Any]]:
    """Scan every PXD's llm/responses.json; return {normalized_span: info}."""
    spans: dict[str, dict[str, Any]] = {}
    for pxd_dir in sorted(data_dir.iterdir()):
        if not pxd_dir.is_dir():
            continue
        llm_path = pxd_dir / "llm" / "responses.json"
        if not llm_path.is_file():
            continue
        try:
            payload = json.load(llm_path.open(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        entry = data.get("comment[cross-linker]") if isinstance(data, dict) else None
        for name, accession, evidence_quote in extract_reagent_mentions(entry):
            key = normalize_key(name)
            info = spans.setdefault(
                key, {"original": name, "accessions": set(), "pxds": set(), "count": 0, "evidence_quote": None}
            )
            if accession:
                info["accessions"].add(accession)
            if evidence_quote and not info["evidence_quote"]:
                info["evidence_quote"] = evidence_quote[:300]
            info["pxds"].add(pxd_dir.name)
            info["count"] += 1
    return spans


def classify_batch(
    llm: Any, database: CrosslinkerDatabase, spans: list[tuple[str, str | None]]
) -> list[dict[str, Any]]:
    """spans: [(span_text, evidence_quote_or_None), ...]"""
    lines = []
    for i, (span, quote) in enumerate(spans):
        if quote:
            lines.append(f'{i + 1}. "{span}" (context: "{quote}")')
        else:
            lines.append(f'{i + 1}. "{span}"')
    spans_block = "\n".join(lines)
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
        database_block=database.render_reference_block(), spans_block=spans_block
    )
    raw = llm.query(prompt, "Classify the text spans listed in the prompt above.")
    if not raw:
        return []
    parsed = llm.parse_json_response(raw)
    if not isinstance(parsed, list):
        return []
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Result store root to scan")
    parser.add_argument("--crosslinker-db", type=Path, default=DEFAULT_DB_PATH, help="Crosslinker database JSON to read/update")
    parser.add_argument("--pending-review", type=Path, default=DEFAULT_PENDING_PATH, help="Output file for new-candidate drafts awaiting human review")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH, help="Persistent per-span decision cache (makes re-runs incremental)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="xHAMLET config.yaml (for default LLM model)")
    parser.add_argument("--model", default=None, help="Override the LLM model to use")
    parser.add_argument("--llm-base-url", default=None, metavar="URL", help="Override the LLM API base URL (auto-detects OpenRouter vs OpenAI from environment when unset)")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Distinct spans per LLM call (default: %(default)s)")
    parser.add_argument("--force", action="store_true", help="Re-classify spans even if already present in the decision cache")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing any files")
    parser.add_argument("--skip-llm", action="store_true", help="Apply only the free deterministic tier (name/alias/accession/isotope-strip) and write its results; skip the batched LLM classification pass entirely")
    args = parser.parse_args()

    database = CrosslinkerDatabase(args.crosslinker_db)
    cache: dict[str, dict[str, Any]] = load_json(args.cache, {})
    pending: dict[str, Any] = load_json(args.pending_review, {"candidates": []})

    print(f"Scanning {args.data_dir} for extracted crosslinker mentions...")
    spans = scan_store(args.data_dir)
    print(f"Found {sum(s['count'] for s in spans.values())} mentions across {len(spans)} distinct text spans.")

    counts = Counter()
    aliases_added = 0
    still_unmatched: list[str] = []

    for key, info in spans.items():
        original = info["original"]

        match = database.match_by_name(original)
        if match is None:
            for accession in info["accessions"]:
                match = database.match_by_accession_safe(accession, original)
                if match:
                    break

        if match:
            counts["matched_deterministic"] += 1
            if not args.dry_run and database.add_alias(match, original):
                aliases_added += 1
            continue

        cached = cache.get(key)
        if cached and not args.force:
            counts[f"cached_{cached['verdict']}"] += 1
            continue

        still_unmatched.append(key)

    print(f"Deterministic matches (name/alias/accession/isotope-strip): {counts['matched_deterministic']}")
    print(f"Already classified in cache (skipped): {sum(v for k, v in counts.items() if k.startswith('cached_'))}")
    print(f"Distinct spans needing LLM classification: {len(still_unmatched)}")
    print(f"New aliases added to database: {aliases_added}")

    if args.skip_llm:
        print(f"\n--skip-llm: applying only the deterministic tier; {len(still_unmatched)} spans left unclassified for a future run.")
        if args.dry_run:
            print("--dry-run: no files were written.")
            return 0
        database.save()
        print(f"\nUpdated {args.crosslinker_db}")
        return 0

    if still_unmatched and args.dry_run:
        print("\n--dry-run: skipping LLM classification (no API calls made) and file writes.")
        for key in still_unmatched[:20]:
            print(f"  would classify: {spans[key]['original']!r}")
        if len(still_unmatched) > 20:
            print(f"  ... and {len(still_unmatched) - 20} more")
        return 0

    if still_unmatched:
        import yaml

        config = yaml.safe_load(args.config.read_text()) if args.config.is_file() else {}
        llm_config = config.get("llm", {}) or {}
        model = args.model or llm_config.get("model", "gpt-4o-mini-2024-07-18")
        base_url = args.llm_base_url if args.llm_base_url is not None else llm_config.get("base_url")

        from pxd_enhancer.llm_client import LLMClient

        llm = LLMClient(model=model, temperature=0.0, base_url=base_url)

        for batch_start in range(0, len(still_unmatched), args.batch_size):
            batch_keys = still_unmatched[batch_start : batch_start + args.batch_size]
            batch_spans = [(spans[key]["original"], spans[key].get("evidence_quote")) for key in batch_keys]
            print(f"Classifying spans {batch_start + 1}-{batch_start + len(batch_keys)} of {len(still_unmatched)}...")
            results = classify_batch(llm, database, batch_spans)
            results_by_span = {normalize_key(r.get("span", "")): r for r in results if isinstance(r, dict)}

            for key in batch_keys:
                original = spans[key]["original"]
                result = results_by_span.get(key)
                if result is None:
                    print(f"  WARNING: no classification returned for {original!r}; leaving unclassified")
                    continue

                verdict = result.get("verdict")
                cache[key] = {
                    "span": original,
                    "verdict": verdict,
                    "pxds": sorted(spans[key]["pxds"]),
                }

                if verdict == "map_to_existing":
                    matched_name = result.get("matched_name")
                    target = database.by_name.get(str(matched_name).lower()) if matched_name else None
                    if target is None:
                        print(f"  WARNING: {original!r} -> map_to_existing {matched_name!r}, but no such entry exists; treating as new_candidate instead")
                        verdict = cache[key]["verdict"] = "new_candidate"
                        result["new_candidate"] = result.get("new_candidate") or {"name": original}
                    else:
                        counts["llm_mapped"] += 1
                        if not args.dry_run and database.add_alias(target, original):
                            aliases_added += 1
                        continue

                if verdict == "new_candidate":
                    counts["llm_new_candidate"] += 1
                    draft = dict(result.get("new_candidate") or {})
                    draft["_source_span"] = original
                    draft["_reasoning"] = result.get("reasoning")
                    draft["_confidence"] = result.get("confidence")
                    draft["_seen_in_pxds"] = sorted(spans[key]["pxds"])
                    pending.setdefault("candidates", []).append(draft)
                elif verdict == "not_a_crosslinker":
                    counts["llm_not_a_crosslinker"] += 1
                else:
                    print(f"  WARNING: unrecognized verdict {verdict!r} for {original!r}")

    print()
    print("=== Summary ===")
    print(f"Deterministic matches:         {counts['matched_deterministic']}")
    print(f"LLM-mapped to existing entry:  {counts['llm_mapped']}")
    print(f"LLM-flagged new candidates:    {counts['llm_new_candidate']}  (see {args.pending_review})")
    print(f"LLM-flagged not-a-crosslinker: {counts['llm_not_a_crosslinker']}")
    print(f"New aliases added to database: {aliases_added}")

    if args.dry_run:
        print("\n--dry-run: no files were written.")
        return 0

    database.save()
    save_json(args.cache, cache)
    save_json(args.pending_review, pending)
    print(f"\nUpdated {args.crosslinker_db}, {args.cache}, {args.pending_review}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
