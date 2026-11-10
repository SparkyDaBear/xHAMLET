# Crosslink evidence for stored AlphaFold3 structures

Snapshot: 2026-11-09. Generated from the promoted structures and the committed
rank-1 search exports, with every structure's spectrum-observation count checked
against the local result catalog.

**211 structure copies across 17 PXDs; 843 supporting spectrum-to-pair observations.**

## Interpretation

- Dataset labels describe the AF3 experiment: **Complex Portal test**,
  **Negative control**, or **Earlier PDK1 pilot**. They are assigned by protein
  pair, so shared PXD observations retain the same label. The negative-control
  P05141–Q9H0C2 observation in mixed human/virus PXD060825 is included.
- Negative means absent from the reference releases used for selection, not
  experimentally disproven. Organism-assignment discrepancies remain unresolved
  for some test-set PXDs; these labels do not validate the search proteome.
- Every row below is one passing, non-decoy, rank-1 spectrum match supporting
  that candidate pair. Multiple spectra can support the same peptide/residue
  combination; these are not counts of unique residue-level crosslinks.
- The AF3 structure models the **protein pair**, not an individual crosslink.
  This report does not establish that the crosslink is geometrically satisfied.
- Protein pairs use the catalog's base-accession normalization. Original
  isoform mappings and peptide modifications remain in each PXD's crosslink CSV.
- Ranges are inclusive protein peptide coordinates. Link sites are peptide-local
  mzIdentML positions, not protein residue numbers. **`-1` means the output does
  not supply a localized site; do not calculate a protein residue from it.**
  Terminal/out-of-range site values also require interpretation before distance analysis.
- Ambiguous means the source peptides had multiple candidate protein mappings;
  one spectrum can therefore support multiple candidate-pair sections.
- `scan_id` joins to that PXD's `scan_map.csv`; the ID is not a global ID or
  necessarily the instrument's scan number. Search group retains taxid/chemistry.
- Failed AF3 jobs are excluded because they have no stored structure.

## PXD overview

