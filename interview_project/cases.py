from dataclasses import dataclass


@dataclass(frozen=True)
class PatientCase:
    case_id: str
    title: str
    clinical_summary: str
    imaging_findings: str
    pathology_report: str

    def render(self) -> str:
        return f"""
            CLINICAL SUMMARY:
            {self.clinical_summary}

            IMAGING FINDINGS:
            {self.imaging_findings}

            PATHOLOGY REPORT:
            {self.pathology_report}
        """.strip()


CASES = [
    PatientCase(
        case_id="case_1_breast",
        title="Early-stage ER-positive breast cancer",
        clinical_summary=(
            "A 54-year-old postmenopausal woman presents after screening mammography. "
            "No major comorbidities. ECOG 0. Family history negative for breast/ovarian cancer."
        ),
        imaging_findings=(
            "Diagnostic mammography and ultrasound show a 1.8 cm irregular mass in the left upper outer quadrant. "
            "No suspicious axillary lymph nodes. Breast MRI shows no multifocal disease."
        ),
        pathology_report=(
            "Lumpectomy specimen: invasive ductal carcinoma, grade 2, 1.8 cm. "
            "Margins negative, closest margin 4 mm. Sentinel lymph nodes 0/2 positive. "
            "ER 95% positive, PR 70% positive, HER2 IHC 1+ negative. Ki-67 12%. "
            "No lymphovascular invasion. Associated low-grade DCIS present, margins negative."
        ),
    ),
    PatientCase(
        case_id="case_2_lung",
        title="Lung adenocarcinoma with limited tissue and pending molecular markers",
        clinical_summary=(
            "A 67-year-old man with a 35 pack-year smoking history presents with cough and 5 kg weight loss. "
            "COPD, ECOG 1."
        ),
        imaging_findings=(
            "CT chest shows a 4.3 cm right upper lobe mass and enlarged right hilar and mediastinal nodes. "
            "PET-CT shows FDG uptake in the primary mass and mediastinal nodes, without clear distant metastasis. "
            "Brain MRI is negative."
        ),
        pathology_report=(
            "EBUS-guided biopsy of station 4R lymph node: poorly differentiated non-small cell carcinoma, favor adenocarcinoma. "
            "TTF-1 patchy positive, p40 negative. Tissue is scant. PD-L1 TPS estimated 30%, but report notes limited tumor cellularity. "
            "EGFR/ALK/ROS1/BRAF/MET/RET/NTRK testing pending; insufficient material may require repeat biopsy."
        ),
    ),
    PatientCase(
        case_id="case_3_colon",
        title="Colon cancer where mismatch repair status changes adjuvant thinking",
        clinical_summary=(
            "A 46-year-old woman presents with iron-deficiency anemia and right-sided abdominal discomfort. "
            "No known inflammatory bowel disease. Her father had colorectal cancer at age 49. ECOG 0."
        ),
        imaging_findings=(
            "CT abdomen/pelvis shows a localized ascending colon mass with small regional nodes, no liver lesions or distant metastases. "
            "CT chest is negative."
        ),
        pathology_report=(
            "Right hemicolectomy specimen: moderately differentiated adenocarcinoma, 4.8 cm, invading through muscularis propria into pericolonic tissue. "
            "Margins negative. 0/24 lymph nodes positive. No lymphovascular invasion; no perineural invasion. Tumor budding low. "
            "Mismatch repair IHC shows loss of MLH1 and PMS2 with intact MSH2/MSH6. BRAF V600E pending; MLH1 promoter methylation pending."
        ),
    ),
]


def get_case(case_id: str) -> PatientCase:
    for case in CASES:
        if case.case_id == case_id:
            return case
    raise KeyError(f"Unknown case_id: {case_id}")
