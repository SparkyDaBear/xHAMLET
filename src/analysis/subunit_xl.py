"""Inputs and site-localized crosslinks for the subunit coverage notebook."""

import csv
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FASTA = ROOT / "reference_data/uniprot_fasta/taxid_9606_reviewed.fasta"
ASSETS = ROOT / "assets"
sys.path.insert(0, str(ROOT / "scripts"))
from sync_result_database import parse_mzid, sha256_file

QUERY = """
SELECT p.accession, s.search_run_id, s.crosslinker_config, m.relative_path, m.source_sha256,
       x.spectrum_native_id, x.crosslink_group_key,
       x.alpha_sequence, x.beta_sequence, x.alpha_positions, x.beta_positions
FROM crosslink_match x
JOIN mzid_document m USING (mzid_document_id)
JOIN search_run s USING (search_run_id)
JOIN pipeline_run r USING (pipeline_run_id)
JOIN project p USING (project_id)
WHERE r.accepted AND m.is_complete AND x.pass_threshold
ORDER BY m.mzid_document_id, x.crosslink_match_id
"""

XL_ACCESSIONS = """
SELECT s.search_run_id, x.alpha_proteins, x.beta_proteins
FROM crosslink_match x
JOIN mzid_document m USING (mzid_document_id)
JOIN search_run s USING (search_run_id)
JOIN pipeline_run r USING (pipeline_run_id)
WHERE r.accepted AND m.is_complete AND x.pass_threshold
"""

LINEAR_ARTIFACTS = """
SELECT s.search_run_id, s.crosslinker_config, p.accession, a.relative_path, a.sha256
FROM search_run s
JOIN pipeline_run r USING (pipeline_run_id)
JOIN project p USING (project_id)
LEFT JOIN output_artifact a ON a.pipeline_run_id = r.pipeline_run_id
 AND a.relative_path GLOB s.run_path || '/results/linear_search/*_linear.csv'
WHERE r.accepted AND EXISTS (
    SELECT 1 FROM mzid_document m WHERE m.search_run_id = s.search_run_id AND m.is_complete
)
"""


def read_fasta(path=FASTA):
    records = {}
    with path.open() as handle:
        for line in handle:
            if line.startswith(">"):
                accession = line.split("|")[1]
                if accession in records:
                    raise ValueError(f"Duplicate FASTA accession: {accession}")
                records[accession] = []
            elif line.strip():
                records[accession].append(line.strip())
    return {accession: "".join(lines) for accession, lines in records.items()}


def subunit_count(text, terms):
    # Do not interpret oligomers of interacting partners later in the annotation.
    lead = re.sub(r"\{[^}]*\}|\([^)]*\)", "", text.split(".", 1)[0].lower())
    lead = re.sub(r"^subunit:\s*", "", lead).strip()
    pattern = r"\b(?:" + "|".join(re.escape(term) for term in terms) + r")s?\b"
    if not re.match(r"^(?:(?:predominantly|mainly)\s+)?(?:(?:forms?|exists? as|is)\s+)?(?:an?\s+)?" + pattern, lead):
        return None
    counts = {terms[m.group().removesuffix("s")] for m in re.finditer(pattern, lead)}
    if len(counts) != 1 or re.search(r"\bor\b|higher.order|depending|in complex with", lead):
        return None
    return counts.pop()


def load_proteins():
    terms = json.loads((ASSETS / "subunit_count_mapping.json").read_text())
    with (ASSETS / "uniprot_9606_reviewed_subunits.tsv").open(newline="") as handle:
        annotations = {r["uniprot_id"]: r for r in csv.DictReader(handle, delimiter="\t")}
    fasta = read_fasta()
    if annotations.keys() != fasta.keys():
        raise ValueError("UniProt annotation accessions do not match the cached FASTA")
    return {
        acc: {"sequence": seq, "subunit_text": row["subunit_text"],
              "subunit_count": subunit_count(row["subunit_text"], terms),
              "uniprot_status": row["status"]}
        for acc, seq in fasta.items() for row in [annotations[acc]]
    }


def linker_rules():
    definitions = json.loads((ASSETS / "crosslinker_definitions.json").read_text())["crosslinkers"]
    rules = {}
    for row in definitions:
        tokens = {x.strip().lower() for x in re.sub(r"\([^)]*\)", "", row.get("linked_aminoacids") or "").split(",")}
        tokens.discard("")
        if tokens and all(re.fullmatch(r"[a-z]|nterm|cterm", token) for token in tokens):
            rules[row["name"].casefold()] = tokens
    return rules


