"""Manager for compressing raw oncology agent trajectories.

This module intentionally uses heuristic compression only. It does not call an
external LLM API and is not clinical decision support.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.memory.schemas import WorkflowSummary
from src.utils.io import read_jsonl, write_dataclass_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_TRAJECTORIES_PATH = DATA_DIR / "raw_trajectories.jsonl"
WORKFLOW_SUMMARIES_PATH = DATA_DIR / "workflow_summaries.jsonl"


QUESTION_TYPE_BY_CATEGORY = {
    "treatment_guideline": "treatment_strategy",
    "biomarker_matching": "biomarker_to_therapy_match",
    "drug_mechanism": "mechanism_explanation",
    "adverse_effect": "toxicity_identification",
    "clinical_trial_interpretation": "trial_evidence_interpretation",
}


STRATEGY_BY_CATEGORY = {
    "treatment_guideline": [
        "Identify disease, stage, molecular context, and treatment line.",
        "Prioritize guideline-level sources or trial-backed summaries.",
        "Separate metastatic, localized, neoadjuvant, and adjuvant settings.",
    ],
    "biomarker_matching": [
        "Identify the biomarker, assay threshold, and cancer type.",
        "Connect the biomarker to therapy eligibility or prognostic role.",
        "Check exclusions such as actionable drivers before applying broad regimens.",
    ],
    "drug_mechanism": [
        "Map the drug target to the affected cancer biology pathway.",
        "Explain why the tumor context creates sensitivity.",
        "Avoid overclaiming beyond the mechanism supported by the evidence.",
    ],
    "adverse_effect": [
        "Search by drug class plus signature toxicity pattern.",
        "Capture the main organ systems and common monitoring approach.",
        "Distinguish mechanism-linked toxicity from chemotherapy or immune toxicity.",
    ],
    "clinical_trial_interpretation": [
        "Identify endpoint, comparison arms, and direction of effect.",
        "Interpret hazard ratios or response endpoints with their limitations.",
        "Use confidence intervals and clinical magnitude when available.",
    ],
}


FAILURE_MODES_BY_CATEGORY = {
    "treatment_guideline": [
        "Mixing treatment settings such as metastatic versus adjuvant disease.",
        "Giving a recommendation without molecular or staging context.",
    ],
    "biomarker_matching": [
        "Confusing prognostic and predictive biomarker roles.",
        "Ignoring assay type or positivity threshold.",
    ],
    "drug_mechanism": [
        "Listing a drug target without explaining the pathway consequence.",
        "Overstating that pathway inhibition guarantees tumor response.",
    ],
    "adverse_effect": [
        "Reporting a single symptom while missing the broader toxicity pattern.",
        "Confusing toxicities from different oncology drug classes.",
    ],
    "clinical_trial_interpretation": [
        "Treating hazard ratios as absolute survival probabilities.",
        "Ignoring confidence intervals, endpoint definitions, or surrogate limitations.",
    ],
}


EVIDENCE_PATTERN_KEYWORDS = {
    "guideline": "guideline-level treatment recommendation",
    "first-line": "line-of-therapy evidence",
    "biomarker": "biomarker eligibility pattern",
    "IHC": "assay threshold evidence",
    "ISH": "assay threshold evidence",
    "mechanism": "target-to-pathway mechanism",
    "synthetic lethality": "genotype-specific vulnerability pattern",
    "toxicity": "class-specific toxicity pattern",
    "monitoring": "toxicity monitoring pattern",
    "hazard ratio": "trial statistics interpretation pattern",
    "confidence interval": "statistical precision pattern",
    "overall survival": "definitive endpoint pattern",
    "response rate": "surrogate endpoint limitation pattern",
}


class Manager:
    """Compress raw trajectories into reusable workflow summaries."""

    def __init__(
        self,
        raw_trajectories_path: Path = RAW_TRAJECTORIES_PATH,
        workflow_summaries_path: Path = WORKFLOW_SUMMARIES_PATH,
    ) -> None:
        self.raw_trajectories_path = raw_trajectories_path
        self.workflow_summaries_path = workflow_summaries_path

    def load_raw_trajectories(self) -> list[dict[str, Any]]:
        """Load raw trajectory dictionaries from JSONL."""

        return read_jsonl(self.raw_trajectories_path)

    def compress_all(self, trajectories: list[dict[str, Any]]) -> list[WorkflowSummary]:
        """Compress all raw trajectories into workflow summaries."""

        return [self.compress_trajectory(trajectory) for trajectory in trajectories]

    def compress_trajectory(self, trajectory: dict[str, Any]) -> WorkflowSummary:
        """Create a heuristic WorkflowSummary from one raw trajectory."""

        category = str(trajectory.get("category", "unknown"))
        question = str(trajectory.get("question", ""))
        search_steps = self._search_steps(trajectory)
        useful_queries = self._extract_queries(search_steps)
        observations = self._extract_observations(search_steps)
        successful_strategy = self._successful_strategy(category, trajectory)
        key_evidence_patterns = self._key_evidence_patterns(category, observations)
        failure_modes = self._failure_modes(category, trajectory)
        question_type = str(
            trajectory.get("question_type") or QUESTION_TYPE_BY_CATEGORY.get(category, "research_question")
        )

        return WorkflowSummary(
            task_id=str(trajectory.get("task_id", "")),
            category=category,
            question_type=question_type,
            original_question=question,
            successful_strategy=successful_strategy,
            useful_queries=useful_queries,
            key_evidence_patterns=key_evidence_patterns,
            failure_modes=failure_modes,
            compressed_summary_text=self._compressed_summary_text(
                category=category,
                question_type=question_type,
                question=question,
                strategy=successful_strategy,
                evidence_patterns=key_evidence_patterns,
                failure_modes=failure_modes,
            ),
        )

    def save_summaries(self, summaries: list[WorkflowSummary]) -> None:
        """Persist workflow summaries as JSONL."""

        write_dataclass_jsonl(self.workflow_summaries_path, summaries)

    def run(self) -> list[WorkflowSummary]:
        """Load, compress, save, and return workflow summaries."""

        trajectories = self.load_raw_trajectories()
        summaries = self.compress_all(trajectories)
        self.save_summaries(summaries)
        return summaries

    @staticmethod
    def _search_steps(trajectory: dict[str, Any]) -> list[dict[str, Any]]:
        raw_steps = trajectory.get("search_steps", [])
        if not isinstance(raw_steps, list):
            return []
        return [step for step in raw_steps if isinstance(step, dict)]

    @staticmethod
    def _extract_queries(search_steps: list[dict[str, Any]]) -> list[str]:
        queries: list[str] = []
        for step in search_steps:
            query = str(step.get("query", "")).strip()
            if query:
                queries.append(query)
        return queries

    @staticmethod
    def _extract_observations(search_steps: list[dict[str, Any]]) -> list[str]:
        observations: list[str] = []
        for step in search_steps:
            observation = str(step.get("observation", "")).strip()
            if observation:
                observations.append(observation)
        return observations

    @staticmethod
    def _successful_strategy(category: str, trajectory: dict[str, Any]) -> list[str]:
        strategy = list(STRATEGY_BY_CATEGORY.get(category, ["Decompose the question before searching."]))
        reflection = str(trajectory.get("reflection", "")).strip()
        if reflection:
            first_sentence = reflection.split(".")[0].strip()
            if first_sentence:
                strategy.append(first_sentence + ".")
        return strategy

    @staticmethod
    def _failure_modes(category: str, trajectory: dict[str, Any]) -> list[str]:
        failure_modes = list(FAILURE_MODES_BY_CATEGORY.get(category, ["Using generic evidence without context."]))
        reflection = str(trajectory.get("reflection", "")).strip()
        for marker in ("Avoid ", "avoid "):
            if marker in reflection:
                caution = reflection.split(marker, maxsplit=1)[1].strip()
                if caution:
                    failure_modes.append("Avoid " + caution)
                break
        return failure_modes

    @staticmethod
    def _key_evidence_patterns(category: str, observations: list[str]) -> list[str]:
        patterns: list[str] = []
        combined = " ".join(observations).lower()
        for keyword, pattern in EVIDENCE_PATTERN_KEYWORDS.items():
            if keyword.lower() in combined and pattern not in patterns:
                patterns.append(pattern)

        if not patterns:
            patterns.append(f"{category.replace('_', ' ')} evidence pattern")
        return patterns

    @staticmethod
    def _compressed_summary_text(
        category: str,
        question_type: str,
        question: str,
        strategy: list[str],
        evidence_patterns: list[str],
        failure_modes: list[str],
    ) -> str:
        strategy_text = " ".join(strategy[:2])
        evidence_text = "; ".join(evidence_patterns[:3])
        failure_text = "; ".join(failure_modes[:2])
        return (
            f"For {category} / {question_type} questions like '{question}', "
            f"use this workflow: {strategy_text} Look for evidence patterns: "
            f"{evidence_text}. Watch for failure modes: {failure_text}."
        )


def main() -> None:
    manager = Manager()
    summaries = manager.run()
    print(f"Created {len(summaries)} workflow summaries.")
    if summaries:
        example = summaries[0]
        print("Example summary preview:")
        print(f"- task_id: {example.task_id}")
        print(f"- category: {example.category}")
        print(f"- question_type: {example.question_type}")
        print(f"- summary: {example.compressed_summary_text[:300]}")


if __name__ == "__main__":
    main()
