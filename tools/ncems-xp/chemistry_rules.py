"""Reagent-specific reaction-site assessment, independent of XP coefficients.

This module assesses a reported candidate against documented reaction rules. It
does not validate a mass spectrum or prove a covalent bond. Residue letters alone
never establish terminal chemistry. All functions use the Python standard library.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")
SIDE_GROUP = {
    "K": "SIDECHAIN_AMINE", "D": "SIDECHAIN_CARBOXYL",
    "E": "SIDECHAIN_CARBOXYL", "C": "SIDECHAIN_THIOL",
    "S": "SIDECHAIN_HYDROXYL", "T": "SIDECHAIN_HYDROXYL",
    "Y": "SIDECHAIN_PHENOL", "M": "SIDECHAIN_THIOETHER",
}
AMINES = frozenset({"SIDECHAIN_AMINE", "PROTEIN_NTERM", "PEPTIDE_NTERM"})
ACIDS = frozenset({"SIDECHAIN_CARBOXYL", "PROTEIN_CTERM", "PEPTIDE_CTERM"})
HYDROXYLS = frozenset({"SIDECHAIN_HYDROXYL", "SIDECHAIN_PHENOL"})
TERMINI = frozenset({"PROTEIN_NTERM", "PEPTIDE_NTERM", "PROTEIN_CTERM", "PEPTIDE_CTERM"})


def label(value):
    """Normalize punctuation only; no fuzzy or substring reagent matching."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _text(value):
    return "" if value is None else str(value).strip()


def aa(row, side):
    return _text(row.get("protein_" + side + "_aa") or row.get("aa1" if side == "a" else "aa2")).upper()