def configured_linker(config, rules):
    """Only identify an explicit single covalent linker, not warning text."""
    names = {m.group(1).casefold() for line in json.loads(config)
             if line.startswith("crosslinker:") and "NonCovalentBound" not in line
             if (m := re.search(r":Name:([^;]+)", line))}
    return next(iter(names)) if len(names) == 1 and names <= rules.keys() else None


def document_matches(job):
    path, checksum, linker, requests = job
    if not path.is_file() or sha256_file(path) != checksum:
        return [], Counter({"missing_or_changed_source": len(requests)})
    summary = parse_mzid(path)
    if not summary["is_complete"] or summary["metadata"].get("parse_error"):
        raise ValueError(f"Invalid source mzIdentML: {path}")
    found = defaultdict(list)
    for match in summary["crosslinks"]:
        key = match["spectrum_native_id"], match["crosslink_group_key"]
        found[key].append(match)
    output, audit = [], Counter()
    for native, group, alpha, beta, alpha_pos, beta_pos in requests:
        candidates = [
            m for m in found[native, group]
            if (m["alpha_sequence"], m["beta_sequence"], m["alpha_positions"], m["beta_positions"])
            == (alpha, beta, json.loads(alpha_pos), json.loads(beta_pos))
        ]
        if len(candidates) != 1:
            audit["not_uniquely_matched_to_source"] += 1
            continue
        match = candidates[0]
        output.append((linker, tuple(
            (match[f"{side}_sequence"], match[f"{side}_positions"], match[f"{side}_link_sites"])
            for side in ("alpha", "beta")
        )))
    return output, audit


def localize(pep, spans, offsets, proteins):
    if not pep or len(spans) != 1 or len(offsets) != 1:
        return None
    match = re.fullmatch(r"(.+):(\d+)-(\d+)", spans[0])
    if not match or not re.fullmatch(r"\d+", offsets[0]):
        return None
    acc, lo, hi = match.groups()
    start, end, offset = int(lo), int(hi), int(offsets[0])
    if start < 1 or end - start + 1 != len(pep) or not 0 <= offset <= len(pep) + 1:
        return None
    sequence = proteins[acc]["sequence"] if acc in proteins else None
    if sequence is not None and sequence[start - 1:end] != pep:
        return None
    if offset == 0:
        if start != 1:
            return None
        return acc, start, "nterm"
    if offset == len(pep) + 1:
        if sequence is None or end != len(sequence):
            return None
        return acc, end, "cterm"
    return acc, start + offset - 1, pep[offset - 1].lower()


def eligible_positions(sequence, rules):
    eligible = {i for i, aa in enumerate(sequence, 1) if aa.lower() in rules}
    if "nterm" in rules:
        eligible.add(1)
    if "cterm" in rules:
        eligible.add(len(sequence))
    return eligible


def add_coverage_fields(proteins, rules):
    for row in proteins.values():
        row["eligible_xl_residues_by_linker"] = {
            linker: sorted(eligible_positions(row["sequence"], rules[linker]))
            for linker in row["linkers"]
        }
        denominator = row["eligible_residue_count"]
        row["fraction_xl"] = len(row["observed_eligible_residues"]) / denominator if denominator else None


def linear_accessions(paths):
    import pandas as pd

    accessions = set()
    for path in paths:
        for chunk in pd.read_csv(path, usecols=["MatchRank", "decoy", "Protein1"], dtype=str,
                                 keep_default_na=False, chunksize=100_000, encoding="utf-8-sig"):
            for value in chunk.loc[chunk.MatchRank.eq("1") & chunk.decoy.eq("0"), "Protein1"].unique():
                mapped = {part.strip() for part in value.split(";") if part.strip()}
                if len(mapped) == 1:
                    accessions.update(mapped)
    return accessions


def collect_linear_group(job):
    run_id, files = job
    for path, digest in files:
        if path is None or not digest or not path.is_file() or sha256_file(path) != digest:
            return run_id, None
    return run_id, linear_accessions(path for path, _ in files)


def linear_coverage(accession, sequence, detected_runs, xl_by_run, linkers_by_run, sites_by_run, rules):
    has_xl = any(accession in xl_by_run.get(run, ()) for run in detected_runs)
    linkers = {linkers_by_run[run] for run in detected_runs if linkers_by_run[run] is not None}
    eligible = set().union(*(eligible_positions(sequence, rules[name]) for name in linkers))
    observed = set().union(*(sites_by_run.get((run, accession), set()) for run in detected_runs))
    if not has_xl:
        return "linear_only", 0.0
    if not observed:
        return "xl_not_quantifiable", None
    return "xl_localized", len(observed) / len(eligible)


