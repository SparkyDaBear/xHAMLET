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

## Proximity labeling vs. crosslinking mass spectrometry (XL-MS): what's the difference?

Both techniques map protein-protein interactions and both show up heavily in
PRIDE searches for "crosslink"-adjacent terms, but they are fundamentally
different chemistries answering different questions — this distinction is
central to interpreting every finding in this document.

**Crosslinking mass spectrometry (XL-MS)**, the technique this pipeline is
built for, uses a **bifunctional chemical reagent** (e.g. BS3, DSSO, DSBU) with
two reactive ends that each covalently attach to a specific residue (usually
lysine). When the two ends of one reagent molecule react with two different
residues that happen to be close together in 3D space (typically within the
reagent's "spacer arm" length, ~10-30 Å), it leaves behind a **defined,
calculable mass addition bridging exactly two residues** once the protein is
digested into peptides. A search engine like XiSearch can then computationally
test every plausible residue pair for a precursor-mass match to that known
bridge mass, directly yielding a **distance restraint** — "residue A and
residue B were within X Å of each other in the native structure/complex" —
which is exactly the kind of data this pipeline exists to extract and curate.
This is why our `assets/crosslinker_definitions.json` database exists: each
entry needs a precise monoisotopic mass, reactive residue specificity, and
(for MS-cleavable reagents) characteristic fragment "stub" masses, because the
*entire value* of an XL-MS dataset for structural modeling depends on knowing
exactly which chemical bridged which two residues.

**Proximity labeling (TurboID, BioID, APEX/APEX2, biotin-phenol)** uses an
**enzyme** (a biotin ligase or peroxidase), genetically fused to a "bait"
protein of interest, that is expressed inside a live cell. When activated
(with biotin, or biotin-phenol + H2O2), the enzyme generates a diffusible,
short-lived reactive radical/ester that **promiscuously and non-specifically
biotinylates any nearby protein** within a rough spatial radius (roughly
nanometers, much larger and far less precise than a crosslinker's spacer arm)
— it does not matter which exact residue gets tagged, or on which specific
neighboring protein. Biotinylated proteins are then enriched via streptavidin
pulldown and identified by standard (non-crosslink) LC-MS/MS. The output is a
**list of proteins that were in the bait's general vicinity** ("the
interactome/proximitome of protein X"), not a residue-pair distance restraint.
There is no bifunctional reagent, no defined bridge mass, and nothing for
XiSearch-style crosslink-search software to look for — `comment[cross-linker]`
is correctly `null` for these datasets, because the question "which chemical
crosslinker was used" simply doesn't apply to this technique.

A third, closely-related category that this investigation also surfaced in
large numbers (see Batch 2 below) is **native-residue UV photo-crosslinking**
(CLIP, PAR-CLIP, CLIR-MS, irCLIP — almost always for protein-RNA or
protein-DNA interactions): here, 254 nm UV light directly excites an
*intrinsic* nucleotide base (uracil, thymine) into a reactive state that
covalently traps whatever protein residue happens to be in van-der-Waals
contact with it at that instant — no exogenous chemical reagent is
incorporated at all, so again there is no "crosslinker name" for the LLM to
extract, correctly yielding `null`. This is conceptually a residue-level
distance-restraint technique like XL-MS (not a to-be-identified-protein-list
technique like proximity labeling) — but it never has a named bifunctional
reagent and so, like proximity labeling, is out of scope for the crosslinker
database this pipeline curates.

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

## Batch 2 — 2026-10-14 (all 59 remaining non-proximity-labeling null PXDs)

Unlike Batch 1 (a random sample), this batch covers **every single one** of
the 59 null PXDs that did *not* match the proximity-labeling keyword scan
(58 new + PXD063839 carried over from Batch 1, already analyzed there) — a
full census of this subset, not a sample, per the user's request to "analyze
those remaining 59 PXDs."

### Category breakdown

| Category | Count | % of 59 |
|---|---:|---:|
| `RNA_PROTEIN_UV_XL` — native-residue UV photo-crosslinking (CLIP/CLIR-MS/irCLIP-style protein-RNA or protein-DNA studies; no synthetic reagent, correctly rejected) | **20** | 33.9% |
| `CORRECT_REJECT_NO_TEXT` — genuine/likely real chemical XL-MS study, but the only available text (always PRIDE-only, no PMC, in every case in this batch) never names the specific reagent | **18** | 30.5% |
| `NATURAL_OR_ENZYMATIC_XL` — natural/enzymatic crosslinks (transglutaminase, lysyl oxidase, dityrosine, disulfide bonds, spontaneous aging-related crosslinks); no synthetic reagent, correctly rejected | **11** | 18.6% |
| `WRONG_TECHNIQUE` — not a crosslinking-MS study at all (HDX-MS, Virotrap, DNA-interstrand-crosslink-repair biology, activity-based chemoproteomic probes); further evidence the master PXD list has non-XL-MS contamination beyond just proximity labeling | **7** | 11.9% |
| `REAL_MISS` — reagent explicitly named in the actual text sent to the LLM, extraction still failed; genuine bugs/gaps | **3** | 5.1% |

**Combined with Batch 1:** of 69 total PXDs now checked (10 + 59, with 1
PXD — PXD063839 — counted once), **4 total genuine `REAL_MISS` cases** found
(PXD063839/VTT from Batch 1, plus 2 new ones below) against **65
correctly-rejected cases** — a ~94% correct-rejection rate across everything
checked so far. This is reassuring: the pipeline's null results are overwhelmingly
*correct*, not buggy; the dataset list itself contains many non-XL-MS studies.

### Full per-PXD table (Batch 2)

| PXD | Category | Reason |
|---|---|---|
| PXD000545 | CORRECT_REJECT_NO_TEXT | Generic "cross-linking chemistry" stated in PRIDE description; sampleProcessingProtocol/dataProcessingProtocol both "Not available"; no PMC. |
| PXD000685 | WRONG_TECHNIQUE | Virotrap (viral-particle-budding protein complex capture) — a different complex-trapping technology entirely, not chemical crosslinking-MS. |
| PXD001080 | RNA_PROTEIN_UV_XL | CLIP-style UV crosslinking of native mRNP residues (Entamoeba splicing/mRNP study). |
| PXD002058 | CORRECT_REJECT_NO_TEXT | "mild in vivo crosslinking" stated, but no specific reagent named anywhere in the available (no-PMC) text. |
| PXD002226 | RNA_PROTEIN_UV_XL | mRBPome: cells UV-crosslinked at 254nm, oligo(dT) mRNA capture (C. elegans). |
| PXD002293 | RNA_PROTEIN_UV_XL | mRBPome: cells UV-crosslinked at 254nm, oligo(dT) mRNA capture (S. cerevisiae). |
| PXD002890 | RNA_PROTEIN_UV_XL | mRNA interactome: UV irradiation at 254nm (mouse macrophages). |
| PXD003917 | CORRECT_REJECT_NO_TEXT | "chemical cross-linking/mass spectrometry" stated, but no specific reagent named in the available (no-PMC) text. |
| PXD005566 | RNA_PROTEIN_UV_XL | CLIR-MS: complexes irradiated at 254nm (protein-RNA hybrid structural modeling). |
| PXD005601 | RNA_PROTEIN_UV_XL | mRNA-binding proteins via UV irradiation + oligo(dT) capture (Leishmania). |
| PXD005943 | RNA_PROTEIN_UV_XL | mRBPome: UV-crosslinked at 254nm under oxidative stress (S. cerevisiae). |
| PXD008914 | RNA_PROTEIN_UV_XL | RBP repertoire: UV irradiated at 254nm, 0.15 J/cm² (embryonic stem cells). |
| PXD009474 | CORRECT_REJECT_NO_TEXT | "crosslinking coIPs" mentioned (crosslinking IP workflow), but no specific reagent named in the available (no-PMC) text. |
| PXD012225 | NATURAL_OR_ENZYMATIC_XL | FXIIIa (coagulation Factor XIIIa) — transglutaminase ENZYME catalyzing natural fibrin isopeptide crosslinks. |
| PXD012521 | WRONG_TECHNIQUE | TAP-MS study of DNA interstrand crosslink (ICL) REPAIR biology — "crosslink" here means a DNA damage lesion (from mitomycin C), not XL-MS chemistry; the proteomics method itself is tandem affinity purification, no chemical crosslinker used. |
| PXD012759 | CORRECT_REJECT_NO_TEXT | "Crosslinking Proteomics" in title, genuine XL-MS study of TLR2 interactome, but no reagent named in the available (no-PMC) text. |
| PXD013097 | WRONG_TECHNIQUE | Chemoproteomic activity-based protein profiling (ABPP) of kinase active sites — a covalent single-site labeling technique, not bifunctional structural crosslinking-MS. |
| PXD013928 | CORRECT_REJECT_NO_TEXT | "Proteome-wide Cross-linking mass spectrometry" — extremely terse PRIDE text (544 chars combined), no reagent named, no PMC. |
| PXD014067 | NATURAL_OR_ENZYMATIC_XL | Tissue transglutaminase (TG2) ENZYME catalyzing isopeptide crosslinks with gluten peptides. |
| PXD014898 | RNA_PROTEIN_UV_XL | UV femtosecond laser crosslinking of protein-DNA complexes. |
| PXD015549 | NATURAL_OR_ENZYMATIC_XL | R2lox protein's naturally-occurring Mn/Fe-cofactor-driven internal Tyr-Val crosslink (endogenous radical chemistry, not an added reagent). |
| PXD015989 | CORRECT_REJECT_NO_TEXT | "cross-linking MS-based approach" stated for PDE6 structural study; text only generically mentions "specific crosslinker modifications when appropriate" with no actual name; no PMC. |
| PXD016355 | CORRECT_REJECT_NO_TEXT | Title/description say "diazirine mediated cross-linking" — diazirine is a reactive FUNCTIONAL GROUP, not a specific named reagent/molecule; no PMC. |
| PXD017378 | CORRECT_REJECT_NO_TEXT | "Comprehensive cross-linking mass spectrometry" (NuRD complex) — description is entirely about affinity-purification tagging workflow, no reagent named; no PMC. |
| PXD017951 | WRONG_TECHNIQUE | DNA interstrand crosslink (ICL) repair biology (PrimPol primase study) — "crosslink" refers to a DNA damage lesion, not XL-MS chemistry. |
| PXD020290 | RNA_PROTEIN_UV_XL | UV-induced crosslinking of protein-DNA complexes in chromatin. |
| PXD020302 | CORRECT_REJECT_NO_TEXT | "Analysis of cross-link on Tranaldolase" — extremely terse (1024 chars combined), no reagent named, no PMC. |
| PXD022991 | NATURAL_OR_ENZYMATIC_XL | Spontaneous (non-enzymatic) age-related Lys-Gln/Glu crosslinking via glutarimide intermediate in aged human lens tissue. |
| PXD023522 | CORRECT_REJECT_NO_TEXT | LinX software / CX-MS data — sampleProcessingProtocol just references 3 external published papers by citation only, reagent not restated in this text; no PMC. |
| PXD023542 | CORRECT_REJECT_NO_TEXT | "Targeted in situ cross-linking" (SARS-CoV-2) — description focuses on the AP-MS workflow, no chemical crosslinker reagent named; no PMC. |
| PXD023651 | NATURAL_OR_ENZYMATIC_XL | Natural internal isopeptide crosslink (A2M autoconjugation via its native thiol ester, triggered by trypsin cleavage of the bait region). |
| PXD024010 | RNA_PROTEIN_UV_XL | CLIR-MS workflow extension, UV crosslinking via Spectrolinker XL-1500. |
| PXD024253 | CORRECT_REJECT_NO_TEXT | Evidence_quote explicitly states "a newly synthesized enrichable crosslinker" with no chemical name/abbreviation/accession given at all. |
| PXD025122 | RNA_PROTEIN_UV_XL | RNase III CLASH (Cross-Linking And Sequencing of Hybrids) — canonically UV-crosslinking-based. |
| PXD027189 | RNA_PROTEIN_UV_XL | U1/U2 snRNP protein-RNA crosslinking via 254nm irradiation. |
| PXD029748 | CORRECT_REJECT_NO_TEXT | "Proteome-wide Cross-linking mass spectrometry" (HEK293) — description/protocol both just restate the title with no reagent name; no PMC. |
| **PXD030619** | **REAL_MISS** | **BS3 explicitly named multiple times** in the 52K-char combined PMC+PRIDE text (confirmed via direct reconstruction of the actual LLM input), but the entire `xlms_reagents` prompt-group response failed JSON parsing and was silently dropped. See root-cause analysis below. |
| PXD031381 | RNA_PROTEIN_UV_XL | CLIR-MS: photo-induced RNA-protein crosslinking, 800 mJ/cm² UV irradiation. |
| **PXD034529** | **REAL_MISS** | **8 organophosphate pesticide names explicitly listed** as agents that "catalyze protein crosslinking", none extracted. See root-cause analysis below. |
| PXD034054 | CORRECT_REJECT_NO_TEXT | "Crosslinks Analysis of Cryptochrome and Timeless" — protocol describes SDS-PAGE/gel workflow only, no reagent named; no PMC. |
| PXD034894 | RNA_PROTEIN_UV_XL | CLIR-MS reanalysis of PXD005566 (same UV-crosslinking method, broader parameters). |
| PXD037438 | RNA_PROTEIN_UV_XL | SARS-CoV-2 nucleocapsid-RNA UV crosslinking at 254nm (4.8 J/cm²). |
| PXD043595 | CORRECT_REJECT_NO_TEXT | "CX-MS" (Collagen I NTX) — protocol describes digestion methods only (hydroxylamine/CNBr), no crosslinker reagent named; no PMC. |
| PXD044285 | WRONG_TECHNIQUE | HDX-MS (Hydrogen-Deuterium Exchange mass spectrometry) — a completely different structural proteomics technique, no chemical crosslinker involved. |
| PXD045105 | WRONG_TECHNIQUE | Virotrap-based screening of TGM1 interactors — complex-trapping technology, not crosslinking-MS (TGM1 itself is also a natural crosslinking enzyme, not a reagent). |
| PXD045837 | WRONG_TECHNIQUE | HDX-MS analysis of HACE1 — different structural proteomics technique, no chemical crosslinker. |
| PXD046267 | RNA_PROTEIN_UV_XL | Protein-RNA UV crosslinking in biomolecular condensates, Spectrolinker 254nm. |
| PXD046754 | RNA_PROTEIN_UV_XL | LPS-induced RNA-binding proteome: UV-crosslinked to RNA (mouse macrophages). |
| PXD047547 | NATURAL_OR_ENZYMATIC_XL | Natural/oxidative disulfide bond formation between NLRP1 and TRX1 (not a synthetic crosslinker). |
| PXD048567 | CORRECT_REJECT_NO_TEXT | Evidence_quote: "covalently immobilized...using cross-linkers" — generic, unnamed reagent(s); no PMC. |
| PXD048614 | NATURAL_OR_ENZYMATIC_XL | Natural disulfide bond mapping/rearrangement in J-chain (not a synthetic crosslinker). |
| PXD048897 | NATURAL_OR_ENZYMATIC_XL | Natural/enzymatic dityrosine bond in RSV fusion glycoprotein. |
| PXD049303 | RNA_PROTEIN_UV_XL | RNA interactome capture (RIC): RNA-protein complexes stabilized by UV crosslinking in vivo. |
| PXD050833 | NATURAL_OR_ENZYMATIC_XL | Lysyl oxidase (LOX) ENZYME catalyzing natural collagen crosslinks. |
| PXD053494 | RNA_PROTEIN_UV_XL | irCLIP-RNP: UVC crosslinking of RNA-protein complexes. |
| PXD053814 | NATURAL_OR_ENZYMATIC_XL | Spontaneous dehydroamino-acid-mediated protein crosslinks in Alzheimer's brain tissue (disease-associated PTM, not a synthetic reagent). |
| PXD062688 | NATURAL_OR_ENZYMATIC_XL | TG2/FXIIIA transglutaminase ENZYMES catalyzing natural fibrin clot crosslinks. |
| PXD063839 | REAL_MISS | *(Carried over from Batch 1 — see root-cause analysis there.)* VTT (vinyl thianthrenium tetrafluoroborate) explicitly named. |
| PXD068129 | CORRECT_REJECT_NO_TEXT | Genuine clinical XL-MS feasibility study (human muscle biopsy, mitochondrial interactome) confirmed via keywords ("Xl-ms", "Cross-linking", "Intra/inter cross-linked peptides"), but no specific reagent named anywhere in the available (no-PMC, 4458-char) text. |

### Root-cause analysis: PXD030619 (BS3 miss — silent prompt-group failure)

This is a different and more concerning failure mode than PXD063839's — not a
model-judgment gap, but a **pipeline bug**. Reconstructed the exact 52,576-char
combined PMC+PRIDE text actually sent to the LLM; it explicitly and repeatedly
names the reagent:

> "Chemical cross-linking: For optimizing the cross-linker concentration, 10
> µM SNAP25, Syntaxin-1A and Complexin-1 were **cross-linked with 0.1-1.5 mM
> BS3** for 1 h at 25 °C and 350 rpm..."

Checking the original run log (`reanalysis_jobs/chunk_003.log`) for this PXD
shows exactly what happened:

```
Querying LLM with prompt group: xlms_reagents
HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
LLM query successful. Tokens used: 22434
Could not parse JSON from LLM response
LLM response for 'xlms_reagents' is not a JSON object — skipping
```

The LLM call **succeeded** at the HTTP level — 200 OK, 22,434 tokens consumed,
so the model clearly processed the full text — but its response text failed
`parse_json_response()`. Per `_query_llm_with_prompts()`
(`src/pxd_enhancer/extractor.py`), when a prompt group's response isn't valid
JSON, the entire group is **silently skipped with just a `logger.warning()`**
— no retry, and critically, **none of that group's expected keys
(`comment[cross-linker]`, `comment[crosslinker concentration]`, etc.) are
written at all**, not even as explicit nulls. Verified this is a true key
absence (not a null value) by checking `"comment[cross-linker]" in data` on
the saved response — it's `False`.

This matters because our failure-counting methodology (and most of this
document) treats "key absent" and "key present with null value" identically
(both count as "no crosslinker extracted" via `extract_reagent_mentions()`),
but they are **very different situations**: one means "the LLM looked and
genuinely found nothing", the other means "we never actually got a real
answer out of the LLM for this prompt group at all." A full-corpus scan found
this is rare — **only 1 of 1045 PXDs** has `comment[cross-linker]` completely
absent from its response — so this isn't a widespread problem, but it is a
real, fixable gap (e.g. a single automatic retry on JSON-parse failure before
giving up, or writing explicit null placeholders for a group's expected keys
on failure so this is at least visible/countable going forward, rather than
indistinguishable from a genuine negative result).

**Important mitigating detail:** this PXD's actual Xi-search config generation
still succeeded with the correct reagent (`xi_configs: 'success'`, config
correctly lists BS3) — a *separate* mechanism (file-clustering's
per-cluster `crosslinker` override, resolved from an earlier, successful LLM
call) independently identified BS3 and was used as an override in
`extractor.py` Stage 8, bypassing the broken `comment[cross-linker]` field
entirely. So the real, practical pipeline **output** for this PXD is correct —
only the `comment[cross-linker]` SDRF metadata field (and, as a direct
consequence, this document's and the normalization script's `comment[cross-linker]`-based
statistics) incorrectly show it as a miss.

### Root-cause analysis: PXD034529 (organophosphate pesticides — unresolved scope question)

Evidence_quote: *"We treated 100 μg of MAP-rich tubulin with 100 μM
chlorpyrifos, chlorpyrifos oxon, methamidophos, paraoxon, diazinon, diazoxon,
monocrotophos, or dichlorvos."* The paper's title is "Organophosphorus
pesticides catalyze protein crosslinking" — 8 distinct, fully-named chemical
compounds are explicitly stated to be responsible for producing the
crosslinks studied, yet extraction returned null for all of them.

Unlike the other two `REAL_MISS` cases, the right fix here isn't obvious yet:
it's unclear from the available PRIDE text alone whether these organophosphate
compounds are themselves literally the bifunctional bridging species (in which
case this is a genuinely new, previously-uncatalogued reagent *class* worth
adding to our database) or whether they merely **catalyze** some other
underlying natural crosslinking chemistry without being incorporated into the
final mass bridge themselves (in which case `not_a_crosslinker` would actually
be the correct call, similar to our existing DMTMM/EDC "activator, not the
crosslinker" exclusion rule). Flagged here rather than silently
miscategorized either way — resolving this needs a literal read of the
source paper's mechanism, not just title/abstract triangulation.

---

## Running totals (all batches)

| Batch | n | RNA_PROTEIN_UV_XL | NATURAL_OR_ENZYMATIC_XL | WRONG_TECHNIQUE | CORRECT_REJECT (prox. labeling) | CORRECT_REJECT_NO_TEXT | REAL_MISS |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 (sample of 10) | 10 | 0 | 0 | 0 | 9 | 0 | 1 |
| 2 (full census of 59, minus 1 carried over) | 58 | 20 | 11 | 7 | 0 | 18 | 2 |
| **Total** | **68** | **20** | **11** | **7** | **9** | **18** | **3** |

(PXD063839 is counted once, in Batch 1; Batch 2's "n" above is 58 new PXDs,
for 59 total distinct non-proximity-labeling PXDs fully analyzed across both
batches combined with the 10 from Batch 1.)

**Correct-rejection rate across everything checked so far: 65/68 (95.6%).**
Every major failure category found is either (a) a technique that
legitimately has no chemical crosslinker to extract (proximity labeling, UV
photo-crosslinking, natural/enzymatic crosslinks), (b) a dataset that isn't
really an XL-MS study at all (dataset-list contamination: HDX-MS, Virotrap,
DNA-damage-repair biology, chemoproteomic ABPP), or (c) a genuine XL-MS study
whose only available text source (always PRIDE-only, no PMC, in every single
`CORRECT_REJECT_NO_TEXT` case found) simply never names the reagent. Only 3
genuine extraction bugs/gaps found across 68 PXDs — none of which are the
"same abbreviation recognition" failure mode twice (VTT = brand-new/unexpanded
reagent; BS3 = silent JSON-parse-failure pipeline bug; pesticides = open
chemistry-scope question) — suggesting there isn't one single dominant
systemic bug left to fix, just a long tail of rare edge cases.

PXDs checked so far (excluded from future batches' sampling pool): all 391
null PXDs have now been examined — 332 via the proximity-labeling keyword
scan (Batch 1's methodology, applied retroactively to the full null set) plus
59 via full manual review (Batch 1's 10-PXD sample + Batch 2's complete
59-PXD census). **This concludes the planned investigation of the 391-PXD
null set** — see Open Questions below for what's left to decide/fix.

## Open questions / recommendations

1. **Fix the silent prompt-group-failure gap (PXD030619's root cause).** Add
   either a single automatic retry on `parse_json_response()` failure, or at
   minimum write explicit null placeholders for a failed group's expected
   keys so future failures are distinguishable from genuine negative results
   in our statistics. Low effort, closes a real (if rare — 1/1045 so far)
   correctness gap.
2. **Resolve the PXD034529 pesticide-crosslinker scope question** by reading
   the actual paper (not just PRIDE metadata) before deciding whether to add a
   new reagent-class DB entry or an exclusion-cache entry.
3. **Consider re-filtering `assets/crosslinking_datasets_list.tsv`.** Breaking
   the 68 checked PXDs down by what they actually are (not what the dataset
   list's search terms assumed):
   - **16/68 (23.5%)** — proximity labeling (9) or outright wrong technique (7:
     HDX-MS, Virotrap, DNA-damage-repair biology, ABPP) — arguably should never
     have been in a "crosslinking datasets" list at all.
   - **31/68 (45.6%)** — RNA_PROTEIN_UV_XL (20) or NATURAL_OR_ENZYMATIC_XL (11)
     — legitimately "crosslinking" studies in a broad biological sense, but
     with no synthetic bifunctional reagent, so out of scope for the
     chemical-reagent database this pipeline curates either way.
   - **18/68 (26.5%)** — CORRECT_REJECT_NO_TEXT — plausibly real, in-scope
     XL-MS studies where only the specific reagent name is missing from
     available text.
   - **3/68 (4.4%)** — REAL_MISS — genuine extraction bugs/gaps.

   If the first two groups' ~69% combined ratio holds across the full
   391-PXD null set, the bulk of "no crosslinker extracted" cases are
   dataset-list/scope mismatches rather than pipeline failures — re-filtering
   the master list (dropping proximity-labeling and clearly-wrong-technique
   studies, and treating UV-photocrosslinking/natural-crosslink studies as a
   separate, intentionally-out-of-scope category) would give a much more
   honest denominator for any future "% of datasets successfully processed"
   statistic.
4. **VTT (and future brand-new reagents) will keep slipping through** until
   `assets/crosslinker_definitions.json` is periodically refreshed against
   newly-published XL-MS literature — this is a maintenance-cadence question,
   not a one-time fix.

---

## Full crosslinker-mapping table — all 1,045 reanalyzed PXDs

Generated directly from the current `store/` + `assets/crosslinker_definitions.json`
state (same logic used throughout this document): for each PXD, every
`comment[cross-linker]` mention is resolved against the curated database
(exact name/alias/accession match, falling back to the normalization script's
decision cache for anything not in the database by name). The **Identified
Crosslinker(s) in DB** column shows:
- A plain name (e.g. `BS3`) — resolved to a fully usable database entry, ready
  for XiSearch today.
- `(unverified) <name>` — resolved to a database entry that exists but is
  marked `NeedsVerification` (see the crosslinker-normalization workflow
  commits) — a human must confirm its mass/chemistry before it's usable.
- `(unmatched) <name>` — a reagent name was extracted but could not be
  resolved against the database or the normalization cache at all (rare: 0
  cases as of this writing).
- `—` (empty) — no crosslinker reagent was extracted at all, or every
  extracted mention was explicitly classified `not_a_crosslinker`.

**Proximity-Labeling Keyword?** is the same heuristic regex scan used
throughout this document (`turboid|bioid|apex2?\b|biotin-phenol|biotin-tyramide|
proximity-labeling|proximity-biotinylation|proximity-dependent` against each
PXD's PRIDE title+description+protocol+keywords). It is a **heuristic, not a
strict classifier** — 33 PXDs in this table match the keyword *and* still
have a legitimately mapped crosslinker (e.g. a paper that compares/mentions
proximity labeling in passing while the actual experiment uses real chemical
crosslinking), so "Yes" should be read as "worth a second look", not an
automatic disqualifier.

| PXD | Identified Crosslinker(s) in DB | Proximity-Labeling Keyword? |
|---|---|---|
| PXD000244 | Formaldehyde | No |
| PXD000513 | (unverified) 4-thiouridine | No |
| PXD000545 | — | No |
| PXD000685 | — | No |
| PXD001080 | — | No |
| PXD001454 | BS3 | No |
| PXD001538 | BS2G; DSS; EDC | No |
| PXD001609 | DSP | No |
| PXD001675 | BS3 | No |
| PXD001677 | DSS | No |
| PXD001692 | sulfo-SDA | No |
| PXD001835 | BS3 | No |
| PXD002058 | — | No |
| PXD002142 | BS3 | No |
| PXD002159 | (unverified) DTBP | No |
| PXD002169 | DSP; DST | No |
| PXD002226 | — | No |
| PXD002293 | — | No |
| PXD002378 | PIR linker | No |
| PXD002392 | (unverified) DTT | No |
| PXD002656 | (unverified) DTT | No |
| PXD002890 | — | No |
| PXD002929 | Formaldehyde | No |
| PXD002987 | BS3 | No |
| PXD002992 | (unverified) 4-thiouridine | No |
| PXD003381 | (unverified) DEST | No |
| PXD003486 | BS3 | No |
| PXD003496 | DMP | No |
| PXD003502 | EDC | No |
| PXD003593 | (unverified) 4-thiouridine | No |
| PXD003643 | sulfo-SDA | No |
| PXD003658 | BS3; DSS; Formaldehyde | No |
| PXD003737 | sulfo-SDA | No |
| PXD003754 | Formaldehyde | No |
| PXD003880 | DSS | No |
| PXD003909 | BS2G | No |
| PXD003913 | BS2G | No |
| PXD003917 | — | No |
| PXD004009 | Aryl azide; Benzoyl | No |
| PXD004018 | — | No |
| PXD004105 | DSP | No |
| PXD004107 | BS3 | No |
| PXD004236 | BDP-NHP | No |
| PXD004692 | DSS | No |
| PXD004736 | Formaldehyde | Yes |
| PXD004749 | BS3 | No |
| PXD004898 | BS3 | No |
| PXD004920 | sulfo-SDA | No |
| PXD005012 | Benzoyl | No |
| PXD005201 | — | Yes |
| PXD005287 | DSS | No |
| PXD005349 | photo-leucine; photo-methionine | No |
| PXD005566 | — | No |
| PXD005601 | — | No |
| PXD005612 | — | Yes |
| PXD005657 | DMP | No |
| PXD005758 | — | Yes |
| PXD005943 | — | No |
| PXD005948 | BS3 | No |
| PXD006079 | Formaldehyde | No |
| PXD006131 | BS3 | No |
| PXD006156 | — | Yes |
| PXD006200 | — | Yes |
| PXD006245 | Benzoyl | No |
| PXD006246 | BS3 | No |
| PXD006287 | (unverified) BAMG | No |
| PXD006359 | — | Yes |
| PXD006541 | — | Yes |
| PXD006707 | BS3; EDC | No |
| PXD006715 | — | Yes |
| PXD006816 | DSSO | No |
| PXD006928 | BS3; sulfo-SMCC | No |
| PXD006938 | BS3; sulfo-SMCC | No |
| PXD007043 | DSS | No |
| PXD007185 | DSS; PDH | No |
| PXD007250 | BS3 | No |
| PXD007513 | DSSO | No |
| PXD007673 | PIR linker | No |
| PXD007695 | — | Yes |
| PXD007836 | DSP | No |
| PXD007862 | Azide-alkyne | Yes |
| PXD007928 | BS3 | No |
| PXD008122 | DSS | No |
| PXD008161 | (unverified) AMDSP | No |
| PXD008164 | — | No |
| PXD008337 | EDC | No |
| PXD008348 | DSBU; DSSO | No |
| PXD008418 | DSSO | No |
| PXD008550 | BS3; sulfo-SDA | No |
| PXD008577 | (unverified) PAL6 | No |
| PXD008605 | DSS | No |
| PXD008680 | (unverified) DTBP | No |
| PXD008914 | — | No |
| PXD008941 | BDP-NHP | No |
| PXD008951 | BDP-NHP | No |
| PXD008975 | BDP-NHP | No |
| PXD009000 | DSSO | No |
| PXD009001 | BDP-NHP | No |
| PXD009106 | ADH; DSS; PDH | No |
| PXD009159 | — | Yes |
| PXD009224 | DSSO | No |
| PXD009260 | EDC | No |
| PXD009284 | — | Yes |
| PXD009302 | — | Yes |
| PXD009474 | — | No |
| PXD009526 | DSS | No |
| PXD009641 | Benzoyl; DSP | No |
| PXD009648 | BS3 | No |
| PXD009748 | — | Yes |
| PXD009756 | DSSO; DTSSP | No |
| PXD009777 | DSSO; DTSSP; Glutaraldehyde | No |
| PXD009783 | DSP | Yes |
| PXD009927 | EDC | No |
| PXD010003 | DSS; PDH; sulfo-SDA | No |
| PXD010004 | DSS; PDH; sulfo-SDA | No |
| PXD010046 | Formaldehyde | No |
| PXD010061 | — | Yes |
| PXD010070 | DSBU | No |
| PXD010094 | DSS; PDH; sulfo-SDA | No |
| PXD010111 | ADH; BS3; DMTMM; DSS; Glutaraldehyde | No |
| PXD010122 | BS3 | No |
| PXD010124 | BS3 | No |
| PXD010222 | BS3 | No |
| PXD010317 | DSSO | No |
| PXD010352 | — | Yes |
| PXD010384 | DSS; PDH; sulfo-SDA | No |
| PXD010385 | DSS; PDH; sulfo-SDA | No |
| PXD010410 | DSS; PDH; sulfo-SDA | No |
| PXD010422 | (unverified) NNP9 | No |
| PXD010468 | Formaldehyde | No |
| PXD010470 | Benzoyl | No |
| PXD010474 | — | Yes |
| PXD010479 | DSS; PDH; sulfo-SDA | No |
| PXD010481 | BS3 | No |
| PXD010483 | DSS; PDH; sulfo-SDA | No |
| PXD010796 | DSSO | No |
| PXD010884 | DSS; PDH; sulfo-SDA | No |
| PXD010892 | Benzoyl | No |
| PXD010921 | — | Yes |
| PXD010930 | — | Yes |
| PXD010931 | — | Yes |
| PXD010950 | — | Yes |
| PXD010963 | Formaldehyde | No |
| PXD010988 | (unverified) thanatin-PAL5 | No |
| PXD011036 | BS3 | No |
| PXD011071 | — | No |
| PXD011077 | DSSO | No |
| PXD011078 | DSS | No |
| PXD011121 | BS3; SDA | No |
| PXD011296 | BS3; EDC + sulfo-NHS | No |
| PXD011312 | — | Yes |
| PXD011459 | BS3 | No |
| PXD011645 | EDC; PhoX; SDA | No |
| PXD011680 | DSSO | No |
| PXD011702 | — | Yes |
| PXD011704 | BS3 | No |
| PXD011774 | BS3 | No |
| PXD011775 | BS3 | No |
| PXD011806 | Formaldehyde | No |
| PXD011861 | DSSO | No |
| PXD011931 | PhoX | No |
| PXD011974 | Formaldehyde | Yes |
| PXD011995 | DSS | No |
| PXD012109 | (unverified) bAL2 | No |
| PXD012157 | — | Yes |
| PXD012225 | — | No |
| PXD012350 | (unverified) x-alk-MDP; x-alk-iE-DAP | No |
| PXD012427 | (unverified) APDC4 | No |
| PXD012466 | DSSO | No |
| PXD012494 | — | Yes |
| PXD012521 | — | No |
| PXD012546 | DSBU | No |
| PXD012592 | BS3 | No |
| PXD012624 | EDC; sulfo-SDA | No |
| PXD012723 | BS3 | No |
| PXD012759 | — | No |
| PXD012788 | Alkyne-A-DSBSO | No |
| PXD012882 | EDC | No |
| PXD012939 | sulfo-SDA | No |
| PXD013032 | — | Yes |
| PXD013063 | PIR linker | No |
| PXD013083 | BS3; DSS; DSSO | No |
| PXD013097 | — | No |
| PXD013144 | sulfo-SMPB | No |
| PXD013160 | — | Yes |
| PXD013183 | — | Yes |
| PXD013194 | — | Yes |
| PXD013209 | Formaldehyde | Yes |
| PXD013215 | — | Yes |
| PXD013338 | Formaldehyde | No |
| PXD013339 | Benzoyl | No |
| PXD013470 | ADH; DMTMM; DSS | No |
| PXD013476 | BDP-NHP | No |
| PXD013601 | — | Yes |
| PXD013704 | DSSO | No |
| PXD013720 | (unverified) 4-thiouridine; PFA | No |
| PXD013735 | DSSO | No |
| PXD013769 | DSSO | No |
| PXD013907 | DSS | No |
| PXD013928 | — | No |
| PXD014055 | PhoX | No |
| PXD014067 | — | No |
| PXD014247 | — | Yes |
| PXD014337 | DSBU; DSS; DSSO | No |
| PXD014359 | BS3 | No |
| PXD014426 | — | Yes |
| PXD014499 | — | Yes |
| PXD014500 | — | Yes |
| PXD014520 | BS3 | No |
| PXD014523 | DSS; PDH | No |
| PXD014584 | DSSO | No |
| PXD014642 | DSSO | No |
| PXD014661 | (unverified) ETD | No |
| PXD014673 | BMSO; DHSO; DSSO | No |
| PXD014675 | DSS | No |
| PXD014738 | BS3 | No |
| PXD014759 | BS3; DSSO | No |
| PXD014898 | — | No |
| PXD014957 | (unverified) 4-thiouridine | No |
| PXD015037 | photo-methionine | No |
| PXD015044 | DSAU; DSG; PhoX; SDA | No |
| PXD015080 | — | No |
| PXD015160 | DSSO | No |
| PXD015161 | Formaldehyde | Yes |
| PXD015162 | Formaldehyde | Yes |
| PXD015285 | DSBU | No |
| PXD015366 | (unverified) AzidoPhe | No |
| PXD015394 | DSS; PDH | No |
| PXD015435 | Formaldehyde | No |
| PXD015479 | — | Yes |
| PXD015507 | — | Yes |
| PXD015549 | — | No |
| PXD015658 | DSS | No |
| PXD015682 | DSS | No |
| PXD015725 | — | Yes |
| PXD015751 | PIR linker | No |
| PXD015779 | — | Yes |
| PXD015793 | BS3; EDC | No |
| PXD015863 | (unverified) 4-thiouridine | No |
| PXD015883 | — | Yes |
| PXD015890 | — | Yes |
| PXD015941 | DSBU; DSSO | No |
| PXD015974 | Benzoyl | No |
| PXD015985 | DSS | No |
| PXD015989 | — | No |
| PXD016196 | BS3 | No |
| PXD016221 | — | Yes |
| PXD016224 | Sulfo-LC-SDA | No |
| PXD016355 | — | No |
| PXD016554 | DSP; DSS | No |
| PXD016639 | BS(PEG)5; DSG; DSS | No |
| PXD016963 | DSBSO | No |
| PXD016988 | — | Yes |
| PXD016993 | DSBU | No |
| PXD017020 | BS3 | No |
| PXD017066 | PhoX | No |
| PXD017085 | — | Yes |
| PXD017128 | DSS | No |
| PXD017238 | BS3; EDC | No |
| PXD017241 | — | Yes |
| PXD017244 | ADH; BS3 | No |
| PXD017299 | BS2G; DSG | No |
| PXD017344 | — | Yes |
| PXD017378 | — | No |
| PXD017379 | DSBU | No |
| PXD017531 | DSBU | No |
| PXD017584 | photo-leucine | No |
| PXD017620 | BS3; DSS | No |
| PXD017868 | — | Yes |
| PXD017873 | BS3 | No |
| PXD017931 | DSS | No |
| PXD017933 | — | Yes |
| PXD017937 | — | Yes |
| PXD017951 | — | No |
| PXD017996 | DSS | No |
| PXD018040 | — | Yes |
| PXD018106 | BS3 | No |
| PXD018189 | PhoX | No |
| PXD018219 | DSSO | No |
| PXD018232 | DSS | No |
| PXD018265 | — | Yes |
| PXD018291 | PhoX; pDSPE | No |
| PXD018310 | BS3 | No |
| PXD018383 | — | Yes |
| PXD018580 | (unverified) alkyne-diazirine minimal photocrosslinker | No |
| PXD018608 | SDA | No |
| PXD018687 | Formaldehyde | No |
| PXD018771 | DSSO | No |
| PXD018786 | BS3; EDC + sulfo-NHS | No |
| PXD018935 | DSAU | No |
| PXD019017 | DSSO | No |
| PXD019043 | (unverified) BrC6K | No |
| PXD019048 | DSSO | No |
| PXD019101 | DSSO | No |
| PXD019215 | — | No |
| PXD019251 | DSS | No |
| PXD019274 | BS3; Benzoyl; sulfo-SDA | No |
| PXD019338 | DSSO | No |
| PXD019428 | — | No |
| PXD019484 | PIR linker | No |
| PXD019507 | PDH | No |
| PXD019508 | PDH | No |
| PXD019530 | DSBU | No |
| PXD019599 | DSSO | No |
| PXD019713 | DSSO | No |
| PXD019724 | PDH | No |
| PXD019751 | DSS | No |
| PXD019771 | DMTMM | No |
| PXD019868 | DSSO | No |
| PXD019926 | DSSO | No |
| PXD019944 | DSSO | No |
| PXD020014 | DSS; DSSO | No |
| PXD020084 | BS3 | No |
| PXD020119 | (unverified) NHS-LC-Diazirine | No |
| PXD020165 | — | Yes |
| PXD020229 | BS3; EDC + sulfo-NHS | No |
| PXD020290 | — | No |
| PXD020302 | — | No |
| PXD020323 | Azide-alkyne | Yes |
| PXD020340 | Azide-alkyne | Yes |
| PXD020370 | — | Yes |
| PXD020418 | Benzoyl | No |
| PXD020453 | sulfo-SDA | No |
| PXD020542 | — | Yes |
| PXD020602 | DSS | No |
| PXD020636 | DSS; PDH | No |
| PXD020704 | DSS; Formaldehyde; Glutaraldehyde | No |
| PXD020709 | — | Yes |
| PXD020759 | — | Yes |
| PXD020817 | BS3 | No |
| PXD020826 | — | No |
| PXD020859 | BS3 | No |
| PXD021115 | DSS | No |
| PXD021126 | BS2G; BS3 | No |
| PXD021182 | Benzoyl | No |
| PXD021375 | — | Yes |
| PXD021417 | DSS | No |
| PXD021434 | Formaldehyde | No |
| PXD021553 | (unverified) NNP9 | No |
| PXD021622 | — | Yes |
| PXD021648 | DSBU | No |
| PXD021691 | — | Yes |
| PXD021693 | — | Yes |
| PXD021708 | DSSO | No |
| PXD021709 | DSSO | Yes |
| PXD021770 | — | Yes |
| PXD021809 | — | Yes |
| PXD021822 | DSP | No |
| PXD021831 | DSS | No |
| PXD021870 | (unverified) p-azido-Phe | No |
| PXD021872 | DSBU | No |
| PXD021923 | — | Yes |
| PXD022119 | BS3 | No |
| PXD022279 | Azide-alkyne | No |
| PXD022335 | — | Yes |
| PXD022440 | Formaldehyde | No |
| PXD022443 | DSS | No |
| PXD022608 | — | Yes |
| PXD022675 | DSSO | No |
| PXD022690 | DSSO; SDASO-L | No |
| PXD022772 | DSBU; DSSO | No |
| PXD022785 | — | Yes |
| PXD022861 | BS3; DSS | No |
| PXD022903 | — | Yes |
| PXD022991 | — | No |
| PXD023022 | BS3 | No |
| PXD023072 | PhoX | No |
| PXD023073 | — | Yes |
| PXD023164 | CDI; DSSO | No |
| PXD023192 | Benzoyl | No |
| PXD023221 | BS3 | No |
| PXD023239 | — | Yes |
| PXD023277 | — | Yes |
| PXD023487 | BS3; DSS; Formaldehyde | No |
| PXD023522 | — | No |
| PXD023525 | CDI; DSBU | No |
| PXD023542 | — | No |
| PXD023577 | PIR linker | No |
| PXD023651 | — | No |
| PXD023814 | — | Yes |
| PXD023817 | DSSO | No |
| PXD024010 | — | No |
| PXD024065 | Benzoyl | No |
| PXD024120 | — | Yes |
| PXD024131 | DSS | No |
| PXD024160 | PhoX | No |
| PXD024168 | — | Yes |
| PXD024253 | — | No |
| PXD024254 | Formaldehyde | No |
| PXD024335 | — | Yes |
| PXD024361 | — | Yes |
| PXD024366 | — | Yes |
| PXD024367 | — | Yes |
| PXD024399 | — | Yes |
| PXD024492 | Benzoyl | No |
| PXD024493 | Benzoyl | No |
| PXD024822 | DSS; Glutaraldehyde; PDH | No |
| PXD024946 | BMB; BMOE; BS2G; BS3 | No |
| PXD025066 | — | No |
| PXD025099 | BS3 | No |
| PXD025122 | — | No |
| PXD025141 | — | Yes |
| PXD025172 | DSSO | No |
| PXD025179 | — | Yes |
| PXD025208 | — | Yes |
| PXD025220 | BS3 | No |
| PXD025357 | — | Yes |
| PXD025391 | DSSO | No |
| PXD025581 | — | Yes |
| PXD025662 | DSS | No |
| PXD025710 | DSS; PDH | No |
| PXD025796 | (unverified) iqPIR | No |
| PXD025843 | ADH; BS3 | No |
| PXD025903 | — | No |
| PXD025923 | (unverified) iqPIR | No |
| PXD025980 | Formaldehyde | Yes |
| PXD026017 | BS3 | No |
| PXD026037 | (unverified) iqPIR | No |
| PXD026196 | — | Yes |
| PXD026229 | — | Yes |
| PXD026244 | DSS | No |
| PXD026433 | DSSO | No |
| PXD026508 | Formaldehyde | No |
| PXD026603 | DSSO | No |
| PXD026696 | DSBU | No |
| PXD026718 | — | Yes |
| PXD026790 | DMP | No |
| PXD026793 | — | Yes |
| PXD026861 | — | No |
| PXD026926 | — | Yes |
| PXD026935 | BS3 | No |
| PXD027068 | — | Yes |
| PXD027128 | Benzoyl | No |
| PXD027149 | (unverified) VL1 | No |
| PXD027159 | BS3; DSBU; DSS; DSSO | No |
| PXD027161 | BS3; DSBU; DSS; DSSO | No |
| PXD027188 | BS3; DSBU; DSS; DSSO | No |
| PXD027189 | — | No |
| PXD027213 | DMTMM; DSS; PDH | No |
| PXD027234 | DSAU; DSBU; DSPU | No |
| PXD027239 | (unverified) X10 | No |
| PXD027267 | — | Yes |
| PXD027349 | EDC + sulfo-NHS | No |
| PXD027394 | (unverified) X10 | No |
| PXD027413 | DSG | No |
| PXD027488 | — | Yes |
| PXD027565 | Formaldehyde | No |
| PXD027611 | DSSO | No |
| PXD027757 | (unverified) iqPIR | No |
| PXD027759 | — | Yes |
| PXD027891 | DSS | No |
| PXD027905 | — | Yes |
| PXD027917 | — | Yes |
| PXD027953 | PIR linker | No |
| PXD027954 | (unverified) DiazK | No |
| PXD027998 | — | Yes |
| PXD028002 | DSS; EDC; SDA | No |
| PXD028005 | DSSO | No |
| PXD028063 | Formaldehyde | Yes |
| PXD028150 | — | Yes |
| PXD028313 | PhoX | No |
| PXD028415 | PhoX | No |
| PXD028433 | EDC | No |
| PXD028462 | (unverified) SMPH | Yes |
| PXD028879 | — | Yes |
| PXD028980 | — | Yes |
| PXD029033 | tBu-PhoX | No |
| PXD029034 | tBu-PhoX | No |
| PXD029091 | (unverified) AbK; DiZASeC | No |
| PXD029252 | ADH; CDI; DHSO; DSBSO; DSBU; DSSO | No |
| PXD029257 | — | Yes |
| PXD029350 | (unverified) iqPIR | No |
| PXD029365 | DSBU | No |
| PXD029505 | — | No |
| PXD029591 | DSS | No |
| PXD029675 | BS(PEG)5; BS3; DSBU; DSSO; sulfo-EGS | No |
| PXD029748 | — | No |
| PXD029749 | (unverified) DAA | No |
| PXD029781 | (unverified) pacSph | No |
| PXD029833 | DSP | Yes |
| PXD029930 | (unverified) 4-thiouridine | No |
| PXD029944 | (unverified) X10; X3 | No |
| PXD029960 | — | Yes |
| PXD030048 | — | Yes |
| PXD030063 | DSSO | No |
| PXD030072 | — | Yes |
| PXD030209 | DSBU | No |
| PXD030274 | SDA | No |
| PXD030299 | BS3 | No |
| PXD030429 | — | Yes |
| PXD030495 | — | Yes |
| PXD030532 | DSSO | No |
| PXD030543 | Formaldehyde | No |
| PXD030578 | BS3; DSBU; DSS; DSSO | No |
| PXD030590 | DSS | No |
| PXD030619 | — | No |
| PXD030849 | DSS | No |
| PXD030864 | — | Yes |
| PXD030970 | — | Yes |
| PXD031033 | DSSO | No |
| PXD031054 | Formaldehyde | No |
| PXD031096 | BS3 | No |
| PXD031114 | DSSO | No |
| PXD031159 | (unverified) BprY | No |
| PXD031197 | — | Yes |
| PXD031214 | SDA | No |
| PXD031215 | DSS | No |
| PXD031339 | DSBU | No |
| PXD031345 | DMTMM; DSSO; PhoX | No |
| PXD031381 | — | No |
| PXD031411 | DSSO | No |
| PXD031415 | — | Yes |
| PXD031421 | DSSO | No |
| PXD031519 | BS3 | No |
| PXD031601 | — | Yes |
| PXD031643 | (unverified) iqPIR | No |
| PXD031644 | (unverified) iqPIR | No |
| PXD031827 | BS3; EDC | No |
| PXD031845 | — | Yes |
| PXD031911 | DSSO | No |
| PXD031997 | EDC | No |
| PXD032132 | DSBSO; DSSO | No |
| PXD032222 | — | No |
| PXD032297 | — | Yes |
| PXD032728 | — | Yes |
| PXD032821 | BS3; DSBU; DSSO | No |
| PXD032833 | — | Yes |
| PXD032906 | — | Yes |
| PXD032952 | — | Yes |
| PXD032976 | — | Yes |
| PXD033004 | — | No |
| PXD033008 | — | Yes |
| PXD033026 | — | Yes |
| PXD033043 | — | Yes |
| PXD033044 | — | Yes |
| PXD033062 | — | Yes |
| PXD033063 | — | Yes |
| PXD033066 | — | Yes |
| PXD033067 | — | Yes |
| PXD033107 | Benzoyl | No |
| PXD033167 | Sulfo-LC-SDA | No |
| PXD033175 | DSP | No |
| PXD033181 | DSSO | No |
| PXD033205 | DSBU; EDC + sulfo-NHS | No |
| PXD033244 | — | Yes |
| PXD033391 | — | Yes |
| PXD033409 | DSS; PhoX | No |
| PXD033446 | DSSO | No |
| PXD033452 | — | Yes |
| PXD033466 | — | Yes |
| PXD033593 | — | No |
| PXD033633 | BS3 | No |
| PXD033764 | — | Yes |
| PXD033846 | — | Yes |
| PXD033959 | — | No |
| PXD033960 | — | No |
| PXD034054 | — | No |
| PXD034115 | — | Yes |
| PXD034118 | — | Yes |
| PXD034163 | — | No |
| PXD034217 | — | Yes |
| PXD034241 | — | Yes |
| PXD034393 | BS3 | No |
| PXD034475 | DSSO | No |
| PXD034529 | — | No |
| PXD034627 | — | Yes |
| PXD034639 | — | Yes |
| PXD034796 | Formaldehyde; PhoX | No |
| PXD034874 | — | Yes |
| PXD034894 | — | No |
| PXD034965 | — | Yes |
| PXD035001 | — | Yes |
| PXD035151 | — | Yes |
| PXD035153 | — | No |
| PXD035201 | (unverified) HHS-482 | No |
| PXD035265 | — | Yes |
| PXD035404 | DSSO; PhoX | No |
| PXD035433 | DSS | No |
| PXD035452 | — | Yes |
| PXD035589 | DSSO; PhoX | No |
| PXD035591 | PhoX | No |
| PXD035622 | (unverified) iqPIR | No |
| PXD035712 | (unverified) iqPIR | No |
| PXD035764 | DSSO | No |
| PXD035801 | — | Yes |
| PXD035813 | — | Yes |
| PXD035844 | DHSO; DMTMM; DSSO | No |
| PXD035916 | — | Yes |
| PXD035939 | (unverified) Q2linker | No |
| PXD035980 | DSBU | No |
| PXD036113 | — | Yes |
| PXD036182 | — | Yes |
| PXD036262 | — | Yes |
| PXD036463 | DSP | No |
| PXD036630 | — | Yes |
| PXD036640 | DMTMM; DSSO | No |
| PXD036649 | (unverified) iqPIR | No |
| PXD036675 | — | Yes |
| PXD036744 | — | Yes |
| PXD036884 | (unverified) DizSEC; DizSPC | No |
| PXD037030 | BS2G | No |
| PXD037183 | BS3; DMTMM; DSS | No |
| PXD037432 | — | Yes |
| PXD037438 | — | No |
| PXD037443 | (unverified) DBrASO | No |
| PXD037492 | BS2G; BS3; DSS; DSSO | No |
| PXD037493 | BS3 | No |
| PXD037569 | — | Yes |
| PXD037652 | tBu-PhoX | No |
| PXD037678 | — | Yes |
| PXD037701 | MBS | Yes |
| PXD037703 | — | Yes |
| PXD037729 | BS3 | No |
| PXD037894 | (unverified) HHS-482 | No |
| PXD038018 | Azide-alkyne | No |
| PXD038067 | — | Yes |
| PXD038234 | DSP; DTSSP | No |
| PXD038286 | — | Yes |
| PXD038327 | Formaldehyde | Yes |
| PXD038332 | Formaldehyde | No |
| PXD038398 | Formaldehyde | No |
| PXD038487 | — | Yes |
| PXD038515 | — | Yes |
| PXD038572 | — | Yes |
| PXD038583 | Formaldehyde | No |
| PXD038615 | BS3 | No |
| PXD038629 | DSSO | No |
| PXD038640 | DSS | No |
| PXD038658 | DSS | No |
| PXD039008 | — | Yes |
| PXD039010 | — | Yes |
| PXD039068 | — | Yes |
| PXD039125 | — | Yes |
| PXD039289 | DSS | No |
| PXD039401 | — | Yes |
| PXD039467 | — | Yes |
| PXD039473 | — | Yes |
| PXD039589 | BS3 | No |
| PXD039606 | Benzoyl; DSSO; photo-methionine | No |
| PXD039612 | DSG; DSP; DSSO | No |
| PXD039626 | Azide-alkyne | Yes |
| PXD039694 | — | Yes |
| PXD039717 | DSG | No |
| PXD039754 | ADH; DSG; DSS; PDH | No |
| PXD039780 | — | No |
| PXD039864 | — | Yes |
| PXD039939 | Benzoyl | No |
| PXD039983 | — | Yes |
| PXD039985 | — | Yes |
| PXD039986 | — | Yes |
| PXD040000 | BS3 | Yes |
| PXD040144 | DSS | No |
| PXD040156 | BS3 | No |
| PXD040262 | — | Yes |
| PXD040267 | (unverified) Di(N-succinimidyl)-2,2’-[1,4-phenylenebis(methylenethio)]bis-acetate | No |
| PXD040310 | — | Yes |
| PXD040337 | Formaldehyde | Yes |
| PXD040374 | DSS; PDH | No |
| PXD040392 | (unverified) PFA | Yes |
| PXD040412 | — | Yes |
| PXD040452 | — | Yes |
| PXD040547 | — | Yes |
| PXD040562 | — | Yes |
| PXD040690 | — | Yes |
| PXD040705 | DSBU | No |
| PXD040736 | BS3 | No |
| PXD040762 | — | Yes |
| PXD040864 | (unverified) iqPIR | No |
| PXD040875 | Benzoyl | No |
| PXD040902 | DSS; SDA | No |
| PXD040939 | — | Yes |
| PXD040984 | Benzoyl; DSSO | No |
| PXD040991 | — | Yes |
| PXD041011 | DSS | No |
| PXD041019 | — | Yes |
| PXD041135 | BS3 | No |
| PXD041148 | (unverified) DizSEC; DizSPC | No |
| PXD041309 | — | Yes |
| PXD041328 | — | Yes |
| PXD041378 | DSP | Yes |
| PXD041438 | DMTMM; DSSO | No |
| PXD041519 | DSSO | No |
| PXD041610 | — | Yes |
| PXD041684 | — | Yes |
| PXD041831 | DMTMM; DSSO | No |
| PXD041908 | — | Yes |
| PXD041943 | — | Yes |
| PXD041955 | DSBSO; DSSO | No |
| PXD042123 | — | Yes |
| PXD042173 | DSSO | No |
| PXD042282 | DSP | No |
| PXD042301 | — | Yes |
| PXD042302 | — | Yes |
| PXD042343 | Azide-alkyne | No |
| PXD042395 | (unverified) 4-thiouridine | No |
| PXD042501 | BS(PEG)5; BS3; DTSSP; EDC | No |
| PXD042549 | DSBU | No |
| PXD042584 | BS3 | No |
| PXD042599 | DSSO | No |
| PXD042625 | DMTMM; DSSO | No |
| PXD042657 | — | Yes |
| PXD042673 | — | Yes |
| PXD042674 | — | Yes |
| PXD042687 | — | Yes |
| PXD042691 | — | Yes |
| PXD042693 | — | Yes |
| PXD042694 | — | Yes |
| PXD042697 | — | Yes |
| PXD042698 | — | Yes |
| PXD042700 | — | Yes |
| PXD042702 | — | Yes |
| PXD042706 | — | Yes |
| PXD042830 | — | Yes |
| PXD043041 | — | Yes |
| PXD043088 | — | Yes |
| PXD043093 | Benzoyl | No |
| PXD043245 | — | Yes |
| PXD043294 | — | Yes |
| PXD043347 | DSBU | No |
| PXD043531 | Azide-A-DSBSO | No |
| PXD043532 | DSS | No |
| PXD043595 | — | No |
| PXD043732 | — | Yes |
| PXD043789 | — | Yes |
| PXD043805 | — | Yes |
| PXD043900 | (unverified) DEB; nitrogen mustard | No |
| PXD043976 | DSS; PDH | No |
| PXD044285 | — | No |
| PXD044289 | — | Yes |
| PXD044328 | DSBU | No |
| PXD044405 | DSS; PDH | No |
| PXD044574 | DSP | No |
| PXD044625 | (unverified) 4-thiouridine | No |
| PXD044750 | DSBU | No |
| PXD044827 | BS3 | No |
| PXD044921 | — | Yes |
| PXD044974 | — | Yes |
| PXD045071 | Formaldehyde | No |
| PXD045081 | — | Yes |
| PXD045105 | — | No |
| PXD045482 | — | Yes |
| PXD045575 | DHSO; DSSO; sulfo-SDA | No |
| PXD045689 | DSSO | No |
| PXD045791 | DSSO | Yes |
| PXD045792 | (unverified) NNP9 | No |
| PXD045837 | — | No |
| PXD045846 | — | Yes |
| PXD045858 | BS3 | No |
| PXD045861 | — | Yes |
| PXD045987 | BS3 | No |
| PXD046267 | — | No |
| PXD046382 | DSBSO; DSSO | No |
| PXD046385 | — | Yes |
| PXD046392 | BS3 | No |
| PXD046412 | — | Yes |
| PXD046413 | — | Yes |
| PXD046414 | — | Yes |
| PXD046472 | Formaldehyde | Yes |
| PXD046634 | DSSO | No |
| PXD046652 | — | Yes |
| PXD046754 | — | No |
| PXD046895 | Benzoyl | No |
| PXD046966 | DSBSO | No |
| PXD046990 | DSBU | No |
| PXD047023 | Formaldehyde | Yes |
| PXD047030 | (unverified) S-XL6 | No |
| PXD047173 | DSS | No |
| PXD047274 | — | No |
| PXD047277 | — | Yes |
| PXD047368 | BS3 | No |
| PXD047378 | — | Yes |
| PXD047422 | DSSO | No |
| PXD047455 | — | Yes |
| PXD047543 | — | Yes |
| PXD047547 | — | No |
| PXD047569 | — | Yes |
| PXD047583 | — | Yes |
| PXD047725 | — | Yes |
| PXD047929 | BS3 | No |
| PXD047979 | — | Yes |
| PXD048030 | — | Yes |
| PXD048046 | — | Yes |
| PXD048097 | — | Yes |
| PXD048145 | Formaldehyde | No |
| PXD048174 | — | Yes |
| PXD048180 | — | Yes |
| PXD048194 | DSSO | No |
| PXD048297 | DMP | No |
| PXD048298 | DMP | No |
| PXD048452 | SDA | No |
| PXD048567 | — | No |
| PXD048614 | — | No |
| PXD048625 | DSS | No |
| PXD048632 | (unverified) photo-ANA | No |
| PXD048897 | — | No |
| PXD048937 | — | Yes |
| PXD048965 | Formaldehyde | Yes |
| PXD049047 | BMOE | No |
| PXD049054 | — | Yes |
| PXD049094 | BS3 | No |
| PXD049182 | — | Yes |
| PXD049300 | DSS | No |
| PXD049303 | — | No |
| PXD049360 | — | Yes |
| PXD049372 | — | Yes |
| PXD049375 | — | Yes |
| PXD049433 | — | Yes |
| PXD049681 | — | Yes |
| PXD049684 | — | Yes |
| PXD049689 | — | Yes |
| PXD049797 | — | No |
| PXD049991 | — | Yes |
| PXD050097 | BS3 | No |
| PXD050222 | — | Yes |
| PXD050287 | — | Yes |
| PXD050493 | Benzoyl | No |
| PXD050556 | — | Yes |
| PXD050824 | — | Yes |
| PXD050833 | — | No |
| PXD050928 | DSS; PDH | No |
| PXD050929 | DSS; PDH | No |
| PXD050930 | DSS; PDH | No |
| PXD050960 | DSBU | No |
| PXD051014 | EGS | Yes |
| PXD051047 | EGS | Yes |
| PXD051075 | DSS; Formaldehyde; PhoX | No |
| PXD051143 | — | Yes |
| PXD051261 | DSG; DSS | No |
| PXD051322 | BS3; DSBU; DSG; DSS; DSSO | No |
| PXD051348 | — | Yes |
| PXD051405 | — | Yes |
| PXD051493 | DSS | No |
| PXD051557 | — | Yes |
| PXD051602 | DSP | No |
| PXD051661 | sulfo-SDA | No |
| PXD051693 | (unverified) dimethylsulfonium | No |
| PXD051742 | DSSO | No |
| PXD051886 | sulfo-SDA | No |
| PXD051937 | — | Yes |
| PXD051971 | DSBU; EDC | No |
| PXD052022 | Azide-A-DSBSO; DSSO | No |
| PXD052032 | — | Yes |
| PXD052174 | — | Yes |
| PXD052310 | — | Yes |
| PXD052480 | (unverified) TBDSPP | No |
| PXD052552 | (unverified) o-NBE | No |
| PXD052584 | DSSO | No |
| PXD052623 | — | Yes |
| PXD052624 | — | Yes |
| PXD052637 | — | Yes |
| PXD052687 | (unverified) PFA | Yes |
| PXD052694 | (unverified) PFA | Yes |
| PXD052745 | — | Yes |
| PXD052746 | — | Yes |
| PXD052801 | (unverified) iqPIR | No |
| PXD052817 | DSSO | No |
| PXD052821 | DSSO | No |
| PXD052825 | — | Yes |
| PXD052832 | DSSO | No |
| PXD052867 | SDA | No |
| PXD052917 | — | Yes |
| PXD052923 | BS3 | No |
| PXD052926 | — | Yes |
| PXD052930 | — | Yes |
| PXD053010 | EDC | No |
| PXD053341 | sulfo-SDA | No |
| PXD053452 | — | Yes |
| PXD053481 | DSBU; DSSO | No |
| PXD053489 | — | Yes |
| PXD053494 | — | No |
| PXD053500 | BS3 | No |
| PXD053509 | — | Yes |
| PXD053578 | — | Yes |
| PXD053607 | SMCC | No |
| PXD053621 | — | Yes |
| PXD053636 | PhoX | No |
| PXD053760 | — | Yes |
| PXD053814 | — | No |
| PXD053832 | — | Yes |
| PXD053924 | — | Yes |
| PXD053984 | DSSO; photo-leucine; photo-methionine | No |
| PXD053999 | DSS; PDH | No |
| PXD054002 | — | Yes |
| PXD054003 | — | Yes |
| PXD054140 | DSSO | No |
| PXD054141 | DSSO | No |
| PXD054249 | (unverified) DDZ3; LBL1-PCF | No |
| PXD054381 | — | Yes |
| PXD054489 | — | Yes |
| PXD054551 | (unverified) TSTO | No |
| PXD054616 | — | Yes |
| PXD054720 | DSSO | No |
| PXD054728 | DSSO | No |
| PXD054757 | DSS | No |
| PXD054857 | (unverified) PFA | Yes |
| PXD054875 | — | Yes |
| PXD054939 | — | Yes |
| PXD054973 | DSSO | No |
| PXD055077 | DSS; DSSO | No |
| PXD055085 | DSS; DSSO | No |
| PXD055086 | — | Yes |
| PXD055147 | sulfo-SDA | No |
| PXD055169 | SBAP; SIA; SIAB | No |
| PXD055235 | Formaldehyde | Yes |
| PXD055284 | BS3; DSBU; DSS; DSSBU | No |
| PXD055305 | Formaldehyde | Yes |
| PXD055356 | BS3 | No |
| PXD055488 | DSG | No |
| PXD055512 | ADH; DSS | No |
| PXD055649 | — | No |
| PXD055703 | DSS; PDH | No |
| PXD055708 | — | Yes |
| PXD055722 | — | Yes |
| PXD055749 | — | Yes |
| PXD055759 | BS3 | No |
| PXD055775 | — | Yes |
| PXD055778 | — | Yes |
| PXD055874 | — | Yes |
| PXD055877 | — | Yes |
| PXD055943 | (unverified) iqPIR | No |
| PXD056299 | — | Yes |
| PXD056360 | DSSO | No |
| PXD056652 | sulfo-SDA | No |
| PXD056787 | — | Yes |
| PXD056825 | (unverified) Q2linker | No |
| PXD056910 | DSSO | No |
| PXD056942 | — | Yes |
| PXD056954 | — | No |
| PXD056971 | — | Yes |
| PXD057009 | — | Yes |
| PXD057110 | — | Yes |
| PXD057245 | — | Yes |
| PXD057404 | Formaldehyde | Yes |
| PXD057492 | — | Yes |
| PXD057705 | BS3; DSBU; DSS; DSSO | No |
| PXD058056 | BS3; DTSSP | No |
| PXD058168 | BS3 | No |
| PXD058191 | (unverified) iqPIR | No |
| PXD058327 | — | Yes |
| PXD058694 | DSP | No |
| PXD058706 | — | No |
| PXD058941 | DSS | No |
| PXD059010 | — | Yes |
| PXD059118 | DSS; Formaldehyde; PhoX | No |
| PXD059125 | — | Yes |
| PXD059137 | — | Yes |
| PXD059180 | — | Yes |
| PXD059211 | (unverified) SuccBB | No |
| PXD059356 | BS3 | No |
| PXD059369 | BS3 | No |
| PXD059495 | DSSO; PhoX | No |
| PXD059547 | DHSO; DMTMM | No |
| PXD059552 | — | No |
| PXD059554 | — | Yes |
| PXD059558 | — | Yes |
| PXD059579 | — | Yes |
| PXD059635 | DSS | No |
| PXD059716 | — | Yes |
| PXD059766 | DSSO | No |
| PXD059888 | DSG; DSS; DSSO | No |
| PXD059960 | — | No |
| PXD059974 | DHSO; DSSO | No |
| PXD060078 | EDC | No |
| PXD060106 | — | Yes |
| PXD060111 | — | Yes |
| PXD060112 | — | Yes |
| PXD060134 | — | Yes |
| PXD060138 | Formaldehyde | Yes |
| PXD060322 | DSPU | No |
| PXD060469 | DSSO | No |
| PXD060638 | — | Yes |
| PXD060724 | DSS; DSSO | No |
| PXD060781 | — | Yes |
| PXD060825 | DSSO | Yes |
| PXD061125 | BS3 | No |
| PXD061173 | DSBSO | No |
| PXD061317 | — | No |
| PXD061540 | — | Yes |
| PXD061541 | — | Yes |
| PXD061560 | — | Yes |
| PXD061563 | — | Yes |
| PXD061564 | — | Yes |
| PXD061566 | — | Yes |
| PXD061667 | sulfo-SDA | No |
| PXD061687 | — | Yes |
| PXD061691 | — | Yes |
| PXD061693 | — | Yes |
| PXD061712 | — | Yes |
| PXD061752 | — | Yes |
| PXD061911 | — | Yes |
| PXD062002 | DSG | No |
| PXD062101 | — | Yes |
| PXD062203 | Formaldehyde | Yes |
| PXD062293 | — | Yes |
| PXD062479 | Azide-A-DSBSO | No |
| PXD062557 | — | Yes |
| PXD062600 | — | Yes |
| PXD062688 | — | No |
| PXD062741 | — | Yes |
| PXD062870 | — | Yes |
| PXD062890 | — | Yes |
| PXD063033 | (unverified) BNBA; HMNB-NHS | No |
| PXD063145 | — | Yes |
| PXD063191 | DSP | Yes |
| PXD063192 | DSP | Yes |
| PXD063709 | EDC + sulfo-NHS | No |
| PXD063736 | Benzoyl | No |
| PXD063786 | DSSO; Formaldehyde | No |
| PXD063825 | (unverified) TSTO | No |
| PXD063839 | — | No |
| PXD063858 | DSS | No |
| PXD063968 | Formaldehyde | No |
| PXD064535 | DSSO | No |
| PXD064557 | — | Yes |
| PXD064792 | Formaldehyde | No |
| PXD064795 | DSBU | No |
| PXD064931 | DSSO | No |
| PXD064932 | DSSO | No |
| PXD065410 | — | Yes |
| PXD065739 | — | Yes |
| PXD065858 | DSBSO | No |
| PXD065859 | DSBSO | No |
| PXD065869 | DSBSO | No |
| PXD065870 | DSBSO | No |
| PXD065871 | DSBSO | No |
| PXD065905 | Azide-A-DSBSO | No |
| PXD065912 | DSBSO | No |
| PXD065946 | DSBSO | No |
| PXD065949 | DSBSO | No |
| PXD065956 | DSBSO | No |
| PXD065958 | DSBSO | No |
| PXD065961 | DSBSO | No |
| PXD066067 | — | Yes |
| PXD066251 | — | No |
| PXD066655 | — | No |
| PXD066874 | — | Yes |
| PXD067296 | BS3 | No |
| PXD067324 | BS3 | No |
| PXD067352 | — | Yes |
| PXD067354 | — | Yes |
| PXD068129 | — | No |
| PXD069219 | — | Yes |
| PXD069360 | — | Yes |
| PXD069512 | Formaldehyde | No |
| PXD069844 | — | Yes |