def positive_site(value):
    """Canonical positions are positive integers, not lists or rounded floats."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    text = _text(value)
    return int(text) if re.fullmatch(r"[1-9][0-9]*", text) else None


def bool_state(value):
    if value is True or value == 1:
        return True
    if value is False or value == 0:
        return False
    text = _text(value).lower()
    if text in {"true", "yes", "1", "blocked"}:
        return True
    if text in {"false", "no", "0", "unblocked", "free"}:
        return False
    return None


def load_rules(data_dir=None):
    path = (Path(data_dir) if data_dir else ROOT / "data_v33") / "chemistry_rules.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not obj.get("version") or not isinstance(obj.get("reagents"), list):
        raise ValueError("Invalid versioned chemistry rule file")
    aliases = {}
    for reagent in obj["reagents"]:
        if not reagent.get("id") or not reagent.get("family") or not reagent.get("sources"):
            raise ValueError("Reagent rule requires identity, family and sources")
        for name in [reagent["id"], *reagent.get("aliases", [])]:
            key = label(name)
            if not key or (key in aliases and aliases[key]["id"] != reagent["id"]):
                raise ValueError("Ambiguous reagent alias: " + str(name))
            aliases[key] = reagent
    return obj, aliases


def identify(row, rules=None):
    payload, aliases = rules or load_rules()
    checks = []
    for field in ("chemistry", "chemistry_raw", "linker_normalized", "search_group"):
        value = _text(row.get(field))
        if not value:
            continue
        if field == "search_group":
            value = value.rstrip("/").rsplit("/", 1)[-1]
            if re.fullmatch(r"(?:taxid_)?[0-9]+", value):
                continue
        hit = aliases.get(label(value))
        checks.append({"field": field, "reported": value, "id": hit["id"] if hit else ""})
    found = {x["id"] for x in checks if x["id"]}
    if len(found) > 1:
        status, reagent = "CONFLICTING_CHEMISTRY_LABELS", None
    elif not checks:
        status, reagent = "MISSING_CHEMISTRY", None
    elif any(not x["id"] for x in checks):
        status, reagent = "UNRESOLVED_CHEMISTRY_LABEL", None
    else:
        status = "IDENTIFIED_REPORTED_CHEMISTRY"
        reagent = next(x for x in payload["reagents"] if x["id"] == next(iter(found)))
    return {"chemistry_identity_status": status, "linker_normalized": reagent["id"] if reagent else "",
            "chemistry_family": reagent["family"] if reagent else "",
            "chemistry_sources": ";".join(reagent["sources"]) if reagent else "",
            "chemistry_identity_checks": checks}


def _kind(value, residue):
    raw = _text(value).upper().replace("-", "_").replace(" ", "_")
    aliases = {"NTERM": "PROTEIN_NTERM", "N_TERMINUS": "PROTEIN_NTERM",
               "PROTEIN_N_TERMINUS": "PROTEIN_NTERM", "PROTEIN_N_TERM": "PROTEIN_NTERM",
               "PEPTIDE_N_TERMINUS": "PEPTIDE_NTERM", "PEPTIDE_N_TERM": "PEPTIDE_NTERM",
               "CTERM": "PROTEIN_CTERM", "C_TERMINUS": "PROTEIN_CTERM",
               "PROTEIN_C_TERMINUS": "PROTEIN_CTERM", "PROTEIN_C_TERM": "PROTEIN_CTERM",
               "PEPTIDE_C_TERMINUS": "PEPTIDE_CTERM", "PEPTIDE_C_TERM": "PEPTIDE_CTERM"}
    raw = aliases.get(raw, raw)
    expected = SIDE_GROUP.get(residue, "SIDECHAIN_OTHER")
    if raw in {"", "SIDECHAIN", "SIDE_CHAIN"}:
        return expected, bool(raw)
    return raw, True


def _mod_items(value):
    """Endpoint-localized modifications only; caller must orient/filter peptide mods."""
    if value is None or value == "":
        return [], "NOT_REPORTED"
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return [], "NOT_REPORTED"
        if text.lower() in {"none", "unmodified", "no modifications", "[]"}:
            return [], "EXPLICITLY_UNMODIFIED"
        if text[:1] in "[{":
            try:
                value = json.loads(text)
            except (ValueError, TypeError):
                return [text], "UNPARSEABLE"
        else:
            value = [text]
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return [repr(value)], "UNPARSEABLE"
    return value, "EXPLICITLY_UNMODIFIED" if not value else "REPORTED"


def _modification_effect(value, group, residue):
    items, state = _mod_items(value)
    if not items:
        return "CLEAR", state
    blockers = []
    unresolved = []
    for item in items:
        if isinstance(item, dict):
            localization = _text(item.get("endpoint_localization")).upper()
            if localization and localization not in {"LOCALIZED", "CONFIRMED", "ENDPOINT_LOCALIZED"}:
                unresolved.append("ENDPOINT_MODIFICATION_LOCALIZATION_UNRESOLVED")
                continue
            text = " ".join(_text(item.get(k)) for k in ("name", "description", "modification", "accession", "residues"))
            # Modifications passed here are already localized to this endpoint.
            mass = item.get("monoisotopicMassDelta", item.get("mass_delta"))
            try:
                mass = float(mass)
                if not math.isfinite(mass):
                    mass = None
            except (ValueError, TypeError):
                mass = None
            residues = _text(item.get("residues")).upper()
            if residues and residue not in residues:
                unresolved.append("MODIFICATION_RESIDUE_SCOPE_MISMATCH")
                continue
        else:
            text, mass = _text(item), None
        lower = text.lower()
        blocked = False
        if group in AMINES:
            blocked = any(x in lower for x in ("acetyl", "carbamyl", "succinyl", "trimethyl", "dimethyl", "guanidin", "ubiquitin"))
            blocked |= mass is not None and abs(mass - 42.010565) < 0.002
        elif group == "SIDECHAIN_THIOL":
            blocked = any(x in lower for x in ("carbamidomethyl", "carbamidoethyl", "alkyl", "disulfide", "disulphide", "sulfin", "sulfon"))
            blocked |= mass is not None and abs(mass - 57.021464) < 0.002
        elif group in ACIDS:
            blocked = any(x in lower for x in ("amidat", "amide", "methyl ester", "methylester", "esterif"))
        elif group in HYDROXYLS:
            blocked = any(x in lower for x in ("phospho", "sulfat", "sulpho", "glycos", "acetyl"))
            blocked |= mass is not None and abs(mass - 79.966331) < 0.002
        if blocked:
            blockers.append("REACTIVE_GROUP_OCCUPIED_BY_MODIFICATION")
        else:
            unresolved.append("ENDPOINT_MODIFICATION_REQUIRES_REVIEW")
    if blockers:
        return "BLOCKED", ";".join(sorted(set(blockers + unresolved)))
    return "UNRESOLVED", ";".join(sorted(set(unresolved))) or "MODIFICATION_REQUIRES_REVIEW"


def endpoint(row, side):
    residue = aa(row, side)
    site = positive_site(row.get("protein_" + side + "_site", row.get("site1" if side == "a" else "site2")))
    prefix = "endpoint_" + side + "_"
    group, explicit = _kind(row.get(prefix + "kind"), residue)
    block_input = row.get(prefix + "blocked")
    blocked = bool_state(block_input)
    evidence = _text(row.get(prefix + "evidence"))
    modifications = row.get(prefix + "modifications", row.get(prefix + "mods"))
    effect, modification_note = _modification_effect(modifications, group, residue)
    reasons, assumptions = [], []
    state = "SUPPORTED_ENDPOINT"
    if residue not in STANDARD_AA or site is None:
        state = "UNRESOLVED_ENDPOINT"
        reasons.append("RESIDUE_OR_LOCALIZED_POSITION_REQUIRED")
    expected = SIDE_GROUP.get(residue, "SIDECHAIN_OTHER")
    if group not in TERMINI and group != expected:
        state = "UNRESOLVED_ENDPOINT"
        reasons.append("ENDPOINT_GROUP_RESIDUE_MISMATCH")
    if block_input not in (None, "") and blocked is None:
        state = "UNRESOLVED_ENDPOINT"
        reasons.append("UNRESOLVED_BLOCKING_STATUS")
    if blocked is True or effect == "BLOCKED":
        state = "BLOCKED_ENDPOINT"
        reasons.append("REPORTED_BLOCKED_REACTIVE_GROUP")
    elif effect == "UNRESOLVED":
        state = "UNRESOLVED_ENDPOINT"
        reasons.append(modification_note)
    if group in TERMINI:
        if not evidence or blocked is not False:
            if state != "BLOCKED_ENDPOINT":
                state = "UNRESOLVED_ENDPOINT"
            reasons.append("TERMINAL_IDENTITY_AND_FREE_GROUP_EVIDENCE_REQUIRED")
        if group in AMINES and residue == "P":
            if state != "BLOCKED_ENDPOINT":
                state = "UNRESOLVED_ENDPOINT"
            reasons.append("NTERMINAL_PROLINE_SECONDARY_AMINE_REVIEW_REQUIRED")
        # A mature/cleaved terminus may be at a canonical position other than 1;
        # explicit evidence is required, never inferred from its residue letter.
    elif not explicit and site == 1:
        if state != "BLOCKED_ENDPOINT":
            state = "UNRESOLVED_ENDPOINT"
        reasons.append("POSITION_ONE_SIDECHAIN_VERSUS_NTERMINUS_UNRESOLVED")
    elif not explicit:
        assumptions.append("SIDECHAIN_ENDPOINT_ASSUMED_FROM_RESIDUE")
    if blocked is None and modification_note == "NOT_REPORTED" and group not in TERMINI:
        assumptions.append("UNMODIFIED_REACTIVE_GROUP_ASSUMED_NOT_EXPERIMENTALLY_VERIFIED")
    if state == "SUPPORTED_ENDPOINT" and assumptions:
        state = "SUPPORTED_ENDPOINT_WITH_ASSUMPTIONS"
    return {"aa": residue, "site": site, "group": group, "status": state,
            "blocked": blocked, "evidence": evidence, "modification_status": effect,
            "modification_note": modification_note, "reasons": reasons,
            "assumptions": assumptions, "kind_was_explicit": explicit}


def assess(row, data_dir=None, rules=None):
    rules = rules or load_rules(data_dir)
    out = identify(row, rules)
    first, second = endpoint(row, "a"), endpoint(row, "b")
    out["endpoints"] = {"a": first, "b": second}
    states = {first["status"], second["status"]}
    reasons = list(dict.fromkeys(first["reasons"] + second["reasons"]))
    assumptions = list(dict.fromkeys(first["assumptions"] + second["assumptions"]))
    if "BLOCKED_ENDPOINT" in states:
        endpoint_state = "BLOCKED_ENDPOINT"
    elif "UNRESOLVED_ENDPOINT" in states:
        endpoint_state = "UNRESOLVED_ENDPOINT"
    elif assumptions:
        endpoint_state = "SUPPORTED_ENDPOINTS_WITH_ASSUMPTIONS"
    else:
        endpoint_state = "SUPPORTED_ENDPOINTS"
    status, orientation = "UNRESOLVED", ""
    identity = out["chemistry_identity_status"]
    family = out["chemistry_family"]
    a, b = first["group"], second["group"]
    if identity == "CONFLICTING_CHEMISTRY_LABELS":
        status = "CONFLICTING"
        reasons.append(identity)
    elif identity != "IDENTIFIED_REPORTED_CHEMISTRY":
        reasons.append(identity)
    elif family == "NONCOVALENT":
        status = "CONFLICTING"
        reasons.append("NONCOVALENT_SEARCH_IS_NOT_COVALENT_CROSSLINK_EVIDENCE")
    elif endpoint_state == "BLOCKED_ENDPOINT":
        status = "CONFLICTING"
    elif endpoint_state == "UNRESOLVED_ENDPOINT":
        status = "UNRESOLVED"
    elif family == "NHS_ESTER":
        if a in AMINES and b in AMINES:
            status, orientation = "SUPPORTED", "SYMMETRIC_AMINE_AMINE"
        elif a in AMINES | HYDROXYLS and b in AMINES | HYDROXYLS:
            status, orientation = "CONDITIONAL", "NHS_NONPRIMARY_ENDPOINT"
            reasons.append("STY_ENDPOINT_REACTIVITY_AND_LOCALIZATION_REQUIRE_REVIEW")
        else:
            status = "CONFLICTING"
            reasons.append("ENDPOINTS_CONFLICT_WITH_NHS_REACTION_RULE")
    elif family == "CARBODIIMIDE":
        if a in ACIDS and b in AMINES:
            status, orientation = "SUPPORTED", "A_CARBOXYL_B_AMINE"
        elif b in ACIDS and a in AMINES:
            status, orientation = "SUPPORTED", "A_AMINE_B_CARBOXYL"
        else:
            status = "CONFLICTING"
            reasons.append("EDC_REQUIRES_ONE_CARBOXYL_AND_ONE_AMINE")
    elif family == "BIS_MALEIMIDE":
        if a == b == "SIDECHAIN_THIOL":
            status, orientation = "SUPPORTED", "SYMMETRIC_THIOL_THIOL"
        else:
            status = "CONFLICTING"
            reasons.append("MALEIMIDE_RULE_REQUIRES_FREE_THIOLS")
    elif family == "NHS_MALEIMIDE":
        if a in AMINES and b == "SIDECHAIN_THIOL":
            status, orientation = "SUPPORTED", "A_AMINE_B_THIOL"
        elif b in AMINES and a == "SIDECHAIN_THIOL":
            status, orientation = "SUPPORTED", "A_THIOL_B_AMINE"
        else:
            status = "CONFLICTING"
            reasons.append("HETEROBIFUNCTIONAL_RULE_REQUIRES_AMINE_AND_THIOL")
    elif family == "NHS_DIAZIRINE":
        if a in AMINES or b in AMINES:
            status, orientation = "CONDITIONAL", "AMINE_ANCHOR_PHOTO_CAPTURE_ORIENTATION_REVIEW"
            reasons.append("PHOTO_PRODUCT_SITE_AND_ACTIVATION_REQUIRE_REVIEW")
        else:
            reasons.append("PHOTO_REAGENT_AMINE_ANCHOR_NOT_ESTABLISHED")
    else:
        reasons.append("REACTION_SPECIFIC_RULE_NOT_IMPLEMENTED")
    out.update(chemistry_status=status, endpoint_status=endpoint_state,
               reaction_orientation=orientation, chemistry_review_reason=";".join(dict.fromkeys(reasons)),
               endpoint_assumptions=";".join(assumptions),
               chemical_eligibility=status in {"SUPPORTED", "CONDITIONAL"},
               validation_status="REQUIRES_EXPERIMENTAL_VALIDATION",
               chemistry_rule_version=rules[0]["version"])
    return out
