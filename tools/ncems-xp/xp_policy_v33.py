"""Chemistry-aware XP and explicitly separate discovery geometry diagnostics.

Numeric values never establish a valid identification or PPI. The common-reference
geometry score is deliberately counterfactual and is never exported in ``xp``.
This core does not invoke a legacy scorer, install software, or contact a service.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil

from chemistry_rules import assess, load_rules, positive_site, aa, STANDARD_AA

ROOT = Path(__file__).resolve().parent
VERSION = "3.3.0-chemistry-aware-discovery"
METRIC = "JWALK_CA_SASD"
METRICS = {METRIC: METRIC, "JWALK_CA_TO_CA_SASD_ANGSTROM": METRIC}
GEOMETRY_TOLERANCE_A = 0.05  # Engineering guard, not an XP scientific parameter.
VALIDATION_STATUS = "REQUIRES_EXPERIMENTAL_VALIDATION"
BAD_MAPPING = frozenset({
    "AMBIGUOUS_OR_INVALID_PROTEIN_POSITIONS", "UNLOCALIZED_LINK_SITE",
    "UNIPROT_TO_CIF_NUMBERING_MISMATCH", "INPUT_CHECK_FAILED",
    "PEPTIDE_NOT_IN_EXPECTED_CHAIN", "PEPTIDE_REPEATED_IN_EXPECTED_CHAIN",
    "PEPTIDE_MATCHES_BOTH_CHAINS", "NOT_CROSSLINK_SEARCH_STAGE",
    "INVALID_LINK_SITE", "OUT_OF_RANGE_LINK_SITE", "PROTEIN_ACCESSION_MISMATCH",
    "PEPTIDE_RANGE_LENGTH_MISMATCH", "LINK_AA_SEQUENCE_MISMATCH", "INVALID_PEPTIDE_SEQUENCE",
})
BAD_COMPLETION = frozenset({"MODEL_FAILED", "ENGINE_FAILED", "ENGINE_RESULT_MISSING",
                            "MAPPED_CHECK_ONLY", "MAPPED_FOR_XP"})
BASE_FIELDS = [
    "xp", "xp_primary", "xp_exploratory",
    "reference_geometry_score", "mnxl2016_contribution", "mnxl2016_status",
    "mnxl2016_scope", "mnxl2016_violation_count", "mnxl2016_violation_excess_A",
    "mnxl2016_nonaccessible_count",
    "score_status", "xp_status", "xp_primary_status", "xp_exploratory_status",
    "reference_geometry_status", "scoring_convention", "validation_status",
    "review_reason", "distance_eligible", "distance_status", "geometry_qc",
    "coordinate_check", "euclidean_recomputed_A", "distance_metric", "distance_protocol",
    "geometry_mapping_status", "chemistry_status", "endpoint_status",
    "linker_normalized", "chemistry_identity_status", "chemistry_family",
    "chemistry_sources", "chemistry_evidence_status", "chemistry_evidence_origin",
    "chemistry_rule_version", "endpoint_assumptions", "reaction_orientation",
    "endpoint_a_resolved_kind", "endpoint_b_resolved_kind",
    "endpoint_a_status", "endpoint_b_status", "residue_pair_type",
    "parameter_status", "parameter_profile", "parameter_tier", "parameter_source",
    "mu_A", "sigma_A", "variance_A2", "cutoff_A", "xp_units", "score_policy_version",
    "discovery_shortlist_eligible", "discovery_scope", "legacy_xp_unverified",
    "legacy_score_status", "reference_geometry_interpretation",
]
PROFILE_FIELDS = ["profile_id", "mu_A", "sigma_A", "variance_A2", "cutoff_A", "source", "convention", "parameter_basis"]
FIELDS = BASE_FIELDS + [prefix + "_" + key for prefix in
                       ("xp_primary", "xp_exploratory", "reference_geometry") for key in PROFILE_FIELDS]


def finite_number(value):
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None
    return number if math.isfinite(number) else None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _coefficients(p):
    values = tuple(finite_number(p.get(k)) for k in ("mu_A", "sigma_A", "cutoff_A"))
    if any(x is None or x <= 0 for x in values):
        raise ValueError("Profile mean, SD and cutoff must be finite and positive")
    if "variance_A2" in p and not math.isclose(p["variance_A2"], values[1] ** 2, rel_tol=1e-12):
        raise ValueError("Variance must equal SD squared")
    return values


def normal_density(distance, mu, sigma):
    if not all(math.isfinite(x) for x in (distance, mu, sigma)) or distance < 0 or sigma <= 0:
        raise ValueError("Invalid distance or Gaussian coefficient")
    return math.exp(-0.5 * ((distance - mu) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))


def _value(distance, profile):
    mu, sigma, cutoff = _coefficients(profile)
    return normal_density(distance, mu, sigma) if distance <= cutoff else 0.0


def _profile(pid, values, source, convention, basis):
    p = {"profile_id": pid, **values, "source": source, "convention": convention, "parameter_basis": basis}
    p["variance_A2"] = p["sigma_A"] ** 2
    _coefficients(p)
    return p


def _mapping(row):
    """Localization can precede structure acquisition; scoring additionally needs mapping."""
    if str(row.get("status") or "") in BAD_MAPPING:
        return False, "SOURCE_MAPPING_REJECTED"
    for field in ("mapping_status", "site_mapping_status"):
        status = str(row.get(field) or "").upper()
        if any(x in status for x in ("AMBIGU", "MISMATCH", "UNMAPPED", "INVALID", "FAILED")):
            return False, "SOURCE_MAPPING_REJECTED"
    for side, fallback in (("a", "site1"), ("b", "site2")):
        if aa(row, side) not in STANDARD_AA or positive_site(row.get("protein_" + side + "_site", row.get(fallback))) is None:
            return False, "LOCALIZED_STANDARD_RESIDUE_PAIR_REQUIRED"
    chains = [str(row.get("chain_" + x) or "").strip() for x in ("a", "b")]
    sites = [positive_site(row.get("pdb_site_" + x)) for x in ("a", "b")]
    if all(chains) and all(x is not None for x in sites):
        if chains[0] == chains[1] and sites[0] == sites[1]:
            return False, "SAME_PHYSICAL_ENDPOINT_REJECTED"
        return True, "LOCALIZED_AND_STRUCTURE_MAPPED"
    return True, "LOCALIZED_STRUCTURE_MAPPING_REQUIRED"


def _evidence(row):
    state = str(row.get("chemistry_evidence_status") or "").strip()
    source = str(row.get("chemistry_evidence") or "").strip()
    if state == "EXPERIMENT_REAGENT_CONFIRMED" and source:
        return state
    if state == "EXPERIMENT_REAGENT_CONFIRMED":
        return "CONFIRMATION_EVIDENCE_MISSING"
    return "SEARCH_CONFIG_ASSUMPTION"


class Policy:
    def __init__(self, data_dir=None, mode="discovery"):
        if mode not in {"discovery", "strict"}:
            raise ValueError("mode must be discovery or strict")
        self.data = Path(data_dir) if data_dir else ROOT / "data_v33"
        self.mode = mode
        self.rules = load_rules(self.data)
        self.profiles = json.loads((self.data / "score_profiles.json").read_text(encoding="utf-8"))
        self.sources = json.loads((self.data / "source_catalog.json").read_text(encoding="utf-8"))
        if self.profiles.get("metric") != METRIC or self.profiles.get("distance_unit") != "angstrom" or self.profiles.get("score_unit") != "angstrom^-1":
            raise ValueError("Score profile metric or units incompatible")
        if not self.profiles.get("version") or not self.sources.get("version"):
            raise ValueError("Versioned profiles and sources required")
        for p in self.profiles["dsbu_pairs"].values():
            _coefficients(p)
        for name in ("mnxl2016", "reference_geometry"):
            p = self.profiles[name]
            variance = finite_number(p.get("variance_A2"))
            if variance is None or variance <= 0:
                raise ValueError("Positive reference variance required")
            _coefficients({**p, "sigma_A": math.sqrt(variance)})
        lengths = self.profiles["generalized_source_model"]["effective_length_A"]
        if lengths != {"K": 6.3, "S": 2.5, "T": 2.5, "Y": 6.5, "M": 1.5}:
            raise ValueError("Unsupported change to source effective-length model")

    def _profiles_for(self, chemistry):
        rid = chemistry["linker_normalized"]
        endpoints = chemistry["endpoints"]
        a, b = endpoints["a"]["aa"], endpoints["b"]["aa"]
        key = "-".join(sorted((a, b)))
        if chemistry["chemistry_status"] not in {"SUPPORTED", "CONDITIONAL"}:
            return None, None, "NO_CHEMICALLY_APPLICABLE_XP_PROFILE"
        groups = [endpoints[x]["group"] for x in ("a", "b")]
        sidechain = all(group.startswith("SIDECHAIN_") for group in groups)
        if key == "K-K" and sidechain and chemistry["chemistry_status"] == "SUPPORTED":
            if rid == "DSBU":
                p = _profile("DSBU_KK_PGK2025_TABLE_S2_LITERAL", self.profiles["dsbu_pairs"][key],
                             self.profiles["dsbu_source"], "PUBLISHED_DSBU_XP_DENSITY_ZERO_ABOVE_CUTOFF", "LITERAL_PUBLISHED_SOURCE_MODEL")
                return p, None, "SOURCE_SCOPED_PRIMARY_PROFILE_AVAILABLE"
            if rid in {"DSS", "BS3"}:
                m = self.profiles["mnxl2016"]
                p = _profile(rid + "_KK_MNXL2016_POSITIVE_COMPONENT", {"mu_A": m["mu_A"], "sigma_A": math.sqrt(m["variance_A2"]), "cutoff_A": m["cutoff_A"]},
                             m["source"], "XP_ZERO_CUTOFF_ADAPTATION_OF_MNXL2016", "PUBLISHED_COEFFICIENTS_EXPLICIT_ZERO_CUTOFF_ADAPTATION")
                return p, None, "SOURCE_SCOPED_PRIMARY_PROFILE_AVAILABLE"
        # Source lengths are residue/endpoint conventions. A lysine N terminus
        # cannot silently borrow the lysine sidechain's6.3 angstrom constant.
        terminal_m = False
        for ep in endpoints.values():
            if ep["group"].startswith("SIDECHAIN_"):
                continue
            if ep["aa"] == "M" and ep["group"] in {"PROTEIN_NTERM", "PEPTIDE_NTERM"} and ep["evidence"]:
                terminal_m = True
            else:
                return None, None, "TERMINAL_ENDPOINT_PARAMETER_CONVENTION_UNSUPPORTED"
        if rid == "DSBU" and key in self.profiles["dsbu_pairs"]:
            p = _profile("DSBU_" + key.replace("-", "") + "_PGK2025_TABLE_S2_EXPLORATORY", self.profiles["dsbu_pairs"][key],
                         self.profiles["dsbu_source"], "PUBLISHED_DSBU_XP_DENSITY_ZERO_ABOVE_CUTOFF",
                         "PUBLISHED_PARAMETERS_CONDITIONAL_ENDPOINT_SCOPE")
            if terminal_m:
                p["parameter_basis"] += ";M_TERMINAL_MODEL_CONVENTION_REQUIRES_AUTHOR_CONFIRMATION"
            return None, p, "CONDITIONAL_SOURCE_PROFILE_EXPLORATORY_ONLY"
        model = self.profiles["generalized_source_model"]
        lengths = model["effective_length_A"]
        if rid not in model["spacer_length_A"] or a not in lengths or b not in lengths:
            return None, None, "NO_MATCHING_XP_PARAMETERS"
        offset = model["spacer_length_A"][rid] - model["baseline_spacer_A"]
        mu = 18.6 + offset + lengths[a] + lengths[b] - 12.6
        sigma = (mu - 0.6) / 3.0
        cutoff = 33.0 + offset + mu - (18.6 + offset)
        p = _profile("SOURCE_SCORE_XL_" + rid + "_" + key.replace("-", "") + "_HEURISTIC",
                     {"mu_A": mu, "sigma_A": sigma, "cutoff_A": cutoff}, model["source"] + ";" + model["spacer_sources"][rid],
                     "SOURCE_EQUATION_HEURISTIC_TRANSFER_ZERO_CUTOFF", model["status"])
        if terminal_m:
            p["parameter_basis"] += ";M_TERMINAL_MODEL_CONVENTION_REQUIRES_AUTHOR_CONFIRMATION"
        return None, p, "GENERALIZED_SOURCE_MODEL_EXPLORATORY_ONLY"

    def decision(self, row):
        chemistry = assess(row, rules=self.rules)
        primary, exploratory, parameter_status = self._profiles_for(chemistry)
        evidence = _evidence(row)
        review = [chemistry["chemistry_review_reason"]]
        if evidence != "EXPERIMENT_REAGENT_CONFIRMED":
            review.append(evidence)
            if primary:
                exploratory, primary = dict(primary), None
                exploratory["parameter_basis"] += ";EXPERIMENT_REAGENT_NOT_CONFIRMED"
                parameter_status = "KNOWN_PROFILE_UNDER_SEARCH_CHEMISTRY_ASSUMPTION"
        localized, mapping = _mapping(row)
        metric = METRICS.get(str(row.get("distance_metric") or METRIC), "")
        eligible = localized and bool(metric) and (self.mode == "discovery" or primary is not None)
        if not localized:
            review.append(mapping)
        if not metric:
            review.append("INCOMPATIBLE_DISTANCE_METRIC")
        if self.mode == "strict" and primary is None:
            review.append("STRICT_MODE_REQUIRES_PRIMARY_PROFILE")
        if exploratory:
            review.append(exploratory["parameter_basis"])
        if not primary and not exploratory:
            review.append(parameter_status)
        out = {k: chemistry[k] for k in ("chemistry_status", "endpoint_status", "linker_normalized", "chemistry_identity_status",
                                        "chemistry_family", "chemistry_sources", "chemistry_rule_version", "endpoint_assumptions", "reaction_orientation")}
        out.update(chemistry_evidence_status=evidence,
                   chemistry_evidence_origin="DECLARED_EVIDENCE_NOT_INDEPENDENTLY_VALIDATED" if evidence == "EXPERIMENT_REAGENT_CONFIRMED" else "SEARCH_CONFIGURATION_ONLY",
                   residue_pair_type="-".join(sorted((aa(row, "a"), aa(row, "b")))),
                   distance_eligible=eligible, distance_metric=metric or str(row.get("distance_metric") or ""),
                   geometry_mapping_status=mapping, parameter_status=parameter_status,
                   primary_profile=primary, exploratory_profile=exploratory,
                   validation_status=VALIDATION_STATUS, score_policy_version=VERSION,
                   review_reason=";".join(dict.fromkeys(x for x in review if x)),
                   discovery_shortlist_eligible=False,
                   discovery_scope="LOCALIZED_GEOMETRY_CANDIDATE_NOT_VALIDATED_XL_OR_PPI",
                   chemistry_identity_checks=chemistry["chemistry_identity_checks"],
                   endpoint_details=chemistry["endpoints"])
        for side in ("a", "b"):
            out["endpoint_" + side + "_resolved_kind"] = chemistry["endpoints"][side]["group"]
            out["endpoint_" + side + "_status"] = chemistry["endpoints"][side]["status"]
        return out

    @staticmethod
    def _put_profile(out, prefix, p):
        if p:
            for field in PROFILE_FIELDS:
                out[prefix + "_" + field] = p.get(field, "")

    def evaluate(self, row, diagnostic=None):
        diagnostic = diagnostic or {}
        out = dict(row)
        for field in FIELDS:
            out[field] = ""
        out["legacy_xp_unverified"] = row.get("xp", "")
        out["legacy_score_status"] = row.get("score_status", row.get("xp_status", row.get("status", "")))
        dec = self.decision(row)
        out.update({k: v for k, v in dec.items() if k in FIELDS})
        out.update(xp_units="angstrom^-1", score_status="UNSCORED", xp_status="UNSCORED",
                   xp_primary_status="NO_PRIMARY_SCORE", xp_exploratory_status="NO_EXPLORATORY_SCORE",
                   reference_geometry_status="NO_USABLE_GEOMETRY", mnxl2016_status="OUTSIDE_ORIGINAL_MNXL_SCOPE",
                   reference_geometry_interpretation="COUNTERFACTUAL_REFERENCE_GEOMETRY_NOT_XP_OR_CHEMICAL_VALIDITY")
        primary, exploratory = dec["primary_profile"], dec["exploratory_profile"]
        mnxl_scoped = primary is not None and dec["linker_normalized"] in {"DSS", "BS3"}
        out["mnxl2016_scope"] = "CONFIRMED_DSS_BS3_KK_SOURCE_SCOPE" if mnxl_scoped else "OUTSIDE_CONFIRMED_DSS_BS3_KK_SCOPE"
        if mnxl_scoped:
            out["mnxl2016_status"] = "SCOPED_BUT_USABLE_GEOMETRY_NOT_ESTABLISHED"
        self._put_profile(out, "xp_primary", primary)
        self._put_profile(out, "xp_exploratory", exploratory)
        selected = primary or exploratory
        if selected:
            out.update(parameter_profile=selected["profile_id"], parameter_source=selected["source"],
                       parameter_tier="SOURCE_SCOPED" if primary else "EXPLORATORY",
                       mu_A=selected["mu_A"], sigma_A=selected["sigma_A"], variance_A2=selected["variance_A2"],
                       cutoff_A=selected["cutoff_A"], scoring_convention=selected["convention"])
        reasons = [out["review_reason"]]
        def reject(reason, distance_status=None):
            out["score_status"] = out["xp_status"] = reason
            out["distance_status"] = distance_status or reason
            out["review_reason"] = ";".join(dict.fromkeys(x for x in reasons + [reason] if x))
            return out
        if dec["geometry_mapping_status"] != "LOCALIZED_AND_STRUCTURE_MAPPED":
            return reject("MAPPING_REQUIRED_OR_REJECTED")
        if str(row.get("status") or "") in BAD_COMPLETION:
            return reject("SOURCE_DISTANCE_NOT_COMPLETED")
        if dec["distance_metric"] != METRIC:
            return reject("INCOMPATIBLE_DISTANCE_METRIC")
        distance = finite_number(row.get("sasd_A"))
        usable_distance = distance is not None and distance >= 0
        backend_reason = str(diagnostic.get("reason") or "")
        # An absent path is not evidence of nonaccessibility. Only an explicit
        # backend accessibility result can select the original MNXL penalty.
        # A malformed/nonfinite numeric input is never reinterpreted as a path result.
        missing_sentinel = row.get("sasd_A") in (None, "") or distance == -1
        explicit_nonaccessible = (mnxl_scoped and missing_sentinel and backend_reason in {
            "ACCESSIBILITY_FILTER_REJECTED", "BACKEND_LOG_REPORTED_NONACCESSIBLE"})
        if not usable_distance and not explicit_nonaccessible:
            return reject("NO_USABLE_SASD", backend_reason or "MISSING_NEGATIVE_OR_NONFINITE_SASD")
        out["distance_status"] = "SASD_RETURNED" if usable_distance else backend_reason
        coordinate_check = diagnostic.get("coordinate_check", row.get("coordinate_check", ""))
        out["coordinate_check"] = coordinate_check
        out["distance_protocol"] = diagnostic.get("distance_protocol", row.get("distance_protocol", "UNSPECIFIED_DISTANCE_PROTOCOL"))
        euclidean = finite_number(diagnostic.get("euclidean_recomputed_A", row.get("euclidean_recomputed_A", row.get("euclidean_A"))))
        out["euclidean_recomputed_A"] = euclidean if euclidean is not None else ""
        flags = []
        pass_flags = {"", "PASS", "OK", "NONE", "FALSE", "0", "GEOMETRY_OK", "EUCLIDEAN_RECHECK_PASSED"}
        for field in ("geometry_flag", "geometry_qc", "coordinate_flag"):
            for flag in str(row.get(field) or "").split(";"):
                if flag.strip().upper() not in pass_flags:
                    flags.append(flag.strip())
        if coordinate_check != "EUCLIDEAN_RECHECK_PASSED":
            flags.append("COORDINATE_RECHECK_REQUIRED_OR_FAILED")
        if euclidean is None or euclidean <= 0:
            flags.append("EUCLIDEAN_UNAVAILABLE_OR_NONPOSITIVE")
        elif usable_distance and distance + GEOMETRY_TOLERANCE_A < euclidean:
            flags.append("SASD_BELOW_EUCLIDEAN_REVIEW")
        reported = finite_number(row.get("euclidean_A"))
        if reported is not None and euclidean is not None and abs(reported - euclidean) > GEOMETRY_TOLERANCE_A:
            flags.append("REPORTED_VERSUS_RECOMPUTED_EUCLIDEAN_MISMATCH")
        if flags:
            out["geometry_qc"] = ";".join(dict.fromkeys(flags))
            reasons.append(out["geometry_qc"])
            return reject("DISTANCE_QC_REVIEW")
        if not usable_distance:
            out["mnxl2016_contribution"] = self.profiles["mnxl2016"]["violation_penalty"]
            out["mnxl2016_nonaccessible_count"] = 1
            out["mnxl2016_status"] = "ORIGINAL_PENALTY_FOR_EXPLICIT_BACKEND_NONACCESSIBILITY_NOT_EXPERIMENTAL_VALIDATION"
            reasons.append("MNXL_NONACCESSIBILITY_IS_BACKEND_EVIDENCE_NOT_A_MEASURED_DISTANCE")
            return reject("NO_USABLE_SASD", backend_reason)
        # Uniform diagnostic is emitted for every usable mapped candidate. This
        # is a common-reference shape, never the unparameterized reagent's XP.
        r = self.profiles["reference_geometry"]
        reference = _profile(r["profile_id"], {"mu_A": r["mu_A"], "sigma_A": math.sqrt(r["variance_A2"]), "cutoff_A": r["cutoff_A"]},
                             r["source"], "COUNTERFACTUAL_COMMON_REFERENCE_ZERO_CUTOFF", r["status"])
        self._put_profile(out, "reference_geometry", reference)
        out["reference_geometry_score"] = _value(distance, reference)
        out["reference_geometry_status"] = "COUNTERFACTUAL_DIAGNOSTIC_ONLY"
        if dec["chemistry_status"] == "CONFLICTING":
            out["reference_geometry_status"] = "CHEMISTRY_CONFLICT_DIAGNOSTIC_EXCLUDED_FROM_SHORTLIST"
        out["discovery_shortlist_eligible"] = dec["chemistry_status"] in {"SUPPORTED", "CONDITIONAL"}
        if primary:
            out["xp"] = out["xp_primary"] = _value(distance, primary)
            out["xp_primary_status"] = "SOURCE_SCOPED_SCORE" if distance <= primary["cutoff_A"] else "SOURCE_SCOPED_ABOVE_CUTOFF_ZERO"
            out["score_status"] = out["xp_status"] = "PRIMARY_SOURCE_SCOPED_NOT_VALIDATED"
        elif exploratory and self.mode == "discovery":
            out["xp_exploratory"] = _value(distance, exploratory)
            out["xp_exploratory_status"] = "EXPLORATORY_MODEL_NOT_VALIDATED"
            out["score_status"] = out["xp_status"] = "EXPLORATORY_ONLY_NOT_PRIMARY"
        else:
            out["score_status"] = out["xp_status"] = "REFERENCE_GEOMETRY_ONLY_NOT_XP"
            if exploratory:
                out["xp_exploratory_status"] = "SUPPRESSED_IN_STRICT_MODE"
        # Exact original MNXL contribution stays distinct from the XP adaptation.
        if mnxl_scoped:
            m = self.profiles["mnxl2016"]
            out["mnxl2016_contribution"] = normal_density(distance, m["mu_A"], math.sqrt(m["variance_A2"])) if distance <= m["cutoff_A"] else m["violation_penalty"]
            out["mnxl2016_violation_count"] = int(distance > m["cutoff_A"])
            out["mnxl2016_violation_excess_A"] = max(0.0, distance - m["cutoff_A"])
            out["mnxl2016_nonaccessible_count"] = 0
            out["mnxl2016_status"] = "ORIGINAL_PAPER_SINGLE_LINK_CONTRIBUTION_NOT_COMPLETE_MODEL_SCORE"
        return out

    def manifest(self):
        return {"version": VERSION, "mode": self.mode, "metric": METRIC,
                "chemistry_rule_version": self.rules[0]["version"], "profile_version": self.profiles["version"],
                "validation_status": VALIDATION_STATUS,
                "source_files_sha256": {name: sha(self.data / name) for name in ("chemistry_rules.json", "score_profiles.json", "source_catalog.json")},
                "software_sha256": {name: sha(ROOT / name) for name in ("chemistry_rules.py", "xp_policy_v33.py")},
                "scope": "Primary source-scoped models, separate exploratory values and counterfactual geometry; no numerical field validates XL/PPI."}

    def snapshot(self, dest):
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=False)
        for name in ("chemistry_rules.json", "score_profiles.json", "source_catalog.json"):
            shutil.copy2(self.data / name, dest / name)
        (dest / "manifest.json").write_text(json.dumps(self.manifest(), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        return dest
