export type CaseImage = {
  file: string;
  caption: string;
};

export type CasePacket = {
  clinical_summary: string;
  imaging_findings: string;
  pathology_report: string;
};

export type EvaluationTarget = {
  diagnosis: string;
  biomarkers?: string;
  expected_plan: string;
  follow_up: string;
  negative_checks: string;
};

export type TumorBoardCase = {
  id: string;
  title: string;
  source: string;
  case_packet: CasePacket;
  images: CaseImage[];
  evaluation_target: EvaluationTarget;
};

export const NSCLC_CASE: TumorBoardCase = {
  id: "nsclc_egfr_l858r_advanced",
  title: "NSCLC — EGFR L858R, Advanced",
  source: "https://pmc.ncbi.nlm.nih.gov/articles/PMC6822184/",
  case_packet: {
    clinical_summary:
      "A 63-year-old woman who has never smoked presents with 3 months of progressive dyspnea, fatigue, and unintentional 20 lb weight loss. She has no significant past medical history and no family history of cancer. Physical examination reveals wheezing over the right upper chest and a firm, nontender supraclavicular lymph node.",
    imaging_findings:
      "Chest X-ray shows a 5-cm opacity in the right upper lung field. CT chest shows a solitary spiculated 4.5-cm radiodense mass in the right upper lobe, suspicious for malignancy.",
    pathology_report: [
      "FNA and core biopsy, right upper lobe lung mass:",
      "",
      "- Non-small cell carcinoma, adenocarcinoma.",
      "- Core biopsy: infiltrative malignant cells forming glandular spaces with pleomorphic hyperchromatic nuclei.",
      "- FNA: malignant cells in small three-dimensional clusters with increased nuclear-to-cytoplasmic ratio and vacuolated cytoplasm.",
      "- IHC: TTF-1 positive (nuclear); Napsin-A positive (cytoplasmic); p40 negative.",
      "- Molecular: EGFR exon 21 L858R substitution detected.",
      "- Additional molecular markers: not reported."
    ].join("\n")
  },
  images: [],
  evaluation_target: {
    diagnosis:
      "Lung adenocarcinoma (TTF-1+, Napsin-A+, p40−) with EGFR exon 21 L858R driver mutation.",
    biomarkers:
      "EGFR L858R confirmed. PD-L1, ALK, ROS1, KRAS, MET not reported.",
    expected_plan:
      "First-line osimertinib (EGFR TKI). Complete staging with PET/CT and brain MRI. Comprehensive NGS and PD-L1 testing on biopsy tissue.",
    follow_up:
      "If unresectable Stage III confirmed: concurrent chemoradiation + consolidation osimertinib (LAURA). If Stage IV: osimertinib monotherapy first-line.",
    negative_checks:
      "Do not classify as squamous. Do not lead with immunotherapy or platinum-doublet when EGFR driver is known."
  }
};

export const BREAST_HER2_CASE: TumorBoardCase = {
  id: "breast_her2_equivocal_then_fish_positive",
  title: "Breast Cancer — HER2 Equivocal IHC, FISH Positive",
  source: "https://pmc.ncbi.nlm.nih.gov/articles/PMC8642036/",
  case_packet: {
    clinical_summary:
      "A 65-year-old woman with no relevant past medical history is found to have a new spiculated right breast mass on routine screening mammogram. Family history is significant for breast cancer in her mother and maternal grandmother, both diagnosed after age 75. No symptoms are reported.",
    imaging_findings:
      "Screening mammogram shows a spiculated right breast mass measuring approximately 1.6 cm. Clinical staging based on physical examination and imaging is cT1cN0.",
    pathology_report: [
      "Core needle biopsy, right breast mass:",
      "",
      "- Poorly differentiated invasive ductal carcinoma.",
      "- No lymphovascular invasion identified.",
      "- No in situ carcinoma identified in sampled cores.",
      "- ER: negative.",
      "- PR: negative.",
      "- HER2 IHC: 2+ equivocal; moderate complete membrane staining in greater than 10% of tumor cells.",
      "- Reflex HER2 FISH: amplified; HER2/CEP17 ratio 3.7, average HER2 copy number 9.4 signals per cell.",
      "- Final HER2 interpretation: positive.",
      "- Grade and margins: not reported."
    ].join("\n")
  },
  images: [],
  evaluation_target: {
    diagnosis:
      "Poorly differentiated invasive ductal carcinoma, ER/PR negative, HER2 positive (FISH-confirmed).",
    biomarkers:
      "Appears triple-negative by IHC alone; HER2 positive by reflex FISH — treatment category is HER2-positive, not triple-negative.",
    expected_plan:
      "HER2-positive early breast cancer; surgical management with sentinel lymph node staging; adjuvant chemotherapy with HER2-targeted therapy (trastuzumab-based); baseline cardiac assessment before anti-HER2 therapy.",
    follow_up:
      "Final surgical pathology for nodal status, margins, and definitive pathologic stage; cardiac function assessment if anti-HER2 therapy is planned.",
    negative_checks:
      "Do not stop at equivocal HER2 IHC without reflex FISH; do not treat as triple-negative; do not make endocrine therapy a primary strategy given ER/PR negativity."
  }
};

