# Intelligent metadata compilation to enhance the reusability and discoverability of mass spectrometrybased proteomics data

## Project Abstract
Crosslinking  mass  spectrometry  (XL-MS)  is  a  powerful  structural  proteomics  method  that  can  provide high-resolution  structural  information  about  complex  mixtures  of  proteins  in  their  native  physiological context.[1],[2],[3]  The method works by chemically crosslinking two reactive amino acid residues that are close to  one  another  in  3-D  space,  thereby  freezing  this  spatial  information  into  a  covalent  bond,  and  then retrieving  this  information  by sequencing  crosslinked  peptides  following  enzymatic  digest  of  the constituent proteins (like Hi-C,[4] but for proteins).  Initially developed in the 2000s to interrogate purified proteins, by the late-2010s, methods became available to interrogate protein-protein interactions (PPIs) on the proteome-scale and in the cellular environment.[5]  This project seeks to standardize, combine, and integrate existing publicly available crosslinking datasets from PRIDE to make these data more re-usable and useful for integrative and hybrid modeling.  We will also create a meta-dataset to catalogue PPIs in human  and  other  model  organisms.    Because  XL-MS  encodes  information  about  both  protein  identity and  interacting  residues,  these  findings  can  be  cross-validated  to  structural  predictions  of  protein complexes  using  AlphaFold3,  thereby  providing  stronger  evidence  for  their  existence  compared  to huMAP3.0, which predicts protein complexes without structural evidence.  We will integrate these findings into the EBI Complex Portal to make it accessible to the life science community. 
  
## Contacts and Important Links

*Working Group Leadership*  
Lead: Stephen D. Fried, Johns Hopkins University, sdfried@jhu.edu   
Co-Lead: Yasset Perez-Riverol, EMBL-EBI, yperez@ebi.ac.uk  
Co-Lead: Henning Hermjakob, EMBL-EBI, hhe@ebi.ac.uk    

*NCEMS Staff*  
Staff Scientist: Ian Sitarik, Penn State University, ims86@psu.edu  
Project Coordinator: Maowei Dong, Penn State University, mod5361@psu.edu  

*Communication links*  
Zoom: https://psu.zoom.us/j/2163369137?pwd=K0l5Mmo2ZGpFSitwTVVBOUljaE1Fdz09 

[Slack Channel](https://friedlab.slack.com/archives/C09L906UPUH)  

The proposal can be located [here](documents/NCEMS_proposal_v3.pdf)

The progress documentation can be located [here]()  

## Tasks as of 12/12/2025
1. Gain access to GitHub repo with selected crosslinking projects.
2. Cross reference selected crosslinking projects with the identified crosslinking projects in the internal NCEMS proteomics database to see if I can suggest more similar projects. 
3. Once the new SDRF-XL guidelines have been finalized help annotate the select XL-MS project SDRFs 
    - Use internal NCEMS metadata extraction pipeline followed by expert curation (?)
4. Apply internal NCEMS metadata extraction pipeline to test project PXD042173. **(DONE)**  
    - These results can be found in the aggregated metadata JSON [PXD042173_aggregated_results.json](IntelligentMetadata_Extraction/results/PXD042173_aggregated_results.json).  
    - Detailed description of the results can be found [AGGREGATED_JSON_SPECIFICATION.md](IntelligentMetadata_Extraction/documents/AGGREGATED_JSON_SPECIFICATION.md).  
   
## Milestones and progress

## Proposal request for NCEMS staff scientist 
- Activity a will require 6 months of a data scientist’s FTE.  
- This researcher will work closely with Dr. Perez and  the  EBI  team.    Hence,  whilst  they  will  be  based  at  Penn  State/NCEMS,  we  expect  that  they  will  benefit greatly from spending some time at EMBL-EBI in the United Kingdom for face-to-face interaction and cross-training, so some money for travel should be budgeted ($10k).  

- To estimate the compute costs for data reanalysis, we offer the following approximation: (100 crosslinking PXDs)×(200 raw files/PXD on average)×(~1h Scout run/raw file), which is 20,000 h on a workstation that has 20 cores @ 5.0 GHz and 32 GB of memory.  
    - <span style="color: #0066CC;">Our workstations have 112 cores @ 4.8MHz and x2 NVIDIA RTX 6000 Ada. The staff scientist of the graduate student can be given remote access to use one of these stations. We also have ACCESS resources as well but I do not think we will need it. </span>

- This  activity  will  be  computationally  expensive,  as  we  estimate  there  will  be  ~10,000  AlphaFold3 calculations on pairs of proteins with average lengths of 500 residues. 
    - <span style="color: #0066CC;"> We have the inhouse skills and resources to do this and can train any trainees as well. </span>

## References

1: Graziadei, A. & Rappsilber, J. Leveraging crosslinking mass spectrometry in structural and cell biology. *Structure* **30**, 37–54 (2022).

2: Sinz, A. Cross-Linking/Mass Spectrometry for Studying Protein Structures and Protein–Protein Interactions: Where Are We Now and Where Should We Go from Here? *Angew. Chem. Int. Ed.* **57**, 6390–6396 (2018).

3: Leitner, A., Faini, M., Stengel, F. & Aebersold, R. Crosslinking and Mass Spectrometry: An Integrated Technology to Understand the Structure and Function of Molecular Machines. *Trends Biochem. Sci.* **41**, 20–32 (2016).

4: Eagen, K. P. Principles of Chromosome Architecture Revealed by Hi-C. *Trends Biochem. Sci.* **43**, 469–478 (2018).

5: Matzinger, M. & Mechtler, K. Cleavable Cross-Linkers and Mass Spectrometry for the Ultimate Task of Profiling Protein–Protein Interaction Networks in Vivo. *J. Proteome Res.* **20**, 78–93 (2021).



