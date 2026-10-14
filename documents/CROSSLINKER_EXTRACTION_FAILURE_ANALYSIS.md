# Crosslinker Extraction Failure Analysis

## Purpose

After the full 1044-PXD reanalysis (`--no-relink`, refreshed LLM extraction + SDRF +
Xi config generation), **391 of 1045 PXDs (37.4%)** ended up with no crosslinker
reagent extracted at all (`comment[cross-linker]` empty/null, or every mention
rejected as `not_a_crosslinker`).

This document tracks a manual, PXD-by-PXD spot-check investigation into *why*
each sampled PXD failed, to build up a reliable picture of the failure-mode
distribution before deciding what (if anything) is worth fixing in the
pipeline vs. simply being an unavoidable floor given the input data.

**Method:** each batch draws a reproducible random sample (seeded) from the
full 391-PXD null set, excluding PXDs already checked in a prior batch. For
each PXD we pull the real PRIDE metadata (and PMC full text, when cached) that
was actually sent to the LLM, and classify the failure into one of:

- **CORRECT_REJECT** — the dataset is not actually a chemical crosslinking-MS
  study (e.g. proximity labeling: TurboID/BioID/APEX), so null is the right
  answer; nothing to fix.
- **CORRECT_REJECT_NO_TEXT** — the dataset may be a real XL-MS study, but the
  available text (PMC and/or PRIDE) never names a specific reagent at all
  (e.g. "cross-linking chemistry" stated generically, protocol marked "Not
  available") — null is the right answer given the available text, though a
  better/fuller text source (if one exists) might change that.
- **REAL_MISS** — the reagent *is* explicitly named in the text actually sent
  to the LLM, but extraction still returned null. A genuine extraction bug or
  gap, worth investigating further.

## Headline finding so far (Batch 1)

**The single largest cause of "no crosslinker extracted" in this corpus is not
a pipeline bug — it's dataset-list contamination.** A large fraction of the
391 null PXDs are **proximity-labeling studies (TurboID / BioID / APEX /
biotin-phenol)**, not chemical crosslinking-MS studies at all. These were
*correctly* rejected by the (intentionally strict) extraction rules — there is
no chemical crosslinking reagent to find because the technique itself doesn't
use one.

A full-corpus keyword scan (`turboid|bioid|apex2?\b|biotin-phenol|biotin-tyramide|
proximity-labeling|proximity-biotinylation|proximity-dependent` against each
PXD's PRIDE title+description+protocol+keywords) found:

| | Count | % of 391 |
|---|---:|---:|
| Matches a proximity-labeling keyword | **332** | **84.9%** |
| No proximity-labeling keyword match | 59 | 15.1% |

This strongly suggests `assets/crosslinking_datasets_list.tsv` (the master
1044-PXD list driving the whole reanalysis) was built from a PRIDE search that
was **not filtered strictly enough to exclude proximity-labeling studies** —
plausible, since PRIDE search terms like "crosslink"/"protein-protein
interaction" are shared loosely between the two adjacent-but-distinct fields.
(Supporting evidence: literally the *first* row of that TSV, `PXD038515`, is
titled "TurboID reveals the interaction network of VESICLE-INDUCING PROTEIN IN
PLASTIDS...".) No record of how/when the list was originally built was found
in git history — it was present in the initial commit with no accompanying
build script or query documented.

**Implication:** most of the 391 "failures" are not something to fix in the
*extraction* pipeline at all — they're PXDs that arguably should never have
been in the reanalysis target list in the first place. The remaining ~15%
(the non-proximity-labeling null PXDs) is where genuine extraction misses are
concentrated and worth continued spot-checking.

---

## Batch 1 — 2026-10-14 (10 PXDs, seed=42)

Random sample drawn from the full 391-PXD null set (`random.seed(42)`,
`random.sample(null_pxds, 10)`).

| PXD | Has PMC? | Proximity-labeling keyword? | Verdict | Reason |
|---|---|---|---|---|
| PXD054616 | No | Yes (TurboID) | CORRECT_REJECT | "Using proximity labeling by turboID (biotin ligase) fused with PAICS..." — TurboID proximity labeling, no chemical crosslinker used. |
| PXD015725 | Yes | Yes (BioID, via keywords) | CORRECT_REJECT | "Wnt activator FOXB2..." — BioID proximity-dependent biotinylation study (FOXB2 interactome via BioID). No crosslink-related keyword anywhere in the 22K-char combined PMC+PRIDE text. |
| PXD005758 | No | Yes (APEX) | CORRECT_REJECT | "A method for spatially and temporally resolved protein network interrogation..." — explicitly APEX-mediated proximity labeling (engineered ascorbic acid peroxidase + biotinylation), not chemical crosslinking. |
| **PXD063839** | No | **No** | **REAL_MISS** | Title: "In cellulo cysteine umpolung for protein structure probing: XL LC-MS/MS Data". `sampleProcessingProtocol` explicitly states *"Cells were treated with **VTT**, lysed..."* — VTT = vinyl thianthrenium tetrafluoroborate, a genuine, very recently published (Hartmann et al., *J. Am. Chem. Soc.* 2025, 147, 39, 35587–35594) single-step in-cellulo cysteine-umpolung crosslinking reagent. The LLM was given this exact text (verified by reconstructing the real combined-text payload) and still returned null. See root-cause analysis below. |
| PXD031197 | No | Yes (TurboID) | CORRECT_REJECT | "TurboID-based proximity labeling to identify LONP1-targeting proteins" — TurboID, no chemical crosslinker. |
| PXD027917 | No | Yes (BioID) | CORRECT_REJECT | "A proximity interactome map of the VAC14-FIG4 complex using BioID" — BioID (birA fusion), no chemical crosslinker. |
| PXD026196 | No | Yes (BioID/TurboID) | CORRECT_REJECT | "BioID-screening reveals the Alk 'proximitome'..." — BioID/miniTurbo proximity labeling. (Note: this PXD's PRIDE text separately contains the literal word "linear" in an unrelated sentence — a reminder that simple keyword string-matching for QA purposes, as used in some of our own diagnostic scripts, is itself fragile; this did not affect the real LLM-based extraction, only a crude keyword-scan side-check.) |
| PXD017937 | No | Yes (BioID2) | CORRECT_REJECT | "Identifying interactors through BioID2 in rat cortical neurons" — BioID2, no chemical crosslinker. |
| PXD062890 | Yes | Yes (TurboID) | CORRECT_REJECT | "Immunoprecipitation of U2AF2-TurboID-HA" — TurboID + co-IP comparison study, no chemical crosslinker. |
| PXD014500 | Yes | Yes (APEX2/biotin-phenol, via keywords) | CORRECT_REJECT | "Molecular basis of b-adrenergic regulation of cardiac calcium current" — APEX2/biotin-phenol-H2O2 proximity labeling (the one "formaldehyde" mention found in full text is a 4% PFA microscopy fixation step for imaging, unrelated to the MS crosslinking workflow). |

**Batch 1 summary:** 9/10 CORRECT_REJECT (all proximity labeling), 1/10
REAL_MISS (PXD063839 / VTT).

### Root-cause analysis: PXD063839 (VTT miss)

Reconstructed the *exact* text payload actually sent to the LLM for this PXD
(no PMC available; PRIDE-only, 1314 chars total). It unambiguously states:

> "In-Cellulo Crosslinking with Different Cell Types: **Cells were treated
> with VTT**, lysed, and the protein concentration was determined using a BCA
> assay..."

Likely contributing factors (not yet fixed, just diagnosed):
1. **Bare, unexpanded abbreviation.** Unlike the vast majority of reagent
   mentions elsewhere in this corpus (which are almost always written as
   `full chemical name (ABBREV)`, e.g. "pimelic acid dihydrazide (PDH)"), VTT
   appears completely bare with no full name, no parenthetical expansion, and
   no further chemical description anywhere in the available text. The
   extraction prompt's instructions and examples lean on exactly that
   full-name/abbreviation pairing as the strongest signal of "this is a named
   chemical reagent."
2. **Very recent chemistry, likely outside training data.** VTT
   (vinyl thianthrenium tetrafluoroborate) was only published in 2025
   (Hartmann et al., JACS) — a model may have no prior association between the
   bare string "VTT" and crosslinking chemistry to draw on, unlike well-known
   abbreviations (DSS, BS3, DSSO) it may recognize from pretraining alone.
3. **Not yet in our curated reference database.** The `{{CROSSLINKER_DATABASE}}`
   block injected into the prompt (see `prompts/xlms_reagents.txt`) is meant to
   catch exactly this kind of case by giving the model a list of known reagents
   to check against — but VTT isn't in `assets/crosslinker_definitions.json`
   yet, so the reference list offers no help here. (This is itself a reminder
   that our curated DB needs occasional refreshes as new chemistries get
   published, separately from the normalization-script workflow which only
   catches reagents *already* mentioned somewhere in our own corpus.)

No prompt/code changes made yet from this single data point — flagging for
awareness and will revisit if future batches turn up a similar pattern (bare,
un-expanded abbreviations for brand-new reagents).

---

## Running totals (all batches)

| Batch | n | CORRECT_REJECT (prox. labeling) | CORRECT_REJECT (other/no-text) | REAL_MISS |
|---|---:|---:|---:|---:|
| 1 | 10 | 9 | 0 | 1 |
| **Total** | **10** | **9** | **0** | **1** |

PXDs checked so far (excluded from future batches' sampling pool):
PXD054616, PXD015725, PXD005758, PXD063839, PXD031197, PXD027917, PXD026196,
PXD017937, PXD062890, PXD014500.

## Open questions for future batches

- Does the ~15.1% "non-proximity-labeling null" bucket (59 of 391) contain more
  `REAL_MISS` cases like VTT, or is it dominated by other legitimate
  `CORRECT_REJECT_NO_TEXT` cases (generic "cross-linking chemistry" with no
  named reagent, as seen in PXD000545 during the original statistics
  investigation)? Worth biasing a future batch's sample toward this subset
  specifically, since it's where genuine misses are concentrated.
- Should `assets/crosslinking_datasets_list.tsv` be re-filtered to exclude
  proximity-labeling studies, given ~85% of the null bucket (and an unknown
  fraction of the "mapped" bucket too, not yet checked) may not be true
  chemical-crosslinking datasets at all? Would meaningfully shrink the target
  list and raise the *effective* crosslinker-extraction success rate once
  non-XL-MS studies are excluded from the denominator.