| PXD | Stored structure copies by dataset | Spectrum-to-pair observations | Source exports |
| --- | --- | --- | --- |
| [PXD009641](#pxd009641) | Negative control: 35 | 35 | [Crosslinks](../store/PXD009641/search_results/crosslinks.csv) / [Scan map](../store/PXD009641/search_results/scan_map.csv) |
| [PXD010470](#pxd010470) | Complex Portal test: 1 | 1 | [Crosslinks](../store/PXD010470/search_results/crosslinks.csv) / [Scan map](../store/PXD010470/search_results/scan_map.csv) |
| [PXD012882](#pxd012882) | Complex Portal test: 4 | 351 | [Crosslinks](../store/PXD012882/search_results/crosslinks.csv) / [Scan map](../store/PXD012882/search_results/scan_map.csv) |
| [PXD014520](#pxd014520) | Complex Portal test: 4 | 8 | [Crosslinks](../store/PXD014520/search_results/crosslinks.csv) / [Scan map](../store/PXD014520/search_results/scan_map.csv) |
| [PXD017996](#pxd017996) | Complex Portal test: 3 | 19 | [Crosslinks](../store/PXD017996/search_results/crosslinks.csv) / [Scan map](../store/PXD017996/search_results/scan_map.csv) |
| [PXD021708](#pxd021708) | Negative control: 1 | 2 | [Crosslinks](../store/PXD021708/search_results/crosslinks.csv) / [Scan map](../store/PXD021708/search_results/scan_map.csv) |
| [PXD026508](#pxd026508) | Negative control: 57 | 61 | [Crosslinks](../store/PXD026508/search_results/crosslinks.csv) / [Scan map](../store/PXD026508/search_results/scan_map.csv) |
| [PXD027611](#pxd027611) | Complex Portal test: 5 | 14 | [Crosslinks](../store/PXD027611/search_results/crosslinks.csv) / [Scan map](../store/PXD027611/search_results/scan_map.csv) |
| [PXD030063](#pxd030063) | Negative control: 1 | 1 | [Crosslinks](../store/PXD030063/search_results/crosslinks.csv) / [Scan map](../store/PXD030063/search_results/scan_map.csv) |
| [PXD031827](#pxd031827) | Earlier PDK1 pilot: 1 | 103 | [Crosslinks](../store/PXD031827/search_results/crosslinks.csv) / [Scan map](../store/PXD031827/search_results/scan_map.csv) |
| [PXD040144](#pxd040144) | Complex Portal test: 14 | 64 | [Crosslinks](../store/PXD040144/search_results/crosslinks.csv) / [Scan map](../store/PXD040144/search_results/scan_map.csv) |
| [PXD040984](#pxd040984) | Complex Portal test: 1; Negative control: 3 | 4 | [Crosslinks](../store/PXD040984/search_results/crosslinks.csv) / [Scan map](../store/PXD040984/search_results/scan_map.csv) |
| [PXD041011](#pxd041011) | Negative control: 1 | 1 | [Crosslinks](../store/PXD041011/search_results/crosslinks.csv) / [Scan map](../store/PXD041011/search_results/scan_map.csv) |
| [PXD060825](#pxd060825) | Complex Portal test: 10; Negative control: 1 | 36 | [Crosslinks](../store/PXD060825/search_results/crosslinks.csv) / [Scan map](../store/PXD060825/search_results/scan_map.csv) |
| [PXD064792](#pxd064792) | Complex Portal test: 3 | 3 | [Crosslinks](../store/PXD064792/search_results/crosslinks.csv) / [Scan map](../store/PXD064792/search_results/scan_map.csv) |
| [PXD064931](#pxd064931) | Complex Portal test: 35 | 81 | [Crosslinks](../store/PXD064931/search_results/crosslinks.csv) / [Scan map](../store/PXD064931/search_results/scan_map.csv) |
| [PXD064932](#pxd064932) | Complex Portal test: 31 | 59 | [Crosslinks](../store/PXD064932/search_results/crosslinks.csv) / [Scan map](../store/PXD064932/search_results/scan_map.csv) |

## PXD009641

### A1L3X4 — P22087

**Dataset:** Negative control. **ipTM:** 0.40. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/a1l3x4__p22087__2f288eae/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/a1l3x4__p22087__2f288eae/pair.json) · [Confidence](../store/PXD009641/af3_predictions/a1l3x4__p22087__2f288eae/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5305 | taxid_9606/benzoyl | A1L3X4 | NCCSCCPMGCAK | 32-43 | -1 | P22087 | GGGGGGGGGGGGGR | 46-59 | -1 | 6.774061 | No |

### A1Z1Q3 — P49908

**Dataset:** Negative control. **ipTM:** 0.18. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/a1z1q3__p49908__6cfa0e39/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/a1z1q3__p49908__6cfa0e39/pair.json) · [Confidence](../store/PXD009641/af3_predictions/a1z1q3__p49908__6cfa0e39/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5176 | taxid_9606/benzoyl | A1Z1Q3 | APGEDTPR | 385-392 | -1 | P49908 | KUEUPSN | 375-381 | -1 | 3.350406 | No |

### A6NEN9 — Q92820

**Dataset:** Negative control. **ipTM:** 0.10. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/a6nen9__q92820__e78de656/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/a6nen9__q92820__e78de656/pair.json) · [Confidence](../store/PXD009641/af3_predictions/a6nen9__q92820__e78de656/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5707 | taxid_9606/benzoyl | A6NEN9 | IQCDALERR | 111-119 | -1 | Q92820 | KFFNVLTTNTDGK | 212-224 | -1 | 4.508408 | No |

### A6NGU5 — Q9UBE8

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/a6ngu5__q9ube8__7996a467/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/a6ngu5__q9ube8__7996a467/pair.json) · [Confidence](../store/PXD009641/af3_predictions/a6ngu5__q9ube8__7996a467/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5827 | taxid_9606/benzoyl | A6NGU5 | GGEPAGY | 562-568 | -1 | Q9UBE8 | YHTCMCK | 434-440 | -1 | 5.658679 | Yes |

### A6NMY6 — Q01085

**Dataset:** Negative control. **ipTM:** 0.16. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/a6nmy6__q01085__4530fb1f/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/a6nmy6__q01085__4530fb1f/pair.json) · [Confidence](../store/PXD009641/af3_predictions/a6nmy6__q01085__4530fb1f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5834 | taxid_9606/benzoyl | A6NMY6 | GLGTDEDSLIEIICSR | 120-135 | -1 | Q01085 | ISDARVVK | 123-130 | -1 | 9.221327 | Yes |

### B1AK53 — P55957

**Dataset:** Negative control. **ipTM:** 0.34. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/b1ak53__p55957__b86ed9f9/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/b1ak53__p55957__b86ed9f9/pair.json) · [Confidence](../store/PXD009641/af3_predictions/b1ak53__p55957__b86ed9f9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6444 | taxid_9606/benzoyl | B1AK53 | LGPAAR | 556-561 | -1 | P55957 | SLARNGMD | 188-195 | -1 | 3.306699 | No |

### B2RXH8 — P49908

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/b2rxh8__p49908__eaee7e70/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/b2rxh8__p49908__eaee7e70/pair.json) · [Confidence](../store/PXD009641/af3_predictions/b2rxh8__p49908__eaee7e70/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5746 | taxid_9606/benzoyl | B2RXH8 | DSTNGQDDS | 285-293 | -1 | P49908 | KUEUPSN | 375-381 | -1 | 3.0763249999999998 | Yes |

### E9PKD4 — Q9NYZ2

**Dataset:** Negative control. **ipTM:** 0.24. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/e9pkd4__q9nyz2__ecf4ed00/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/e9pkd4__q9nyz2__ecf4ed00/pair.json) · [Confidence](../store/PXD009641/af3_predictions/e9pkd4__q9nyz2__ecf4ed00/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5376 | taxid_9606/benzoyl | E9PKD4 | AEDYYR | 195-200 | -1 | Q9NYZ2 | DGGGGK | 23-28 | -1 | 4.551038 | Yes |

### O00295 — Q96AA8

**Dataset:** Negative control. **ipTM:** 0.19. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/o00295__q96aa8__cc63b38b/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/o00295__q96aa8__cc63b38b/pair.json) · [Confidence](../store/PXD009641/af3_predictions/o00295__q96aa8__cc63b38b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6312 | taxid_9606/benzoyl | O00295 | GEGGTDSDHMR | 244-254 | -1 | Q96AA8 | GQDSHWVEDK | 537-546 | -1 | 5.998655 | No |

### O75807 — Q8NAB2

**Dataset:** Negative control. **ipTM:** 0.33. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/o75807__q8nab2__25eef711/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/o75807__q8nab2__25eef711/pair.json) · [Confidence](../store/PXD009641/af3_predictions/o75807__q8nab2__25eef711/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6231 | taxid_9606/benzoyl | O75807 | TLQGSDKNPGEEK | 150-162 | -1 | Q8NAB2 | NDFFLVSTMK | 381-390 | -1 | 6.346143 | No |

### P01116 — P61366

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p01116__p61366__6e293256/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p01116__p61366__6e293256/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p01116__p61366__6e293256/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5131 | taxid_9606/benzoyl | P01116 | TPGCVK | 177-182 | -1 | P61366 | FGIPMDR | 116-122 | -1 | 4.627191 | No |

### P04264 — P37108

**Dataset:** Negative control. **ipTM:** 0.41. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p04264__p37108__30848894/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p04264__p37108__30848894/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p04264__p37108__30848894/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5579 | taxid_9606/benzoyl | P04264 | WELLQQVDTSTR | 212-223 | -1 | P37108 | ANMDGLK | 89-95 | -1 | 9.47784 | No |

### P04264 — Q5JVX7

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p04264__q5jvx7__3b1da8e6/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p04264__q5jvx7__3b1da8e6/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p04264__q5jvx7__3b1da8e6/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5776 | taxid_9606/benzoyl | P04264 | YEELQITAGR | 377-386 | -1 | Q5JVX7 | KSPQMNDFNIK | 141-151 | -1 | 7.765877 | Yes |

### P05305 — P07438

**Dataset:** Negative control. **ipTM:** 0.10. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p05305__p07438__743da786/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p05305__p07438__743da786/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p05305__p07438__743da786/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5915 | taxid_9606/benzoyl | P05305 | CSCSSLMDK | 53-61 | -1 | P07438 | KCCCSCCPVGCAK | 31-43 | -1 | 2.8067409999999997 | No |

### P07996 — Q92522

**Dataset:** Negative control. **ipTM:** 0.15. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p07996__q92522__9507c93d/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p07996__q92522__9507c93d/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p07996__q92522__9507c93d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5308 | taxid_9606/benzoyl | P07996 | DFTAYR | 1104-1109 | -1 | Q92522 | TAAAGGK | 189-195 | -1 | 7.0958689999999995 | No |

### P0CJ92 — Q14669

**Dataset:** Negative control. **ipTM:** 0.25. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p0cj92__q14669__0ce5329f/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p0cj92__q14669__0ce5329f/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p0cj92__q14669__0ce5329f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6331 | taxid_9606/benzoyl | P0CJ92 | ARTEWK | 204-209 | -1 | Q14669 | LLDTNPEINQSDSQDSR | 1640-1656 | -1 | 6.882621 | Yes |

### P12956 — P61011

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p12956__p61011__0a4f75c2/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p12956__p61011__0a4f75c2/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p12956__p61011__0a4f75c2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6596 | taxid_9606/benzoyl | P12956 | DIISIAEDEDLR | 219-230 | -1 | P61011 | TTTCSK | 115-120 | -1 | 8.476967 | No |

### P14406 — Q9Y5T4

**Dataset:** Negative control. **ipTM:** 0.06. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p14406__q9y5t4__ffecd30a/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p14406__q9y5t4__ffecd30a/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p14406__q9y5t4__ffecd30a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5459 | taxid_9606/benzoyl | P14406 | NLLALRQIGQR | 4-14 | -1 | Q9Y5T4 | DLLETTTKH | 142-150 | -1 | 8.575423 | No |

### P15104 — Q8NEK8

**Dataset:** Negative control. **ipTM:** 0.15. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p15104__q8nek8__bd8534e4/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p15104__q8nek8__bd8534e4/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p15104__q8nek8__bd8534e4/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5170 | taxid_9606/benzoyl | P15104 | TVGQEK | 328-333 | -1 | Q8NEK8 | GSNGMS | 384-389 | -1 | 4.041271 | No |

### P19440 — Q9UBE8

**Dataset:** Negative control. **ipTM:** 0.19. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p19440__q9ube8__6a3061b9/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p19440__q9ube8__6a3061b9/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p19440__q9ube8__6a3061b9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5827 | taxid_9606/benzoyl | P19440 | GGEPAGY | 563-569 | -1 | Q9UBE8 | YHTCMCK | 434-440 | -1 | 5.658679 | Yes |

### P21802 — P29034

**Dataset:** Negative control. **ipTM:** 0.23. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p21802__p29034__e72e2bbe/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p21802__p29034__e72e2bbe/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p21802__p29034__e72e2bbe/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5750 | taxid_9606/benzoyl | P21802 | QLVEDLDR | 752-759 | -1 | P29034 | VDEEGLKK | 51-58 | -1 | 9.284076 | Yes |

### P27695 — Q9UH73

**Dataset:** Negative control. **ipTM:** 0.16. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p27695__q9uh73__f901adcd/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p27695__q9uh73__f901adcd/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p27695__q9uh73__f901adcd/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5475 | taxid_9606/benzoyl | P27695 | KNAGFTPQER | 228-237 | -1 | Q9UH73 | NPEMCR | 147-152 | -1 | 4.504495 | Yes |

### P31749 — Q9BZW8

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p31749__q9bzw8__5595c459/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p31749__q9bzw8__5595c459/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p31749__q9bzw8__5595c459/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5141 | taxid_9606/benzoyl | P31749 | KEVIVAK | 183-189 | -1 | Q9BZW8 | LGQVVTLILLLLLK | 2-15 | -1 | 4.997209 | No |

### P35527 — Q5FYA8

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p35527__q5fya8__644fbb44/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p35527__q5fya8__644fbb44/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p35527__q5fya8__644fbb44/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6262 | taxid_9606/benzoyl | P35527 | GGGGSFGYSYGGGSGGGFSASSLGGGFGGGSR | 64-95 | -1 | Q5FYA8 | YGDNVEEMDWMVGKILDALDQER | 289-311 | -1 | 10.846394 | No |

### P35557 — Q9BWW4

**Dataset:** Negative control. **ipTM:** 0.25. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p35557__q9bww4__8d74f2fb/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p35557__q9bww4__8d74f2fb/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p35557__q9bww4__8d74f2fb/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5352 | taxid_9606/benzoyl | P35557 | KACMLGQ | 459-465 | -1 | Q9BWW4 | GKGSAVPSDGQAR | 5-17 | -1 | 4.122784 | No |

### P55084 — Q6IFH4

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p55084__q6ifh4__e9b6136d/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p55084__q6ifh4__e9b6136d/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p55084__q6ifh4__e9b6136d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5779 | taxid_9606/benzoyl | P55084 | AMDSDWFAENYMGRK | 392-406 | -1 | Q6IFH4 | MSGENVTK | 1-8 | -1 | 3.433716 | No |

### P82914 — Q6P2P2

**Dataset:** Negative control. **ipTM:** 0.18. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/p82914__q6p2p2__c9388758/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/p82914__q6p2p2__c9388758/pair.json) · [Confidence](../store/PXD009641/af3_predictions/p82914__q6p2p2__c9388758/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5192 | taxid_9606/benzoyl | P82914 | YLLMSIDQR | 155-163 | -1 | Q6P2P2 | DAGGGAGAAGR | 11-21 | -1 | 7.355013 | No |

### Q06730 — Q9NPF0

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q06730__q9npf0__2c175140/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q06730__q9npf0__2c175140/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q06730__q9npf0__2c175140/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5510 | taxid_9606/benzoyl | Q06730 | DNHYEFSDCEKFLCVK | 271-286 | -1 | Q9NPF0 | LRPLGLLVAMK | 259-269 | -1 | 3.253075 | No |

### Q14511 — Q8TCV5

**Dataset:** Negative control. **ipTM:** 0.22. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q14511__q8tcv5__4f915fba/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q14511__q8tcv5__4f915fba/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q14511__q8tcv5__4f915fba/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6042 | taxid_9606/benzoyl | Q14511 | CYGYMER | 437-443 | -1 | Q8TCV5 | DSDCSGK | 99-105 | -1 | 5.724142 | No |

### Q1W6H9 — Q8N7X8

**Dataset:** Negative control. **ipTM:** 0.47. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q1w6h9__q8n7x8__b28f8157/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q1w6h9__q8n7x8__b28f8157/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q1w6h9__q8n7x8__b28f8157/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5195 | taxid_9606/benzoyl | Q1W6H9 | TGDEGK | 140-145 | -1 | Q8N7X8 | KAAAIR | 148-153 | -1 | 5.620983 | No |

### Q4G0N4 — Q9NY12

**Dataset:** Negative control. **ipTM:** 0.13. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q4g0n4__q9ny12__5d98a136/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q4g0n4__q9ny12__5d98a136/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q4g0n4__q9ny12__5d98a136/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5835 | taxid_9606/benzoyl | Q4G0N4 | LGGDGGGR | 37-44 | -1 | Q9NY12 | GGGGGGFR | 198-205 | -1 | 9.063986 | Yes |

### Q5JQS6 — Q9NNZ6

**Dataset:** Negative control. **ipTM:** 0.04. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q5jqs6__q9nnz6__0296debc/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q5jqs6__q9nnz6__0296debc/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q5jqs6__q9nnz6__0296debc/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6066 | taxid_9606/benzoyl | Q5JQS6 | KGNPDEER | 21-28 | -1 | Q9NNZ6 | MGSRCAK | 1-7 | -1 | 6.639528 | No |

### Q8N3J9 — Q8NCU7

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q8n3j9__q8ncu7__fc7440a7/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q8n3j9__q8ncu7__fc7440a7/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q8n3j9__q8ncu7__fc7440a7/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5309 | taxid_9606/benzoyl | Q8N3J9 | CCGCGK | 201-206 | -1 | Q8NCU7 | ARDEGR | 343-348 | -1 | 4.233821 | Yes |

### Q96PQ0 — Q9P0M9

**Dataset:** Negative control. **ipTM:** 0.25. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q96pq0__q9p0m9__16e6b76b/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q96pq0__q9p0m9__16e6b76b/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q96pq0__q9p0m9__16e6b76b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5986 | taxid_9606/benzoyl | Q96PQ0 | SPEPGR | 52-57 | -1 | Q9P0M9 | SGGSSK | 35-40 | -1 | 5.150802 | Yes |

### Q96S90 — Q9H0P7

**Dataset:** Negative control. **ipTM:** 0.15. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD009641/af3_predictions/q96s90__q9h0p7__d4da8c18/model.cif) · [Pair provenance](../store/PXD009641/af3_predictions/q96s90__q9h0p7__d4da8c18/pair.json) · [Confidence](../store/PXD009641/af3_predictions/q96s90__q9h0p7__d4da8c18/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5410 | taxid_9606/benzoyl | Q96S90 | KAAAQK | 170-175 | -1 | Q9H0P7 | TTGQGR | 64-69 | -1 | 6.681359 | No |

## PXD010470

### Q8NFD5 — Q92784

**Dataset:** Complex Portal test. **ipTM:** 0.30. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD010470/af3_predictions/q8nfd5__q92784__c093f3c2/model.cif) · [Pair provenance](../store/PXD010470/af3_predictions/q8nfd5__q92784__c093f3c2/pair.json) · [Confidence](../store/PXD010470/af3_predictions/q8nfd5__q92784__c093f3c2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9207 | taxid_9606/benzoyl | Q8NFD5 | AGSGER | 20-25 | -1 | Q92784 | GSAGGR | 178-183 | -1 | 8.103517 | Yes |

## PXD012882

### O15392 — Q53HL2

**Dataset:** Complex Portal test. **ipTM:** 0.86. **Supporting spectrum matches:** 185.

[AF3 model](../store/PXD012882/af3_predictions/o15392__q53hl2__116a93c0/model.cif) · [Pair provenance](../store/PXD012882/af3_predictions/o15392__q53hl2__116a93c0/pair.json) · [Confidence](../store/PXD012882/af3_predictions/o15392__q53hl2__116a93c0/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 913 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 16.991928 | No |
| 915 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | IYNISGNGSPLADSKEIFLTVPVGGGESLR | 211-240 | 15 | 16.991503 | No |
| 922 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | CPPSKK | 145-150 | 5 | 11.636614 | No |
| 944 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.216954 | No |
| 946 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | CPPSKK | 145-150 | 4 | 10.175596 | No |
| 949 | taxid_9606/edc | O15392 | EFEETAKK | 123-130 | 1 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 11.241855 | No |
| 952 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 18.599775 | No |
| 963 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 4.337105 | No |
| 968 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | QALEEAATADLDITEINKLTAEAIQTPLK | 81-109 | 26 | 1.501347 | No |
| 972 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 10.554892 | No |
| 974 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 14 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 11.568190999999999 | No |
| 976 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 14 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 13.494076999999999 | No |
| 980 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 17.267107 | No |
| 982 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.532264999999999 | No |
| 983 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | KLASFLK | 20-26 | 1 | 11.29474 | No |
| 985 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 11.001353 | No |
| 995 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | KLASFLK | 20-26 | 1 | 6.427591 | No |
| 996 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 13.177793 | No |
| 998 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 21.064281 | No |
| 1000 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 16.999381 | No |
| 1001 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | KNLQTAR | 135-141 | 1 | 11.749996 | No |
| 1007 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | KNLQTAR | 135-141 | 1 | 13.584349 | No |
| 1012 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | VFKTPGLR | 196-203 | 4 | 8.800276 | No |
| 1017 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 17.673578 | No |
| 1018 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 3 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 11.14803 | No |
| 1019 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 4 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 9.683835 | No |
| 1024 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | CPPSKK | 145-150 | 4 | 12.189071 | No |
| 1029 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 3 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 12.906621 | No |
| 1040 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 8 | 12.198497999999999 | No |
| 1043 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 10.118495 | No |
| 1047 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 11.954011 | No |
| 1048 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 15.791535 | No |
| 1050 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 14 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 14.81812 | No |
| 1059 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 11.916129 | No |
| 1071 | taxid_9606/edc | O15392 | IAKETNNK | 113-120 | 3 | Q53HL2 | VIQVDEMIVEEEEEEENERK | 116-135 | 18 | 3.943019 | No |
| 1072 | taxid_9606/edc | O15392 | IAKETNNK | 113-120 | 3 | Q53HL2 | VIQVDEMIVEEEEEEENERK | 116-135 | 18 | 9.39235 | No |
| 1075 | taxid_9606/edc | O15392 | DHRISTFK | 16-23 | 6 | Q53HL2 | TPAAGER | 204-210 | 6 | 3.14184 | No |
| 1085 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 12.009112 | No |
| 1090 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 15.392161999999999 | No |
| 1096 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 11.621705 | No |
| 1101 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 12.674927 | No |
| 1103 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 10 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 6.521059 | No |
| 1124 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 6.7323710000000005 | No |
| 1127 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 3 | Q53HL2 | LAQICSSIR | 269-277 | 7 | 9.63423 | No |
| 1131 | taxid_9606/edc | O15392 | EFEETAK | 123-129 | 1 | Q53HL2 | KNLQTAR | 135-141 | 1 | 11.795387999999999 | No |
| 1132 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 1 | Q53HL2 | LPKALR | 61-66 | 3 | 12.636641 | No |
| 1140 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | KLASFLK | 20-26 | 1 | 12.167176999999999 | No |
| 1153 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 1 | Q53HL2 | KLASFLK | 20-26 | 1 | 13.337359 | No |
| 1157 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 6.001259 | No |
| 1168 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 10.938366 | No |
| 1170 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | CPPSKK | 145-150 | 4 | 9.836453 | No |
| 1178 | taxid_9606/edc | O15392 | EFEETAK | 123-129 | 1 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 11.65396 | No |
| 1192 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | LASFLKDFDR | 21-30 | 3 | 2.830692 | No |
| 1207 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 9.77069 | No |
| 1210 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | CPPSKK | 145-150 | 4 | 11.526041 | No |
| 1217 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | CPPSKK | 145-150 | 4 | 4.365264 | No |
| 1232 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 5.428552 | No |
| 1233 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | KLASFLK | 20-26 | 1 | 12.210123 | No |
| 1247 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | KNLQTAR | 135-141 | 1 | 15.731638 | No |
| 1249 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 16.141454 | No |
| 1250 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 15.450275 | No |
| 1253 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 12.971229 | No |
| 1259 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | KLASFLK | 20-26 | 1 | 15.521433 | No |
| 1261 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 8.091698000000001 | No |
| 1264 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 17.736295000000002 | No |
| 1266 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 8.483468 | No |
| 1271 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | VFKTPGLR | 196-203 | 4 | 7.657261999999999 | No |
| 1280 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | KNLQTAR | 135-141 | 1 | 16.542441 | No |
| 1283 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 13.586913 | No |
| 1284 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | LASFLK | 21-26 | 3 | 4.830088 | No |
| 1292 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 3 | Q53HL2 | LAQICSSIR | 269-277 | 7 | 8.353146 | No |
| 1300 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | KNLQTAR | 135-141 | 1 | 9.104752 | No |
| 1308 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 14.462079 | No |
| 1316 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 3 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 16.091969 | No |
| 1324 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 3 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 7.920324000000001 | No |
| 1330 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 12.660803999999999 | No |
| 1338 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | CPPSKK | 145-150 | 4 | 4.838524 | No |
| 1342 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 13.805617999999999 | No |
| 1346 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 1 | Q53HL2 | QALEEAATADLDITEINK | 81-98 | 5 | 15.101825999999999 | No |
| 1349 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | CPPSKK | 145-150 | 4 | 8.472962 | No |
| 1352 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 18.928191 | No |
| 1359 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 14 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.28439 | No |
| 1368 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 16.161543 | No |
| 1369 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | TQSIQGK | 152-158 | 3 | 13.902531 | No |
| 1374 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | KNLQTAR | 135-141 | 1 | 12.237191 | No |
| 1385 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 17.510048 | No |
| 1387 | taxid_9606/edc | O15392 | ISTFKNWPFLEGCACTPER | 19-37 | 5 | Q53HL2 | LTAEAIQTPLK | 99-109 | 4 | 15.305707 | No |
| 1388 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 13.894409999999999 | No |
| 1393 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | KLASFLK | 20-26 | 4 | 5.11571 | No |
| 1396 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 20.946127 | No |
| 1403 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 11 | Q53HL2 | IYNISGNGSPLADSKEIFLTVPVGGGESLR | 211-240 | 13 | 13.167762 | No |
| 1407 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 17.172473 | No |
| 1408 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 14.673639 | No |
| 1418 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 15.607345 | No |
| 1435 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 14 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 11.426608 | No |
| 1454 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 3 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.853762 | No |
| 1456 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 17.300167000000002 | No |
| 1462 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 12.68989 | No |
| 1468 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 11.559671 | No |
| 1473 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | CPPSKK | 145-150 | 4 | 7.904311 | No |
| 1496 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 16 | Q53HL2 | VFKTPGLR | 196-203 | 4 | 9.73191 | No |
| 1499 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | KNLQTAR | 135-141 | 1 | 15.190582 | No |
| 1504 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 3.802464 | No |
| 1505 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 19.249589 | No |
| 1510 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 14.817188999999999 | No |
| 1511 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 19.901166 | No |
| 1512 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | KNLQTAR | 135-141 | 1 | 6.856173 | No |
| 1528 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 9.503938 | No |
| 1534 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | KLASFLK | 20-26 | 1 | 12.988653 | No |
| 1542 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 3.545527 | No |
| 1554 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | TQSIQGK | 152-158 | 3 | 9.665833 | No |
| 1555 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 16 | Q53HL2 | VFKTPGLR | 196-203 | 4 | 4.614467 | No |
| 1558 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 21.632095 | No |
| 1559 | taxid_9606/edc | O15392 | IAKETNNK | 113-120 | 3 | Q53HL2 | LTAEAIQTPLK | 99-109 | 4 | 12.853613 | No |
| 1563 | taxid_9606/edc | O15392 | QFEELTLGEFLKLDR | 92-106 | 12 | Q53HL2 | LTAEAIQTPLK | 99-109 | 4 | 17.825597000000002 | No |
| 1580 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 15.416421 | No |
| 1581 | taxid_9606/edc | O15392 | EFEETAKK | 123-130 | 1 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 12.157527 | No |
| 1595 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 18.019218000000002 | No |
| 1611 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 19.108399 | No |
| 1614 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 3 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 12.765252 | No |
| 1620 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 8.597079 | No |
| 1630 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 18.711069000000002 | No |
| 1632 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 14 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 8.874984 | No |
| 1633 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 10 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 12.672055 | No |
| 1647 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 9 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 10.546968 | No |
| 1651 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 8 | 17.662756 | No |
| 1652 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 14.750479 | No |
| 1659 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LPKALR | 61-66 | 3 | 12.919101999999999 | No |
| 1667 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | KLASFLK | 20-26 | 1 | 16.004174 | No |
| 1670 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 18.330501 | No |
| 1678 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | KLASFLK | 20-26 | 4 | 12.495401 | No |
| 1684 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | CPPSKK | 145-150 | 4 | 4.534542 | No |
| 1685 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | VAKTNSLR | 10-17 | 4 | 4.247901000000001 | No |
| 1686 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 9.120771 | No |
| 1689 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 16 | Q53HL2 | VFKTPGLR | 196-203 | 4 | 9.130232 | No |
| 1696 | taxid_9606/edc | O15392 | HSSGCAFLSVKK | 80-91 | 9 | Q53HL2 | TPAAGER | 204-210 | 6 | 13.342255999999999 | No |
| 1699 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | VAKTNSLR | 10-17 | 4 | 15.011462 | No |
| 1713 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 17.317542 | No |
| 1719 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.866086 | No |
| 1725 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 19.616256 | No |
| 1730 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | CPPSKK | 145-150 | 4 | 4.056489 | No |
| 1737 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | LPKALR | 61-66 | 3 | 11.780825 | No |
| 1752 | taxid_9606/edc | O15392 | ISTFKNWPFLEGCACTPER | 19-37 | 3 | Q53HL2 | TPAAGER | 204-210 | 6 | 12.929694999999999 | No |
| 1753 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 5.445615 | No |
| 1758 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 15.455458 | No |
| 1761 | taxid_9606/edc | O15392 | HSSGCAFLSVK | 80-90 | 9 | Q53HL2 | TPAAGER | 204-210 | 6 | 4.327171 | No |
| 1766 | taxid_9606/edc | O15392 | ISTFKNWPFLEGCACTPER | 19-37 | 5 | Q53HL2 | QALEEAATADLDITEINK | 81-98 | 5 | 17.316973 | No |
| 1792 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 18.117273 | No |
| 1795 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | CPPSKK | 145-150 | 4 | 7.883978000000001 | No |
| 1819 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 5 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 13.297813999999999 | No |
| 1828 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 14.219477 | No |
| 1838 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 15.126737 | No |
| 1847 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 3 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 9.623454 | No |
| 1849 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 16.106804 | No |
| 1851 | taxid_9606/edc | O15392 | IAKETNNK | 113-120 | 3 | Q53HL2 | VIQVDEMIVEEEEEEENERK | 116-135 | 18 | 10.802669 | No |
| 1857 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 8 | 13.264918 | No |
| 1867 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 16.463377 | No |
| 1874 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | CPPSKK | 145-150 | 4 | 9.145651 | No |
| 1902 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | CPPSKK | 145-150 | 5 | 9.670457 | No |
| 1908 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 8 | 15.362138999999999 | No |
| 1916 | taxid_9606/edc | O15392 | KQFEELTLGEFLK | 91-103 | 4 | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | 11.886962 | No |
| 1926 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 3.1038170000000003 | No |
| 1942 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 1 | Q53HL2 | CPPSKK | 145-150 | 4 | 2.22705 | No |
| 1945 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 18.492916 | No |
| 1946 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | KNLQTAR | 135-141 | 1 | 9.556082 | No |
| 1947 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 24.524843999999998 | No |
| 1958 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | KNLQTAR | 135-141 | 1 | 14.219573 | No |
| 1964 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 8 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 9.866497 | No |
| 1978 | taxid_9606/edc | O15392 | QFEELTLGEFLK | 92-103 | 4 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 13.24283 | No |
| 1979 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 14 | Q53HL2 | CPPSKK | 145-150 | 5 | 8.428097 | No |
| 2001 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 12 | Q53HL2 | KNLQTAR | 135-141 | 1 | 16.918878 | No |
| 2005 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHK | 63-78 | 3 | Q53HL2 | VAKTNSLR | 10-17 | 3 | 13.669122999999999 | No |
| 2008 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 19.478912 | No |
| 2009 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 6 | Q53HL2 | VFKTPGLR | 196-203 | 3 | 14.852022999999999 | No |
| 2027 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 14 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.820224999999999 | No |
| 2032 | taxid_9606/edc | O15392 | NWPFLEGCACTPER | 24-37 | 6 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 5.25915 | No |
| 2033 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 9 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 14.021562 | No |
| 2038 | taxid_9606/edc | O15392 | MAEAGFIHCPTENEPDLAQCFFCFK | 38-62 | 16 | Q53HL2 | VFKTPGLR | 196-203 | 4 | 3.53497 | No |
| 2045 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 6.547233 | No |
| 2049 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 1 | Q53HL2 | CPPSKK | 145-150 | 4 | 12.540823 | No |
| 2050 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 3 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 13.625649 | No |
| 2066 | taxid_9606/edc | O15392 | ISTFKNWPFLEGCACTPER | 19-37 | 5 | Q53HL2 | QALEEAATADLDITEINK | 81-98 | 4 | 15.935411 | No |
| 2071 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | 15.882838999999999 | No |
| 2082 | taxid_9606/edc | O15392 | ELEGWEPDDDPIEEHKK | 63-79 | 14 | Q53HL2 | TQSIQGKGK | 152-160 | 7 | 12.837155 | No |
| 2092 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | 14.683186 | No |

### O15392 — Q9NQS7

**Dataset:** Complex Portal test. **ipTM:** 0.79. **Supporting spectrum matches:** 15.

[AF3 model](../store/PXD012882/af3_predictions/o15392__q9nqs7__3dd3d735/model.cif) · [Pair provenance](../store/PXD012882/af3_predictions/o15392__q9nqs7__3dd3d735/pair.json) · [Confidence](../store/PXD012882/af3_predictions/o15392__q9nqs7__3dd3d735/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1025 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 3 | 3.4879100000000003 | No |
| 1076 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 4 | 3.359395 | No |
| 1189 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 3 | 12.219958 | No |
| 1347 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 3 | 4.394672 | No |
| 1417 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | MFTREFSK | 44-51 | 7 | 2.266929 | No |
| 1441 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 4 | 5.451973000000001 | No |
| 1583 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q9NQS7 | EFSKEPELMP | 48-57 | 4 | 10.410526 | No |
| 1591 | taxid_9606/edc | O15392 | IAKETNNK | 113-120 | 3 | Q9NQS7 | LMEFLCNMDNK | 19-29 | 9 | 3.815734 | No |
| 1615 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q9NQS7 | MFTREFSK | 44-51 | 7 | 5.875017 | No |
| 1739 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 4 | 15.231888999999999 | No |
| 1826 | taxid_9606/edc | O15392 | IAKETNNK | 113-120 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 9 | 11.149654 | No |
| 1865 | taxid_9606/edc | O15392 | AIEQLAAMD | 134-142 | 9 | Q9NQS7 | EFSKEPELMP | 48-57 | 3 | 4.03951 | No |
| 1985 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q9NQS7 | EFSKEPELMP | 48-57 | 3 | 12.376652 | No |
| 2043 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q9NQS7 | EFSKEPELMP | 48-57 | 4 | 11.862485999999999 | No |
| 2056 | taxid_9606/edc | O15392 | RAIEQLAAMD | 133-142 | 10 | Q9NQS7 | EFSKEPELMP | 48-57 | 4 | 11.517318999999999 | No |

### P06899 — P0C0S8

**Dataset:** Complex Portal test. **ipTM:** 0.72. **Supporting spectrum matches:** 15.

[AF3 model](../store/PXD012882/af3_predictions/p06899__p0c0s8__84efe2d2/model.cif) · [Pair provenance](../store/PXD012882/af3_predictions/p06899__p0c0s8__84efe2d2/pair.json) · [Confidence](../store/PXD012882/af3_predictions/p06899__p0c0s8__84efe2d2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 919 | taxid_9606/edc | P06899 | IAGEASR | 73-79 | 6 | P0C0S8 | GNYAER | 37-42 | 5 | 2.4904520000000003 | No |
| 933 | taxid_9606/edc | P06899 | QVHPDTGISSKAMGIMNSFVNDIFER | 47-72 | 5 | P0C0S8 | GKQGGK | 4-9 | 2 | 2.086729 | No |
| 1113 | taxid_9606/edc | P06899 | SAPAPK | 6-11 | 1 | P0C0S8 | GNYAER | 37-42 | 5 | 13.239124 | No |
| 1133 | taxid_9606/edc | P06899 | AVTKAQK | 17-23 | 4 | P0C0S8 | KGNYAER | 36-42 | 6 | 6.981408999999999 | No |
| 1224 | taxid_9606/edc | P06899 | QVHPDTGISSKAMGIMNSFVNDIFER | 47-72 | 5 | P0C0S8 | GKQGGK | 4-9 | 2 | 3.807148 | No |
| 1285 | taxid_9606/edc | P06899 | SAPAPK | 6-11 | 1 | P0C0S8 | KGNYAER | 36-42 | 6 | 12.754023 | No |
| 1389 | taxid_9606/edc | P06899 | ESYSIYVYK | 35-43 | 1 | P0C0S8 | KGNYAER | 36-42 | 1 | 13.270527999999999 | No |
| 1415 | taxid_9606/edc | P06899 | STITSR | 87-92 | 1 | P0C0S8 | GNYAER | 37-42 | 5 | 13.50007 | No |
| 1593 | taxid_9606/edc | P06899 | AVTKAQK | 17-23 | 4 | P0C0S8 | GNYAER | 37-42 | 5 | 13.179115 | No |
| 1771 | taxid_9606/edc | P06899 | AMGIMNSFVNDIFERIAGEASR | 58-79 | 21 | P0C0S8 | KGNYAER | 36-42 | 6 | 8.531903 | No |
| 1797 | taxid_9606/edc | P06899 | IAGEASRLAHYNK | 73-85 | 6 | P0C0S8 | KGNYAER | 36-42 | 6 | 3.736122 | No |
| 1934 | taxid_9606/edc | P06899 | QVHPDTGISSK | 47-57 | 5 | P0C0S8 | GKQGGK | 4-9 | 2 | 14.339939 | No |
| 2020 | taxid_9606/edc | P06899 | STITSR | 87-92 | 1 | P0C0S8 | KGNYAER | 36-42 | 6 | 20.232983 | No |
| 2077 | taxid_9606/edc | P06899 | AVTKAQK | 17-23 | 4 | P0C0S8 | KGNYAER | 36-42 | 6 | 11.344873999999999 | No |
| 2088 | taxid_9606/edc | P06899 | AMGIMNSFVNDIFERIAGEASR | 58-79 | 21 | P0C0S8 | KGNYAER | 36-42 | 6 | 8.058286 | No |

### Q53HL2 — Q9NQS7

**Dataset:** Complex Portal test. **ipTM:** 0.37. **Supporting spectrum matches:** 136.

[AF3 model](../store/PXD012882/af3_predictions/q53hl2__q9nqs7__94984ec7/model.cif) · [Pair provenance](../store/PXD012882/af3_predictions/q53hl2__q9nqs7__94984ec7/pair.json) · [Confidence](../store/PXD012882/af3_predictions/q53hl2__q9nqs7__94984ec7/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 914 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 13.879989 | No |
| 917 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 8.207508 | No |
| 923 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 13.261187 | No |
| 924 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 6 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 4.202058 | No |
| 931 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 6.847474 | No |
| 932 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EPELMP | 52-57 | 3 | 10.913506 | No |
| 938 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 11.391603 | No |
| 951 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 10.879953 | No |
| 966 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 4.644941 | No |
| 978 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 14.180309 | No |
| 1004 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 12.819723 | No |
| 1006 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 12 | 11.786108 | No |
| 1011 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 5 | 9.29329 | No |
| 1021 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 8.210184 | No |
| 1033 | taxid_9606/edc | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 22.783045 | No |
| 1035 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 8.751181 | No |
| 1045 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 16.138654 | No |
| 1057 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 15.138598 | No |
| 1061 | taxid_9606/edc | Q53HL2 | TPGLRTPAAGER | 199-210 | 1 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 3.731878 | No |
| 1064 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 12.983091 | No |
| 1065 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 6 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 13.556439 | No |
| 1097 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 14.124627 | No |
| 1100 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 12 | 9.197992 | No |
| 1105 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 5.82927 | No |
| 1119 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 5 | 15.442197 | No |
| 1120 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 7 | 6.3809439999999995 | No |
| 1126 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 19.043845 | No |
| 1129 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 4.229267 | No |
| 1147 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 15.770461 | No |
| 1149 | taxid_9606/edc | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 8 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 14.273268 | No |
| 1151 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 9.359012 | No |
| 1161 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 11.07691 | No |
| 1176 | taxid_9606/edc | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 16.945183 | No |
| 1179 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 15.932832 | No |
| 1183 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 8.442988 | No |
| 1193 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 13.67384 | No |
| 1195 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 10.343806 | No |
| 1211 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 12.374225 | No |
| 1219 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EPELMP | 52-57 | 6 | 13.012622 | No |
| 1220 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 18.404628 | No |
| 1231 | taxid_9606/edc | Q53HL2 | IYNISGNGSPLADSKEIFLTVPVGGGESLR | 211-240 | 15 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 1 | 12.016219999999999 | No |
| 1238 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 7 | 7.862182000000001 | No |
| 1239 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 16.554380000000002 | No |
| 1254 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 1 | 3.913348 | No |
| 1260 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 6.905063999999999 | No |
| 1270 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 15.848772 | No |
| 1296 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 15.722933 | No |
| 1297 | taxid_9606/edc | Q53HL2 | LAQICSSIR | 269-277 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 7.69769 | No |
| 1319 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 16.264011 | No |
| 1321 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 16.289664000000002 | No |
| 1328 | taxid_9606/edc | Q53HL2 | QALEEAATADLDITEINK | 81-98 | 5 | Q9NQS7 | MGTTAPGPIHLLELCDQK | 1-18 | 1 | 17.395362000000002 | No |
| 1331 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 8.62946 | No |
| 1345 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 9.783026 | No |
| 1351 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 16.063096 | No |
| 1354 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 15.298499 | No |
| 1380 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 14.078653 | No |
| 1409 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 6 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 12.726056999999999 | No |
| 1419 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 12.518447 | No |
| 1431 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 4 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 10.040506 | No |
| 1436 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 7 | 5.699239 | No |
| 1446 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 7 | 11.431735999999999 | No |
| 1447 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 15.641148 | No |
| 1453 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 15.960734 | No |
| 1502 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 8.465678 | No |
| 1518 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 12.168621 | No |
| 1522 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 10.925313000000001 | No |
| 1525 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EPELMP | 52-57 | 1 | 11.558482 | No |
| 1529 | taxid_9606/edc | Q53HL2 | CPPSKK | 145-150 | 5 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 12.153114 | No |
| 1531 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 6.333616 | No |
| 1536 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 15.721204 | No |
| 1541 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 17.900777 | No |
| 1546 | taxid_9606/edc | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 19.057623 | No |
| 1549 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 8.711455 | No |
| 1552 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 7 | 17.875942000000002 | No |
| 1562 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 7.141011000000001 | No |
| 1589 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 9.957684 | No |
| 1592 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 10.961553 | No |
| 1594 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 12.133894999999999 | No |
| 1607 | taxid_9606/edc | Q53HL2 | LTAEAIQTPLKSAK | 99-112 | 11 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 15.579253 | No |
| 1616 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 13.780959 | No |
| 1626 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 7 | 23.935586999999998 | No |
| 1645 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 13.217267999999999 | No |
| 1646 | taxid_9606/edc | Q53HL2 | CPPSKK | 145-150 | 4 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 11.859532999999999 | No |
| 1663 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 11.240359999999999 | No |
| 1671 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 14.171189 | No |
| 1690 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 1 | 12.587316999999999 | No |
| 1697 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 15.628712 | No |
| 1703 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 17.299409 | No |
| 1710 | taxid_9606/edc | Q53HL2 | CPPSKK | 145-150 | 5 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 16.250450999999998 | No |
| 1722 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 13.362176 | No |
| 1724 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 17.128479000000002 | No |
| 1728 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 16.055973 | No |
| 1735 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 12.082248 | No |
| 1754 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 6 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 11.215423 | No |
| 1762 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 3.773097 | No |
| 1767 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EPELMP | 52-57 | 6 | 9.86593 | No |
| 1775 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 8.497474 | No |
| 1776 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 13.806735999999999 | No |
| 1780 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 7 | 20.740103 | No |
| 1793 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 4 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 9.611871 | No |
| 1796 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 17.384271000000002 | No |
| 1799 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 15.496445999999999 | No |
| 1800 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 5 | 10.560311 | No |
| 1811 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 13 | 13.969633 | No |
| 1822 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 6 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 14.014657999999999 | No |
| 1824 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 10.282867 | No |
| 1832 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 9.032517 | No |
| 1833 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 15.961922999999999 | No |
| 1844 | taxid_9606/edc | Q53HL2 | CPPSKK | 145-150 | 5 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 21 | 14.436128 | No |
| 1863 | taxid_9606/edc | Q53HL2 | CPPSKK | 145-150 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 11.384914 | No |
| 1866 | taxid_9606/edc | Q53HL2 | VAKTNSLR | 10-17 | 3 | Q9NQS7 | EFSKEPELMP | 48-57 | 5 | 9.850617 | No |
| 1871 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 14.002409 | No |
| 1887 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 11.43713 | No |
| 1900 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 18 | 15.002025999999999 | No |
| 1906 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 9.581489 | No |
| 1911 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 15.890758 | No |
| 1914 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 16.579579 | No |
| 1940 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 12.431445 | No |
| 1941 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 13 | 7.856876 | No |
| 1960 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 7 | 15.562553 | No |
| 1971 | taxid_9606/edc | Q53HL2 | HSIAQLDPEALGNIKK | 249-264 | 15 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 20.351207 | No |
| 1993 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 16.967044 | No |
| 1998 | taxid_9606/edc | Q53HL2 | LAQICSSIR | 269-277 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 11.125048 | No |
| 2003 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 6.752276999999999 | No |
| 2035 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 13 | 13.707018 | No |
| 2046 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 3.319535 | No |
| 2047 | taxid_9606/edc | Q53HL2 | KNLQTAR | 135-141 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 10 | 15.013974 | No |
| 2048 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 13.877844 | No |
| 2052 | taxid_9606/edc | Q53HL2 | KVIQVDEMIVEEEEEEENER | 115-134 | 1 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 6 | 13.161119 | No |
| 2054 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 7 | 13.459938 | No |
| 2058 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 22 | 11.333703 | No |
| 2068 | taxid_9606/edc | Q53HL2 | TQSIQGKGK | 152-160 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 4.287177 | No |
| 2070 | taxid_9606/edc | Q53HL2 | LPKALR | 61-66 | 3 | Q9NQS7 | DLVWLEEIQEEAER | 30-43 | 11 | 10.675992 | No |
| 2073 | taxid_9606/edc | Q53HL2 | VFKTPGLR | 196-203 | 4 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 17 | 15.392422999999999 | No |
| 2085 | taxid_9606/edc | Q53HL2 | KLASFLK | 20-26 | 1 | Q9NQS7 | EFSKEPELMP | 48-57 | 10 | 6.674793 | No |
| 2093 | taxid_9606/edc | Q53HL2 | LEVSMVKPTPGLTPR | 177-191 | 7 | Q9NQS7 | LMEFLCNMDNKDLVWLEEIQEEAER | 19-43 | 24 | 3.9369810000000003 | No |

## PXD014520

### O00303 — Q7L2H7

**Dataset:** Complex Portal test. **ipTM:** 0.67. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD014520/af3_predictions/o00303__q7l2h7__bd2a55b9/model.cif) · [Pair provenance](../store/PXD014520/af3_predictions/o00303__q7l2h7__bd2a55b9/pair.json) · [Confidence](../store/PXD014520/af3_predictions/o00303__q7l2h7__bd2a55b9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15380 | taxid_9606/bs3 | O00303 | MSIKAYVSTLMGVPGR | 211-226 | 4 | Q7L2H7 | LQLLSNLFHGMDKNTPVR | 103-120 | 13 | 12.117895 | No |
| 15470 | taxid_9606/bs3 | O00303 | MSIKAYVSTLMGVPGR | 211-226 | 4 | Q7L2H7 | LQLLSNLFHGMDKNTPVR | 103-120 | 13 | 17.773288 | No |

### P23396 — P62861

**Dataset:** Complex Portal test. **ipTM:** 0.17. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD014520/af3_predictions/p23396__p62861__3ee06dc1/model.cif) · [Pair provenance](../store/PXD014520/af3_predictions/p23396__p62861__3ee06dc1/pair.json) · [Confidence](../store/PXD014520/af3_predictions/p23396__p62861__3ee06dc1/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15390 | taxid_9606/bs3 | P23396 | YKLLGGLAVR | 107-116 | 2 | P62861 | FVNVVPTFGKK | 42-52 | 10 | 13.799603000000001 | No |
| 15562 | taxid_9606/bs3 | P23396 | YKLLGGLAVR | 107-116 | 2 | P62861 | FVNVVPTFGKK | 42-52 | 10 | 16.542993000000003 | No |

### P46781 — P62847

**Dataset:** Complex Portal test. **ipTM:** 0.65. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD014520/af3_predictions/p46781__p62847__cfb108d2/model.cif) · [Pair provenance](../store/PXD014520/af3_predictions/p46781__p62847__cfb108d2/pair.json) · [Confidence](../store/PXD014520/af3_predictions/p46781__p62847__cfb108d2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15384 | taxid_9606/bs3 | P46781 | KQVVNIPSFIVR | 139-150 | 1 | P62847 | THFGGGKTTGFGMIYDSLDYAK | 62-83 | 7 | 18.127989 | No |
| 15464 | taxid_9606/bs3 | P46781 | KQVVNIPSFIVR | 139-150 | 1 | P62847 | THFGGGKTTGFGMIYDSLDYAK | 62-83 | 7 | 18.260881 | No |

### P46782 — P62851

**Dataset:** Complex Portal test. **ipTM:** 0.73. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD014520/af3_predictions/p46782__p62851__4a09bd3b/model.cif) · [Pair provenance](../store/PXD014520/af3_predictions/p46782__p62851__4a09bd3b/pair.json) · [Confidence](../store/PXD014520/af3_predictions/p46782__p62851__4a09bd3b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15490 | taxid_9606/bs3 | P46782 | TIAECLADELINAAKGSSNSYAIK | 168-191 | 15 | P62851 | EVPNYKLITPAVVSER | 61-76 | 6 | 8.166805 | No |
| 15500 | taxid_9606/bs3 | P46782 | TIAECLADELINAAKGSSNSYAIK | 168-191 | 15 | P62851 | EVPNYKLITPAVVSER | 61-76 | 6 | 19.950782999999998 | No |

## PXD017996

### Q5TA45 — Q96HW7

**Dataset:** Complex Portal test. **ipTM:** 0.74. **Supporting spectrum matches:** 8.

[AF3 model](../store/PXD017996/af3_predictions/q5ta45__q96hw7__72f9b044/model.cif) · [Pair provenance](../store/PXD017996/af3_predictions/q5ta45__q96hw7__72f9b044/pair.json) · [Confidence](../store/PXD017996/af3_predictions/q5ta45__q96hw7__72f9b044/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10500 | taxid_9606/dss | Q5TA45 | KLEMEGR | 369-375 | 1 | Q96HW7 | AKELYSSGEFSSGR | 339-352 | 2 | 15.543486 | No |
| 10528 | taxid_9606/dss | Q5TA45 | QKIEQELR | 425-432 | 2 | Q96HW7 | KLMSDLR | 324-330 | 1 | 16.589757 | No |
| 10534 | taxid_9606/dss | Q5TA45 | QKIEQELR | 425-432 | 2 | Q96HW7 | KLMSDLR | 324-330 | 1 | 15.688473 | No |
| 10548 | taxid_9606/dss | Q5TA45 | QKIEQELR | 425-432 | 2 | Q96HW7 | KLMSDLR | 324-330 | 1 | 18.771455 | No |
| 10652 | taxid_9606/dss | Q5TA45 | KLEMEGR | 369-375 | 1 | Q96HW7 | AKELYSSGEFSSGR | 339-352 | 2 | 17.643335999999998 | No |
| 10657 | taxid_9606/dss | Q5TA45 | QKIEQELR | 425-432 | 2 | Q96HW7 | KLMSDLR | 324-330 | 1 | 18.573582000000002 | No |
| 10658 | taxid_9606/dss | Q5TA45 | KLEMEGR | 369-375 | 1 | Q96HW7 | AKELYSSGEFSSGR | 339-352 | 2 | 17.181165 | No |
| 10660 | taxid_9606/dss | Q5TA45 | KLEMEGR | 369-375 | 1 | Q96HW7 | AKELYSSGEFSSGR | 339-352 | 2 | 15.596076 | No |

### Q5TA45 — Q9NV88

**Dataset:** Complex Portal test. **ipTM:** 0.78. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD017996/af3_predictions/q5ta45__q9nv88__89578289/model.cif) · [Pair provenance](../store/PXD017996/af3_predictions/q5ta45__q9nv88__89578289/pair.json) · [Confidence](../store/PXD017996/af3_predictions/q5ta45__q9nv88__89578289/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10540 | taxid_9606/dss | Q5TA45 | LVSSEQALKELGLAEHQLR | 492-510 | 9 | Q9NV88 | AEVLALPFKR | 502-511 | 9 | 18.437835 | No |
| 10589 | taxid_9606/dss | Q5TA45 | LVSSEQALKELGLAEHQLR | 492-510 | 9 | Q9NV88 | AEVLALPFKR | 502-511 | 9 | 8.833016 | No |
| 10656 | taxid_9606/dss | Q5TA45 | LVSSEQALKELGLAEHQLR | 492-510 | 9 | Q9NV88 | AEVLALPFKR | 502-511 | 9 | 20.94925 | No |

### Q96HW7 — Q9NV88

**Dataset:** Complex Portal test. **ipTM:** 0.76. **Supporting spectrum matches:** 8.

[AF3 model](../store/PXD017996/af3_predictions/q96hw7__q9nv88__774a9c97/model.cif) · [Pair provenance](../store/PXD017996/af3_predictions/q96hw7__q9nv88__774a9c97/pair.json) · [Confidence](../store/PXD017996/af3_predictions/q96hw7__q9nv88__774a9c97/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10515 | taxid_9606/dss | Q96HW7 | VYIMPKPAR | 954-962 | 6 | Q9NV88 | LKHYPSIHGDFSNDFR | 373-388 | 2 | 8.784613 | No |
| 10522 | taxid_9606/dss | Q96HW7 | VYIMPKPAR | 954-962 | 6 | Q9NV88 | LKHYPSIHGDFSNDFR | 373-388 | 2 | 18.476532 | No |
| 10568 | taxid_9606/dss | Q96HW7 | KPVEAESVEGVVR | 62-74 | 1 | Q9NV88 | LLPSPLKDAVEVSTWR | 164-179 | 7 | 17.814992 | No |
| 10569 | taxid_9606/dss | Q96HW7 | KPVEAESVEGVVR | 62-74 | 1 | Q9NV88 | NKDIQR | 158-163 | 2 | 16.487819000000002 | No |
| 10595 | taxid_9606/dss | Q96HW7 | VYIMPKPAR | 954-962 | 6 | Q9NV88 | LKHYPSIHGDFSNDFR | 373-388 | 2 | 14.059741 | No |
| 10607 | taxid_9606/dss | Q96HW7 | KPVEAESVEGVVR | 62-74 | 1 | Q9NV88 | LLPSPLKDAVEVSTWR | 164-179 | 7 | 24.758933 | No |
| 10621 | taxid_9606/dss | Q96HW7 | VYIMPKPAR | 954-962 | 6 | Q9NV88 | LKHYPSIHGDFSNDFR | 373-388 | 2 | 15.72291 | No |
| 10634 | taxid_9606/dss | Q96HW7 | KPVEAESVEGVVR | 62-74 | 1 | Q9NV88 | NKDIQR | 158-163 | 2 | 19.658532 | No |

## PXD021708

### Q9NSB8 — Q9UHB9

**Dataset:** Negative control. **ipTM:** 0.12. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD021708/af3_predictions/q9nsb8__q9uhb9__5b31b4c6/model.cif) · [Pair provenance](../store/PXD021708/af3_predictions/q9nsb8__q9uhb9__5b31b4c6/pair.json) · [Confidence](../store/PXD021708/af3_predictions/q9nsb8__q9uhb9__5b31b4c6/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4525 | taxid_9606/dsso | Q9NSB8 | TQEKIETSSNHSQESGRETPSSTQASSVNGTDDEK | 117-151 | 4 | Q9UHB9 | AAEKQVPGGGGGGGSGGGGGSGGGGSGGGRGAGGEENK | 2-39 | 4 | 20.009311999999998 | No |
| 4534 | taxid_9606/dsso | Q9NSB8 | TQEKIETSSNHSQESGRETPSSTQASSVNGTDDEK | 117-151 | 4 | Q9UHB9 | MAAEKQVPGGGGGGGSGGGGGSGGGGSGGGRGAGGEENK | 1-39 | 5 | 22.138769999999997 | No |

## PXD026508

### A0A286YEY9 — O43548

**Dataset:** Negative control. **ipTM:** 0.22. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/a0a286yey9__o43548__a4de13c0/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/a0a286yey9__o43548__a4de13c0/pair.json) · [Confidence](../store/PXD026508/af3_predictions/a0a286yey9__o43548__a4de13c0/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8870 | taxid_9606/formaldehyde | A0A286YEY9 | GCCGCGGCGGCGGCGGGCGGGCGR | 2-25 | -1 | O43548 | GYRNVYVDFAL | 710-720 | -1 | 2.688072 | No |

### A0A286YF77 — A0A286YFB4

**Dataset:** Negative control. **ipTM:** 0.42. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/a0a286yf77__a0a286yfb4__3e6b2f30/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/a0a286yf77__a0a286yfb4__3e6b2f30/pair.json) · [Confidence](../store/PXD026508/af3_predictions/a0a286yf77__a0a286yfb4__3e6b2f30/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10675 | taxid_9606/formaldehyde | A0A286YF77 | TCHSCGCGCGCGK | 72-84 | -1 | A0A286YFB4 | TCHSCGCGCGK | 95-105 | -1 | 1.945481 | No |

### A0JD36 — P61296

**Dataset:** Negative control. **ipTM:** 0.30. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/a0jd36__p61296__3a8dd045/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/a0jd36__p61296__3a8dd045/pair.json) · [Confidence](../store/PXD026508/af3_predictions/a0jd36__p61296__3a8dd045/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8905 | taxid_9606/formaldehyde | A0JD36 | DEGSYYCACDT | 105-115 | -1 | P61296 | DDQNGEAEAFK | 158-168 | -1 | 2.900855 | No |

### A8MTL0 — Q9BPU6

**Dataset:** Negative control. **ipTM:** 0.29. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/a8mtl0__q9bpu6__3cfb8243/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/a8mtl0__q9bpu6__3cfb8243/pair.json) · [Confidence](../store/PXD026508/af3_predictions/a8mtl0__q9bpu6__3cfb8243/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9524 | taxid_9606/formaldehyde | A8MTL0 | TIMTER | 7-12 | -1 | Q9BPU6 | GLADPK | 118-123 | -1 | 7.261184 | No |

### E9PGG2 — P12104

**Dataset:** Negative control. **ipTM:** 0.28. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/e9pgg2__p12104__0e8d98c9/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/e9pgg2__p12104__0e8d98c9/pair.json) · [Confidence](../store/PXD026508/af3_predictions/e9pgg2__p12104__0e8d98c9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9742 | taxid_9606/formaldehyde | E9PGG2 | GPDLLQPSGNPR | 216-227 | -1 | P12104 | AFDSTWK | 2-8 | -1 | 5.104604 | No |

### O14863 — Q9UKU7

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o14863__q9uku7__319afa60/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o14863__q9uku7__319afa60/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o14863__q9uku7__319afa60/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9270 | taxid_9606/formaldehyde | O14863 | GSGCER | 257-262 | -1 | Q9UKU7 | TGGPGPK | 207-213 | -1 | 4.87607 | No |

### O15066 — O43405

**Dataset:** Negative control. **ipTM:** 0.15. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o15066__o43405__2ab99964/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o15066__o43405__2ab99964/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o15066__o43405__2ab99964/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11019 | taxid_9606/formaldehyde | O15066 | LKHLIIENFIPLEEK | 582-596 | -1 | O43405 | ALKHTAQK | 247-254 | -1 | 3.5315719999999997 | No |

### O43315 — P05129

**Dataset:** Negative control. **ipTM:** 0.12. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o43315__p05129__94110491/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o43315__p05129__94110491/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o43315__p05129__94110491/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10712 | taxid_9606/formaldehyde | O43315 | MQPEGAEK | 1-8 | -1 | P05129 | ITDFGMCK | 496-503 | -1 | 4.794602 | No |

### O75077 — Q6S8J7

**Dataset:** Negative control. **ipTM:** 0.18. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o75077__q6s8j7__af3912cb/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o75077__q6s8j7__af3912cb/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o75077__q6s8j7__af3912cb/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11420 | taxid_9606/formaldehyde | O75077 | GVKDSK | 204-209 | -1 | Q6S8J7 | GPGINK | 89-94 | -1 | 9.483231 | No |

### O75373 — Q8N8U2

**Dataset:** Negative control. **ipTM:** 0.19. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o75373__q8n8u2__ebef6251/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o75373__q8n8u2__ebef6251/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o75373__q8n8u2__ebef6251/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9155 | taxid_9606/formaldehyde | O75373 | VIHTGEK | 529-535 | -1 | Q8N8U2 | GTSHKR | 101-106 | -1 | 6.585076 | Yes |

### O75391 — Q5JWF8

**Dataset:** Negative control. **ipTM:** 0.21. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o75391__q5jwf8__9a393be3/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o75391__q5jwf8__9a393be3/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o75391__q5jwf8__9a393be3/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10244 | taxid_9606/formaldehyde | O75391 | SIEEAMNEIRAK | 202-213 | -1 | Q5JWF8 | AMYQECGSR | 230-238 | -1 | 4.0212959999999995 | No |

### O76013 — Q9P2P1

**Dataset:** Negative control. **ipTM:** 0.20. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o76013__q9p2p1__3ccc0c96/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o76013__q9p2p1__3ccc0c96/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o76013__q9p2p1__3ccc0c96/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10727 | taxid_9606/formaldehyde | O76013 | SVGSCR | 33-38 | -1 | Q9P2P1 | APAASK | 656-661 | -1 | 4.881576 | No |

### O94805 — P21462

**Dataset:** Negative control. **ipTM:** 0.25. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o94805__p21462__221295de/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o94805__p21462__221295de/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o94805__p21462__221295de/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10161 | taxid_9606/formaldehyde | O94805 | TPPSMR | 369-374 | -1 | P21462 | TVSLAK | 138-143 | -1 | 5.522101 | Yes |

### O94887 — Q15058

**Dataset:** Negative control. **ipTM:** 0.29. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/o94887__q15058__ed4599f4/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/o94887__q15058__ed4599f4/pair.json) · [Confidence](../store/PXD026508/af3_predictions/o94887__q15058__ed4599f4/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9030 | taxid_9606/formaldehyde | O94887 | MGEIEGTYRVLQTAGMR | 1-17 | -1 | Q15058 | NIDPERYR | 735-742 | -1 | 4.422355 | No |

### P00325 — Q7RTT4

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p00325__q7rtt4__489bee4f/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p00325__q7rtt4__489bee4f/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p00325__q7rtt4__489bee4f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9650 | taxid_9606/formaldehyde | P00325 | AAGAAR | 214-219 | -1 | Q7RTT4 | DPEEDDE | 181-187 | -1 | 3.218017 | Yes |

### P03973 — P50991

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD026508/af3_predictions/p03973__p50991__08c2ba34/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p03973__p50991__08c2ba34/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p03973__p50991__08c2ba34/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11657 | taxid_9606/formaldehyde | P03973 | CCMGMCGK | 117-124 | -1 | P50991 | ITGCASPGK | 376-384 | -1 | 1.9190939999999999 | No |
| 11657 | taxid_9606/formaldehyde | P03973 | CCMGMCGK | 117-124 | -1 | P50991 | ITGCASPGK | 376-384 | -1 | 1.9190939999999999 | No |

### P05106 — Q9NVN3

**Dataset:** Negative control. **ipTM:** 0.19. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p05106__q9nvn3__8133b164/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p05106__q9nvn3__8133b164/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p05106__q9nvn3__8133b164/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11451 | taxid_9606/formaldehyde | P05106 | SCMGLK | 411-416 | -1 | Q9NVN3 | IDKGSSYR | 353-360 | -1 | 6.933537 | No |

### P08195 — P41208

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p08195__p41208__f68aa683/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p08195__p41208__f68aa683/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p08195__p41208__f68aa683/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9816 | taxid_9606/formaldehyde | P08195 | ELPAQK | 111-116 | -1 | P41208 | EEILKAFK | 104-111 | -1 | 12.740641 | No |

### P09769 — Q0D2K2

**Dataset:** Negative control. **ipTM:** 0.28. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p09769__q0d2k2__e9d5b8c7/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p09769__q0d2k2__e9d5b8c7/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p09769__q0d2k2__e9d5b8c7/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11454 | taxid_9606/formaldehyde | P09769 | DWDQTR | 186-191 | -1 | Q0D2K2 | HGALPR | 546-551 | -1 | 5.590075 | No |

### P0DX52 — Q9NWL6

**Dataset:** Negative control. **ipTM:** 0.16. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p0dx52__q9nwl6__41f31632/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p0dx52__q9nwl6__41f31632/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p0dx52__q9nwl6__41f31632/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11009 | taxid_9606/formaldehyde | P0DX52 | NSPGVPAGAK | 24-33 | -1 | Q9NWL6 | GPNSSK | 31-36 | -1 | 7.229789 | Yes |

### P10082 — Q56P03

**Dataset:** Negative control. **ipTM:** 0.12. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD026508/af3_predictions/p10082__q56p03__a2078b26/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p10082__q56p03__a2078b26/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p10082__q56p03__a2078b26/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10970 | taxid_9606/formaldehyde | P10082 | SEGPDLW | 91-97 | -1 | Q56P03 | EMEAELNSTMKTMEDK | 64-79 | -1 | 3.178496 | No |
| 10970 | taxid_9606/formaldehyde | P10082 | SEGPDLW | 91-97 | -1 | Q56P03 | EMEAELNSTMKTMEDK | 64-79 | -1 | 3.178496 | No |

### P16401 — Q5RIA9

**Dataset:** Negative control. **ipTM:** 0.29. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p16401__q5ria9__aec5c660/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p16401__q5ria9__aec5c660/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p16401__q5ria9__aec5c660/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10735 | taxid_9606/formaldehyde | P16401 | KAGAAK | 125-130 | -1 | Q5RIA9 | SGLGAK | 36-41 | -1 | 8.469605000000001 | Yes |

### P16401 — Q5T2T1

**Dataset:** Negative control. **ipTM:** 0.23. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD026508/af3_predictions/p16401__q5t2t1__c6b97114/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p16401__q5t2t1__c6b97114/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p16401__q5t2t1__c6b97114/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11669 | taxid_9606/formaldehyde | P16401 | KAGAAK | 125-130 | -1 | Q5T2T1 | GGAADR | 170-175 | -1 | 2.591099 | Yes |
| 11669 | taxid_9606/formaldehyde | P16401 | KAAGAK | 144-149 | -1 | Q5T2T1 | GGAADR | 170-175 | -1 | 2.591099 | Yes |

### P16949 — Q86XT9

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p16949__q86xt9__316e747b/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p16949__q86xt9__316e747b/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p16949__q86xt9__316e747b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11526 | taxid_9606/formaldehyde | P16949 | KSHEAEVLK | 62-70 | -1 | Q86XT9 | ESHWSR | 232-237 | -1 | 5.442483 | No |

### P20648 — Q86V71

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p20648__q86v71__690d80dc/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p20648__q86v71__690d80dc/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p20648__q86v71__690d80dc/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9346 | taxid_9606/formaldehyde | P20648 | VPADIR | 210-215 | -1 | Q86V71 | TVGDCK | 119-124 | -1 | 5.765655 | Yes |

### P22492 — Q9UKS7

**Dataset:** Negative control. **ipTM:** 0.12. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p22492__q9uks7__b8109fb9/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p22492__q9uks7__b8109fb9/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p22492__q9uks7__b8109fb9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9854 | taxid_9606/formaldehyde | P22492 | ALAAAGYDVEKNNSR | 69-83 | -1 | Q9UKS7 | APKGSLK | 449-455 | -1 | 5.874597 | Yes |

### P23769 — Q7L8A9

**Dataset:** Negative control. **ipTM:** 0.19. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p23769__q7l8a9__d512df6a/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p23769__q7l8a9__d512df6a/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p23769__q7l8a9__d512df6a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10293 | taxid_9606/formaldehyde | P23769 | ARSCSEGR | 286-293 | -1 | Q7L8A9 | CWHVLKK | 250-256 | -1 | 3.431844 | No |

### P27816 — Q9NR45

**Dataset:** Negative control. **ipTM:** 0.24. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p27816__q9nr45__33ef3c9c/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p27816__q9nr45__33ef3c9c/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p27816__q9nr45__33ef3c9c/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9499 | taxid_9606/formaldehyde | P27816 | TEAPLAK | 554-560 | -1 | Q9NR45 | MAKECGADCAK | 42-52 | -1 | 4.034984 | No |

### P42892 — Q13619

**Dataset:** Negative control. **ipTM:** 0.49. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p42892__q13619__4be34653/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p42892__q13619__4be34653/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p42892__q13619__4be34653/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10851 | taxid_9606/formaldehyde | P42892 | WMDEETRK | 484-491 | -1 | Q13619 | DMELSK | 497-502 | -1 | 7.19033 | Yes |

### P46977 — P49908

**Dataset:** Negative control. **ipTM:** 0.16. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p46977__p49908__63412924/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p46977__p49908__63412924/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p46977__p49908__63412924/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9289 | taxid_9606/formaldehyde | P46977 | HNTPEDAK | 514-521 | -1 | P49908 | UEUPSN | 376-381 | -1 | 1.7635699999999999 | No |

### P49221 — P60709

**Dataset:** Negative control. **ipTM:** 0.23. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p49221__p60709__f54b5607/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p49221__p60709__f54b5607/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p49221__p60709__f54b5607/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9752 | taxid_9606/formaldehyde | P49221 | FVFSEVNGDR | 384-393 | -1 | P60709 | DSYVGDEAQSKR | 51-62 | -1 | 7.844812 | Yes |

### P55039 — Q9UBK9

**Dataset:** Negative control. **ipTM:** 0.16. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p55039__q9ubk9__2cf94f04/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p55039__q9ubk9__2cf94f04/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p55039__q9ubk9__2cf94f04/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10087 | taxid_9606/formaldehyde | P55039 | GASVEHVCHR | 312-321 | -1 | Q9UBK9 | MATPPK | 1-6 | -1 | 4.531789 | Yes |

### P60033 — Q86UL3

**Dataset:** Negative control. **ipTM:** 0.40. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p60033__q86ul3__7ea0bd59/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p60033__q86ul3__7ea0bd59/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p60033__q86ul3__7ea0bd59/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10710 | taxid_9606/formaldehyde | P60033 | MGVEGCTK | 1-8 | -1 | Q86UL3 | GMETIMDDEVTK | 122-133 | -1 | 3.559144 | No |

### P60852 — Q9NZH4

**Dataset:** Negative control. **ipTM:** 0.12. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/p60852__q9nzh4__784d707a/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/p60852__q9nzh4__784d707a/pair.json) · [Confidence](../store/PXD026508/af3_predictions/p60852__q9nzh4__784d707a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10645 | taxid_9606/formaldehyde | P60852 | TQMVALDGATPFQSHYQR | 487-504 | -1 | Q9NZH4 | ALDGRSQVSISCFGK | 34-48 | -1 | 4.392887 | No |

### Q00169 — Q709F0

**Dataset:** Negative control. **ipTM:** 0.30. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q00169__q709f0__4773c8e3/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q00169__q709f0__4773c8e3/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q00169__q709f0__4773c8e3/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9876 | taxid_9606/formaldehyde | Q00169 | GMTADD | 265-270 | -1 | Q709F0 | AAHSMDTLGSAGAK | 691-704 | -1 | 3.208905 | No |

### Q03395 — Q9BZG8

**Dataset:** Negative control. **ipTM:** 0.13. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q03395__q9bzg8__d0885680/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q03395__q9bzg8__d0885680/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q03395__q9bzg8__d0885680/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9033 | taxid_9606/formaldehyde | Q03395 | MAPVLPLVLPLQPRIR | 1-16 | -1 | Q9BZG8 | VAPLAP | 433-438 | -1 | 1.339157 | No |

### Q08E93 — Q107X0

**Dataset:** Negative control. **ipTM:** 0.08. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q08e93__q107x0__e838da76/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q08e93__q107x0__e838da76/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q08e93__q107x0__e838da76/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10275 | taxid_9606/formaldehyde | Q08E93 | HTHRVL | 108-113 | -1 | Q107X0 | VSPPGTATNPNPK | 69-81 | -1 | 3.460852 | No |

### Q13404 — Q9NVC6

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q13404__q9nvc6__8d78ae6c/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q13404__q9nvc6__8d78ae6c/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q13404__q9nvc6__8d78ae6c/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9861 | taxid_9606/formaldehyde | Q13404 | AISVLAK | 104-110 | -1 | Q9NVC6 | LSGPQAFDK | 407-415 | -1 | 7.195454 | No |

### Q14152 — Q9BUF5

**Dataset:** Negative control. **ipTM:** 0.18. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q14152__q9buf5__58c9794d/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q14152__q9buf5__58c9794d/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q14152__q9buf5__58c9794d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10393 | taxid_9606/formaldehyde | Q14152 | TADEDR | 1031-1036 | -1 | Q9BUF5 | GPMSMK | 319-324 | -1 | 4.803739 | No |

### Q5BKX5 — Q9NS23

**Dataset:** Negative control. **ipTM:** 0.15. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q5bkx5__q9ns23__19aa704d/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q5bkx5__q9ns23__19aa704d/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q5bkx5__q9ns23__19aa704d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11307 | taxid_9606/formaldehyde | Q5BKX5 | AGPVPK | 88-93 | -1 | Q9NS23 | GTACNPTR | 37-44 | -1 | 5.510929 | Yes |

### Q5RKV6 — Q6ZQY3

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q5rkv6__q6zqy3__56a91f08/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q5rkv6__q6zqy3__56a91f08/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q5rkv6__q6zqy3__56a91f08/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9251 | taxid_9606/formaldehyde | Q5RKV6 | MPGDHR | 1-6 | -1 | Q6ZQY3 | DVIHYSVK | 104-111 | -1 | 3.9616629999999997 | No |

### Q5T0U0 — Q9NP74

**Dataset:** Negative control. **ipTM:** 0.12. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q5t0u0__q9np74__ddde0c12/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q5t0u0__q9np74__ddde0c12/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q5t0u0__q9np74__ddde0c12/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9985 | taxid_9606/formaldehyde | Q5T0U0 | EDNQDTSSLADAVEK | 15-29 | -1 | Q9NP74 | MEEAELVKGR | 1-10 | -1 | 5.255349 | No |

### Q68EA5 — Q8NGL2

**Dataset:** Negative control. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q68ea5__q8ngl2__12fdf9a6/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q68ea5__q8ngl2__12fdf9a6/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q68ea5__q8ngl2__12fdf9a6/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10315 | taxid_9606/formaldehyde | Q68EA5 | SHECQSYSK | 531-539 | -1 | Q8NGL2 | KVMGSK | 303-308 | -1 | 3.595888 | Yes |

### Q6DRA6 — Q96PF2

**Dataset:** Negative control. **ipTM:** 0.18. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q6dra6__q96pf2__a5c22a69/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q6dra6__q96pf2__a5c22a69/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q6dra6__q96pf2__a5c22a69/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10067 | taxid_9606/formaldehyde | Q6DRA6 | MPEPAK | 1-6 | -1 | Q96PF2 | KTPTDFVER | 47-55 | -1 | 3.8166700000000002 | Yes |

### Q6PGQ1 — Q8TBE9

**Dataset:** Negative control. **ipTM:** 0.43. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q6pgq1__q8tbe9__d30130f2/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q6pgq1__q8tbe9__d30130f2/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q6pgq1__q8tbe9__d30130f2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11431 | taxid_9606/formaldehyde | Q6PGQ1 | MPTGPPEDR | 67-75 | -1 | Q8TBE9 | GGAANR | 85-90 | -1 | 4.6768339999999995 | No |

### Q6X4T0 — Q96PC2

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD026508/af3_predictions/q6x4t0__q96pc2__e84fb317/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q6x4t0__q96pc2__e84fb317/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q6x4t0__q96pc2__e84fb317/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11642 | taxid_9606/formaldehyde | Q6X4T0 | GMSNCSMTPMTSAPR | 65-79 | -1 | Q96PC2 | MIDFAHTTYK | 367-376 | -1 | 2.730912 | No |
| 11642 | taxid_9606/formaldehyde | Q6X4T0 | GMSNCSMTPMTSAPR | 65-79 | -1 | Q96PC2 | MIDFAHTTYK | 367-376 | -1 | 2.730912 | No |

### Q7L3S4 — Q9BPY3

**Dataset:** Negative control. **ipTM:** 0.30. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q7l3s4__q9bpy3__bac72967/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q7l3s4__q9bpy3__bac72967/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q7l3s4__q9bpy3__bac72967/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9476 | taxid_9606/formaldehyde | Q7L3S4 | CPECEGS | 311-317 | -1 | Q9BPY3 | MEDSGK | 138-143 | -1 | 2.646407 | Yes |

### Q86SJ2 — Q9NP50

**Dataset:** Negative control. **ipTM:** 0.25. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q86sj2__q9np50__c96d345f/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q86sj2__q9np50__c96d345f/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q86sj2__q9np50__c96d345f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11186 | taxid_9606/formaldehyde | Q86SJ2 | KAGAGK | 459-464 | -1 | Q9NP50 | TLSGNR | 97-102 | -1 | 5.07292 | No |

### Q86UB2 — Q96M53

**Dataset:** Negative control. **ipTM:** 0.22. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q86ub2__q96m53__10e36f97/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q86ub2__q96m53__10e36f97/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q86ub2__q96m53__10e36f97/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9537 | taxid_9606/formaldehyde | Q86UB2 | MPNVAETER | 1-9 | -1 | Q96M53 | KTSKPR | 343-348 | -1 | 4.939442 | No |

### Q8IWC1 — Q9BSJ6

**Dataset:** Negative control. **ipTM:** 0.14. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q8iwc1__q9bsj6__701829e1/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q8iwc1__q9bsj6__701829e1/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q8iwc1__q9bsj6__701829e1/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11695 | taxid_9606/formaldehyde | Q8IWC1 | KSEMDK | 472-477 | -1 | Q9BSJ6 | DVYASP | 243-248 | -1 | 4.209068 | No |

### Q8NGQ4 — Q8NHX4

**Dataset:** Negative control. **ipTM:** 0.11. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q8ngq4__q8nhx4__43ff2d53/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q8ngq4__q8nhx4__43ff2d53/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q8ngq4__q8nhx4__43ff2d53/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11333 | taxid_9606/formaldehyde | Q8NGQ4 | KAASDAN | 313-319 | -1 | Q8NHX4 | AGPLIR | 100-105 | -1 | 6.666387 | No |

### Q92922 — Q9BZI7

**Dataset:** Negative control. **ipTM:** 0.18. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q92922__q9bzi7__32ac4674/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q92922__q9bzi7__32ac4674/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q92922__q9bzi7__32ac4674/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9705 | taxid_9606/formaldehyde | Q92922 | GASAGR | 616-621 | -1 | Q9BZI7 | KEGGEE | 478-483 | -1 | 4.324091 | No |

### Q92932 — Q9BRR8

**Dataset:** Negative control. **ipTM:** 0.16. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q92932__q9brr8__9fc9152b/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q92932__q9brr8__9fc9152b/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q92932__q9brr8__9fc9152b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10177 | taxid_9606/formaldehyde | Q92932 | QPAEVR | 317-322 | -1 | Q9BRR8 | GPDKSR | 674-679 | -1 | 5.369315 | No |

### Q96PD5 — Q99943

**Dataset:** Negative control. **ipTM:** 0.33. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q96pd5__q99943__fd04647f/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q96pd5__q99943__fd04647f/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q96pd5__q99943__fd04647f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9569 | taxid_9606/formaldehyde | Q96PD5 | REPPPR | 563-568 | -1 | Q99943 | KPGGGG | 278-283 | -1 | 3.001587 | Yes |

### Q99624 — Q9H2S9

**Dataset:** Negative control. **ipTM:** 0.25. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q99624__q9h2s9__4a3de42e/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q99624__q9h2s9__4a3de42e/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q99624__q9h2s9__4a3de42e/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11178 | taxid_9606/formaldehyde | Q99624 | VEDPAR | 35-40 | -1 | Q9H2S9 | TPGSHR | 19-24 | -1 | 5.199403 | No |

### Q9BPX1 — Q9Y3L5

**Dataset:** Negative control. **ipTM:** 0.10. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q9bpx1__q9y3l5__d91b1192/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q9bpx1__q9y3l5__d91b1192/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q9bpx1__q9y3l5__d91b1192/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8884 | taxid_9606/formaldehyde | Q9BPX1 | GIGAGIVR | 20-27 | -1 | Q9Y3L5 | VDLEPER | 118-124 | -1 | 10.170283 | No |

### Q9BYU1 — Q9H5H4

**Dataset:** Negative control. **ipTM:** 0.37. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD026508/af3_predictions/q9byu1__q9h5h4__9119c9c5/model.cif) · [Pair provenance](../store/PXD026508/af3_predictions/q9byu1__q9h5h4__9119c9c5/pair.json) · [Confidence](../store/PXD026508/af3_predictions/q9byu1__q9h5h4__9119c9c5/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11584 | taxid_9606/formaldehyde | Q9BYU1 | GGAVAR | 102-107 | -1 | Q9H5H4 | THAAGR | 534-539 | -1 | 7.529486 | No |

## PXD027611

### O14497 — Q92925

**Dataset:** Complex Portal test. **ipTM:** 0.75. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD027611/af3_predictions/o14497__q92925__0d50462b/model.cif) · [Pair provenance](../store/PXD027611/af3_predictions/o14497__q92925__0d50462b/pair.json) · [Confidence](../store/PXD027611/af3_predictions/o14497__q92925__0d50462b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7652 | taxid_9606/dsso | O14497 | LEKLYSTMVR | 2144-2153 | 3 | Q92925 | KLDQTIAR | 168-175 | 1 | 11.611282 | No |
| 7661 | taxid_9606/dsso | O14497 | LEKLYSTMVR | 2144-2153 | 3 | Q92925 | KLDQTIAR | 168-175 | 1 | 20.890475000000002 | No |

### P62805 — P68431

**Dataset:** Complex Portal test. **ipTM:** 0.73. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD027611/af3_predictions/p62805__p68431__15a86a44/model.cif) · [Pair provenance](../store/PXD027611/af3_predictions/p62805__p68431__15a86a44/pair.json) · [Confidence](../store/PXD027611/af3_predictions/p62805__p68431__15a86a44/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7620 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | P68431 | EIAQDFKTDLR | 74-84 | 7 | 10.805824000000001 | Yes |
| 7649 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | P68431 | EIAQDFKTDLR | 74-84 | 7 | 24.624726000000003 | Yes |
| 7653 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | P68431 | EIAQDFKTDLR | 74-84 | 7 | 16.932262 | Yes |

### P62805 — Q16695

**Dataset:** Complex Portal test. **ipTM:** 0.67. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD027611/af3_predictions/p62805__q16695__663f6a12/model.cif) · [Pair provenance](../store/PXD027611/af3_predictions/p62805__q16695__663f6a12/pair.json) · [Confidence](../store/PXD027611/af3_predictions/p62805__q16695__663f6a12/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7620 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | Q16695 | EIAQDFKTDLR | 74-84 | 7 | 10.805824000000001 | Yes |
| 7649 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | Q16695 | EIAQDFKTDLR | 74-84 | 7 | 24.624726000000003 | Yes |
| 7653 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | Q16695 | EIAQDFKTDLR | 74-84 | 7 | 16.932262 | Yes |

### P62805 — Q71DI3

**Dataset:** Complex Portal test. **ipTM:** 0.67. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD027611/af3_predictions/p62805__q71di3__c287d867/model.cif) · [Pair provenance](../store/PXD027611/af3_predictions/p62805__q71di3__c287d867/pair.json) · [Confidence](../store/PXD027611/af3_predictions/p62805__q71di3__c287d867/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7620 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | Q71DI3 | EIAQDFKTDLR | 74-84 | 7 | 10.805824000000001 | Yes |
| 7649 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | Q71DI3 | EIAQDFKTDLR | 74-84 | 7 | 24.624726000000003 | Yes |
| 7653 | taxid_9606/dsso | P62805 | DAVTYTEHAKR | 69-79 | 10 | Q71DI3 | EIAQDFKTDLR | 74-84 | 7 | 16.932262 | Yes |

### Q8TAQ2 — Q92922

**Dataset:** Complex Portal test. **ipTM:** 0.25. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD027611/af3_predictions/q8taq2__q92922__5a0d1a0d/model.cif) · [Pair provenance](../store/PXD027611/af3_predictions/q8taq2__q92922__5a0d1a0d/pair.json) · [Confidence](../store/PXD027611/af3_predictions/q8taq2__q92922__5a0d1a0d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7644 | taxid_9606/dsso | Q8TAQ2 | AKHLAAVEER | 873-882 | 2 | Q92922 | VASAAAKAALEEFSR | 710-724 | 7 | 23.148803 | Yes |
| 7658 | taxid_9606/dsso | Q8TAQ2 | AKHLAAVEER | 873-882 | 2 | Q92922 | VASAAAKAALEEFSR | 710-724 | 7 | 24.907716 | Yes |
| 7666 | taxid_9606/dsso | Q8TAQ2 | AKHLAAVEER | 873-882 | 2 | Q92922 | VASAAAKAALEEFSR | 710-724 | 7 | 19.692848 | Yes |

## PXD030063

### P05141 — Q9H0C2

**Dataset:** Negative control. **ipTM:** 0.13. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD030063/af3_predictions/p05141__q9h0c2__c635be0a/model.cif) · [Pair provenance](../store/PXD030063/af3_predictions/p05141__q9h0c2__c635be0a/pair.json) · [Confidence](../store/PXD030063/af3_predictions/p05141__q9h0c2__c635be0a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7135 | taxid_9606/dsso | P05141 | YKQIFLGGVDK | 95-105 | 2 | Q9H0C2 | YFPTQALNFAFKDK | 93-106 | 12 | 13.774501999999998 | Yes |

## PXD031827

### PDK1_LKD_S241A — PDK1_SKD_S241A

**Dataset:** Earlier PDK1 pilot. **ipTM:** 0.56. **Supporting spectrum matches:** 103.

[AF3 model](../store/PXD031827/af3_predictions/PXD031827__pdk1lkds241a__pdk1skds241a/model.cif) · [Pair provenance](../store/PXD031827/af3_predictions/PXD031827__pdk1lkds241a__pdk1skds241a/pair.json) · [Confidence](../store/PXD031827/af3_predictions/PXD031827__pdk1lkds241a__pdk1skds241a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2194 | taxid_9606/bs3 | PDK1_LKD_S241A | KRPEDFK | 7-13 | 1 | PDK1_SKD_S241A | GPQPRK | 1-6 | 1 | 9.574309 | Yes |
| 2195 | taxid_9606/bs3 | PDK1_LKD_S241A | EYAIKILEK | 37-45 | 5 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 12.722623 | Yes |
| 2196 | taxid_9606/bs3 | PDK1_LKD_S241A | DLKPENILLNEDMHIQITDFGTAK | 135-158 | 22 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 10.295888 | Yes |
| 2197 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 15.229189 | Yes |
| 2198 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 16.34799 | Yes |
| 2199 | taxid_9606/bs3 | PDK1_LKD_S241A | DLKPENILLNEDMHIQITDFGTAKVLSPESK | 135-165 | 24 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 14.048576 | Yes |
| 2200 | taxid_9606/bs3 | PDK1_LKD_S241A | RPEDFKFGK | 8-16 | 6 | PDK1_SKD_S241A | GPQPRK | 1-6 | 1 | 8.081424 | Yes |
| 2201 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | KRPEDFK | 7-13 | 1 | 7.809149 | Yes |
| 2202 | taxid_9606/bs3 | PDK1_LKD_S241A | LLVLDATKR | 246-254 | 8 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 11.563631 | Yes |
| 2203 | taxid_9606/bs3 | PDK1_LKD_S241A | RPEDFKFGK | 8-16 | 6 | PDK1_SKD_S241A | GPQPRK | 1-6 | 1 | 7.894229 | Yes |
| 2204 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | RPEDFKFGK | 8-16 | 6 | 13.48718 | Yes |
| 2205 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | NGELLKYIR | 94-102 | 6 | 17.305757 | Yes |
| 2206 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | EYAIKILEK | 37-45 | 5 | 11.260955000000001 | Yes |
| 2207 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 14.329034 | Yes |
| 2208 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | AGNEYLIFQKIIK | 214-226 | 10 | 11.151176 | Yes |
| 2209 | taxid_9606/bs3 | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | RPEDFKFGK | 8-16 | 6 | 15.721175 | Yes |
| 2210 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 12.547271 | Yes |
| 2211 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 13.678662 | Yes |
| 2212 | taxid_9606/bs3 | PDK1_LKD_S241A | EYAIKILEK | 37-45 | 5 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 11.050291999999999 | Yes |
| 2213 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | KRPEDFK | 7-13 | 1 | 9.761562999999999 | Yes |
| 2214 | taxid_9606/bs3 | PDK1_LKD_S241A | LGCEEMEGYGPLK | 255-267 | 9 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 4.033626 | Yes |
| 2215 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 12.032896000000001 | Yes |
| 2216 | taxid_9606/bs3 | PDK1_LKD_S241A | RLGCEEMEGYGPLK | 254-267 | 10 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 5.040194 | Yes |
| 2217 | taxid_9606/bs3 | PDK1_LKD_S241A | ANAFVGTAQYVSPELLTEKSACK | 169-191 | 19 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 15.847619 | Yes |
| 2218 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | EYAIKILEK | 37-45 | 5 | 13.133917 | Yes |
| 2219 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | EYAIKILEK | 37-45 | 5 | 9.798122 | Yes |
| 2220 | taxid_9606/bs3 | PDK1_LKD_S241A | LGCEEMEGYGPLK | 255-267 | 9 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 3.317213 | Yes |
| 2221 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 11.259864 | Yes |
| 2222 | taxid_9606/bs3 | PDK1_LKD_S241A | KRPEDFK | 7-13 | 1 | PDK1_SKD_S241A | GPQPRK | 1-6 | 1 | 6.54223 | Yes |
| 2223 | taxid_9606/bs3 | PDK1_LKD_S241A | LGCEEMEGYGPLK | 255-267 | 9 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 5.444052 | Yes |
| 2224 | taxid_9606/bs3 | PDK1_LKD_S241A | ILGEGSFSTVVLAR | 17-30 | 6 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 14.304817 | Yes |
| 2225 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | RPEDFKFGK | 8-16 | 6 | 2.491668 | Yes |
| 2226 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 16.409653 | Yes |
| 2227 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | AGNEYLIFQKIIK | 214-226 | 10 | 3.930505 | Yes |
| 2228 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 14.808105 | Yes |
| 2229 | taxid_9606/bs3 | PDK1_LKD_S241A | LGCEEMEGYGPLK | 255-267 | 9 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 4.586526 | Yes |
| 2230 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | KIGSFDETCTR | 103-113 | 1 | 13.18603 | Yes |
| 2231 | taxid_9606/bs3 | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | VPYVTR | 54-59 | 3 | 6.324421 | Yes |
| 2232 | taxid_9606/bs3 | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | NGELLKYIR | 94-102 | 6 | 13.977004 | Yes |
| 2233 | taxid_9606/bs3 | PDK1_LKD_S241A | ANAFVGTAQYVSPELLTEKSACK | 169-191 | 19 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 12.555357 | Yes |
| 2234 | taxid_9606/bs3 | PDK1_LKD_S241A | RLGCEEMEGYGPLK | 254-267 | 10 | PDK1_SKD_S241A | VLSPESK | 159-165 | 3 | 3.20052 | Yes |
| 2235 | taxid_9606/bs3 | PDK1_LKD_S241A | ILGEGSFSTVVLAR | 17-30 | 6 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 6.926598 | Yes |
| 2236 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 15.047522 | Yes |
| 2237 | taxid_9606/bs3 | PDK1_LKD_S241A | FGKILGEGSFSTVVLAR | 14-30 | 3 | PDK1_SKD_S241A | KIGSFDETCTR | 103-113 | 1 | 18.604184 | Yes |
| 2238 | taxid_9606/bs3 | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | NGELLKYIR | 94-102 | 6 | 10.155177 | Yes |
| 2239 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | ENKVPYVTR | 51-59 | 3 | 11.264847 | Yes |
| 2240 | taxid_9606/bs3 | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | VPYVTR | 54-59 | 3 | 9.479231 | Yes |
| 2241 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | EYAIKILEK | 37-45 | 5 | 12.888036 | Yes |
| 2242 | taxid_9606/bs3 | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | VPYVTR | 54-59 | 3 | 14.786264 | Yes |
| 2243 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | RPEDFKFGK | 8-16 | 6 | 14.747912 | Yes |
| 2244 | taxid_9606/bs3 | PDK1_LKD_S241A | KRPEDFK | 7-13 | 1 | PDK1_SKD_S241A | GPQPRK | 1-6 | 1 | 11.484184 | Yes |
| 2245 | taxid_9606/bs3 | PDK1_LKD_S241A | RPEDFKFGK | 8-16 | 6 | PDK1_SKD_S241A | GPQPRK | 1-6 | 1 | 8.439055 | Yes |
| 2246 | taxid_9606/bs3 | PDK1_LKD_S241A | RPEDFKFGK | 8-16 | 6 | PDK1_SKD_S241A | RPEDFKFGK | 8-16 | 6 | 17.718566000000003 | Yes |
| 2247 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | LLVLDATKR | 246-254 | 8 | 13.75049 | Yes |
| 2248 | taxid_9606/bs3 | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | RPEDFKFGK | 8-16 | 6 | 10.691231 | Yes |
| 2249 | taxid_9606/bs3 | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | KRPEDFK | 7-13 | 1 | 10.123446000000001 | Yes |
| 2250 | taxid_9606/bs3 | PDK1_LKD_S241A | DLKPENILLNEDMHIQITDFGTAKVLSPESK | 135-165 | 18 | PDK1_SKD_S241A | FYTAEIVSALEYLHGKGIIHR | 114-134 | 16 | 10.010402 | Yes |
| 2251 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 15.860281 | Yes |
| 2252 | taxid_9606/bs3 | PDK1_LKD_S241A | LLVLDATKR | 246-254 | 8 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 11.009274999999999 | Yes |
| 2253 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | NGELLKYIR | 94-102 | 6 | 19.544195000000002 | Yes |
| 2254 | taxid_9606/bs3 | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | LEYDFPEKFFPK | 227-238 | 8 | 14.704092 | Yes |
| 3900 | taxid_9606/edc | PDK1_LKD_S241A | ANAFVGTAQYVSPELLTEK | 169-187 | 18 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 4.012529000000001 | Yes |
| 3901 | taxid_9606/edc | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 1 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 10 | 9.228399 | Yes |
| 3902 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 5 | PDK1_SKD_S241A | VPYVTR | 54-59 | 3 | 15.436259999999999 | Yes |
| 3903 | taxid_9606/edc | PDK1_LKD_S241A | ILGEGSFSTVVLAR | 17-30 | 4 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 15.383187 | Yes |
| 3904 | taxid_9606/edc | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 1 | PDK1_SKD_S241A | LEYDFPEK | 227-234 | 3 | 11.198963 | Yes |
| 3905 | taxid_9606/edc | PDK1_LKD_S241A | AGNEYLIFQKIIK | 214-226 | 10 | PDK1_SKD_S241A | LEYDFPEK | 227-234 | 4 | 11.189492999999999 | Yes |
| 3906 | taxid_9606/edc | PDK1_LKD_S241A | FFPKAR | 235-240 | 4 | PDK1_SKD_S241A | RPEDFK | 8-13 | 4 | 7.894306 | Yes |
| 3907 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 11.164522999999999 | Yes |
| 3908 | taxid_9606/edc | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 23.197935 | Yes |
| 3909 | taxid_9606/edc | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 18.530291000000002 | Yes |
| 3910 | taxid_9606/edc | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 9.417538 | Yes |
| 3911 | taxid_9606/edc | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | AGNEYLIFQK | 214-223 | 4 | 10.831702 | Yes |
| 3912 | taxid_9606/edc | PDK1_LKD_S241A | AGNEYLIFQKIIK | 214-226 | 10 | PDK1_SKD_S241A | LEYDFPEK | 227-234 | 2 | 12.191969 | Yes |
| 3913 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 4.307650000000001 | Yes |
| 3914 | taxid_9606/edc | PDK1_LKD_S241A | AGNEYLIFQKIIK | 214-226 | 10 | PDK1_SKD_S241A | LEYDFPEK | 227-234 | 4 | 12.121841 | Yes |
| 3915 | taxid_9606/edc | PDK1_LKD_S241A | AHPFFESVTWENLHQQTPPK | 268-287 | 11 | PDK1_SKD_S241A | FFPKAR | 235-240 | 4 | 5.089752 | Yes |
| 3916 | taxid_9606/edc | PDK1_LKD_S241A | ANAFVGTAQYVSPELLTEK | 169-187 | 18 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 3 | 9.784116000000001 | Yes |
| 3917 | taxid_9606/edc | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | ILGEGSFSTVVLAR | 17-30 | 4 | 19.054072 | Yes |
| 3918 | taxid_9606/edc | PDK1_LKD_S241A | ANAFVGTAQYVSPELLTEK | 169-187 | 18 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 7 | 10.004376 | Yes |
| 3919 | taxid_9606/edc | PDK1_LKD_S241A | KIGSFDETCTR | 103-113 | 1 | PDK1_SKD_S241A | ILGEGSFSTVVLAR | 17-30 | 4 | 11.498899999999999 | Yes |
| 3920 | taxid_9606/edc | PDK1_LKD_S241A | AGNEYLIFQKIIK | 214-226 | 10 | PDK1_SKD_S241A | LEYDFPEK | 227-234 | 2 | 7.863375 | Yes |
| 3921 | taxid_9606/edc | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | LGCEEMEGYGPLK | 255-267 | 5 | 19.418157 | Yes |
| 3922 | taxid_9606/edc | PDK1_LKD_S241A | FFPKAR | 235-240 | 4 | PDK1_SKD_S241A | RPEDFK | 8-13 | 4 | 6.987626000000001 | Yes |
| 3923 | taxid_9606/edc | PDK1_LKD_S241A | ILGEGSFSTVVLAR | 17-30 | 4 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 17.300448 | Yes |
| 3924 | taxid_9606/edc | PDK1_LKD_S241A | AHPFFESVTWENLHQQTPPK | 268-287 | 6 | PDK1_SKD_S241A | FFPKAR | 235-240 | 4 | 12.815729 | Yes |
| 3925 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 5 | PDK1_SKD_S241A | VPYVTR | 54-59 | 3 | 16.008072 | Yes |
| 3926 | taxid_9606/edc | PDK1_LKD_S241A | LEYDFPEK | 227-234 | 3 | PDK1_SKD_S241A | HIIKENK | 47-53 | 5 | 3.978216 | Yes |
| 3927 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 5 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 10 | 6.490905 | Yes |
| 3928 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 5 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 10 | 12.968683 | Yes |
| 3929 | taxid_9606/edc | PDK1_LKD_S241A | ILGEGSFSTVVLAR | 17-30 | 4 | PDK1_SKD_S241A | NGELLKYIR | 94-102 | 6 | 16.242497 | Yes |
| 3930 | taxid_9606/edc | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | RLGCEEMEGYGPLK | 254-267 | 8 | 8.94777 | Yes |
| 3931 | taxid_9606/edc | PDK1_LKD_S241A | EYAIKILEK | 37-45 | 5 | PDK1_SKD_S241A | ERDVMSR | 60-66 | 3 | 10.773112 | Yes |
| 3932 | taxid_9606/edc | PDK1_LKD_S241A | LEYDFPEK | 227-234 | 4 | PDK1_SKD_S241A | HIIKENK | 47-53 | 4 | 9.57424 | Yes |
| 3933 | taxid_9606/edc | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 14.711257 | Yes |
| 3934 | taxid_9606/edc | PDK1_LKD_S241A | ANAFVGTAQYVSPELLTEK | 169-187 | 18 | PDK1_SKD_S241A | VLSPESKQAR | 159-168 | 3 | 11.971192 | Yes |
| 3935 | taxid_9606/edc | PDK1_LKD_S241A | ILGEGSFSTVVLAR | 17-30 | 4 | PDK1_SKD_S241A | NGELLKYIR | 94-102 | 6 | 18.245618 | Yes |
| 3936 | taxid_9606/edc | PDK1_LKD_S241A | VLSPESKQAR | 159-168 | 7 | PDK1_SKD_S241A | LGCEEMEGYGPLK | 255-267 | 7 | 6.224728000000001 | Yes |
| 3937 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 2.395493 | Yes |
| 3938 | taxid_9606/edc | PDK1_LKD_S241A | AHPFFESVTWENLHQQTPPK | 268-287 | 6 | PDK1_SKD_S241A | FFPKAR | 235-240 | 4 | 13.534597999999999 | Yes |
| 3939 | taxid_9606/edc | PDK1_LKD_S241A | AHPFFESVTWENLHQQTPPK | 268-287 | 11 | PDK1_SKD_S241A | FFPKAR | 235-240 | 4 | 8.772574 | Yes |
| 3940 | taxid_9606/edc | PDK1_LKD_S241A | HIIKENK | 47-53 | 4 | PDK1_SKD_S241A | LGSGGSSGSSGQEMFR | 288-303 | 13 | 11.203062 | Yes |
| 3941 | taxid_9606/edc | PDK1_LKD_S241A | ENKVPYVTR | 51-59 | 3 | PDK1_SKD_S241A | LEYDFPEK | 227-234 | 4 | 9.700275 | Yes |

## PXD040144

### P17987 — P48643

**Dataset:** Complex Portal test. **ipTM:** 0.31. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD040144/af3_predictions/p17987__p48643__635deac8/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p17987__p48643__635deac8/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p17987__p48643__635deac8/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12135 | taxid_9606/dss | P17987 | QKIHPTSVISGYR | 110-122 | 2 | P48643 | LMGLEALKSHIMAAK | 28-42 | 8 | 21.829314 | No |
| 12228 | taxid_9606/dss | P17987 | QKIHPTSVISGYR | 110-122 | 2 | P48643 | LMGLEALKSHIMAAK | 28-42 | 8 | 15.886056 | No |

### P17987 — P49368

**Dataset:** Complex Portal test. **ipTM:** 0.49. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040144/af3_predictions/p17987__p49368__0a7e548c/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p17987__p49368__0a7e548c/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p17987__p49368__0a7e548c/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12204 | taxid_9606/dss | P17987 | SQNVMAAASIANIVKSSLGPVGLDK | 19-43 | 15 | P49368 | KVQSGNINAAK | 21-31 | 1 | 17.181427 | No |

### P17987 — P50990

**Dataset:** Complex Portal test. **ipTM:** 0.43. **Supporting spectrum matches:** 5.

[AF3 model](../store/PXD040144/af3_predictions/p17987__p50990__a04f698a/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p17987__p50990__a04f698a/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p17987__p50990__a04f698a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12164 | taxid_9606/dss | P17987 | WIGLDLSNGKPR | 485-496 | 10 | P50990 | ANEVISKLYAVHQEGNK | 460-476 | 7 | 21.95019 | No |
| 12179 | taxid_9606/dss | P17987 | WIGLDLSNGKPR | 485-496 | 10 | P50990 | ALAENSGVKANEVISK | 451-466 | 9 | 18.037742 | No |
| 12235 | taxid_9606/dss | P17987 | WIGLDLSNGKPR | 485-496 | 10 | P50990 | ALAENSGVKANEVISK | 451-466 | 9 | 24.278233999999998 | No |
| 12285 | taxid_9606/dss | P17987 | WIGLDLSNGKPR | 485-496 | 10 | P50990 | ANEVISKLYAVHQEGNK | 460-476 | 7 | 25.395239 | No |
| 12315 | taxid_9606/dss | P17987 | WIGLDLSNGKPR | 485-496 | 10 | P50990 | ANEVISKLYAVHQEGNK | 460-476 | 7 | 18.688591 | No |

### P17987 — P50991

**Dataset:** Complex Portal test. **ipTM:** 0.54. **Supporting spectrum matches:** 4.

[AF3 model](../store/PXD040144/af3_predictions/p17987__p50991__de673f8d/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p17987__p50991__de673f8d/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p17987__p50991__de673f8d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12264 | taxid_9606/dss | P17987 | LACKEAVR | 123-130 | 4 | P50991 | TSLGPKGMDK | 50-59 | 6 | 15.712299999999999 | No |
| 12299 | taxid_9606/dss | P17987 | LACKEAVR | 123-130 | 4 | P50991 | TSLGPKGMDK | 50-59 | 6 | 18.625149 | No |
| 12415 | taxid_9606/dss | P17987 | LACKEAVR | 123-130 | 4 | P50991 | TSLGPKGMDK | 50-59 | 6 | 18.696476 | No |
| 12421 | taxid_9606/dss | P17987 | DDKHGSYEDAVHSGALND | 539-556 | 3 | P50991 | GKGAYQDR | 20-27 | 2 | 21.277279999999998 | No |

### P40227 — P48643

**Dataset:** Complex Portal test. **ipTM:** 0.34. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040144/af3_predictions/p40227__p48643__4d5b956a/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p40227__p48643__4d5b956a/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p40227__p48643__4d5b956a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12362 | taxid_9606/dss | P40227 | TNLGPKGTMK | 36-45 | 6 | P48643 | MILKIDDIR | 526-534 | 4 | 17.173712000000002 | Yes |

### P40227 — P49368

**Dataset:** Complex Portal test. **ipTM:** 0.48. **Supporting spectrum matches:** 7.

[AF3 model](../store/PXD040144/af3_predictions/p40227__p49368__0245bb59/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p40227__p49368__0245bb59/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p40227__p49368__0245bb59/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12216 | taxid_9606/dss | P40227 | AGMSSLKG | 524-531 | 7 | P49368 | EIQVQHPAAKSMIEISR | 69-85 | 10 | 17.673989 | No |
| 12245 | taxid_9606/dss | P40227 | AGMSSLKG | 524-531 | 7 | P49368 | GASKEILSEVER | 378-389 | 4 | 17.241318 | No |
| 12320 | taxid_9606/dss | P40227 | AGMSSLKG | 524-531 | 7 | P49368 | KVQSGNINAAK | 21-31 | 1 | 12.307855 | No |
| 12357 | taxid_9606/dss | P40227 | TLNPKAEVAR | 6-15 | 5 | P49368 | KVQSGNINAAK | 21-31 | 1 | 19.356185 | No |
| 12364 | taxid_9606/dss | P40227 | TLNPKAEVAR | 6-15 | 5 | P49368 | KVQSGNINAAK | 21-31 | 1 | 23.114746999999998 | No |
| 12376 | taxid_9606/dss | P40227 | AGMSSLKG | 524-531 | 7 | P49368 | EIQVQHPAAKSMIEISR | 69-85 | 10 | 16.758522 | No |
| 12395 | taxid_9606/dss | P40227 | AGMSSLKG | 524-531 | 7 | P49368 | KVQSGNINAAK | 21-31 | 1 | 17.381864 | No |

### P40227 — P50990

**Dataset:** Complex Portal test. **ipTM:** 0.54. **Supporting spectrum matches:** 7.

[AF3 model](../store/PXD040144/af3_predictions/p40227__p50990__bb796ed0/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p40227__p50990__bb796ed0/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p40227__p50990__bb796ed0/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12187 | taxid_9606/dss | P40227 | HKSETDTSLIR | 198-208 | 2 | P50990 | AVDDGVNTFKVLTR | 391-404 | 10 | 20.698339 | No |
| 12210 | taxid_9606/dss | P40227 | TLNPKAEVAR | 6-15 | 5 | P50990 | APGFAQMLKEGAK | 8-20 | 9 | 16.39117 | No |
| 12223 | taxid_9606/dss | P40227 | TLNPKAEVAR | 6-15 | 5 | P50990 | EGAKHFSGLEEAVYR | 17-31 | 4 | 21.865495 | No |
| 12253 | taxid_9606/dss | P40227 | HKSETDTSLIR | 198-208 | 2 | P50990 | AVDDGVNTFKVLTR | 391-404 | 10 | 20.677982999999998 | No |
| 12316 | taxid_9606/dss | P40227 | TLNPKAEVAR | 6-15 | 5 | P50990 | EGAKHFSGLEEAVYR | 17-31 | 4 | 13.453828 | No |
| 12378 | taxid_9606/dss | P40227 | HKSETDTSLIR | 198-208 | 2 | P50990 | AVDDGVNTFKVLTR | 391-404 | 10 | 17.159722 | No |
| 12414 | taxid_9606/dss | P40227 | TLNPKAEVAR | 6-15 | 5 | P50990 | APGFAQMLKEGAK | 8-20 | 9 | 15.908405 | No |

### P48643 — P49368

**Dataset:** Complex Portal test. **ipTM:** 0.33. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040144/af3_predictions/p48643__p49368__105aed68/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p48643__p49368__105aed68/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p48643__p49368__105aed68/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12286 | taxid_9606/dss | P48643 | MIIEEAKR | 393-400 | 7 | P49368 | IDDIVSGHKK | 519-528 | 9 | 16.074264999999997 | No |

### P48643 — P50991

**Dataset:** Complex Portal test. **ipTM:** 0.40. **Supporting spectrum matches:** 4.

[AF3 model](../store/PXD040144/af3_predictions/p48643__p50991__790d2358/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p48643__p50991__790d2358/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p48643__p50991__790d2358/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12273 | taxid_9606/dss | P48643 | SHIMAAKAVANTMR | 36-49 | 7 | P50991 | GKGAYQDR | 20-27 | 2 | 18.41959 | No |
| 12372 | taxid_9606/dss | P48643 | SHIMAAKAVANTMR | 36-49 | 7 | P50991 | GKGAYQDR | 20-27 | 2 | 15.597404999999998 | No |
| 12383 | taxid_9606/dss | P48643 | LMGLEALKSHIMAAK | 28-42 | 8 | P50991 | GKGAYQDR | 20-27 | 2 | 20.018017999999998 | No |
| 12407 | taxid_9606/dss | P48643 | QVKEMNPALGIDCLHK | 481-496 | 3 | P50991 | GIHPTIISESFQKALEK | 127-143 | 13 | 22.983456 | No |

### P48643 — P78371

**Dataset:** Complex Portal test. **ipTM:** 0.38. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD040144/af3_predictions/p48643__p78371__be1752a1/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p48643__p78371__be1752a1/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p48643__p78371__be1752a1/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12143 | taxid_9606/dss | P48643 | ALQKYEK | 276-282 | 4 | P78371 | ILKHGINCFINR | 282-293 | 3 | 19.588924 | No |
| 12213 | taxid_9606/dss | P48643 | LIKGVIVDK | 224-232 | 3 | P78371 | IKIFGSR | 249-255 | 2 | 16.479042999999997 | No |

### P48643 — Q99832

**Dataset:** Complex Portal test. **ipTM:** 0.50. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD040144/af3_predictions/p48643__q99832__ec6c657a/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p48643__q99832__ec6c657a/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p48643__q99832__ec6c657a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12242 | taxid_9606/dss | P48643 | MIIEEAKR | 393-400 | 7 | Q99832 | AEKDNAEIR | 248-256 | 3 | 16.002217 | No |
| 12279 | taxid_9606/dss | P48643 | MIIEEAKR | 393-400 | 7 | Q99832 | AEKDNAEIR | 248-256 | 3 | 18.211972 | No |

### P49368 — P50990

**Dataset:** Complex Portal test. **ipTM:** 0.40. **Supporting spectrum matches:** 7.

[AF3 model](../store/PXD040144/af3_predictions/p49368__p50990__7167d421/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p49368__p50990__7167d421/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p49368__p50990__7167d421/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12138 | taxid_9606/dss | P49368 | KVQSGNINAAK | 21-31 | 1 | P50990 | APGFAQMLKEGAK | 8-20 | 9 | 20.363066 | No |
| 12181 | taxid_9606/dss | P49368 | KVQSGNINAAK | 21-31 | 1 | P50990 | ALAENSGVKANEVISK | 451-466 | 9 | 19.36008 | No |
| 12212 | taxid_9606/dss | P49368 | KVQSGNINAAK | 21-31 | 1 | P50990 | ALAENSGVKANEVISK | 451-466 | 9 | 21.286451 | No |
| 12373 | taxid_9606/dss | P49368 | SKAMTGVEQWPYR | 426-438 | 2 | P50990 | QITSYGETCPGLEQYAIKK | 422-440 | 18 | 24.991682 | No |
| 12384 | taxid_9606/dss | P49368 | SKAMTGVEQWPYR | 426-438 | 2 | P50990 | QITSYGETCPGLEQYAIKK | 422-440 | 18 | 22.638787999999998 | No |
| 12411 | taxid_9606/dss | P49368 | KVQSGNINAAK | 21-31 | 1 | P50990 | EGAKHFSGLEEAVYR | 17-31 | 4 | 20.511126 | No |
| 12420 | taxid_9606/dss | P49368 | SKAMTGVEQWPYR | 426-438 | 2 | P50990 | QITSYGETCPGLEQYAIKK | 422-440 | 18 | 16.987045 | No |

### P49368 — P50991

**Dataset:** Complex Portal test. **ipTM:** 0.40. **Supporting spectrum matches:** 4.

[AF3 model](../store/PXD040144/af3_predictions/p49368__p50991__20a4d0ea/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p49368__p50991__20a4d0ea/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p49368__p50991__20a4d0ea/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12148 | taxid_9606/dss | P49368 | KALDDMISTLK | 128-138 | 1 | P50991 | TSLGPKGMDK | 50-59 | 6 | 20.174647 | No |
| 12251 | taxid_9606/dss | P49368 | KALDDMISTLK | 128-138 | 1 | P50991 | TSLGPKGMDK | 50-59 | 6 | 17.905436 | No |
| 12413 | taxid_9606/dss | P49368 | KVQSGNINAAK | 21-31 | 1 | P50991 | GKGAYQDR | 20-27 | 2 | 8.952224000000001 | No |
| 12419 | taxid_9606/dss | P49368 | KVQSGNINAAK | 21-31 | 1 | P50991 | GKGAYQDR | 20-27 | 2 | 15.805359999999999 | No |

### P50991 — P78371

**Dataset:** Complex Portal test. **ipTM:** 0.53. **Supporting spectrum matches:** 17.

[AF3 model](../store/PXD040144/af3_predictions/p50991__p78371__6048d96a/model.cif) · [Pair provenance](../store/PXD040144/af3_predictions/p50991__p78371__6048d96a/pair.json) · [Confidence](../store/PXD040144/af3_predictions/p50991__p78371__6048d96a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12132 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | VDNIIKAAPR | 517-526 | 6 | 16.591144999999997 | No |
| 12165 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | EAESLIAKK | 112-120 | 8 | 18.861449 | No |
| 12173 | taxid_9606/dss | P50991 | KTGCNVLLIQK | 292-302 | 1 | P78371 | VAEIEHAEKEK | 264-274 | 9 | 19.675283999999998 | No |
| 12185 | taxid_9606/dss | P50991 | GAYQDRDKPAQIR | 22-34 | 8 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 9.81039 | No |
| 12209 | taxid_9606/dss | P50991 | DKPAQIR | 28-34 | 2 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 19.23398 | No |
| 12220 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | EAVAMESYAKALR | 432-444 | 10 | 16.422083999999998 | No |
| 12231 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 7.820429 | No |
| 12254 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 16.58467 | No |
| 12255 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | EAESLIAKK | 112-120 | 8 | 15.885185 | No |
| 12259 | taxid_9606/dss | P50991 | DKPAQIR | 28-34 | 2 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 9.581198 | No |
| 12263 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | VDNIIKAAPR | 517-526 | 6 | 20.320462 | No |
| 12276 | taxid_9606/dss | P50991 | GAYQDRDKPAQIR | 22-34 | 8 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 15.022013 | No |
| 12304 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | EAVAMESYAKALR | 432-444 | 10 | 13.618613 | No |
| 12305 | taxid_9606/dss | P50991 | GKGAYQDR | 20-27 | 2 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 13.57153 | No |
| 12399 | taxid_9606/dss | P50991 | GAYQDRDKPAQIR | 22-34 | 8 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 20.740757 | No |
| 12403 | taxid_9606/dss | P50991 | DKPAQIR | 28-34 | 2 | P78371 | KIHPQTIIAGWR | 120-131 | 1 | 14.272946999999998 | No |
| 12409 | taxid_9606/dss | P50991 | PENVAPR | 2-8 | 1 | P78371 | VDNIIKAAPR | 517-526 | 6 | 15.355068 | No |

## PXD040984

### P04264 — P29375

**Dataset:** Negative control. **ipTM:** 0.19. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040984/af3_predictions/p04264__p29375__8776235f/model.cif) · [Pair provenance](../store/PXD040984/af3_predictions/p04264__p29375__8776235f/pair.json) · [Confidence](../store/PXD040984/af3_predictions/p04264__p29375__8776235f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3453 | taxid_9606/benzoyl | P04264 | SGGGFSSGSAGIINYQR | 13-29 | -1 | P29375 | IVASKGGFEMVTK | 165-177 | -1 | 5.235773 | No |

### P07477 — P35900

**Dataset:** Negative control. **ipTM:** 0.08. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040984/af3_predictions/p07477__p35900__fdb081c2/model.cif) · [Pair provenance](../store/PXD040984/af3_predictions/p07477__p35900__fdb081c2/pair.json) · [Confidence](../store/PXD040984/af3_predictions/p07477__p35900__fdb081c2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2147 | taxid_9606/benzoyl | P07477 | HPQYDR | 96-101 | -1 | P35900 | NLQEAKEQFER | 253-263 | -1 | 4.790411 | Yes |

### P08729 — Q8N1A0

**Dataset:** Negative control. **ipTM:** 0.42. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040984/af3_predictions/p08729__q8n1a0__0c21a952/model.cif) · [Pair provenance](../store/PXD040984/af3_predictions/p08729__q8n1a0__0c21a952/pair.json) · [Confidence](../store/PXD040984/af3_predictions/p08729__q8n1a0__0c21a952/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3425 | taxid_9606/benzoyl | P08729 | SAYGGPVGAGIR | 53-64 | -1 | Q8N1A0 | LEQEIATYRHLLEK | 132-145 | -1 | 2.363192 | Yes |

### Q6KB66 — Q9NSB4

**Dataset:** Complex Portal test. **ipTM:** 0.38. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD040984/af3_predictions/q6kb66__q9nsb4__a79b12b3/model.cif) · [Pair provenance](../store/PXD040984/af3_predictions/q6kb66__q9nsb4__a79b12b3/pair.json) · [Confidence](../store/PXD040984/af3_predictions/q6kb66__q9nsb4__a79b12b3/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3041 | taxid_9606/benzoyl | Q6KB66 | KVSQER | 145-150 | -1 | Q9NSB4 | ALGCLGSR | 48-55 | -1 | 3.407179 | Yes |

## PXD041011

### P80297 — Q8N339

**Dataset:** Negative control. **ipTM:** 0.23. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD041011/af3_predictions/p80297__q8n339__b8583508/model.cif) · [Pair provenance](../store/PXD041011/af3_predictions/p80297__q8n339__b8583508/pair.json) · [Confidence](../store/PXD041011/af3_predictions/p80297__q8n339__b8583508/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 39708 | taxid_9606/dss | P80297 | DPNCSCSPVGSCACAGSCKCK | 2-22 | 19 | Q8N339 | KSCCSCCPVGCAK | 31-43 | 1 | 4.8583479999999994 | Yes |

## PXD060825

### P05141 — Q9H0C2

**Dataset:** Negative control. **ipTM:** 0.13. **Supporting spectrum matches:** 4.

[AF3 model](../store/PXD060825/af3_predictions/p05141__q9h0c2__c635be0a/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p05141__q9h0c2__c635be0a/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p05141__q9h0c2__c635be0a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20705 | taxid_9606/dsso | P05141 | YKQIFLGGVDK | 95-105 | 2 | Q9H0C2 | YFPTQALNFAFKDK | 93-106 | 12 | 25.290643 | Yes |
| 21151 | taxid_9606/dsso | P05141 | IPKEQGVLSFWR | 61-72 | 3 | Q9H0C2 | YFPTQALNFAFKDK | 93-106 | 12 | 25.346449 | Yes |
| 21241 | taxid_9606/dsso | P05141 | QIFLGGVDKR | 97-106 | 9 | Q9H0C2 | YFPTQALNFAFKDK | 93-106 | 12 | 18.140065 | Yes |
| 21373 | taxid_9606/dsso | P05141 | LAADVGKAGAER | 141-152 | 7 | Q9H0C2 | YFPTQALNFAFKDK | 93-106 | 12 | 21.044151 | Yes |

### P05165 — P05166

**Dataset:** Complex Portal test. **ipTM:** 0.83. **Supporting spectrum matches:** 15.

[AF3 model](../store/PXD060825/af3_predictions/p05165__p05166__3e18a5c1/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p05165__p05166__3e18a5c1/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p05165__p05166__3e18a5c1/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19960 | taxid_9606/dsso | P05165 | FMLEKVTEDTSSVLR | 649-663 | 5 | P05166 | IDAQHKR | 55-61 | 6 | 19.001983 | No |
| 19968 | taxid_9606/dsso | P05165 | FMLEKVTEDTSSVLR | 649-663 | 5 | P05166 | IDAQHKR | 55-61 | 6 | 21.62512 | No |
| 19996 | taxid_9606/dsso | P05165 | VYAEDPYKSFGLPSIGR | 400-416 | 8 | P05166 | TVGIVGNQPKVASGCLDINSSVK | 351-373 | 10 | 36.255939 | No |
| 20044 | taxid_9606/dsso | P05165 | LAAELNKFMLEK | 642-653 | 7 | P05166 | IDAQHKR | 55-61 | 6 | 23.360416 | No |
| 20347 | taxid_9606/dsso | P05165 | LAAELNKFMLEK | 642-653 | 7 | P05166 | IDAQHKR | 55-61 | 6 | 21.779277 | No |
| 20414 | taxid_9606/dsso | P05165 | LAAELNKFMLEK | 642-653 | 7 | P05166 | IDAQHKR | 55-61 | 6 | 23.18521 | No |
| 20434 | taxid_9606/dsso | P05165 | VYAEDPYKSFGLPSIGR | 400-416 | 8 | P05166 | TVGIVGNQPKVASGCLDINSSVK | 351-373 | 10 | 30.98535 | No |
| 20441 | taxid_9606/dsso | P05165 | FMLEKVTEDTSSVLR | 649-663 | 5 | P05166 | IDAQHKR | 55-61 | 6 | 20.632207 | No |
| 20532 | taxid_9606/dsso | P05165 | FMLEKVTEDTSSVLR | 649-663 | 5 | P05166 | SVTNEDVTQEELGGAKTHTTMSGVAHR | 233-259 | 16 | 18.303429 | No |
| 20572 | taxid_9606/dsso | P05165 | FMLEKVTEDTSSVLR | 649-663 | 5 | P05166 | IDAQHKR | 55-61 | 6 | 25.250731000000002 | No |
| 21013 | taxid_9606/dsso | P05165 | LAAELNKFMLEK | 642-653 | 7 | P05166 | IDAQHKR | 55-61 | 6 | 24.971321 | No |
| 21137 | taxid_9606/dsso | P05165 | FMLEKVTEDTSSVLR | 649-663 | 5 | P05166 | SVTNEDVTQEELGGAKTHTTMSGVAHR | 233-259 | 16 | 29.905818 | No |
| 21167 | taxid_9606/dsso | P05165 | TGTVKSVHCQAGDTVGEGDLLVELE | 704-728 | 5 | P05166 | IDAQHKR | 55-61 | 6 | 17.659137 | No |
| 21296 | taxid_9606/dsso | P05165 | TGTVKSVHCQAGDTVGEGDLLVELE | 704-728 | 5 | P05166 | IDAQHKR | 55-61 | 6 | 21.549603 | No |
| 21364 | taxid_9606/dsso | P05165 | VYAEDPYKSFGLPSIGR | 400-416 | 8 | P05166 | EFFEIMPNYAKNIIVGFAR | 328-346 | 11 | 30.955893 | No |

### P09496 — Q00610

**Dataset:** Complex Portal test. **ipTM:** 0.58. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD060825/af3_predictions/p09496__q00610__1efbbf85/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p09496__q00610__1efbbf85/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p09496__q00610__1efbbf85/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20405 | taxid_9606/dsso | P09496 | SVLISLKQAPLVH | 236-248 | 7 | Q00610 | DSLYKDAMQYASESK | 1531-1545 | 5 | 26.803105000000002 | No |

### P18077 — Q02878

**Dataset:** Complex Portal test. **ipTM:** 0.88. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD060825/af3_predictions/p18077__q02878__055dd38f/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p18077__q02878__055dd38f/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p18077__q02878__055dd38f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20615 | taxid_9606/dsso | P18077 | VIWGKVTR | 69-76 | 5 | Q02878 | THQKFVIATSTK | 189-200 | 4 | 19.64913 | No |
| 20757 | taxid_9606/dsso | P18077 | VIWGKVTR | 69-76 | 5 | Q02878 | THQKFVIATSTK | 189-200 | 4 | 22.215523 | No |

### P21912 — P31040

**Dataset:** Complex Portal test. **ipTM:** 0.89. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD060825/af3_predictions/p21912__p31040__0e8a8802/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p21912__p31040__0e8a8802/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p21912__p31040__0e8a8802/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20968 | taxid_9606/dsso | P21912 | DESQEGKQQYLQSIEER | 161-177 | 7 | P31040 | TEDGKIYQR | 163-171 | 5 | 27.378890000000002 | No |

### P56381 — Q5VTU8

**Dataset:** Complex Portal test. **ipTM:** 0.34. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD060825/af3_predictions/p56381__q5vtu8__d8128935/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p56381__q5vtu8__d8128935/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p56381__q5vtu8__d8128935/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20656 | taxid_9606/dsso | P56381 | YSQICAKAVR | 15-24 | 7 | Q5VTU8 | DALKTEFK | 25-32 | 4 | 16.928104 | Yes |

### P62424 — Q9Y3U8

**Dataset:** Complex Portal test. **ipTM:** 0.82. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD060825/af3_predictions/p62424__q9y3u8__afa798ba/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/p62424__q9y3u8__afa798ba/pair.json) · [Confidence](../store/PXD060825/af3_predictions/p62424__q9y3u8__afa798ba/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20388 | taxid_9606/dsso | P62424 | HWGGNVLGPKSVAR | 236-249 | 10 | Q9Y3U8 | AMELLKVSK | 57-65 | 6 | 20.801951 | No |
| 21292 | taxid_9606/dsso | P62424 | HWGGNVLGPKSVAR | 236-249 | 10 | Q9Y3U8 | AMELLKVSK | 57-65 | 6 | 16.565101 | No |

### Q15393 — Q9BWJ5

**Dataset:** Complex Portal test. **ipTM:** 0.89. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD060825/af3_predictions/q15393__q9bwj5__bad9e02e/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/q15393__q9bwj5__bad9e02e/pair.json) · [Confidence](../store/PXD060825/af3_predictions/q15393__q9bwj5__bad9e02e/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20716 | taxid_9606/dsso | Q15393 | AVMISAIEKQK | 129-139 | 9 | Q9BWJ5 | YTIHSQLEHLQSKYIGTGHADTTK | 5-28 | 13 | 20.555033 | No |
| 20858 | taxid_9606/dsso | Q15393 | AVMISAIEKQK | 129-139 | 9 | Q9BWJ5 | YTIHSQLEHLQSKYIGTGHADTTK | 5-28 | 13 | 23.946999 | No |

### Q86VS8 — Q9UJC3

**Dataset:** Complex Portal test. **ipTM:** 0.34. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD060825/af3_predictions/q86vs8__q9ujc3__99f390e7/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/q86vs8__q9ujc3__99f390e7/pair.json) · [Confidence](../store/PXD060825/af3_predictions/q86vs8__q9ujc3__99f390e7/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20740 | taxid_9606/dsso | Q86VS8 | SQLETYKR | 366-373 | 7 | Q9UJC3 | KANAAR | 363-368 | 1 | 15.317352 | Yes |

### Q8NCA5 — Q9Y224

**Dataset:** Complex Portal test. **ipTM:** 0.53. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD060825/af3_predictions/q8nca5__q9y224__04c5c72c/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/q8nca5__q9y224__04c5c72c/pair.json) · [Confidence](../store/PXD060825/af3_predictions/q8nca5__q9y224__04c5c72c/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20976 | taxid_9606/dsso | Q8NCA5 | SVLSPKTTISVAHLLAAR | 255-272 | 6 | Q9Y224 | HDDYLVMLKAIR | 146-157 | 9 | 29.519047 | No |

### Q96RQ3 — Q9HCC0

**Dataset:** Complex Portal test. **ipTM:** 0.83. **Supporting spectrum matches:** 6.

[AF3 model](../store/PXD060825/af3_predictions/q96rq3__q9hcc0__24ed153f/model.cif) · [Pair provenance](../store/PXD060825/af3_predictions/q96rq3__q9hcc0__24ed153f/pair.json) · [Confidence](../store/PXD060825/af3_predictions/q96rq3__q9hcc0__24ed153f/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20128 | taxid_9606/dsso | Q96RQ3 | HTPLVEFEEEESDKR | 708-722 | 14 | Q9HCC0 | EGKQFSSADEAALK | 493-506 | 3 | 22.800711 | No |
| 20551 | taxid_9606/dsso | Q96RQ3 | HTPLVEFEEEESDKR | 708-722 | 14 | Q9HCC0 | LGGGEKAR | 65-72 | 6 | 15.969224 | No |
| 20830 | taxid_9606/dsso | Q96RQ3 | HTPLVEFEEEESDKR | 708-722 | 14 | Q9HCC0 | EGKQFSSADEAALK | 493-506 | 3 | 20.415159 | No |
| 20957 | taxid_9606/dsso | Q96RQ3 | HTPLVEFEEEESDKR | 708-722 | 14 | Q9HCC0 | EYEAEGIAKDGAK | 412-424 | 9 | 21.91906 | No |
| 21077 | taxid_9606/dsso | Q96RQ3 | HTPLVEFEEEESDKR | 708-722 | 14 | Q9HCC0 | LGGGEKAR | 65-72 | 6 | 22.832976000000002 | No |
| 21276 | taxid_9606/dsso | Q96RQ3 | HTPLVEFEEEESDKR | 708-722 | 14 | Q9HCC0 | EYEAEGIAKDGAK | 412-424 | 9 | 14.589780000000001 | No |

## PXD064792

### P0C0S8 — P68431

**Dataset:** Complex Portal test. **ipTM:** 0.58. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064792/af3_predictions/p0c0s8__p68431__93229585/model.cif) · [Pair provenance](../store/PXD064792/af3_predictions/p0c0s8__p68431__93229585/pair.json) · [Confidence](../store/PXD064792/af3_predictions/p0c0s8__p68431__93229585/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21067 | taxid_9606/fa | P0C0S8 | VTIAQGGVLPNIQAVLLPK | 101-119 | -1 | P68431 | QLATKAARK | 20-28 | -1 | 10.090633 | Yes |

### P29374 — Q9UK53

**Dataset:** Complex Portal test. **ipTM:** 0.20. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064792/af3_predictions/p29374__q9uk53__04116592/model.cif) · [Pair provenance](../store/PXD064792/af3_predictions/p29374__q9uk53__04116592/pair.json) · [Confidence](../store/PXD064792/af3_predictions/p29374__q9uk53__04116592/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19567 | taxid_9606/fa | P29374 | QEDSDK | 535-540 | -1 | Q9UK53 | ERAYNR | 417-422 | -1 | 9.103353 | No |

### Q8N3P4 — Q9H270

**Dataset:** Complex Portal test. **ipTM:** 0.44. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064792/af3_predictions/q8n3p4__q9h270__4a0c6d86/model.cif) · [Pair provenance](../store/PXD064792/af3_predictions/q8n3p4__q9h270__4a0c6d86/pair.json) · [Confidence](../store/PXD064792/af3_predictions/q8n3p4__q9h270__4a0c6d86/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18798 | taxid_9606/fa | Q8N3P4 | AVVGLSGDASK | 530-540 | -1 | Q9H270 | ASPKIFQK | 812-819 | -1 | 11.114309 | No |

## PXD064931

### O00231 — O00232

**Dataset:** Complex Portal test. **ipTM:** 0.54. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/o00231__o00232__b2ac8326/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00231__o00232__b2ac8326/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00231__o00232__b2ac8326/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14803 | taxid_9606/dsso | O00231 | IMLNTPEDVQALVSGKLALR | 259-278 | 16 | O00232 | TQIISKK | 202-208 | 6 | 7.068136 | No |
| 14818 | taxid_9606/dsso | O00231 | IMLNTPEDVQALVSGKLALR | 259-278 | 16 | O00232 | TQIISKK | 202-208 | 6 | 11.055783000000002 | No |
| 15002 | taxid_9606/dsso | O00231 | IMLNTPEDVQALVSGKLALR | 259-278 | 16 | O00232 | TQIISKK | 202-208 | 6 | 18.471629 | No |

### O00231 — P17980

**Dataset:** Complex Portal test. **ipTM:** 0.12. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/o00231__p17980__4d07d777/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00231__p17980__4d07d777/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00231__p17980__4d07d777/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4627 | taxid_9606/bs3 | O00231 | TYEAALETIQNMSK | 396-409 | 13 | P17980 | MATVWDEAEQDGIGEEVLK | 17-35 | 3 | 8.860737 | No |
| 4635 | taxid_9606/bs3 | O00231 | TYEAALETIQNMSK | 396-409 | 13 | P17980 | MATVWDEAEQDGIGEEVLK | 17-35 | 3 | 9.012877 | No |

### O00232 — P35998

**Dataset:** Complex Portal test. **ipTM:** 0.17. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/o00232__p35998__13cd24d8/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00232__p35998__13cd24d8/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00232__p35998__13cd24d8/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4638 | taxid_9606/bs3 | O00232 | LIDTLRMVTEGK | 124-135 | 4 | P35998 | ALDEGDIALLKTYGQSTYSR | 24-43 | 11 | 14.351934 | No |

### O00232 — P49720

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/o00232__p49720__93dcc691/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00232__p49720__93dcc691/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00232__p49720__93dcc691/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4632 | taxid_9606/bs3 | O00232 | EAASILQELQVETYGSMEK | 161-179 | 16 | P49720 | MSIMSYNGGAVMAMKGK | 1-17 | 1 | 13.007359 | No |
| 4639 | taxid_9606/bs3 | O00232 | EAASILQELQVETYGSMEK | 161-179 | 16 | P49720 | MSIMSYNGGAVMAMKGK | 1-17 | 1 | 8.94694 | No |
| 4640 | taxid_9606/bs3 | O00232 | EAASILQELQVETYGSMEK | 161-179 | 16 | P49720 | MSIMSYNGGAVMAMKGK | 1-17 | 1 | 7.052078 | No |

### O00232 — P51665

**Dataset:** Complex Portal test. **ipTM:** 0.59. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/o00232__p51665__76c838a9/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00232__p51665__76c838a9/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00232__p51665__76c838a9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14907 | taxid_9606/dsso | O00232 | TTHLIAKEEMIHNLQ | 442-456 | 7 | P51665 | PELAVQKVVVHPLVLLSVVDHFNR | 2-25 | 7 | 9.465406 | No |
| 14917 | taxid_9606/dsso | O00232 | TTHLIAKEEMIHNLQ | 442-456 | 7 | P51665 | PELAVQKVVVHPLVLLSVVDHFNR | 2-25 | 7 | 21.393354000000002 | No |
| 15004 | taxid_9606/dsso | O00232 | TTHLIAKEEMIHNLQ | 442-456 | 7 | P51665 | PELAVQKVVVHPLVLLSVVDHFNR | 2-25 | 7 | 3.9940490000000004 | No |

### O00232 — Q9UNM6

**Dataset:** Complex Portal test. **ipTM:** 0.69. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/o00232__q9unm6__30e0ce10/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00232__q9unm6__30e0ce10/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00232__q9unm6__30e0ce10/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14870 | taxid_9606/dsso | O00232 | IMAKYYTR | 365-372 | 4 | Q9UNM6 | ALSVGLVKGSIDEVDK | 314-329 | 8 | 15.462758999999998 | No |

### O00487 — P51665

**Dataset:** Complex Portal test. **ipTM:** 0.67. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/o00487__p51665__e31ea424/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00487__p51665__e31ea424/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00487__p51665__e31ea424/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14910 | taxid_9606/dsso | O00487 | KSWMEGLTLQDYSEHCK | 223-239 | 1 | P51665 | DIKDTTVGTLSQR | 178-190 | 3 | 12.402380999999998 | No |
| 15025 | taxid_9606/dsso | O00487 | KSWMEGLTLQDYSEHCK | 223-239 | 1 | P51665 | DIKDTTVGTLSQR | 178-190 | 3 | 11.512367999999999 | No |
| 15034 | taxid_9606/dsso | O00487 | KSWMEGLTLQDYSEHCK | 223-239 | 1 | P51665 | DIKDTTVGTLSQR | 178-190 | 3 | 5.277082 | No |

### O00487 — Q99460

**Dataset:** Complex Portal test. **ipTM:** 0.65. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/o00487__q99460__3ada5afd/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00487__q99460__3ada5afd/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00487__q99460__3ada5afd/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14854 | taxid_9606/dsso | O00487 | NELEQKMLLNLHK | 210-222 | 6 | Q99460 | DKDPILR | 573-579 | 2 | 5.5163720000000005 | Yes |
| 14911 | taxid_9606/dsso | O00487 | NELEQKMLLNLHK | 210-222 | 6 | Q99460 | DKDPILR | 573-579 | 2 | 11.221952000000002 | Yes |

### O00487 — Q9UNM6

**Dataset:** Complex Portal test. **ipTM:** 0.24. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/o00487__q9unm6__7f464e9b/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o00487__q9unm6__7f464e9b/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o00487__q9unm6__7f464e9b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14921 | taxid_9606/dsso | O00487 | AVAVVVDPIQSVKGK | 140-154 | 13 | Q9UNM6 | ALSVGLVKGSIDEVDK | 314-329 | 8 | 18.971663 | No |

### O14818 — P25789

**Dataset:** Complex Portal test. **ipTM:** 0.78. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/o14818__p25789__e268fab8/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o14818__p25789__e268fab8/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o14818__p25789__e268fab8/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14850 | taxid_9606/dsso | O14818 | ALLEVVQSGGKNIELAVMR | 194-212 | 11 | P25789 | ATCIGNNSAAAVSMLKQDYK | 161-180 | 16 | 19.934897 | No |
| 15031 | taxid_9606/dsso | O14818 | ALLEVVQSGGKNIELAVMR | 194-212 | 11 | P25789 | ATCIGNNSAAAVSMLKQDYK | 161-180 | 16 | 20.599500000000003 | No |

### O14818 — P28066

**Dataset:** Complex Portal test. **ipTM:** 0.87. **Supporting spectrum matches:** 4.

[AF3 model](../store/PXD064931/af3_predictions/o14818__p28066__61405dde/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o14818__p28066__61405dde/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o14818__p28066__61405dde/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14766 | taxid_9606/dsso | O14818 | LYQTDPSGTYHAWKANAIGR | 144-163 | 14 | P28066 | LNATNIELATVQPGQNFHMFTKEELEEVIK | 152-181 | 22 | 18.408295 | No |
| 14841 | taxid_9606/dsso | O14818 | LYQTDPSGTYHAWKANAIGR | 144-163 | 14 | P28066 | LNATNIELATVQPGQNFHMFTKEELEEVIK | 152-181 | 22 | 4.508033 | No |
| 14945 | taxid_9606/dsso | O14818 | LYQTDPSGTYHAWKANAIGR | 144-163 | 14 | P28066 | LNATNIELATVQPGQNFHMFTKEELEEVIK | 152-181 | 22 | 17.117436 | No |
| 14979 | taxid_9606/dsso | O14818 | LYQTDPSGTYHAWKANAIGR | 144-163 | 14 | P28066 | LNATNIELATVQPGQNFHMFTKEELEEVIK | 152-181 | 22 | 5.832771 | No |

### O14818 — P35998

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/o14818__p35998__a294d1dd/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o14818__p35998__a294d1dd/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o14818__p35998__a294d1dd/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14825 | taxid_9606/dsso | O14818 | AITVFSPDGHLFQVEYAQEAVKK | 6-28 | 22 | P35998 | VIKSYAK | 416-422 | 3 | 8.974177000000001 | Yes |
| 14989 | taxid_9606/dsso | O14818 | AITVFSPDGHLFQVEYAQEAVKK | 6-28 | 22 | P35998 | VIKSYAK | 416-422 | 3 | 20.174151000000002 | Yes |
| 15007 | taxid_9606/dsso | O14818 | EFLEKNYTDEAIETDDLTIK | 170-189 | 5 | P35998 | IATEKDFLEAVNK | 403-415 | 5 | 20.270824 | Yes |

### O14818 — P49721

**Dataset:** Complex Portal test. **ipTM:** 0.51. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/o14818__p49721__e2448349/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o14818__p49721__e2448349/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o14818__p49721__e2448349/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14968 | taxid_9606/dsso | O14818 | DQSLKILNPEEIEK | 214-227 | 5 | P49721 | NVQLYKMR | 63-70 | 6 | 15.003626 | No |

### O43242 — P25789

**Dataset:** Complex Portal test. **ipTM:** 0.10. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/o43242__p25789__bf59644e/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o43242__p25789__bf59644e/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o43242__p25789__bf59644e/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4628 | taxid_9606/bs3 | O43242 | HNVIKTGVR | 400-408 | 5 | P25789 | LNEDMACSVAGITSDANVLTNELR | 68-91 | 8 | 10.965416000000001 | No |
| 4642 | taxid_9606/bs3 | O43242 | HNVIKTGVR | 400-408 | 5 | P25789 | LNEDMACSVAGITSDANVLTNELR | 68-91 | 8 | 9.896757000000001 | No |

### O43242 — P43686

**Dataset:** Complex Portal test. **ipTM:** 0.12. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/o43242__p43686__de28d532/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o43242__p43686__de28d532/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o43242__p43686__de28d532/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14774 | taxid_9606/dsso | O43242 | AVSGKEPR | 85-92 | 5 | P43686 | KLQQELEFLEVQEEYIK | 46-62 | 1 | 16.145625 | No |

### O43242 — P48556

**Dataset:** Complex Portal test. **ipTM:** 0.59. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/o43242__p48556__4c10739b/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/o43242__p48556__4c10739b/pair.json) · [Confidence](../store/PXD064931/af3_predictions/o43242__p48556__4c10739b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14955 | taxid_9606/dsso | O43242 | DGVIEASINHEKGYVQSK | 444-461 | 12 | P48556 | AYEKILFTEATR | 278-289 | 4 | 14.076194000000001 | No |
| 15033 | taxid_9606/dsso | O43242 | DGVIEASINHEKGYVQSK | 444-461 | 12 | P48556 | AYEKILFTEATR | 278-289 | 4 | 10.951865999999999 | No |

### P17980 — P35998

**Dataset:** Complex Portal test. **ipTM:** 0.33. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p17980__p35998__c428d08a/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p17980__p35998__c428d08a/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p17980__p35998__c428d08a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14949 | taxid_9606/dsso | P17980 | LKPGDLVGVNKDSYLILETLPTEYDSR | 145-171 | 2 | P35998 | YIINVKQFAK | 111-120 | 6 | 16.424902 | No |
| 14990 | taxid_9606/dsso | P17980 | LKPGDLVGVNKDSYLILETLPTEYDSR | 145-171 | 2 | P35998 | YIINVKQFAK | 111-120 | 6 | 9.63794 | No |

### P17980 — P62333

**Dataset:** Complex Portal test. **ipTM:** 0.54. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/p17980__p62333__0afbc70a/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p17980__p62333__0afbc70a/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p17980__p62333__0afbc70a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14958 | taxid_9606/dsso | P17980 | ENSEKIK | 75-81 | 5 | P62333 | SENDLKALQSVGQIVGEVLK | 43-62 | 6 | 14.284664 | No |

### P20618 — P28074

**Dataset:** Complex Portal test. **ipTM:** 0.70. **Supporting spectrum matches:** 6.

[AF3 model](../store/PXD064931/af3_predictions/p20618__p28074__8338a24d/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p20618__p28074__8338a24d/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p20618__p28074__8338a24d/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14813 | taxid_9606/dsso | P20618 | AGGSASAMLQPLLDNQVGFKNMQNVEHVPLSLDR | 165-198 | 20 | P28074 | ATAGAYIASQTVKK | 79-92 | 13 | 5.2624569999999995 | Yes |
| 14835 | taxid_9606/dsso | P20618 | AGGSASAMLQPLLDNQVGFKNMQNVEHVPLSLDR | 165-198 | 20 | P28074 | ATAGAYIASQTVKK | 79-92 | 13 | 11.416895 | Yes |
| 14871 | taxid_9606/dsso | P20618 | AGGSASAMLQPLLDNQVGFKNMQNVEHVPLSLDR | 165-198 | 20 | P28074 | ATAGAYIASQTVKK | 79-92 | 13 | 5.102065 | Yes |
| 14897 | taxid_9606/dsso | P20618 | AGGSASAMLQPLLDNQVGFKNMQNVEHVPLSLDR | 165-198 | 20 | P28074 | ATAGAYIASQTVKK | 79-92 | 13 | 17.876835 | Yes |
| 14914 | taxid_9606/dsso | P20618 | AGGSASAMLQPLLDNQVGFKNMQNVEHVPLSLDR | 165-198 | 20 | P28074 | ATAGAYIASQTVKK | 79-92 | 13 | 26.092913 | Yes |
| 14998 | taxid_9606/dsso | P20618 | AGGSASAMLQPLLDNQVGFKNMQNVEHVPLSLDR | 165-198 | 20 | P28074 | ATAGAYIASQTVKK | 79-92 | 13 | 19.849475 | Yes |

### P20618 — Q99436

**Dataset:** Complex Portal test. **ipTM:** 0.78. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p20618__q99436__1ab732bd/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p20618__q99436__1ab732bd/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p20618__q99436__1ab732bd/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14951 | taxid_9606/dsso | P20618 | LVKDVFISAAER | 202-213 | 3 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 20.858498 | No |
| 15019 | taxid_9606/dsso | P20618 | LVKDVFISAAER | 202-213 | 3 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 6.228155 | No |

### P25786 — P28066

**Dataset:** Complex Portal test. **ipTM:** 0.76. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p25786__p28066__d49450f2/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p25786__p28066__d49450f2/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p25786__p28066__d49450f2/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14934 | taxid_9606/dsso | P25786 | ETLPAEQDLTTKNVSIGIVGK | 203-223 | 12 | P28066 | AIGSASEGAQSSLQEVYHKSMTLK | 111-134 | 19 | 8.904019 | No |
| 14962 | taxid_9606/dsso | P25786 | ETLPAEQDLTTKNVSIGIVGK | 203-223 | 12 | P28066 | AIGSASEGAQSSLQEVYHKSMTLK | 111-134 | 19 | 8.526506000000001 | No |

### P25787 — P28074

**Dataset:** Complex Portal test. **ipTM:** 0.47. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p25787__p28074__bafe875b/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p25787__p28074__bafe875b/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p25787__p28074__bafe875b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4634 | taxid_9606/bs3 | P25787 | LAQQYYLVYQEPIPTAQLVQR | 93-113 | 5 | P28074 | MAGGAADCSFWERLLAR | 1-17 | 1 | 10.878761 | No |
| 4636 | taxid_9606/bs3 | P25787 | LAQQYYLVYQEPIPTAQLVQR | 93-113 | 5 | P28074 | MAGGAADCSFWERLLAR | 1-17 | 1 | 8.713866 | No |

### P25787 — P60900

**Dataset:** Complex Portal test. **ipTM:** 0.83. **Supporting spectrum matches:** 4.

[AF3 model](../store/PXD064931/af3_predictions/p25787__p60900__8cf8797e/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p25787__p60900__8cf8797e/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p25787__p60900__8cf8797e/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14771 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 21.701529 | Yes |
| 14775 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 15.115100000000002 | Yes |
| 14831 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 37.485549 | Yes |
| 14920 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 14.736939 | Yes |

### P25787 — Q16186

**Dataset:** Complex Portal test. **ipTM:** 0.20. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/p25787__q16186__ca375e8e/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p25787__q16186__ca375e8e/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p25787__q16186__ca375e8e/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14776 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | Q16186 | AMQNNAKPEQKEGDTK | 380-395 | 11 | 8.756197 | No |
| 14867 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | Q16186 | AMQNNAKPEQKEGDTK | 380-395 | 11 | 4.401906 | No |
| 15017 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | Q16186 | AMQNNAKPEQKEGDTK | 380-395 | 11 | 7.4096340000000005 | No |

### P25788 — P60900

**Dataset:** Complex Portal test. **ipTM:** 0.83. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p25788__p60900__5742c277/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p25788__p60900__5742c277/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p25788__p60900__5742c277/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14905 | taxid_9606/dsso | P25788 | LQMKEMTCR | 173-181 | 4 | P60900 | VPDKLLDSSTVTHLFK | 56-71 | 4 | 15.684335 | Yes |
| 14935 | taxid_9606/dsso | P25788 | LQMKEMTCR | 173-181 | 4 | P60900 | VPDKLLDSSTVTHLFK | 56-71 | 4 | 5.305349 | Yes |

### P28066 — P35998

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/p28066__p35998__0e844ec0/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p28066__p35998__0e844ec0/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p28066__p35998__0e844ec0/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14777 | taxid_9606/dsso | P28066 | QVMEEKLNATNIELATVQPGQNFHMFTK | 146-173 | 6 | P35998 | IATEKDFLEAVNK | 403-415 | 5 | 3.694599 | Yes |
| 14793 | taxid_9606/dsso | P28066 | QVMEEKLNATNIELATVQPGQNFHMFTK | 146-173 | 6 | P35998 | IATEKDFLEAVNK | 403-415 | 5 | 23.874437 | Yes |
| 14924 | taxid_9606/dsso | P28066 | QVMEEKLNATNIELATVQPGQNFHMFTK | 146-173 | 6 | P35998 | IATEKDFLEAVNK | 403-415 | 5 | 4.411312000000001 | Yes |

### P28070 — Q99436

**Dataset:** Complex Portal test. **ipTM:** 0.72. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/p28070__q99436__438c9aab/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p28070__q99436__438c9aab/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p28070__q99436__438c9aab/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14847 | taxid_9606/dsso | P28070 | EVLEKQPVLSQTEAR | 197-211 | 5 | Q99436 | LPYVTMGSGSLAAMAVFEDKFRPDMEEEEAK | 165-195 | 20 | 14.792432999999999 | No |
| 14851 | taxid_9606/dsso | P28070 | EVLEKQPVLSQTEAR | 197-211 | 5 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 17.868625 | No |
| 14868 | taxid_9606/dsso | P28070 | EVLEKQPVLSQTEAR | 197-211 | 5 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 8.065787 | No |

### P35998 — P43686

**Dataset:** Complex Portal test. **ipTM:** 0.34. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/p35998__p43686__3fe14271/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p35998__p43686__3fe14271/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p35998__p43686__3fe14271/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14836 | taxid_9606/dsso | P35998 | YIINVKQFAK | 111-120 | 6 | P43686 | VVGSEFVQKYLGEGPR | 230-245 | 9 | 20.895177 | No |

### P35998 — P62191

**Dataset:** Complex Portal test. **ipTM:** 0.45. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064931/af3_predictions/p35998__p62191__0a75d862/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p35998__p62191__0a75d862/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p35998__p62191__0a75d862/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14853 | taxid_9606/dsso | P35998 | KINELTGIK | 58-66 | 1 | P62191 | IKDYLLMEEEFIR | 68-80 | 2 | 16.796542 | No |
| 14922 | taxid_9606/dsso | P35998 | KINELTGIK | 58-66 | 1 | P62191 | IKDYLLMEEEFIR | 68-80 | 2 | 7.457042 | No |
| 15037 | taxid_9606/dsso | P35998 | INELTGIKESDTGLAPPALWDLAADK | 59-84 | 8 | P62191 | GPDAASKLPLVTPHTQCR | 42-59 | 7 | 14.344363999999999 | No |

### P35998 — Q13200

**Dataset:** Complex Portal test. **ipTM:** 0.41. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/p35998__q13200__253e6843/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p35998__q13200__253e6843/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p35998__q13200__253e6843/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14895 | taxid_9606/dsso | P35998 | KIATEK | 402-407 | 1 | Q13200 | VGQAVDVVGQAGKPK | 846-860 | 13 | 13.172941999999999 | Yes |

### P43686 — P62333

**Dataset:** Complex Portal test. **ipTM:** 0.35. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064931/af3_predictions/p43686__p62333__585fb8f1/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p43686__p62333__585fb8f1/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p43686__p62333__585fb8f1/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14786 | taxid_9606/dsso | P43686 | VVGSEFVQKYLGEGPR | 230-245 | 9 | P62333 | VVSSSIVDKYIGESAR | 198-213 | 9 | 12.742002 | No |

### P51665 — Q9UNM6

**Dataset:** Complex Portal test. **ipTM:** 0.57. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p51665__q9unm6__e223a321/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p51665__q9unm6__e223a321/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p51665__q9unm6__e223a321/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14845 | taxid_9606/dsso | P51665 | VVGVLLGSWQKK | 35-46 | 11 | Q9UNM6 | YYQTIGNHASYYKDALR | 162-178 | 13 | 14.330223 | No |
| 14994 | taxid_9606/dsso | P51665 | VVGVLLGSWQKK | 35-46 | 11 | Q9UNM6 | YYQTIGNHASYYKDALR | 162-178 | 13 | 4.956185 | No |

### P62191 — P62195

**Dataset:** Complex Portal test. **ipTM:** 0.28. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p62191__p62195__18735fec/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p62191__p62195__18735fec/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p62191__p62195__18735fec/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14802 | taxid_9606/dsso | P62191 | VEKAPQETYADIGGLDNQIQEIK | 176-198 | 3 | P62195 | TMLELLNQLDGFEATKNIK | 264-282 | 16 | 6.255085 | No |
| 14902 | taxid_9606/dsso | P62191 | VEKAPQETYADIGGLDNQIQEIK | 176-198 | 3 | P62195 | TMLELLNQLDGFEATKNIK | 264-282 | 16 | 17.18162 | No |

### P62195 — Q99436

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064931/af3_predictions/p62195__q99436__6d934e66/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/p62195__q99436__6d934e66/pair.json) · [Confidence](../store/PXD064931/af3_predictions/p62195__q99436__6d934e66/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4630 | taxid_9606/bs3 | P62195 | VSGSELVQKFIGEGAR | 206-221 | 9 | Q99436 | TGTTIAGVVYK | 42-52 | 10 | 9.354892 | Yes |
| 4644 | taxid_9606/bs3 | P62195 | VSGSELVQKFIGEGAR | 206-221 | 9 | Q99436 | TGTTIAGVVYK | 42-52 | 10 | 11.206787 | Yes |

### Q13200 — Q99460

**Dataset:** Complex Portal test. **ipTM:** 0.17. **Supporting spectrum matches:** 5.

[AF3 model](../store/PXD064931/af3_predictions/q13200__q99460__beb35c08/model.cif) · [Pair provenance](../store/PXD064931/af3_predictions/q13200__q99460__beb35c08/pair.json) · [Confidence](../store/PXD064931/af3_predictions/q13200__q99460__beb35c08/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14863 | taxid_9606/dsso | Q13200 | DKEQELSEEDK | 40-50 | 2 | Q99460 | TILESNDVPGMLAYSLKLCMSLMQNK | 166-191 | 17 | 7.120331 | Yes |
| 14883 | taxid_9606/dsso | Q13200 | DKEQELSEEDK | 40-50 | 2 | Q99460 | TILESNDVPGMLAYSLKLCMSLMQNK | 166-191 | 17 | 4.581644 | Yes |
| 14927 | taxid_9606/dsso | Q13200 | DKEQELSEEDK | 40-50 | 2 | Q99460 | TILESNDVPGMLAYSLKLCMSLMQNK | 166-191 | 17 | 6.8114040000000005 | Yes |
| 14957 | taxid_9606/dsso | Q13200 | DKEQELSEEDK | 40-50 | 2 | Q99460 | TILESNDVPGMLAYSLKLCMSLMQNK | 166-191 | 17 | 5.344749 | Yes |
| 15029 | taxid_9606/dsso | Q13200 | DKEQELSEEDK | 40-50 | 2 | Q99460 | TILESNDVPGMLAYSLKLCMSLMQNK | 166-191 | 17 | 6.1085840000000005 | Yes |

## PXD064932

### O00231 — O00232

**Dataset:** Complex Portal test. **ipTM:** 0.54. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/o00231__o00232__b2ac8326/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00231__o00232__b2ac8326/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00231__o00232__b2ac8326/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9111 | taxid_9606/dsso | O00231 | CVAQASKNR | 289-297 | 7 | O00232 | TQIISKK | 202-208 | 6 | 15.825968 | No |

### O00231 — O00487

**Dataset:** Complex Portal test. **ipTM:** 0.33. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/o00231__o00487__6398c096/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00231__o00487__6398c096/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00231__o00487__6398c096/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9078 | taxid_9606/dsso | O00231 | TYEAALETIQNMSKVVDSLYNK | 396-417 | 14 | O00487 | NYNKAVEEEDK | 254-264 | 4 | 14.126736 | No |

### O00231 — P49721

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/o00231__p49721__9e548877/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00231__p49721__9e548877/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00231__p49721__9e548877/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9086 | taxid_9606/dsso | O00231 | YMLLCKIMLNTPEDVQALVSGK | 253-274 | 6 | P49721 | IIDKNGIHDLDNISFPK | 182-198 | 4 | 15.410783 | No |

### O00231 — Q15008

**Dataset:** Complex Portal test. **ipTM:** 0.75. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o00231__q15008__614a9ae9/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00231__q15008__614a9ae9/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00231__q15008__614a9ae9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8945 | taxid_9606/dsso | O00231 | LQATLDMQSGIIHAAEEKDWK | 206-226 | 18 | Q15008 | VIKGAEILEVLHSLPAVR | 240-257 | 3 | 14.855575 | No |
| 9020 | taxid_9606/dsso | O00231 | LQATLDMQSGIIHAAEEKDWK | 206-226 | 18 | Q15008 | VIKGAEILEVLHSLPAVR | 240-257 | 3 | 10.489506 | No |

### O00232 — O00487

**Dataset:** Complex Portal test. **ipTM:** 0.43. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064932/af3_predictions/o00232__o00487__a214c660/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00232__o00487__a214c660/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00232__o00487__a214c660/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9041 | taxid_9606/dsso | O00232 | IMAKYYTR | 365-372 | 4 | O00487 | AVAVVVDPIQSVKGK | 140-154 | 13 | 6.0259789999999995 | No |
| 9138 | taxid_9606/dsso | O00232 | IMAKYYTR | 365-372 | 4 | O00487 | AVAVVVDPIQSVKGK | 140-154 | 13 | 8.236881 | No |
| 9155 | taxid_9606/dsso | O00232 | IMAKYYTR | 365-372 | 4 | O00487 | AVAVVVDPIQSVKGK | 140-154 | 13 | 10.132374 | No |

### O00232 — P43686

**Dataset:** Complex Portal test. **ipTM:** 0.12. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o00232__p43686__03f7e554/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00232__p43686__03f7e554/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00232__p43686__03f7e554/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9024 | taxid_9606/dsso | O00232 | SQLKQAVAK | 95-103 | 4 | P43686 | YIVLAKDFEK | 392-401 | 6 | 12.424538 | No |
| 9060 | taxid_9606/dsso | O00232 | SQLKQAVAK | 95-103 | 4 | P43686 | YIVLAKDFEK | 392-401 | 6 | 11.682277 | No |

### O00232 — P51665

**Dataset:** Complex Portal test. **ipTM:** 0.59. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o00232__p51665__76c838a9/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00232__p51665__76c838a9/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00232__p51665__76c838a9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8975 | taxid_9606/dsso | O00232 | TTHLIAKEEMIHNLQ | 442-456 | 7 | P51665 | PELAVQKVVVHPLVLLSVVDHFNR | 2-25 | 7 | 6.792526 | No |
| 9132 | taxid_9606/dsso | O00232 | TTHLIAKEEMIHNLQ | 442-456 | 7 | P51665 | PELAVQKVVVHPLVLLSVVDHFNR | 2-25 | 7 | 13.763821 | No |

### O00232 — Q9UNM6

**Dataset:** Complex Portal test. **ipTM:** 0.69. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o00232__q9unm6__30e0ce10/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00232__q9unm6__30e0ce10/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00232__q9unm6__30e0ce10/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9135 | taxid_9606/dsso | O00232 | ISGDKK | 290-295 | 5 | Q9UNM6 | GSIDEVDKR | 322-330 | 8 | 12.351814 | No |
| 9168 | taxid_9606/dsso | O00232 | ISGDKK | 290-295 | 5 | Q9UNM6 | GSIDEVDKR | 322-330 | 8 | 9.352715 | No |

### O00487 — P62195

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064932/af3_predictions/o00487__p62195__aa2d4dfa/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00487__p62195__aa2d4dfa/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00487__p62195__aa2d4dfa/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8962 | taxid_9606/dsso | O00487 | NVGKQDPK | 274-281 | 4 | P62195 | NELNAKVR | 42-49 | 6 | 8.877465 | No |
| 9030 | taxid_9606/dsso | O00487 | NVGKQDPK | 274-281 | 4 | P62195 | NELNAKVR | 42-49 | 6 | 9.788796 | No |
| 9117 | taxid_9606/dsso | O00487 | QTTSNLGHLNKPSIQALIHGLNR | 176-198 | 11 | P62195 | FVVDVDKNIDINDVTPNCR | 87-105 | 7 | 12.782323 | No |

### O00487 — Q15008

**Dataset:** Complex Portal test. **ipTM:** 0.12. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o00487__q15008__aa3b0d0a/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o00487__q15008__aa3b0d0a/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o00487__q15008__aa3b0d0a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9001 | taxid_9606/dsso | O00487 | AVEEEDKMTPEQLAIK | 258-273 | 7 | Q15008 | NTEKAK | 160-165 | 4 | 11.137554999999999 | No |
| 9014 | taxid_9606/dsso | O00487 | AVEEEDKMTPEQLAIK | 258-273 | 7 | Q15008 | NTEKAK | 160-165 | 4 | 7.369212999999999 | No |

### O14818 — P25789

**Dataset:** Complex Portal test. **ipTM:** 0.78. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064932/af3_predictions/o14818__p25789__e268fab8/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o14818__p25789__e268fab8/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o14818__p25789__e268fab8/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8981 | taxid_9606/dsso | O14818 | SVAKLQDER | 49-57 | 4 | P25789 | ATCIGNNSAAAVSMLKQDYK | 161-180 | 16 | 17.104362000000002 | No |
| 9019 | taxid_9606/dsso | O14818 | SVAKLQDER | 49-57 | 4 | P25789 | QDYKEGEMTLK | 177-187 | 4 | 6.33336 | No |
| 9119 | taxid_9606/dsso | O14818 | SVAKLQDER | 49-57 | 4 | P25789 | QDYKEGEMTLK | 177-187 | 4 | 11.747602 | No |

### O14818 — P35998

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o14818__p35998__a294d1dd/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o14818__p35998__a294d1dd/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o14818__p35998__a294d1dd/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9027 | taxid_9606/dsso | O14818 | AITVFSPDGHLFQVEYAQEAVKK | 6-28 | 22 | P35998 | VIKSYAK | 416-422 | 3 | 15.916106 | Yes |
| 9087 | taxid_9606/dsso | O14818 | AITVFSPDGHLFQVEYAQEAVKK | 6-28 | 22 | P35998 | VIKSYAK | 416-422 | 3 | 8.184108 | Yes |

### O43242 — P43686

**Dataset:** Complex Portal test. **ipTM:** 0.12. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/o43242__p43686__de28d532/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o43242__p43686__de28d532/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o43242__p43686__de28d532/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9173 | taxid_9606/dsso | O43242 | AVSGKEPR | 85-92 | 5 | P43686 | KLQQELEFLEVQEEYIK | 46-62 | 1 | 14.472888 | No |

### O43242 — P48556

**Dataset:** Complex Portal test. **ipTM:** 0.59. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/o43242__p48556__4c10739b/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/o43242__p48556__4c10739b/pair.json) · [Confidence](../store/PXD064932/af3_predictions/o43242__p48556__4c10739b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9000 | taxid_9606/dsso | O43242 | DGVIEASINHEKGYVQSK | 444-461 | 12 | P48556 | AYEKILFTEATR | 278-289 | 4 | 26.780956 | No |
| 9047 | taxid_9606/dsso | O43242 | DGVIEASINHEKGYVQSK | 444-461 | 12 | P48556 | AYEKILFTEATR | 278-289 | 4 | 18.745084000000002 | No |

### P17980 — P35998

**Dataset:** Complex Portal test. **ipTM:** 0.33. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p17980__p35998__c428d08a/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p17980__p35998__c428d08a/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p17980__p35998__c428d08a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9098 | taxid_9606/dsso | P17980 | VKAMEVDERPTEQYSDIGGLDK | 172-193 | 2 | P35998 | CTKIINADSEDPK | 98-110 | 3 | 13.135307 | No |
| 9181 | taxid_9606/dsso | P17980 | VKAMEVDERPTEQYSDIGGLDK | 172-193 | 2 | P35998 | CTKIINADSEDPK | 98-110 | 3 | 7.062641999999999 | No |

### P17980 — P43686

**Dataset:** Complex Portal test. **ipTM:** 0.30. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/p17980__p43686__3b6ccf51/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p17980__p43686__3b6ccf51/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p17980__p43686__3b6ccf51/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9125 | taxid_9606/dsso | P17980 | CAVIKTSTR | 121-129 | 5 | P43686 | VVGSEFVQKYLGEGPR | 230-245 | 9 | 16.943261 | No |

### P17980 — P62195

**Dataset:** Complex Portal test. **ipTM:** 0.31. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/p17980__p62195__23a23eca/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p17980__p62195__23a23eca/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p17980__p62195__23a23eca/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9179 | taxid_9606/dsso | P17980 | CAVIKTSTR | 121-129 | 5 | P62195 | VSGSELVQKFIGEGAR | 206-221 | 9 | 14.749357 | No |

### P17980 — P62333

**Dataset:** Complex Portal test. **ipTM:** 0.54. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p17980__p62333__0afbc70a/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p17980__p62333__0afbc70a/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p17980__p62333__0afbc70a/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8986 | taxid_9606/dsso | P17980 | QTYFLPVIGLVDAEKLKPGDLVGVNK | 130-155 | 15 | P62333 | ELTKQYEK | 35-42 | 4 | 14.295099 | No |
| 8990 | taxid_9606/dsso | P17980 | CAVIKTSTR | 121-129 | 5 | P62333 | VVSSSIVDKYIGESAR | 198-213 | 9 | 16.614703 | No |

### P20618 — Q99436

**Dataset:** Complex Portal test. **ipTM:** 0.78. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p20618__q99436__1ab732bd/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p20618__q99436__1ab732bd/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p20618__q99436__1ab732bd/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9028 | taxid_9606/dsso | P20618 | LVKDVFISAAER | 202-213 | 3 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 13.833025 | No |
| 9063 | taxid_9606/dsso | P20618 | LVKDVFISAAER | 202-213 | 3 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 18.650767000000002 | No |

### P25787 — P25789

**Dataset:** Complex Portal test. **ipTM:** 0.77. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/p25787__p25789__5c422047/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p25787__p25789__5c422047/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p25787__p25789__5c422047/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9042 | taxid_9606/dsso | P25787 | TFLEKR | 172-177 | 5 | P25789 | NIHKLLDEVFFSEK | 51-64 | 4 | 19.034202999999998 | No |

### P25787 — P60900

**Dataset:** Complex Portal test. **ipTM:** 0.83. **Supporting spectrum matches:** 3.

[AF3 model](../store/PXD064932/af3_predictions/p25787__p60900__8cf8797e/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p25787__p60900__8cf8797e/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p25787__p60900__8cf8797e/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8956 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 28.932929 | Yes |
| 9134 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 35.663346 | Yes |
| 9161 | taxid_9606/dsso | P25787 | KLAQQYYLVYQEPIPTAQLVQR | 92-113 | 1 | P60900 | YKYGYEIPVDMLCK | 103-116 | 2 | 27.689381 | Yes |

### P25789 — P62191

**Dataset:** Complex Portal test. **ipTM:** 0.50. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/p25789__p62191__74521e6c/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p25789__p62191__74521e6c/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p25789__p62191__74521e6c/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9133 | taxid_9606/dsso | P25789 | ATCIGNNSAAAVSMLKQDYK | 161-180 | 16 | P62191 | SKENVLYK | 422-429 | 2 | 17.245594 | No |

### P25789 — P62195

**Dataset:** Complex Portal test. **ipTM:** 0.49. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p25789__p62195__fe343fcb/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p25789__p62195__fe343fcb/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p25789__p62195__fe343fcb/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9091 | taxid_9606/dsso | P25789 | LSAEKVEIATLTR | 206-218 | 5 | P62195 | NMSIKK | 390-395 | 5 | 11.440639 | No |
| 9110 | taxid_9606/dsso | P25789 | LSAEKVEIATLTR | 206-218 | 5 | P62195 | NMSIKK | 390-395 | 5 | 10.248306 | No |

### P25789 — P62333

**Dataset:** Complex Portal test. **ipTM:** 0.09. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p25789__p62333__054be822/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p25789__p62333__054be822/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p25789__p62333__054be822/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9154 | taxid_9606/dsso | P25789 | SALALAIKVLNK | 188-199 | 8 | P62333 | VKMIMATNRPDTLDPALLRPGR | 273-294 | 2 | 11.083207999999999 | No |
| 9194 | taxid_9606/dsso | P25789 | SALALAIKVLNK | 188-199 | 8 | P62333 | VKMIMATNRPDTLDPALLRPGR | 273-294 | 2 | 6.578033 | No |

### P28070 — Q99436

**Dataset:** Complex Portal test. **ipTM:** 0.72. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p28070__q99436__438c9aab/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p28070__q99436__438c9aab/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p28070__q99436__438c9aab/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9105 | taxid_9606/dsso | P28070 | EVLEKQPVLSQTEAR | 197-211 | 5 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 17.206457 | No |
| 9148 | taxid_9606/dsso | P28070 | EVLEKQPVLSQTEAR | 197-211 | 5 | Q99436 | LDFLRPYTVPNKK | 226-238 | 12 | 10.721417 | No |

### P35998 — P62191

**Dataset:** Complex Portal test. **ipTM:** 0.45. **Supporting spectrum matches:** 5.

[AF3 model](../store/PXD064932/af3_predictions/p35998__p62191__0a75d862/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p35998__p62191__0a75d862/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p35998__p62191__0a75d862/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8996 | taxid_9606/dsso | P35998 | SYAKFSATPR | 419-428 | 4 | P62191 | VAEEHAPSIVFIDEIDAIGTKR | 273-294 | 21 | 18.490338 | Yes |
| 8997 | taxid_9606/dsso | P35998 | VIKSYAK | 416-422 | 3 | P62191 | VAEEHAPSIVFIDEIDAIGTKR | 273-294 | 21 | 15.647025 | Yes |
| 9034 | taxid_9606/dsso | P35998 | SYAKFSATPR | 419-428 | 4 | P62191 | VAEEHAPSIVFIDEIDAIGTKR | 273-294 | 21 | 11.348127 | Yes |
| 9040 | taxid_9606/dsso | P35998 | VIKSYAK | 416-422 | 3 | P62191 | VAEEHAPSIVFIDEIDAIGTKR | 273-294 | 21 | 13.743329 | Yes |
| 9064 | taxid_9606/dsso | P35998 | SYAKFSATPR | 419-428 | 4 | P62191 | KIEFPLPDEK | 350-359 | 1 | 20.987101 | Yes |

### P35998 — P62333

**Dataset:** Complex Portal test. **ipTM:** 0.45. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/p35998__p62333__cecf177b/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p35998__p62333__cecf177b/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p35998__p62333__cecf177b/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | taxid_9606/dsso | P35998 | YIINVKQFAK | 111-120 | 6 | P62333 | VVSSSIVDKYIGESAR | 198-213 | 9 | 23.109127 | No |

### P43686 — P62195

**Dataset:** Complex Portal test. **ipTM:** 0.44. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p43686__p62195__941c9ed9/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p43686__p62195__941c9ed9/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p43686__p62195__941c9ed9/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8977 | taxid_9606/dsso | P43686 | EAVELPLTHFELYKQIGIDPPR | 179-200 | 14 | P62195 | KMNLTR | 327-332 | 1 | 12.41825 | No |
| 9072 | taxid_9606/dsso | P43686 | EAVELPLTHFELYKQIGIDPPR | 179-200 | 14 | P62195 | KMNLTR | 327-332 | 1 | 14.408291 | No |

### P62195 — P62333

**Dataset:** Complex Portal test. **ipTM:** 0.35. **Supporting spectrum matches:** 1.

[AF3 model](../store/PXD064932/af3_predictions/p62195__p62333__c60b2800/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p62195__p62333__c60b2800/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p62195__p62333__c60b2800/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9005 | taxid_9606/dsso | P62195 | VSGSELVQKFIGEGAR | 206-221 | 9 | P62333 | FIVKATNGPR | 69-78 | 4 | 23.338971 | No |

### P62195 — Q99460

**Dataset:** Complex Portal test. **ipTM:** 0.60. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/p62195__q99460__1f3222ba/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/p62195__q99460__1f3222ba/pair.json) · [Confidence](../store/PXD064932/af3_predictions/p62195__q99460__1f3222ba/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8979 | taxid_9606/dsso | P62195 | FVVDVDKNIDINDVTPNCR | 87-105 | 7 | Q99460 | VINDKHDDVMAK | 716-727 | 5 | 15.308544 | Yes |
| 9197 | taxid_9606/dsso | P62195 | FVVDVDKNIDINDVTPNCR | 87-105 | 7 | Q99460 | VINDKHDDVMAK | 716-727 | 5 | 19.382842 | Yes |

### Q13200 — Q15008

**Dataset:** Complex Portal test. **ipTM:** 0.15. **Supporting spectrum matches:** 2.

[AF3 model](../store/PXD064932/af3_predictions/q13200__q15008__c948a612/model.cif) · [Pair provenance](../store/PXD064932/af3_predictions/q13200__q15008__c948a612/pair.json) · [Confidence](../store/PXD064932/af3_predictions/q13200__q15008__c948a612/summary_confidences.json)

| scan_id | Search group | Protein A accession | Peptide A | Protein A range(s) | Link A | Protein B accession | Peptide B | Protein B range(s) | Link B | xi score | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8950 | taxid_9606/dsso | Q13200 | APVQPQQSPAAAPGGTDEKPSGK | 9-31 | 19 | Q15008 | NTEKAK | 160-165 | 4 | 6.115376 | No |
| 8955 | taxid_9606/dsso | Q13200 | APVQPQQSPAAAPGGTDEKPSGK | 9-31 | 19 | Q15008 | NTEKAK | 160-165 | 4 | 12.233068 | No |