def matched_unique_links(accession, detected_runs, links_by_run):
    return set().union(*(links_by_run.get((run, accession), set()) for run in detected_runs))


def xl_count_thresholds(max_count):
    return sorted({n for n in (0, 1, 2, 5, 10, 15, 20) if n <= max_count}
                  | {min(20, max_count)})


def analyze(workers=3, *, include_linear=False):
    proteins, rules = load_proteins(), linker_rules()
    groups, xl_by_run, linear_files = (defaultdict(list) for _ in range(3))
    linkers_by_run = {}
    with sqlite3.connect(f"{(ROOT / 'xhamlet-results.sqlite3').as_uri()}?mode=ro", uri=True) as db:
        db.execute("BEGIN")
        for pxd, run_id, config, relative, checksum, *match in db.execute(QUERY):
            groups[(ROOT / "store" / pxd / relative, checksum, config, run_id)].append(match)
        if include_linear:
            for run_id, alpha, beta in db.execute(XL_ACCESSIONS):
                xl_by_run[run_id].extend(json.loads(alpha))
                xl_by_run[run_id].extend(json.loads(beta))
            for run_id, config, pxd, relative, digest in db.execute(LINEAR_ARTIFACTS):
                linkers_by_run[run_id] = configured_linker(config, rules)
                linear_files[run_id].append((ROOT / "store" / pxd / relative if relative else None, digest))
    xl_by_run = {run_id: set(ids) for run_id, ids in xl_by_run.items()}
    catalog_xl = set().union(*xl_by_run.values())
    jobs = [(path, sha, configured_linker(config, rules), matches)
            for (path, sha, config, _), matches in groups.items()]
    audit = Counter(catalog_observations=sum(len(job[-1]) for job in jobs))
    eligible, observed, sites, links, chemistries = (defaultdict(set) for _ in range(5))
    sites_by_run, links_by_run, detected = (defaultdict(set) for _ in range(3))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        linear_results = pool.map(collect_linear_group, linear_files.items())
        for (_, _, _, run_id), (matches, errors) in zip(groups, pool.map(document_matches, jobs), strict=True):
            audit.update(errors)
            for linker, sides in matches:
                endpoints = [localize(*side, proteins) for side in sides]
                if not all(endpoints):
                    audit["unlocalized_or_ambiguous"] += 1
                    continue
                pair = tuple(sorted((acc, pos) for acc, pos, _ in endpoints))
                for acc, pos, group in endpoints:
                    if acc not in proteins:
                        continue
                    links[acc].add(pair)
                    if include_linear:
                        links_by_run[run_id, acc].add(pair)
                    sites[acc].add(pos)
                    if linker is None:
                        continue
                    if linker not in chemistries[acc]:
                        eligible[acc].update(eligible_positions(proteins[acc]["sequence"], rules[linker]))
                        chemistries[acc].add(linker)
                    if group in rules[linker]:
                        observed[acc].add(pos)
                        if include_linear:
                            sites_by_run[run_id, acc].add(pos)
                    else:
                        audit["endpoint_outside_reference_rule"] += 1
                audit["localized_observations"] += 1
                if linker is None:
                    audit["localized_without_known_linker"] += 1
        if include_linear:
            audit["linear_groups_cataloged"] = len(linear_files)
            for run_id, accessions in linear_results:
                if accessions is None:
                    audit["linear_groups_missing_or_changed"] += 1
                    continue
                audit["linear_groups_used"] += 1
                for acc in accessions & proteins.keys():
                    detected[acc].add(run_id)
    for acc, row in proteins.items():
        row.update(
            unique_xl_count=len(links[acc]), unique_xl_residue_count=len(sites[acc]),
            xl_residues=sorted(sites[acc]), eligible_xl_residues=sorted(eligible[acc]),
            observed_eligible_residues=sorted(observed[acc]), linkers=sorted(chemistries[acc]),
            eligible_residue_count=len(eligible[acc]),
        )
        if include_linear:
            row["catalog_xl_associated"] = acc in catalog_xl
            row["linear_run_count"] = len(detected[acc])
            row["linear_unique_xl_count"] = len(matched_unique_links(acc, detected[acc], links_by_run))
            row["linear_xl_status"], row["linear_fraction_xl"] = (
                linear_coverage(acc, row["sequence"], detected[acc], xl_by_run,
                                linkers_by_run, sites_by_run, rules)
                if detected[acc] else ("not_detected", None)
            )
    add_coverage_fields(proteins, rules)
    return proteins, dict(audit)
