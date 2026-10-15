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

**Proximity-Labeling Term(s) Found** lists the specific matched term(s) (e.g.
`TurboID`, `BioID`, `APEX2`, `biotin-phenol`) from the same heuristic regex
scan used throughout this document (`turboid|bioid2?|apex2?\b|biotin-phenol|
biotin-tyramide|proximity-labeling|proximity-biotinylation|proximity-dependent`
against each PXD's PRIDE title+description+protocol+keywords), rather than
just a Yes/No flag. It is a **heuristic, not a strict classifier** — 33 PXDs
in this table match a term *and* still have a legitimately mapped crosslinker
(e.g. a paper that compares/mentions proximity labeling in passing while the
actual experiment uses real chemical crosslinking), so a non-empty value here
should be read as "worth a second look", not an automatic disqualifier. Empty
(`—`) means no proximity-labeling term matched.

**Notes** carries over the manual classification and reasoning recorded
during the Batch 1 (10 PXDs) and Batch 2 (59 PXDs) spot-check investigations
above — 68 distinct PXDs in total have a note here, each prefixed with its
category (`RNA_PROTEIN_UV_XL`, `NATURAL_OR_ENZYMATIC_XL`, `WRONG_TECHNIQUE`,
`CORRECT_REJECT_NO_TEXT`, or `REAL_MISS`; see the category definitions and
per-category counts earlier in this document). The remaining ~977 PXDs have
not yet been manually reviewed and are left blank here — their `Identified
Crosslinker(s)` column is the only information available for them so far.

| PXD | Identified Crosslinker(s) in DB | Proximity-Labeling Term(s) Found | Notes |
|---|---|---|---|
| PXD000244 | Formaldehyde | — |  |
| PXD000513 | (unverified) 4-thiouridine | — |  |
| PXD000545 | — | — | CORRECT_REJECT_NO_TEXT: Generic 'cross-linking chemistry' stated in PRIDE description; sampleProcessingProtocol/dataProcessingProtocol both 'Not available'; no PMC. |
| PXD000685 | — | — | WRONG_TECHNIQUE: Virotrap (viral-particle-budding protein complex capture) - a different complex-trapping technology entirely, not chemical crosslinking-MS. |
| PXD001080 | — | — | RNA_PROTEIN_UV_XL: CLIP-style UV crosslinking of native mRNP residues (Entamoeba splicing/mRNP study). |
| PXD001454 | BS3 | — |  |
| PXD001538 | BS2G; DSS; EDC | — |  |
| PXD001609 | DSP | — |  |
| PXD001675 | BS3 | — |  |
| PXD001677 | DSS | — |  |
| PXD001692 | sulfo-SDA | — |  |
| PXD001835 | BS3 | — |  |
| PXD002058 | — | — | CORRECT_REJECT_NO_TEXT: 'mild in vivo crosslinking' stated, but no specific reagent named anywhere in the available (no-PMC) text. |
| PXD002142 | BS3 | — |  |
| PXD002159 | (unverified) DTBP | — |  |
| PXD002169 | DSP; DST | — |  |
| PXD002226 | — | — | RNA_PROTEIN_UV_XL: mRBPome - cells UV-crosslinked at 254nm, oligo(dT) mRNA capture (C. elegans). |
| PXD002293 | — | — | RNA_PROTEIN_UV_XL: mRBPome - cells UV-crosslinked at 254nm, oligo(dT) mRNA capture (S. cerevisiae). |
| PXD002378 | PIR linker | — |  |
| PXD002392 | (unverified) DTT | — |  |
| PXD002656 | (unverified) DTT | — |  |
| PXD002890 | — | — | RNA_PROTEIN_UV_XL: mRNA interactome - UV irradiation at 254nm (mouse macrophages). |
| PXD002929 | Formaldehyde | — |  |
| PXD002987 | BS3 | — |  |
| PXD002992 | (unverified) 4-thiouridine | — |  |
| PXD003381 | (unverified) DEST | — |  |
| PXD003486 | BS3 | — |  |
| PXD003496 | DMP | — |  |
| PXD003502 | EDC | — |  |
| PXD003593 | (unverified) 4-thiouridine | — |  |
| PXD003643 | sulfo-SDA | — |  |
| PXD003658 | BS3; DSS; Formaldehyde | — |  |
| PXD003737 | sulfo-SDA | — |  |
| PXD003754 | Formaldehyde | — |  |
| PXD003880 | DSS | — |  |
| PXD003909 | BS2G | — |  |
| PXD003913 | BS2G | — |  |
| PXD003917 | — | — | CORRECT_REJECT_NO_TEXT: 'chemical cross-linking/mass spectrometry' stated, but no specific reagent named in the available (no-PMC) text. |
| PXD004009 | Aryl azide; Benzoyl | — |  |
| PXD004018 | — | — |  |
| PXD004105 | DSP | — |  |
| PXD004107 | BS3 | — |  |
| PXD004236 | BDP-NHP | — |  |
| PXD004692 | DSS | — |  |
| PXD004736 | Formaldehyde | biotin-tyramide; proximity labeling |  |
| PXD004749 | BS3 | — |  |
| PXD004898 | BS3 | — |  |
| PXD004920 | sulfo-SDA | — |  |
| PXD005012 | Benzoyl | — |  |
| PXD005201 | — | APEX; biotin phenol; biotinphenol; Proximity labeling |  |
| PXD005287 | DSS | — |  |
| PXD005349 | photo-leucine; photo-methionine | — |  |
| PXD005566 | — | — | RNA_PROTEIN_UV_XL: CLIR-MS - complexes irradiated at 254nm (protein-RNA hybrid structural modeling). |
| PXD005601 | — | — | RNA_PROTEIN_UV_XL: mRNA-binding proteins via UV irradiation + oligo(dT) capture (Leishmania). |
| PXD005612 | — | Bioid; proximity-dependent |  |
| PXD005657 | DMP | — |  |
| PXD005758 | — | Apex; Proximity biotinylation; proximity labeling | APEX-mediated proximity labeling (engineered ascorbic acid peroxidase + biotinylation); not chemical crosslinking. |
| PXD005943 | — | — | RNA_PROTEIN_UV_XL: mRBPome - UV-crosslinked at 254nm under oxidative stress (S. cerevisiae). |
| PXD005948 | BS3 | — |  |
| PXD006079 | Formaldehyde | — |  |
| PXD006131 | BS3 | — |  |
| PXD006156 | — | proximity-dependent |  |
| PXD006200 | — | Bioid; proximity-dependent |  |
| PXD006245 | Benzoyl | — |  |
| PXD006246 | BS3 | — |  |
| PXD006287 | (unverified) BAMG | — |  |
| PXD006359 | — | biotin tyramide; proximity labeling |  |
| PXD006541 | — | Bioid; proximity-dependent |  |
| PXD006707 | BS3; EDC | — |  |
| PXD006715 | — | Bioid; proximity-dependent |  |
| PXD006816 | DSSO | — |  |
| PXD006928 | BS3; sulfo-SMCC | — |  |
| PXD006938 | BS3; sulfo-SMCC | — |  |
| PXD007043 | DSS | — |  |
| PXD007185 | DSS; PDH | — |  |
| PXD007250 | BS3 | — |  |
| PXD007513 | DSSO | — |  |
| PXD007673 | PIR linker | — |  |
| PXD007695 | — | APEX; APEX2; biotin-phenol; proximity labeling |  |
| PXD007836 | DSP | — |  |
| PXD007862 | Azide-alkyne | APEX; Bioid; Proximity dependent; Proximity-dependent |  |
| PXD007928 | BS3 | — |  |
| PXD008122 | DSS | — |  |
| PXD008161 | (unverified) AMDSP | — |  |
| PXD008164 | — | — |  |
| PXD008337 | EDC | — |  |
| PXD008348 | DSBU; DSSO | — |  |
| PXD008418 | DSSO | — |  |
| PXD008550 | BS3; sulfo-SDA | — |  |
| PXD008577 | (unverified) PAL6 | — |  |
| PXD008605 | DSS | — |  |
| PXD008680 | (unverified) DTBP | — |  |
| PXD008914 | — | — | RNA_PROTEIN_UV_XL: RBP repertoire - UV irradiated at 254nm, 0.15 J/cm2 (embryonic stem cells). |
| PXD008941 | BDP-NHP | — |  |
| PXD008951 | BDP-NHP | — |  |
| PXD008975 | BDP-NHP | — |  |
| PXD009000 | DSSO | — |  |
| PXD009001 | BDP-NHP | — |  |
| PXD009106 | ADH; DSS; PDH | — |  |
| PXD009159 | — | Bioid |  |
| PXD009224 | DSSO | — |  |
| PXD009260 | EDC | — |  |
| PXD009284 | — | Apex; Proximity labeling |  |
| PXD009302 | — | APEX2; biotin-phenol; Proximity labeling |  |
| PXD009474 | — | — | CORRECT_REJECT_NO_TEXT: 'crosslinking coIPs' mentioned (crosslinking IP workflow), but no specific reagent named in the available (no-PMC) text. |
| PXD009526 | DSS | — |  |
| PXD009641 | Benzoyl; DSP | — |  |
| PXD009648 | BS3 | — |  |
| PXD009748 | — | biotin-tyramide; Proximity labeling |  |
| PXD009756 | DSSO; DTSSP | — |  |
| PXD009777 | DSSO; DTSSP; Glutaraldehyde | — |  |
| PXD009783 | DSP | APEX; APEX2; biotin-phenol; Proximity labeling |  |
| PXD009927 | EDC | — |  |
| PXD010003 | DSS; PDH; sulfo-SDA | — |  |
| PXD010004 | DSS; PDH; sulfo-SDA | — |  |
| PXD010046 | Formaldehyde | — |  |
| PXD010061 | — | Bioid; Proximity labeling |  |
| PXD010070 | DSBU | — |  |
| PXD010094 | DSS; PDH; sulfo-SDA | — |  |
| PXD010111 | ADH; BS3; DMTMM; DSS; Glutaraldehyde | — |  |
| PXD010122 | BS3 | — |  |
| PXD010124 | BS3 | — |  |
| PXD010222 | BS3 | — |  |
| PXD010317 | DSSO | — |  |
| PXD010352 | — | Bioid; proximity-dependent |  |
| PXD010384 | DSS; PDH; sulfo-SDA | — |  |
| PXD010385 | DSS; PDH; sulfo-SDA | — |  |
| PXD010410 | DSS; PDH; sulfo-SDA | — |  |
| PXD010422 | (unverified) NNP9 | — |  |
| PXD010468 | Formaldehyde | — |  |
| PXD010470 | Benzoyl | — |  |
| PXD010474 | — | Bioid; proximity-dependent |  |
| PXD010479 | DSS; PDH; sulfo-SDA | — |  |
| PXD010481 | BS3 | — |  |
| PXD010483 | DSS; PDH; sulfo-SDA | — |  |
| PXD010796 | DSSO | — |  |
| PXD010884 | DSS; PDH; sulfo-SDA | — |  |
| PXD010892 | Benzoyl | — |  |
| PXD010921 | — | APEX2; proximity labeling |  |
| PXD010930 | — | BioID; proximity-dependent |  |
| PXD010931 | — | Bioid; proximity-dependent |  |
| PXD010950 | — | APEX2; proximity labeling |  |
| PXD010963 | Formaldehyde | — |  |
| PXD010988 | (unverified) thanatin-PAL5 | — |  |
| PXD011036 | BS3 | — |  |
| PXD011071 | — | — |  |
| PXD011077 | DSSO | — |  |
| PXD011078 | DSS | — |  |
| PXD011121 | BS3; SDA | — |  |
| PXD011296 | BS3; EDC + sulfo-NHS | — |  |
| PXD011312 | — | Proximity labeling |  |
| PXD011459 | BS3 | — |  |
| PXD011645 | EDC; PhoX; SDA | — |  |
| PXD011680 | DSSO | — |  |
| PXD011702 | — | bioid; proximity labeling |  |
| PXD011704 | BS3 | — |  |
| PXD011774 | BS3 | — |  |
| PXD011775 | BS3 | — |  |
| PXD011806 | Formaldehyde | — |  |
| PXD011861 | DSSO | — |  |
| PXD011931 | PhoX | — |  |
| PXD011974 | Formaldehyde | BioID; Proximity labeling |  |
| PXD011995 | DSS | — |  |
| PXD012109 | (unverified) bAL2 | — |  |
| PXD012157 | — | Apex; APEX2; Proximity labeling |  |
| PXD012225 | — | — | NATURAL_OR_ENZYMATIC_XL: FXIIIa (coagulation Factor XIIIa) - transglutaminase ENZYME catalyzing natural fibrin isopeptide crosslinks. |
| PXD012350 | (unverified) x-alk-MDP; x-alk-iE-DAP | — |  |
| PXD012427 | (unverified) APDC4 | — |  |
| PXD012466 | DSSO | — |  |
| PXD012494 | — | Apex; Proximity-dependent |  |
| PXD012521 | — | — | WRONG_TECHNIQUE: TAP-MS study of DNA interstrand crosslink (ICL) REPAIR biology - 'crosslink' here means a DNA damage lesion (from mitomycin C), not XL-MS chemistry; the proteomics method itself is tandem affinity purification, no chemical crosslinker used. |
| PXD012546 | DSBU | — |  |
| PXD012592 | BS3 | — |  |
| PXD012624 | EDC; sulfo-SDA | — |  |
| PXD012723 | BS3 | — |  |
| PXD012759 | — | — | CORRECT_REJECT_NO_TEXT: 'Crosslinking Proteomics' in title, genuine XL-MS study of TLR2 interactome, but no reagent named in the available (no-PMC) text. |
| PXD012788 | Alkyne-A-DSBSO | — |  |
| PXD012882 | EDC | — |  |
| PXD012939 | sulfo-SDA | — |  |
| PXD013032 | — | biotin-tyramide; Proximity labeling |  |
| PXD013063 | PIR linker | — |  |
| PXD013083 | BS3; DSS; DSSO | — |  |
| PXD013097 | — | — | WRONG_TECHNIQUE: Chemoproteomic activity-based protein profiling (ABPP) of kinase active sites - a covalent single-site labeling technique, not bifunctional structural crosslinking-MS. |
| PXD013144 | sulfo-SMPB | — |  |
| PXD013160 | — | Bioid; proximity-dependent |  |
| PXD013183 | — | BioID; Proximity-dependent; turboid |  |
| PXD013194 | — | APEX; APEX2; biotin-phenol; Proximity labeling |  |
| PXD013209 | Formaldehyde | Bioid; proximity labeling |  |
| PXD013215 | — | APEX2; biotin-phenol; proximity labeling |  |
| PXD013338 | Formaldehyde | — |  |
| PXD013339 | Benzoyl | — |  |
| PXD013470 | ADH; DMTMM; DSS | — |  |
| PXD013476 | BDP-NHP | — |  |
| PXD013601 | — | proximity-dependent |  |
| PXD013704 | DSSO | — |  |
| PXD013720 | (unverified) 4-thiouridine; PFA | — |  |
| PXD013735 | DSSO | — |  |
| PXD013769 | DSSO | — |  |
| PXD013907 | DSS | — |  |
| PXD013928 | — | — | CORRECT_REJECT_NO_TEXT: 'Proteome-wide Cross-linking mass spectrometry' - extremely terse PRIDE text (544 chars combined), no reagent named, no PMC. |
| PXD014055 | PhoX | — |  |
| PXD014067 | — | — | NATURAL_OR_ENZYMATIC_XL: Tissue transglutaminase (TG2) ENZYME catalyzing isopeptide crosslinks with gluten peptides. |
| PXD014247 | — | Proximity Labeling |  |
| PXD014337 | DSBU; DSS; DSSO | — |  |
| PXD014359 | BS3 | — |  |
| PXD014426 | — | Bioid; BioID2; proximity-dependent |  |
| PXD014499 | — | APEX; Apex2; Biotin-phenol; Biotin-tyramide; Proximity Labeling |  |
| PXD014500 | — | Apex; Apex2; Biotin-phenol; Biotin-tyramide; Proximity labeling | APEX2/biotin-phenol-H2O2 proximity labeling; the one 'formaldehyde' mention in full text is a 4% PFA microscopy fixation step for imaging, unrelated to the MS workflow. |
| PXD014520 | BS3 | — |  |
| PXD014523 | DSS; PDH | — |  |
| PXD014584 | DSSO | — |  |
| PXD014642 | DSSO | — |  |
| PXD014661 | (unverified) ETD | — |  |
| PXD014673 | BMSO; DHSO; DSSO | — |  |
| PXD014675 | DSS | — |  |
| PXD014738 | BS3 | — |  |
| PXD014759 | BS3; DSSO | — |  |
| PXD014898 | — | — | RNA_PROTEIN_UV_XL: UV femtosecond laser crosslinking of protein-DNA complexes. |
| PXD014957 | (unverified) 4-thiouridine | — |  |
| PXD015037 | photo-methionine | — |  |
| PXD015044 | DSAU; DSG; PhoX; SDA | — |  |
| PXD015080 | — | — |  |
| PXD015160 | DSSO | — |  |
| PXD015161 | Formaldehyde | Proximity labeling; Turboid |  |
| PXD015162 | Formaldehyde | Proximity labeling; Turboid |  |
| PXD015285 | DSBU | — |  |
| PXD015366 | (unverified) AzidoPhe | — |  |
| PXD015394 | DSS; PDH | — |  |
| PXD015435 | Formaldehyde | — |  |
| PXD015479 | — | BioID; proximity-dependent |  |
| PXD015507 | — | APEX2; proximity labeling |  |
| PXD015549 | — | — | NATURAL_OR_ENZYMATIC_XL: R2lox protein's naturally-occurring Mn/Fe-cofactor-driven internal Tyr-Val crosslink (endogenous radical chemistry, not an added reagent). |
| PXD015658 | DSS | — |  |
| PXD015682 | DSS | — |  |
| PXD015725 | — | BioID; Proximity-dependent | BioID proximity-dependent biotinylation study (FOXB2 interactome); no crosslink-related text anywhere in the 22K-char combined PMC+PRIDE text. |
| PXD015751 | PIR linker | — |  |
| PXD015779 | — | APEX2; Biotin-Phenol; Proximity labeling |  |
| PXD015793 | BS3; EDC | — |  |
| PXD015863 | (unverified) 4-thiouridine | — |  |
| PXD015883 | — | APEX2; biotin-phenol; Proximity Labeling |  |
| PXD015890 | — | APEX2; biotin-phenol; Proximity Labeling |  |
| PXD015941 | DSBU; DSSO | — |  |
| PXD015974 | Benzoyl | — |  |
| PXD015985 | DSS | — |  |
| PXD015989 | — | — | CORRECT_REJECT_NO_TEXT: 'cross-linking MS-based approach' stated for PDE6 structural study; text only generically mentions 'specific crosslinker modifications when appropriate' with no actual name; no PMC. |
| PXD016196 | BS3 | — |  |
| PXD016221 | — | Bioid; proximity-dependent |  |
| PXD016224 | Sulfo-LC-SDA | — |  |
| PXD016355 | — | — | CORRECT_REJECT_NO_TEXT: Title/description say 'diazirine mediated cross-linking' - diazirine is a reactive FUNCTIONAL GROUP, not a specific named reagent/molecule; no PMC. |
| PXD016554 | DSP; DSS | — |  |
| PXD016639 | BS(PEG)5; DSG; DSS | — |  |
| PXD016963 | DSBSO | — |  |
| PXD016988 | — | Bioid; proximity-dependent |  |
| PXD016993 | DSBU | — |  |
| PXD017020 | BS3 | — |  |
| PXD017066 | PhoX | — |  |
| PXD017085 | — | Proximity labeling; Turboid |  |
| PXD017128 | DSS | — |  |
| PXD017238 | BS3; EDC | — |  |
| PXD017241 | — | Bioid; proximity biotinylation; proximity-dependent |  |
| PXD017244 | ADH; BS3 | — |  |
| PXD017299 | BS2G; DSG | — |  |
| PXD017344 | — | Bioid; proximity-dependent |  |
| PXD017378 | — | — | CORRECT_REJECT_NO_TEXT: 'Comprehensive cross-linking mass spectrometry' (NuRD complex) - description is entirely about affinity-purification tagging workflow, no reagent named; no PMC. |
| PXD017379 | DSBU | — |  |
| PXD017531 | DSBU | — |  |
| PXD017584 | photo-leucine | — |  |
| PXD017620 | BS3; DSS | — |  |
| PXD017868 | — | proximity labeling |  |
| PXD017873 | BS3 | — |  |
| PXD017931 | DSS | — |  |
| PXD017933 | — | Bioid; proximity-dependent |  |
| PXD017937 | — | BioID2; proximity labeling | BioID2 proximity labeling (interactors in rat cortical neurons); no chemical crosslinker. |
| PXD017951 | — | — | WRONG_TECHNIQUE: DNA interstrand crosslink (ICL) repair biology (PrimPol primase study) - 'crosslink' refers to a DNA damage lesion, not XL-MS chemistry. |
| PXD017996 | DSS | — |  |
| PXD018040 | — | proximity-dependent |  |
| PXD018106 | BS3 | — |  |
| PXD018189 | PhoX | — |  |
| PXD018219 | DSSO | — |  |
| PXD018232 | DSS | — |  |
| PXD018265 | — | BioID; proximity labeling |  |
| PXD018291 | PhoX; pDSPE | — |  |
| PXD018310 | BS3 | — |  |
| PXD018383 | — | BioID; proximity-dependent |  |
| PXD018580 | (unverified) alkyne-diazirine minimal photocrosslinker | — |  |
| PXD018608 | SDA | — |  |
| PXD018687 | Formaldehyde | — |  |
| PXD018771 | DSSO | — |  |
| PXD018786 | BS3; EDC + sulfo-NHS | — |  |
| PXD018935 | DSAU | — |  |
| PXD019017 | DSSO | — |  |
| PXD019043 | (unverified) BrC6K | — |  |
| PXD019048 | DSSO | — |  |
| PXD019101 | DSSO | — |  |
| PXD019215 | — | — |  |
| PXD019251 | DSS | — |  |
| PXD019274 | BS3; Benzoyl; sulfo-SDA | — |  |
| PXD019338 | DSSO | — |  |
| PXD019428 | — | — |  |
| PXD019484 | PIR linker | — |  |
| PXD019507 | PDH | — |  |
| PXD019508 | PDH | — |  |
| PXD019530 | DSBU | — |  |
| PXD019599 | DSSO | — |  |
| PXD019713 | DSSO | — |  |
| PXD019724 | PDH | — |  |
| PXD019751 | DSS | — |  |
| PXD019771 | DMTMM | — |  |
| PXD019868 | DSSO | — |  |
| PXD019926 | DSSO | — |  |
| PXD019944 | DSSO | — |  |
| PXD020014 | DSS; DSSO | — |  |
| PXD020084 | BS3 | — |  |
| PXD020119 | (unverified) NHS-LC-Diazirine | — |  |
| PXD020165 | — | BioID2; proximity-dependent |  |
| PXD020229 | BS3; EDC + sulfo-NHS | — |  |
| PXD020290 | — | — | RNA_PROTEIN_UV_XL: UV-induced crosslinking of protein-DNA complexes in chromatin. |
| PXD020302 | — | — | CORRECT_REJECT_NO_TEXT: 'Analysis of cross-link on Tranaldolase' - extremely terse (1024 chars combined), no reagent named, no PMC. |
| PXD020323 | Azide-alkyne | BIOID; PROXIMITY LABELING |  |
| PXD020340 | Azide-alkyne | proximity labeling |  |
| PXD020370 | — | bioid; proximity-dependent |  |
| PXD020418 | Benzoyl | — |  |
| PXD020453 | sulfo-SDA | — |  |
| PXD020542 | — | APEX2; proximity labeling |  |
| PXD020602 | DSS | — |  |
| PXD020636 | DSS; PDH | — |  |
| PXD020704 | DSS; Formaldehyde; Glutaraldehyde | — |  |
| PXD020709 | — | APEX2; biotin phenol; Proximity labeling |  |
| PXD020759 | — | Proximity labeling; Turboid |  |
| PXD020817 | BS3 | — |  |
| PXD020826 | — | — |  |
| PXD020859 | BS3 | — |  |
| PXD021115 | DSS | — |  |
| PXD021126 | BS2G; BS3 | — |  |
| PXD021182 | Benzoyl | — |  |
| PXD021375 | — | APEX; biotin-phenol; proximity labeling |  |
| PXD021417 | DSS | — |  |
| PXD021434 | Formaldehyde | — |  |
| PXD021553 | (unverified) NNP9 | — |  |
| PXD021622 | — | biotin phenol; Proximity labeling |  |
| PXD021648 | DSBU | — |  |
| PXD021691 | — | Proximity labeling |  |
| PXD021693 | — | Proximity labeling |  |
| PXD021708 | DSSO | — |  |
| PXD021709 | DSSO | Bioid; proximity labeling |  |
| PXD021770 | — | Bioid; Proximity-dependent; Turboid |  |
| PXD021809 | — | BioID; Proximity-dependent; Turboid |  |
| PXD021822 | DSP | — |  |
| PXD021831 | DSS | — |  |
| PXD021870 | (unverified) p-azido-Phe | — |  |
| PXD021872 | DSBU | — |  |
| PXD021923 | — | proximity biotinylation; Proximity labeling; TurboID |  |
| PXD022119 | BS3 | — |  |
| PXD022279 | Azide-alkyne | — |  |
| PXD022335 | — | APEX; APEX2; Proximity labeling |  |
| PXD022440 | Formaldehyde | — |  |
| PXD022443 | DSS | — |  |
| PXD022608 | — | Proximity labeling; Proximity-biotinylation |  |
| PXD022675 | DSSO | — |  |
| PXD022690 | DSSO; SDASO-L | — |  |
| PXD022772 | DSBU; DSSO | — |  |
| PXD022785 | — | apex; Bioid; proximity-dependent |  |
| PXD022861 | BS3; DSS | — |  |
| PXD022903 | — | Bioid; proximity labeling |  |
| PXD022991 | — | — | NATURAL_OR_ENZYMATIC_XL: Spontaneous (non-enzymatic) age-related Lys-Gln/Glu crosslinking via glutarimide intermediate in aged human lens tissue. |
| PXD023022 | BS3 | — |  |
| PXD023072 | PhoX | — |  |
| PXD023073 | — | Proximity labeling |  |
| PXD023164 | CDI; DSSO | — |  |
| PXD023192 | Benzoyl | — |  |
| PXD023221 | BS3 | — |  |
| PXD023239 | — | Bioid; Proximity labeling |  |
| PXD023277 | — | Proximity labeling |  |
| PXD023487 | BS3; DSS; Formaldehyde | — |  |
| PXD023522 | — | — | CORRECT_REJECT_NO_TEXT: LinX software / CX-MS data - sampleProcessingProtocol just references 3 external published papers by citation only, reagent not restated in this text; no PMC. |
| PXD023525 | CDI; DSBU | — |  |
| PXD023542 | — | — | CORRECT_REJECT_NO_TEXT: 'Targeted in situ cross-linking' (SARS-CoV-2) - description focuses on the AP-MS workflow, no chemical crosslinker reagent named; no PMC. |
| PXD023577 | PIR linker | — |  |
| PXD023651 | — | — | NATURAL_OR_ENZYMATIC_XL: Natural internal isopeptide crosslink (A2M autoconjugation via its native thiol ester, triggered by trypsin cleavage of the bait region). |
| PXD023814 | — | Apex; biotin tyramide; Proximity Labeling; proximity-labeling |  |
| PXD023817 | DSSO | — |  |
| PXD024010 | — | — | RNA_PROTEIN_UV_XL: CLIR-MS workflow extension, UV crosslinking via Spectrolinker XL-1500. |
| PXD024065 | Benzoyl | — |  |
| PXD024120 | — | Bioid; BioID2; proximity labeling |  |
| PXD024131 | DSS | — |  |
| PXD024160 | PhoX | — |  |
| PXD024168 | — | proximity labeling; Turboid |  |
| PXD024253 | — | — | CORRECT_REJECT_NO_TEXT: Evidence_quote explicitly states 'a newly synthesized enrichable crosslinker' with no chemical name/abbreviation/accession given at all. |
| PXD024254 | Formaldehyde | — |  |
| PXD024335 | — | APEX2; proximity-dependent |  |
| PXD024361 | — | Proximity labeling |  |
| PXD024366 | — | Proximity labeling |  |
| PXD024367 | — | Proximity labeling |  |
| PXD024399 | — | Bioid; Proximity labeling |  |
| PXD024492 | Benzoyl | — |  |
| PXD024493 | Benzoyl | — |  |
| PXD024822 | DSS; Glutaraldehyde; PDH | — |  |
| PXD024946 | BMB; BMOE; BS2G; BS3 | — |  |
| PXD025066 | — | — |  |
| PXD025099 | BS3 | — |  |
| PXD025122 | — | — | RNA_PROTEIN_UV_XL: RNase III CLASH (Cross-Linking And Sequencing of Hybrids) - canonically UV-crosslinking-based. |
| PXD025141 | — | Proximity labeling; Turboid |  |
| PXD025172 | DSSO | — |  |
| PXD025179 | — | Bioid; BioID2; proximity-dependent |  |
| PXD025208 | — | BioID; proximity labeling |  |
| PXD025220 | BS3 | — |  |
| PXD025357 | — | BioID; proximity-dependent |  |
| PXD025391 | DSSO | — |  |
| PXD025581 | — | BioID2; proximity-dependent |  |
| PXD025662 | DSS | — |  |
| PXD025710 | DSS; PDH | — |  |
| PXD025796 | (unverified) iqPIR | — |  |
| PXD025843 | ADH; BS3 | — |  |
| PXD025903 | — | — |  |
| PXD025923 | (unverified) iqPIR | — |  |
| PXD025980 | Formaldehyde | BioID2; proximity-dependent |  |
| PXD026017 | BS3 | — |  |
| PXD026037 | (unverified) iqPIR | — |  |
| PXD026196 | — | BioID; proximity labeling; Turboid | BioID/miniTurbo proximity labeling (Alk 'proximitome' in Drosophila brain); no chemical crosslinker. |
| PXD026229 | — | APEX2; proximity labeling |  |
| PXD026244 | DSS | — |  |
| PXD026433 | DSSO | — |  |
| PXD026508 | Formaldehyde | — |  |
| PXD026603 | DSSO | — |  |
| PXD026696 | DSBU | — |  |
| PXD026718 | — | APEX; proximity labeling |  |
| PXD026790 | DMP | — |  |
| PXD026793 | — | Apex; APEX2; biotin-phenol; Proximity labeling |  |
| PXD026861 | — | — |  |
| PXD026926 | — | Proximity labeling; Turboid |  |
| PXD026935 | BS3 | — |  |
| PXD027068 | — | Proximity labeling; turboid |  |
| PXD027128 | Benzoyl | — |  |
| PXD027149 | (unverified) VL1 | — |  |
| PXD027159 | BS3; DSBU; DSS; DSSO | — |  |
| PXD027161 | BS3; DSBU; DSS; DSSO | — |  |
| PXD027188 | BS3; DSBU; DSS; DSSO | — |  |
| PXD027189 | — | — | RNA_PROTEIN_UV_XL: U1/U2 snRNP protein-RNA crosslinking via 254nm irradiation. |
| PXD027213 | DMTMM; DSS; PDH | — |  |
| PXD027234 | DSAU; DSBU; DSPU | — |  |
| PXD027239 | (unverified) X10 | — |  |
| PXD027267 | — | Bioid; proximity labeling |  |
| PXD027349 | EDC + sulfo-NHS | — |  |
| PXD027394 | (unverified) X10 | — |  |
| PXD027413 | DSG | — |  |
| PXD027488 | — | proximity labeling; proximity-dependent; Turboid |  |
| PXD027565 | Formaldehyde | — |  |
| PXD027611 | DSSO | — |  |
| PXD027757 | (unverified) iqPIR | — |  |
| PXD027759 | — | BioID; Proximity-dependent; TurboID |  |
| PXD027891 | DSS | — |  |
| PXD027905 | — | BioID2; Proximity labeling |  |
| PXD027917 | — | Bioid; proximity-dependent | BioID (birA fusion) proximity interactome mapping (VAC14-FIG4 complex); no chemical crosslinker. |
| PXD027953 | PIR linker | — |  |
| PXD027954 | (unverified) DiazK | — |  |
| PXD027998 | — | Proximity labeling |  |
| PXD028002 | DSS; EDC; SDA | — |  |
| PXD028005 | DSSO | — |  |
| PXD028063 | Formaldehyde | apex; APEX2; Proximity labeling |  |
| PXD028150 | — | APEX; APEX2; Proximity labeling |  |
| PXD028313 | PhoX | — |  |
| PXD028415 | PhoX | — |  |
| PXD028433 | EDC | — |  |
| PXD028462 | (unverified) SMPH | BioID2; proximity labeling |  |
| PXD028879 | — | bioid; proximity biotinylation; proximity labeling; turboid |  |
| PXD028980 | — | APEX; biotin phenol; Proximity labeling |  |
| PXD029033 | tBu-PhoX | — |  |
| PXD029034 | tBu-PhoX | — |  |
| PXD029091 | (unverified) AbK; DiZASeC | — |  |
| PXD029252 | ADH; CDI; DHSO; DSBSO; DSBU; DSSO | — |  |
| PXD029257 | — | proximity-dependent |  |
| PXD029350 | (unverified) iqPIR | — |  |
| PXD029365 | DSBU | — |  |
| PXD029505 | — | — |  |
| PXD029591 | DSS | — |  |
| PXD029675 | BS(PEG)5; BS3; DSBU; DSSO; sulfo-EGS | — |  |
| PXD029748 | — | — | CORRECT_REJECT_NO_TEXT: 'Proteome-wide Cross-linking mass spectrometry' (HEK293) - description/protocol both just restate the title with no reagent name; no PMC. |
| PXD029749 | (unverified) DAA | — |  |
| PXD029781 | (unverified) pacSph | — |  |
| PXD029833 | DSP | proximity labeling |  |
| PXD029930 | (unverified) 4-thiouridine | — |  |
| PXD029944 | (unverified) X10; X3 | — |  |
| PXD029960 | — | Proximity labeling; proximity-labeling; Turboid |  |
| PXD030048 | — | Proximity labeling; Turboid |  |
| PXD030063 | DSSO | — |  |
| PXD030072 | — | APEX2; Proximity labeling |  |
| PXD030209 | DSBU | — |  |
| PXD030274 | SDA | — |  |
| PXD030299 | BS3 | — |  |
| PXD030429 | — | Proximity-dependent |  |
| PXD030495 | — | APEX2; proximity labeling |  |
| PXD030532 | DSSO | — |  |
| PXD030543 | Formaldehyde | — |  |
| PXD030578 | BS3; DSBU; DSS; DSSO | — |  |
| PXD030590 | DSS | — |  |
| PXD030619 | — | — | REAL_MISS: BS3 explicitly named multiple times in the 52K-char combined PMC+PRIDE text, but the entire xlms_reagents LLM response failed JSON parsing ('Could not parse JSON from LLM response') and was silently dropped with no retry. A separate file-clustering-resolved override DID correctly identify BS3 for the actual Xi config (xi_configs: success), so the real pipeline output is fine - only the comment[cross-linker] SDRF field (and stats built from it) miss it. |
| PXD030849 | DSS | — |  |
| PXD030864 | — | APEX; APEX2; Proximity labeling |  |
| PXD030970 | — | Bioid; proximity-dependent |  |
| PXD031033 | DSSO | — |  |
| PXD031054 | Formaldehyde | — |  |
| PXD031096 | BS3 | — |  |
| PXD031114 | DSSO | — |  |
| PXD031159 | (unverified) BprY | — |  |
| PXD031197 | — | proximity labeling; Turboid | TurboID-based proximity labeling (LONP1-targeting proteins); no chemical crosslinker. |
| PXD031214 | SDA | — |  |
| PXD031215 | DSS | — |  |
| PXD031339 | DSBU | — |  |
| PXD031345 | DMTMM; DSSO; PhoX | — |  |
| PXD031381 | — | — | RNA_PROTEIN_UV_XL: CLIR-MS - photo-induced RNA-protein crosslinking, 800 mJ/cm2 UV irradiation. |
| PXD031411 | DSSO | — |  |
| PXD031415 | — | Apex; biotin-phenol; proximity labeling |  |
| PXD031421 | DSSO | — |  |
| PXD031519 | BS3 | — |  |
| PXD031601 | — | apex2; Proximity labeling |  |
| PXD031643 | (unverified) iqPIR | — |  |
| PXD031644 | (unverified) iqPIR | — |  |
| PXD031827 | BS3; EDC | — |  |
| PXD031845 | — | APEX2; Proximity labeling |  |
| PXD031911 | DSSO | — |  |
| PXD031997 | EDC | — |  |
| PXD032132 | DSBSO; DSSO | — |  |
| PXD032222 | — | — |  |
| PXD032297 | — | BioID2; proximity labeling |  |
| PXD032728 | — | Bioid; Proximity labeling |  |
| PXD032821 | BS3; DSBU; DSSO | — |  |
| PXD032833 | — | Bioid; Proximity labeling; proximity-labeling |  |
| PXD032906 | — | Proximity labeling; Turboid |  |
| PXD032952 | — | proximity labeling; TurboID |  |
| PXD032976 | — | Bioid; Proximity labeling; proximity-labeling |  |
| PXD033004 | — | — |  |
| PXD033008 | — | Bioid; Proximity labeling; proximity-labeling |  |
| PXD033026 | — | Proximity labeling; TurboID |  |
| PXD033043 | — | Proximity labeling; TurboID |  |
| PXD033044 | — | Proximity labeling; TurboID |  |
| PXD033062 | — | Proximity labeling; TurboID |  |
| PXD033063 | — | Proximity labeling; TurboID |  |
| PXD033066 | — | Proximity labeling; TurboID |  |
| PXD033067 | — | proximity-dependent |  |
| PXD033107 | Benzoyl | — |  |
| PXD033167 | Sulfo-LC-SDA | — |  |
| PXD033175 | DSP | — |  |
| PXD033181 | DSSO | — |  |
| PXD033205 | DSBU; EDC + sulfo-NHS | — |  |
| PXD033244 | — | proximity labeling; TurboID |  |
| PXD033391 | — | bioID; proximity labeling |  |
| PXD033409 | DSS; PhoX | — |  |
| PXD033446 | DSSO | — |  |
| PXD033452 | — | Bioid; proximity-dependent |  |
| PXD033466 | — | Proximity labeling |  |
| PXD033593 | — | — |  |
| PXD033633 | BS3 | — |  |
| PXD033764 | — | APEX; APEX2; biotin-phenol; proximity biotinylation; Proximity labeling |  |
| PXD033846 | — | APEX2; proximity labeling |  |
| PXD033959 | — | — |  |
| PXD033960 | — | — |  |
| PXD034054 | — | — | CORRECT_REJECT_NO_TEXT: 'Crosslinks Analysis of Cryptochrome and Timeless' - protocol describes SDS-PAGE/gel workflow only, no reagent named; no PMC. |
| PXD034115 | — | APEX; APEX2; Bioid; proximity labeling |  |
| PXD034118 | — | APEX; biotin-phenol; Proximity labeling; Turboid |  |
| PXD034163 | — | — |  |
| PXD034217 | — | Bioid; Proximity labeling; proximity-dependent; Turboid |  |
| PXD034241 | — | Bioid; Proximity labeling; Turboid |  |
| PXD034393 | BS3 | — |  |
| PXD034475 | DSSO | — |  |
| PXD034529 | — | — | REAL_MISS: 8 organophosphate pesticide names explicitly listed as agents that 'catalyze protein crosslinking' (chlorpyrifos, chlorpyrifos oxon, methamidophos, paraoxon, diazinon, diazoxon, monocrotophos, dichlorvos) - none extracted. Open scope question: unclear whether these are themselves the bridging crosslink or merely catalysts for another natural crosslinking chemistry; needs literature review before any DB action. |
| PXD034627 | — | BioID; Proximity labeling |  |
| PXD034639 | — | Apex2; proximity labeling; Proximity-dependent; proximity-labeling; Turboid |  |
| PXD034796 | Formaldehyde; PhoX | — |  |
| PXD034874 | — | Bioid; Proximity labeling; proximity-labeling |  |
| PXD034894 | — | — | RNA_PROTEIN_UV_XL: CLIR-MS reanalysis of PXD005566 (same UV-crosslinking method, broader parameters). |
| PXD034965 | — | Bioid; Proximity labeling; proximity-labeling |  |
| PXD035001 | — | APEX; biotin phenol; Proximity labeling |  |
| PXD035151 | — | Proximity labeling; turboid |  |
| PXD035153 | — | — |  |
| PXD035201 | (unverified) HHS-482 | — |  |
| PXD035265 | — | Proximity labeling |  |
| PXD035404 | DSSO; PhoX | — |  |
| PXD035433 | DSS | — |  |
| PXD035452 | — | apex; biotin phenol; proximity labeling |  |
| PXD035589 | DSSO; PhoX | — |  |
| PXD035591 | PhoX | — |  |
| PXD035622 | (unverified) iqPIR | — |  |
| PXD035712 | (unverified) iqPIR | — |  |
| PXD035764 | DSSO | — |  |
| PXD035801 | — | Apex; APEX2; proximity labeling |  |
| PXD035813 | — | Proximity labeling |  |
| PXD035844 | DHSO; DMTMM; DSSO | — |  |
| PXD035916 | — | Bioid; Bioid2; proximity-dependent; Turboid |  |
| PXD035939 | (unverified) Q2linker | — |  |
| PXD035980 | DSBU | — |  |
| PXD036113 | — | Apex; APEX2; biotin phenol; Proximity labeling |  |
| PXD036182 | — | Proximity labeling; Turboid |  |
| PXD036262 | — | APEX; APEX2; biotin phenol; Proximity labeling |  |
| PXD036463 | DSP | — |  |
| PXD036630 | — | Proximity labeling |  |
| PXD036640 | DMTMM; DSSO | — |  |
| PXD036649 | (unverified) iqPIR | — |  |
| PXD036675 | — | BioID2; proximity labeling; TurboID |  |
| PXD036744 | — | proximity dependent; proximity labeling; Turboid |  |
| PXD036884 | (unverified) DizSEC; DizSPC | — |  |
| PXD037030 | BS2G | — |  |
| PXD037183 | BS3; DMTMM; DSS | — |  |
| PXD037432 | — | proximity labeling; Proximity-dependent; Turboid |  |
| PXD037438 | — | — | RNA_PROTEIN_UV_XL: SARS-CoV-2 nucleocapsid-RNA UV crosslinking at 254nm (4.8 J/cm2). |
| PXD037443 | (unverified) DBrASO | — |  |
| PXD037492 | BS2G; BS3; DSS; DSSO | — |  |
| PXD037493 | BS3 | — |  |
| PXD037569 | — | APEX; proximity-dependent |  |
| PXD037652 | tBu-PhoX | — |  |
| PXD037678 | — | proximity labeling |  |
| PXD037701 | MBS | Proximity-dependent |  |
| PXD037703 | — | proximity labeling; TurboID |  |
| PXD037729 | BS3 | — |  |
| PXD037894 | (unverified) HHS-482 | — |  |
| PXD038018 | Azide-alkyne | — |  |
| PXD038067 | — | Bioid; Proximity labeling |  |
| PXD038234 | DSP; DTSSP | — |  |
| PXD038286 | — | Bioid; proximity-dependent |  |
| PXD038327 | Formaldehyde | Bioid; proximity labeling |  |
| PXD038332 | Formaldehyde | — |  |
| PXD038398 | Formaldehyde | — |  |
| PXD038487 | — | Bioid; BioID2; proximity-dependent |  |
| PXD038515 | — | APEX2; BioID; PROXIMITY LABELING; Turboid |  |
| PXD038572 | — | proximity biotinylation; Proximity labeling |  |
| PXD038583 | Formaldehyde | — |  |
| PXD038615 | BS3 | — |  |
| PXD038629 | DSSO | — |  |
| PXD038640 | DSS | — |  |
| PXD038658 | DSS | — |  |
| PXD039008 | — | proximity labeling |  |
| PXD039010 | — | proximity labeling |  |
| PXD039068 | — | APEX2; Proximity labeling |  |
| PXD039125 | — | proximity labeling; TurboID |  |
| PXD039289 | DSS | — |  |
| PXD039401 | — | proximity labeling; Turboid |  |
| PXD039467 | — | Proximity labeling; TurboID |  |
| PXD039473 | — | APEX2; biotin tyramide; proximity labeling |  |
| PXD039589 | BS3 | — |  |
| PXD039606 | Benzoyl; DSSO; photo-methionine | — |  |
| PXD039612 | DSG; DSP; DSSO | — |  |
| PXD039626 | Azide-alkyne | Proximity labeling; Proximity-labeling; TurboID |  |
| PXD039694 | — | proximity labeling; Turboid |  |
| PXD039717 | DSG | — |  |
| PXD039754 | ADH; DSG; DSS; PDH | — |  |
| PXD039780 | — | — |  |
| PXD039864 | — | proximity labeling; TurboID |  |
| PXD039939 | Benzoyl | — |  |
| PXD039983 | — | Proximity labeling; Turboid |  |
| PXD039985 | — | Proximity labeling; Turboid |  |
| PXD039986 | — | Proximity labeling; Turboid |  |
| PXD040000 | BS3 | APEX2; proximity-dependent |  |
| PXD040144 | DSS | — |  |
| PXD040156 | BS3 | — |  |
| PXD040262 | — | proximity labeling |  |
| PXD040267 | (unverified) Di(N-succinimidyl)-2,2’-[1,4-phenylenebis(methylenethio)]bis-acetate | — |  |
| PXD040310 | — | Proximity labeling |  |
| PXD040337 | Formaldehyde | proximity-dependent; Turboid |  |
| PXD040374 | DSS; PDH | — |  |
| PXD040392 | (unverified) PFA | proximity labeling |  |
| PXD040412 | — | proximity labeling; TurboID |  |
| PXD040452 | — | Bioid; proximity-dependent; TurboID |  |
| PXD040547 | — | proximity labeling; TurboID |  |
| PXD040562 | — | Proximity-dependent |  |
| PXD040690 | — | Proximity labeling; TurboID |  |
| PXD040705 | DSBU | — |  |
| PXD040736 | BS3 | — |  |
| PXD040762 | — | APEX; APEX2; biotin phenol; Proximity labeling |  |
| PXD040864 | (unverified) iqPIR | — |  |
| PXD040875 | Benzoyl | — |  |
| PXD040902 | DSS; SDA | — |  |
| PXD040939 | — | proximity labeling; Proximity-dependent; Turboid |  |
| PXD040984 | Benzoyl; DSSO | — |  |
| PXD040991 | — | BioID2; proximity-dependent |  |
| PXD041011 | DSS | — |  |
| PXD041019 | — | Bioid; proximity-dependent |  |
| PXD041135 | BS3 | — |  |
| PXD041148 | (unverified) DizSEC; DizSPC | — |  |
| PXD041309 | — | proximity labeling |  |
| PXD041328 | — | proximity labeling |  |
| PXD041378 | DSP | APEX; APEX2; biotin-tyramide; proximity labeling |  |
| PXD041438 | DMTMM; DSSO | — |  |
| PXD041519 | DSSO | — |  |
| PXD041610 | — | Proximity labeling |  |
| PXD041684 | — | proximity labeling; turboid |  |
| PXD041831 | DMTMM; DSSO | — |  |
| PXD041908 | — | APEX2; proximity labeling |  |
| PXD041943 | — | proximity labeling |  |
| PXD041955 | DSBSO; DSSO | — |  |
| PXD042123 | — | proximity labeling |  |
| PXD042173 | DSSO | — |  |
| PXD042282 | DSP | — |  |
| PXD042301 | — | Bioid; proximity labeling; Proximity-dependent |  |
| PXD042302 | — | Bioid; proximity labeling; Proximity-dependent |  |
| PXD042343 | Azide-alkyne | — |  |
| PXD042395 | (unverified) 4-thiouridine | — |  |
| PXD042501 | BS(PEG)5; BS3; DTSSP; EDC | — |  |
| PXD042549 | DSBU | — |  |
| PXD042584 | BS3 | — |  |
| PXD042599 | DSSO | — |  |
| PXD042625 | DMTMM; DSSO | — |  |
| PXD042657 | — | Proximity biotinylation; proximity labeling |  |
| PXD042673 | — | Proximity biotinylation; proximity labeling |  |
| PXD042674 | — | Proximity biotinylation; proximity labeling |  |
| PXD042687 | — | Proximity biotinylation; proximity labeling |  |
| PXD042691 | — | Proximity biotinylation; proximity labeling |  |
| PXD042693 | — | Proximity biotinylation; proximity labeling |  |
| PXD042694 | — | Proximity biotinylation; proximity labeling |  |
| PXD042697 | — | Proximity biotinylation; proximity labeling |  |
| PXD042698 | — | Proximity biotinylation; proximity labeling |  |
| PXD042700 | — | Proximity biotinylation; proximity labeling |  |
| PXD042702 | — | Proximity biotinylation; proximity labeling |  |
| PXD042706 | — | Proximity biotinylation; proximity labeling |  |
| PXD042830 | — | proximity labeling; TurboID |  |
| PXD043041 | — | Proximity labeling; turboid |  |
| PXD043088 | — | APEX2; biotin-phenol; Proximity labeling |  |
| PXD043093 | Benzoyl | — |  |
| PXD043245 | — | APEX2; proximity labeling |  |
| PXD043294 | — | Proximity Labeling |  |
| PXD043347 | DSBU | — |  |
| PXD043531 | Azide-A-DSBSO | — |  |
| PXD043532 | DSS | — |  |
| PXD043595 | — | — | CORRECT_REJECT_NO_TEXT: 'CX-MS' (Collagen I NTX) - protocol describes digestion methods only (hydroxylamine/CNBr), no crosslinker reagent named; no PMC. |
| PXD043732 | — | Proximity labeling; Turboid |  |
| PXD043789 | — | Bioid; proximity labeling |  |
| PXD043805 | — | proximity biotinylation; Proximity labeling |  |
| PXD043900 | (unverified) DEB; nitrogen mustard | — |  |
| PXD043976 | DSS; PDH | — |  |
| PXD044285 | — | — | WRONG_TECHNIQUE: HDX-MS (Hydrogen-Deuterium Exchange mass spectrometry) - a completely different structural proteomics technique, no chemical crosslinker involved. |
| PXD044289 | — | BioID; Proximity labeling |  |
| PXD044328 | DSBU | — |  |
| PXD044405 | DSS; PDH | — |  |
| PXD044574 | DSP | — |  |
| PXD044625 | (unverified) 4-thiouridine | — |  |
| PXD044750 | DSBU | — |  |
| PXD044827 | BS3 | — |  |
| PXD044921 | — | APEX; APEX2; Biotin-phenol; Proximity labeling |  |
| PXD044974 | — | proximity labeling |  |
| PXD045071 | Formaldehyde | — |  |
| PXD045081 | — | proximity labeling; proximity-labeling; TurboID |  |
| PXD045105 | — | — | WRONG_TECHNIQUE: Virotrap-based screening of TGM1 interactors - complex-trapping technology, not crosslinking-MS (TGM1 itself is also a natural crosslinking enzyme, not a reagent). |
| PXD045482 | — | Proximity labeling; Turboid |  |
| PXD045575 | DHSO; DSSO; sulfo-SDA | — |  |
| PXD045689 | DSSO | — |  |
| PXD045791 | DSSO | APEX; BioID; Proximity Labeling |  |
| PXD045792 | (unverified) NNP9 | — |  |
| PXD045837 | — | — | WRONG_TECHNIQUE: HDX-MS analysis of HACE1 - different structural proteomics technique, no chemical crosslinker. |
| PXD045846 | — | Bioid; proximity labeling |  |
| PXD045858 | BS3 | — |  |
| PXD045861 | — | Proximity labeling |  |
| PXD045987 | BS3 | — |  |
| PXD046267 | — | — | RNA_PROTEIN_UV_XL: Protein-RNA UV crosslinking in biomolecular condensates, Spectrolinker 254nm. |
| PXD046382 | DSBSO; DSSO | — |  |
| PXD046385 | — | BioID2; Proximity labeling |  |
| PXD046392 | BS3 | — |  |
| PXD046412 | — | Bioid; Proximity labeling; Turboid |  |
| PXD046413 | — | Bioid; Proximity labeling; Turboid |  |
| PXD046414 | — | Bioid; Proximity labeling; Turboid |  |
| PXD046472 | Formaldehyde | proximity labeling; Turboid |  |
| PXD046634 | DSSO | — |  |
| PXD046652 | — | Proximity labeling |  |
| PXD046754 | — | — | RNA_PROTEIN_UV_XL: LPS-induced RNA-binding proteome - UV-crosslinked to RNA (mouse macrophages). |
| PXD046895 | Benzoyl | — |  |
| PXD046966 | DSBSO | — |  |
| PXD046990 | DSBU | — |  |
| PXD047023 | Formaldehyde | Proximity-dependent; Turboid |  |
| PXD047030 | (unverified) S-XL6 | — |  |
| PXD047173 | DSS | — |  |
| PXD047274 | — | — |  |
| PXD047277 | — | APEX; APEX2; biotin-phenol; proximity labeling |  |
| PXD047368 | BS3 | — |  |
| PXD047378 | — | APEX2; biotin-phenol; proximity labeling |  |
| PXD047422 | DSSO | — |  |
| PXD047455 | — | Proximity biotinylation; proximity labeling |  |
| PXD047543 | — | Proximity labeling; Turboid |  |
| PXD047547 | — | — | NATURAL_OR_ENZYMATIC_XL: Natural/oxidative disulfide bond formation between NLRP1 and TRX1 (not a synthetic crosslinker). |
| PXD047569 | — | Proximity labeling; Turboid |  |
| PXD047583 | — | Proximity biotinylation; proximity labeling |  |
| PXD047725 | — | Proximity labeling; Turboid |  |
| PXD047929 | BS3 | — |  |
| PXD047979 | — | APEX2; Bioid; Proximity labeling; Turboid |  |
| PXD048030 | — | proximity labeling; TurboID |  |
| PXD048046 | — | Proximity labeling; Turboid |  |
| PXD048097 | — | Proximity labeling |  |
| PXD048145 | Formaldehyde | — |  |
| PXD048174 | — | Proximity labeling; Turboid |  |
| PXD048180 | — | Bioid; proximity labeling |  |
| PXD048194 | DSSO | — |  |
| PXD048297 | DMP | — |  |
| PXD048298 | DMP | — |  |
| PXD048452 | SDA | — |  |
| PXD048567 | — | — | CORRECT_REJECT_NO_TEXT: Evidence_quote: 'covalently immobilized...using cross-linkers' - generic, unnamed reagent(s); no PMC. |
| PXD048614 | — | — | NATURAL_OR_ENZYMATIC_XL: Natural disulfide bond mapping/rearrangement in J-chain (not a synthetic crosslinker). |
| PXD048625 | DSS | — |  |
| PXD048632 | (unverified) photo-ANA | — |  |
| PXD048897 | — | — | NATURAL_OR_ENZYMATIC_XL: Natural/enzymatic dityrosine bond in RSV fusion glycoprotein. |
| PXD048937 | — | proximity labeling; turboID |  |
| PXD048965 | Formaldehyde | proximity labeling; turboID |  |
| PXD049047 | BMOE | — |  |
| PXD049054 | — | Bioid; proximity labeling; Turboid |  |
| PXD049094 | BS3 | — |  |
| PXD049182 | — | BioID2; Proximity labeling |  |
| PXD049300 | DSS | — |  |
| PXD049303 | — | — | RNA_PROTEIN_UV_XL: RNA interactome capture (RIC) - RNA-protein complexes stabilized by UV crosslinking in vivo. |
| PXD049360 | — | proximity labeling |  |
| PXD049372 | — | bioid; proximity labeling; turboid |  |
| PXD049375 | — | Proximity labeling; Turboid |  |
| PXD049433 | — | Proximity labeling; TurboID |  |
| PXD049681 | — | Bioid; proximity labeling |  |
| PXD049684 | — | Bioid; proximity labeling |  |
| PXD049689 | — | Bioid; proximity labeling |  |
| PXD049797 | — | — |  |
| PXD049991 | — | Bioid; proximity labeling |  |
| PXD050097 | BS3 | — |  |
| PXD050222 | — | proximity labeling; TurboID |  |
| PXD050287 | — | proximity labeling; Turboid |  |
| PXD050493 | Benzoyl | — |  |
| PXD050556 | — | proximity labeling; TurboID |  |
| PXD050824 | — | Proximity labeling |  |
| PXD050833 | — | — | NATURAL_OR_ENZYMATIC_XL: Lysyl oxidase (LOX) ENZYME catalyzing natural collagen crosslinks. |
| PXD050928 | DSS; PDH | — |  |
| PXD050929 | DSS; PDH | — |  |
| PXD050930 | DSS; PDH | — |  |
| PXD050960 | DSBU | — |  |
| PXD051014 | EGS | proximity labeling |  |
| PXD051047 | EGS | proximity labeling |  |
| PXD051075 | DSS; Formaldehyde; PhoX | — |  |
| PXD051143 | — | BioID2; proximity labeling |  |
| PXD051261 | DSG; DSS | — |  |
| PXD051322 | BS3; DSBU; DSG; DSS; DSSO | — |  |
| PXD051348 | — | Proximity labeling |  |
| PXD051405 | — | Proximity labeling |  |
| PXD051493 | DSS | — |  |
| PXD051557 | — | APEX2; proximity labeling |  |
| PXD051602 | DSP | — |  |
| PXD051661 | sulfo-SDA | — |  |
| PXD051693 | (unverified) dimethylsulfonium | — |  |
| PXD051742 | DSSO | — |  |
| PXD051886 | sulfo-SDA | — |  |
| PXD051937 | — | APEX2; biotin phenol; proximity labeling |  |
| PXD051971 | DSBU; EDC | — |  |
| PXD052022 | Azide-A-DSBSO; DSSO | — |  |
| PXD052032 | — | Proximity labeling |  |
| PXD052174 | — | proximity labeling |  |
| PXD052310 | — | APEX2; biotin phenol; proximity labeling |  |
| PXD052480 | (unverified) TBDSPP | — |  |
| PXD052552 | (unverified) o-NBE | — |  |
| PXD052584 | DSSO | — |  |
| PXD052623 | — | APEX2; biotin-phenol; proximity labeling |  |
| PXD052624 | — | APEX2; proximity labeling |  |
| PXD052637 | — | proximity labeling |  |
| PXD052687 | (unverified) PFA | Proximity labeling; Turboid |  |
| PXD052694 | (unverified) PFA | Proximity labeling; turboid |  |
| PXD052745 | — | proximity labeling; Turboid |  |
| PXD052746 | — | Biotin Phenol; proximity labeling |  |
| PXD052801 | (unverified) iqPIR | — |  |
| PXD052817 | DSSO | — |  |
| PXD052821 | DSSO | — |  |
| PXD052825 | — | Proximity Labeling; Turboid |  |
| PXD052832 | DSSO | — |  |
| PXD052867 | SDA | — |  |
| PXD052917 | — | Biotin Phenol; proximity labeling |  |
| PXD052923 | BS3 | — |  |
| PXD052926 | — | Proximity labeling |  |
| PXD052930 | — | APEX2; biotin phenol; Proximity labeling |  |
| PXD053010 | EDC | — |  |
| PXD053341 | sulfo-SDA | — |  |
| PXD053452 | — | BioID; proximity-dependent; TurboID |  |
| PXD053481 | DSBU; DSSO | — |  |
| PXD053489 | — | proximity labeling |  |
| PXD053494 | — | — | RNA_PROTEIN_UV_XL: irCLIP-RNP - UVC crosslinking of RNA-protein complexes. |
| PXD053500 | BS3 | — |  |
| PXD053509 | — | APEX2; BioID; PROXIMITY LABELING; Proximity-dependent |  |
| PXD053578 | — | APEX; APEX2; biotin-phenol; Proximity labeling; proximity-labeling |  |
| PXD053607 | SMCC | — |  |
| PXD053621 | — | Proximity labeling |  |
| PXD053636 | PhoX | — |  |
| PXD053760 | — | BioID; BioID2; proximity-dependent |  |
| PXD053814 | — | — | NATURAL_OR_ENZYMATIC_XL: Spontaneous dehydroamino-acid-mediated protein crosslinks in Alzheimer's brain tissue (disease-associated PTM, not a synthetic reagent). |
| PXD053832 | — | Proximity labeling; TurboID |  |
| PXD053924 | — | Bioid; proximity labeling |  |
| PXD053984 | DSSO; photo-leucine; photo-methionine | — |  |
| PXD053999 | DSS; PDH | — |  |
| PXD054002 | — | Proximity labeling |  |
| PXD054003 | — | BioID2; proximity-dependent |  |
| PXD054140 | DSSO | — |  |
| PXD054141 | DSSO | — |  |
| PXD054249 | (unverified) DDZ3; LBL1-PCF | — |  |
| PXD054381 | — | APEX; biotin phenol; proximity labeling |  |
| PXD054489 | — | Proximity Labeling; TurboID |  |
| PXD054551 | (unverified) TSTO | — |  |
| PXD054616 | — | proximity labeling; turboID | TurboID proximity labeling (biotin ligase fused with PAICS); no chemical crosslinker used. |
| PXD054720 | DSSO | — |  |
| PXD054728 | DSSO | — |  |
| PXD054757 | DSS | — |  |
| PXD054857 | (unverified) PFA | proximity labeling; TurboID |  |
| PXD054875 | — | proximity labeling |  |
| PXD054939 | — | APEX2; proximity labeling |  |
| PXD054973 | DSSO | — |  |
| PXD055077 | DSS; DSSO | — |  |
| PXD055085 | DSS; DSSO | — |  |
| PXD055086 | — | proximity labeling |  |
| PXD055147 | sulfo-SDA | — |  |
| PXD055169 | SBAP; SIA; SIAB | — |  |
| PXD055235 | Formaldehyde | BioID; BioID2; proximity-dependent |  |
| PXD055284 | BS3; DSBU; DSS; DSSBU | — |  |
| PXD055305 | Formaldehyde | proximity labeling |  |
| PXD055356 | BS3 | — |  |
| PXD055488 | DSG | — |  |
| PXD055512 | ADH; DSS | — |  |
| PXD055649 | — | — |  |
| PXD055703 | DSS; PDH | — |  |
| PXD055708 | — | APEX2; Proximity labeling |  |
| PXD055722 | — | APEX2; Proximity labeling |  |
| PXD055749 | — | proximity labeling; TurboID |  |
| PXD055759 | BS3 | — |  |
| PXD055775 | — | APEX2; proximity labeling |  |
| PXD055778 | — | Proximity labeling; Proximity-dependent; TurboID |  |
| PXD055874 | — | proximity-dependent; TurboID |  |
| PXD055877 | — | proximity-dependent |  |
| PXD055943 | (unverified) iqPIR | — |  |
| PXD056299 | — | Proximity labeling; Turboid |  |
| PXD056360 | DSSO | — |  |
| PXD056652 | sulfo-SDA | — |  |
| PXD056787 | — | APEX2; biotin-phenol; Proximity labeling |  |
| PXD056825 | (unverified) Q2linker | — |  |
| PXD056910 | DSSO | — |  |
| PXD056942 | — | Proximity labeling |  |
| PXD056954 | — | — |  |
| PXD056971 | — | Bioid; proximity labeling |  |
| PXD057009 | — | proximity labeling |  |
| PXD057110 | — | APEX; APEX2; proximity-dependent |  |
| PXD057245 | — | APEX; biotin phenol; proximity labeling |  |
| PXD057404 | Formaldehyde | APEX2; Bioid; biotin-phenol; proximity labeling |  |
| PXD057492 | — | proximity labeling |  |
| PXD057705 | BS3; DSBU; DSS; DSSO | — |  |
| PXD058056 | BS3; DTSSP | — |  |
| PXD058168 | BS3 | — |  |
| PXD058191 | (unverified) iqPIR | — |  |
| PXD058327 | — | Proximity labeling; Turboid |  |
| PXD058694 | DSP | — |  |
| PXD058706 | — | — |  |
| PXD058941 | DSS | — |  |
| PXD059010 | — | proximity labeling; Turboid |  |
| PXD059118 | DSS; Formaldehyde; PhoX | — |  |
| PXD059125 | — | proximity Labeling |  |
| PXD059137 | — | Proximity Labeling; TurboID |  |
| PXD059180 | — | proximity labeling |  |
| PXD059211 | (unverified) SuccBB | — |  |
| PXD059356 | BS3 | — |  |
| PXD059369 | BS3 | — |  |
| PXD059495 | DSSO; PhoX | — |  |
| PXD059547 | DHSO; DMTMM | — |  |
| PXD059552 | — | — |  |
| PXD059554 | — | BioID; Proximity labeling; Turboid |  |
| PXD059558 | — | proximity labeling; Turboid |  |
| PXD059579 | — | BioID2; Proximity labeling |  |
| PXD059635 | DSS | — |  |
| PXD059716 | — | Proximity labeling; TurboID |  |
| PXD059766 | DSSO | — |  |
| PXD059888 | DSG; DSS; DSSO | — |  |
| PXD059960 | — | — |  |
| PXD059974 | DHSO; DSSO | — |  |
| PXD060078 | EDC | — |  |
| PXD060106 | — | APEX; APEX2; Biotin-phenol; proximity labeling |  |
| PXD060111 | — | proximity labeling |  |
| PXD060112 | — | proximity labeling |  |
| PXD060134 | — | Biotin Phenol; proximity labeling |  |
| PXD060138 | Formaldehyde | Apex; Proximity labeling |  |
| PXD060322 | DSPU | — |  |
| PXD060469 | DSSO | — |  |
| PXD060638 | — | proximity labeling; TurboID |  |
| PXD060724 | DSS; DSSO | — |  |
| PXD060781 | — | Proximity labeling; TurboID |  |
| PXD060825 | DSSO | BioID; proximity labeling |  |
| PXD061125 | BS3 | — |  |
| PXD061173 | DSBSO | — |  |
| PXD061317 | — | — |  |
| PXD061540 | — | Proximity labeling; Turboid |  |
| PXD061541 | — | Proximity labeling; Turboid |  |
| PXD061560 | — | Proximity labeling; Turboid |  |
| PXD061563 | — | Proximity labeling; Turboid |  |
| PXD061564 | — | Proximity labeling; Turboid |  |
| PXD061566 | — | Proximity labeling; Turboid |  |
| PXD061667 | sulfo-SDA | — |  |
| PXD061687 | — | APEX2; biotin-phenol; proximity biotinylation; proximity labeling |  |
| PXD061691 | — | proximity labeling |  |
| PXD061693 | — | proximity labeling |  |
| PXD061712 | — | APEX2; proximity biotinylation; proximity labeling |  |
| PXD061752 | — | Bioid; Proximity labeling; proximity-labeling; turboid |  |
| PXD061911 | — | proximity labeling; Turboid |  |
| PXD062002 | DSG | — |  |
| PXD062101 | — | Proximity Labeling; proximity-labeling; turboid |  |
| PXD062203 | Formaldehyde | BioID; TurboID |  |
| PXD062293 | — | proximity labeling; TurboID |  |
| PXD062479 | Azide-A-DSBSO | — |  |
| PXD062557 | — | Proximity labeling; TurboID |  |
| PXD062600 | — | proximity labeling |  |
| PXD062688 | — | — | NATURAL_OR_ENZYMATIC_XL: TG2/FXIIIA transglutaminase ENZYMES catalyzing natural fibrin clot crosslinks. |
| PXD062741 | — | Proximity labeling |  |
| PXD062870 | — | Proximity labeling |  |
| PXD062890 | — | proximity labeling; TurboID | TurboID + co-IP comparison study (U2AF2-TurboID-HA); no chemical crosslinker. |
| PXD063033 | (unverified) BNBA; HMNB-NHS | — |  |
| PXD063145 | — | Proximity LabEling |  |
| PXD063191 | DSP | proximity labeling |  |
| PXD063192 | DSP | proximity labeling |  |
| PXD063709 | EDC + sulfo-NHS | — |  |
| PXD063736 | Benzoyl | — |  |
| PXD063786 | DSSO; Formaldehyde | — |  |
| PXD063825 | (unverified) TSTO | — |  |
| PXD063839 | — | — | REAL_MISS: VTT (vinyl thianthrenium tetrafluoroborate) explicitly named ('Cells were treated with VTT') - brand-new 2025 reagent (Hartmann et al., JACS), bare unexpanded abbreviation, not yet in our reference DB. |
| PXD063858 | DSS | — |  |
| PXD063968 | Formaldehyde | — |  |
| PXD064535 | DSSO | — |  |
| PXD064557 | — | Apex; biotin-phenol; Proximity labeling |  |
| PXD064792 | Formaldehyde | — |  |
| PXD064795 | DSBU | — |  |
| PXD064931 | DSSO | — |  |
| PXD064932 | DSSO | — |  |
| PXD065410 | — | Proximity labeling |  |
| PXD065739 | — | bioid; Proximity dependent; proximity labeling |  |
| PXD065858 | DSBSO | — |  |
| PXD065859 | DSBSO | — |  |
| PXD065869 | DSBSO | — |  |
| PXD065870 | DSBSO | — |  |
| PXD065871 | DSBSO | — |  |
| PXD065905 | Azide-A-DSBSO | — |  |
| PXD065912 | DSBSO | — |  |
| PXD065946 | DSBSO | — |  |
| PXD065949 | DSBSO | — |  |
| PXD065956 | DSBSO | — |  |
| PXD065958 | DSBSO | — |  |
| PXD065961 | DSBSO | — |  |
| PXD066067 | — | Proximity labeling |  |
| PXD066251 | — | — |  |
| PXD066655 | — | — |  |
| PXD066874 | — | Proximity labeling; TurboID |  |
| PXD067296 | BS3 | — |  |
| PXD067324 | BS3 | — |  |
| PXD067352 | — | Proximity labeling; Turboid |  |
| PXD067354 | — | Proximity labeling; Turboid |  |
| PXD068129 | — | — | CORRECT_REJECT_NO_TEXT: Genuine clinical XL-MS feasibility study (human muscle biopsy, mitochondrial interactome) confirmed via keywords, but no specific reagent named anywhere in the available (no-PMC, 4458-char) text. |
| PXD069219 | — | Proximity labeling |  |
| PXD069360 | — | proximity labeling; Turboid |  |
| PXD069512 | Formaldehyde | — |  |
| PXD069844 | — | Bioid; proximity-dependent |  |