export const SCLC_NSCLC_CASE: TumorBoardCase = {
  id: "synchronous_sclc_nsclc",
  title: "Synchronous SCLC + NSCLC — Two FDG-Avid Lesions",
  source: "https://pmc.ncbi.nlm.nih.gov/articles/PMC3858864/",
  case_packet: {
    clinical_summary:
      "A 74-year-old male with a 60 pack-year smoking history presents with 3 months of unintentional weight loss, exertional dyspnea, and occasional non-productive cough.",
    imaging_findings:
      "CT chest: a 2.6-cm irregular nodular opacity along the pleural surface of the right upper lobe, slightly larger compared to imaging from 3 years prior; a separate new 4-cm right upper lobe perihilar mass. PET: both lesions demonstrate intense FDG avidity. The slow growth of the peripheral nodule over 3 years contrasts with the new and larger perihilar mass.",
    pathology_report: [
      "Specimen 1 — Endobronchial ultrasound-guided biopsy, right hilar mass:",
      "",
      "- Small cell lung carcinoma.",
      "- IHC: TTF-1 positive; CD56 positive; synaptophysin positive; chromogranin A negative; napsin A negative.",
      "",
      "Specimen 2 — CT-guided core needle biopsy, right upper lobe peripheral nodule:",
      "",
      "- Adenosquamous non-small cell lung carcinoma.",
      "- Histology distinct from Specimen 1."
    ].join("\n")
  },
  images: [
    {
      file: "images/fig2_ct_pet_dual_lesions.jpg",
      caption:
        "CT and PET imaging showing two right upper lobe lesions: a 2.6-cm peripheral pleural-based nodule (slow-growing, present 3 years prior) and a new 4-cm perihilar mass. Both are intensely FDG-avid."
    }
  ],
  evaluation_target: {
    diagnosis:
      "Synchronous primaries: limited-stage SCLC (T2a N1 M0) in the right hilum, and stage IA adenosquamous NSCLC (T1b N0 M0) in the right upper lobe periphery.",
    expected_plan:
      "Treat as two synchronous primaries: cisplatin/etoposide with concurrent thoracic radiotherapy for limited-stage SCLC; surgical resection or SBRT for the stage IA NSCLC after SCLC treatment.",
    follow_up:
      "Response assessment imaging after chemoradiotherapy; brain MRI for SCLC staging and PCI consideration; molecular profiling of NSCLC component.",
    negative_checks:
      "Do not classify as extensive-stage SCLC based on two FDG-avid lesions alone without tissue confirmation; do not treat the peripheral nodule as an SCLC metastasis given its 3-year indolent course and distinct histology."
  }
};

export const ALL_CASES: TumorBoardCase[] = [
  NSCLC_CASE,
  BREAST_HER2_CASE,
  SCLC_NSCLC_CASE
];

// kept for API route compatibility
export async function loadCase(): Promise<TumorBoardCase> {
  return NSCLC_CASE;
}

export function publicImagePath(caseId: string, image: CaseImage): string {
  return `/case-assets/${caseId}/${image.file}`;
}
