# NCEMS XP v3.3 — chemistry-aware discovery

Release prepared November 19, 2026. This separate XP candidate package is designed
for all previously attempted PXDs. Computational checks do not establish scientific
validation. Read `PREFLIGHT_AND_RERUN.txt` for setup and the two-job rerun queue.

## Purpose and preserved workflow

Keep reported candidate crosslinks available for established and exploratory
analysis, without assigning chemical validity merely because a distance can be
inserted into an equation. The user-facing input remains a PXD. Existing ReLink
exports, scan maps, the AF3 catalog, pair metadata and structures remain the inputs.
This package does not re-search spectra or run ReLink.

The existing xHAMLET/ReLink installation, original XP engine, Conda environments,
input data and prior result folders remain unchanged. New code, plans, ledgers and
results use a separate directory on the mounted fixed volume:

`/media/volume/xhamlet-data-5/NCEMS_XP_v33/`

## Three distinct numerical outputs

| Output | Meaning | Eligibility |
| --- | --- | --- |
| `xp_primary` and identical alias `xp` | Source-scoped chemistry/model score | Compatible endpoints, suitable source profile, declared experimental reagent evidence, and passed geometry checks |
| `xp_exploratory` | Known profile under an unconfirmed search-chemistry assumption, conditional source context, or documented source-equation transfer | Scope and assumptions recorded; never promoted to primary automatically |
| `reference_geometry_score` | The same explicitly counterfactual geometry reference for every usable candidate | Localized, mapped and coordinate-checked distance; unsupported chemistry may retain this diagnostic |

Every score retains a validation status requiring experimental assessment. A primary
score is not a validated XL identification, calibrated probability, or proven PPI.
Known chemistry conflicts retain an audit diagnostic and are excluded from the
chemistry-supported discovery shortlist. Unknown chemistry remains in the review
queue, including when a numerical output is unavailable.

An unknown protein partner using an established reaction can use an existing scoped
profile. An unknown covalent reaction needs chemical and spectral evidence before
a chemistry-specific XP model can be justified.

## Equation and explicit parameter conventions

For a usable solvent-accessible surface distance `d`, the positive-component score
is `exp(-0.5*((d-mu)/sigma)^2)/(sigma*sqrt(2*pi))` at or below the profile cutoff,
and zero above that cutoff. Units are inverse angstrom, not probability.

| Profile | Mean, Å | SD, Å | Cutoff, Å | Status |
| --- | ---: | ---: | ---: | --- |
| DSBU K–K | 19.7 | 6.4 | 34.1 | Literal supplied/published DSBU profile within its declared scope |
| DSS/BS3 K–K | 18.62 | sqrt(35.94) | 33 | Explicit XP zero-cutoff adaptation of original MNXL's positive component |
| Common geometry reference | 18.62 | sqrt(35.94) | 33 | Uniform counterfactual benchmark; not fitted to unknown chemistry |

The original MNXL negative penalty is separate from zero-cutoff XP. Scoped
single-link contributions, number of violations (NoV), sum of violation distances
(SoVD) and explicit backend nonaccessibility counts are retained. They are not a
complete ensemble-normalized MNXL model score. A missing path is not automatically
a violation, zero or confirmed nonaccessibility.

The six-row supplied DSBU table is retained with its source context. Other eligible
source-supported cases remain conditional/exploratory. The generalized source
algebra uses effective lengths only for K/S/T/Y/M; no constants are invented for
other residue types. Inclusion in a source dictionary does not prove reactivity.
The algebra imposes `mu - 3*sigma = 0.6 Å`; it does not estimate uncertainty from
these new observations. DSSO exploratory transfer uses the manufacturer's 10.3 Å
spacer convention, explicitly reconciled against the legacy 10.1 Å value.

The common reference describes geometry with a fixed ruler. Its peak near 18.62 Å
does not establish that an unknown reaction is most likely there; zero above 33 Å
does not establish impossibility for an unknown or longer linker. Raw SASD and
Euclidean distances remain available. Compare different profile scores cautiously:
different Gaussian widths have different peak densities.

## Chemistry and mapping corrections

- Reagent family and reactive endpoint groups determine compatibility. All amino-acid
  label combinations are not treated as a list of valid covalent reactions.
- Search-group labels are retained as search assumptions. They do not independently
  confirm the reagent used in the sample.
- Free termini require explicit endpoint evidence. M never implies a free N terminus;
  position 1 alone does not identify the reactive group. Contradictory terminal labels
  and peptide link positions remain unresolved.
- Isoform suffixes remain intact. Canonical coordinate projection is not invented.
- The entire matched peptide must have consistent sequence and residue numbering in
  the expected chain. Homomer assignments and ambiguous mappings remain for review.
- Alpha/beta orientation follows endpoint modifications. Unrelated peptide modifications
  are not treated as modifications of the linked residue. Unknown localization stays
  unresolved. Terminal modifications near an unspecified endpoint are conservative
  review cases and may need manual interpretation.
- Modified and unmodified contexts at the same coordinates stay distinct. Geometry
  can be calculated once and reused for these distinct reaction contexts.
- Geometry runs for every localized, mapped observed pair, regardless of parameter
  availability. It does not enumerate hypothetical links between all residues.

## Distance implementation

The existing legacy engine is loaded only when its SHA256 is:

`4fb72ee71b6b050831a2bdf6a59e0629fd190074af1afa11e23661dba5ec3821`

Installed NCLEdetector/Jwalk modules remain unchanged. The adapter uses the existing
1 Å grid and finite 50 Å search, records module hashes and accessibility diagnostics,
and exports distances with blank legacy XP. New scores come only from the v3.3
policy. This is not an unlimited-search reproduction of the original paper.

Independent C-alpha arithmetic checks verify Euclidean distance and structure hash.
A SASD below the Euclidean lower bound beyond the documented engineering tolerance
is flagged, not clipped. This arithmetic check does not recompute the surface path.

## Outputs and accounting

- `xp_unique_pairs.csv`: model-specific observed structural pairs and distinct
  search/reaction/modification contexts, with all score channels and provenance.
- `xp_observations.csv`: supporting model observations, original peptide modification
  arrays, raw row JSON, oriented endpoints, source indexes and score statuses.
- `unmatched_observations.csv`: original observations lacking a stored AF3 pair match.
- `novelty_review_queue.csv`: all mapped contexts plus unresolved/unmatched records;
  a number is never required for a candidate to remain in the audit.
- `model_summary.csv`: computational states, counts and scoped ancillary diagnostics.
- `score_statistics.csv`: descriptive statistics separated by model, chemistry,
  channel and profile. Sample SD is not model sigma, standard error or a confidence interval.
- `run_summary.json`: source-row reconciliation, model failures, score counts and scope.
- `launch_manifest.json`, `reference_snapshot/`, `input_artifact_manifest.json`:
  source commit, software, parameter and copied-input provenance.
- `NCEMS_XP_v33_results.zip`: shareable tables and provenance. Complete copied inputs,
  structures and backend logs remain in the adjacent `distance_run/` directory.

One source row may occur in several stored models. Accounting uses original source
indexes so model copies are not mistaken for new observations. Blank means
missing/unscored; numeric zero means above an applicable reference cutoff. Repeated
spectra do not multiply unique-context scores in descriptive summaries.

## Experimental reagent evidence

The normal PXD input is unchanged. By default, a scan-map linker is a hypothesis.
Known-profile values remain available as exploratory scores until experiment-specific
reagent evidence is supplied. An optional JSON with schema
`NCEMS_EXPERIMENTAL_CONTEXT_V1` can record reviewed evidence for exact PXD/search-group
matches. The shipped `experimental_context.example.json` has no entries and confirms
no real experiments. Required record fields are pxd, search_group, chemistry,
chemistry_evidence_status and chemistry_evidence, all strings. A confirmed status
requires a specific source describing that reagent in that experimental context.

This declaration does not validate spectra. Conflicting labels remain for review.
A citation alone does not calibrate a new linker or confirm a candidate observation.

## Rerun scope

The planner inventories prior XP completed, failed and blocked attempts, including
bounded archive metadata, and reports uncertain records and coverage gaps. The
queue runs the confirmed inventory two PXDs at a time against one frozen Git commit
with a frozen production package, new folders and a durable attempt ledger.

The original 535-PXD list, Ian's 112-assignment exclusion and attempted-PXD exclusions
continue to govern new ReLink dataset selection. The current user-authorized XP
rerun intentionally includes prior XP attempts. It launches no new ReLink datasets.

Old v3.1/v3.2 filtered geometry is not automatically reused. `--from-v33` is limited
to explicit complete v3.3 intake with preserved contexts and full accounting. An
identical installation may be reused; different existing bytes are never overwritten.
The fixed volume must actually be mounted before installation or queued writes.

Published GitHub exports alone do not prove that a particular ReLink run passed
every success criterion. The launch manifest records this provenance limit.

## Verification and scientific limits

See `VALIDATION_REPORT.json` and `VALIDATION_NOTES.txt`. Synthetic checks exercise
equations, chemistry states, mapping, retention, subprocess integration and queue
behavior. Fake-backend fixtures are labelled and remain under `tests/`. They are
never scientific PXD results.

Live Jetstream execution and real Jwalk/PXD results must be assessed after rerunning.
Spectral quality, precursor/product masses, localization, appropriate false-discovery
control, alternatives and controls remain necessary for novel covalent-link claims.
This package preserves xi_score/raw evidence; it does not compute missing FDR or
invent experimental validation. AF3 geometry alone cannot establish a true interaction.

## Sources

`data_v33/source_catalog.json` maps active source identifiers to papers, manufacturer
records, vocabularies and supplied documents. Key sources:

- Bullock et al. 2016, DOI 10.1074/mcp.M116.058560 (original MNXL).
- Supplied DSBU coefficients and 2025 supplementary Table S2, DOI 10.1126/sciadv.ads7379.
- NCLEdetector score_XL source commit 9e3d4ed198c45e04b9aae6f53ec6f0e3e920cd4a
  (generalized algebra only, not proof that a site is reactive).
- Thermo DSS/BS3, DSSO/DSBU, EDC, bismaleimide and SMCC documentation; cited primary
  NHS-hydroxyl, localization and photochemistry papers.

The original v3.2 archive remains unchanged. Its SHA256 is
`93b17b75a3d22ca909d4772ddacb08954819897539da400f20072e5328995527`.
The candidate removes the old executable scoring path; compatibility launchers route
to v3.3. Previous results remain historical records and are not rewritten.
