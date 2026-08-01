"""Template-based Planner for the simplified MIA demo."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.memory.schemas import Plan, ResearchQuestion, WorkflowSummary


RetrievedMemory = WorkflowSummary | tuple[WorkflowSummary, float]


CATEGORY_PLAN_STEPS = {
    "treatment_guideline": [
        "Identify cancer type, stage, and treatment setting.",
        "Identify actionable biomarker or molecular subtype.",
        "Determine line of therapy.",
        "Check guideline-style evidence and pivotal trial context.",
        "Produce concise research answer with caveats.",
    ],
    "biomarker_matching": [
        "Identify biomarker or mutation.",
        "Identify cancer type.",
        "Match biomarker to relevant therapy class.",
        "Verify whether the biomarker is predictive, prognostic, or diagnostic.",
        "Produce concise answer.",
    ],
    "drug_mechanism": [
        "Identify drug or therapy class.",
        "Identify molecular target.",
        "Explain pathway or mechanism of action.",
        "Mention resistance or downstream effect if relevant.",
        "Produce concise answer.",
    ],
    "adverse_effect": [
        "Identify drug or therapy class.",
        "Identify key toxicity or adverse effect.",
        "Explain why it matters clinically.",
        "Mention monitoring or management context at a high level.",
        "Produce concise answer.",
    ],
    "clinical_trial_interpretation": [
        "Identify study population.",
        "Identify intervention and comparator.",
        "Identify endpoint.",
        "Interpret result direction.",
        "Produce concise answer.",
    ],
}


DEFAULT_PLAN_STEPS = [
    "Classify the oncology research question.",
    "Identify the disease context and key terms.",
    "Use retrieved memory to choose the most relevant reasoning path.",
    "Check for caveats or common failure modes.",
    "Produce concise research answer with caveats.",
]


class Planner:
    """Create deterministic plans from a question and retrieved memories."""

    def create_plan(
        self,
        question: ResearchQuestion,
        retrieved_memories: Iterable[RetrievedMemory] | None = None,
        *,
        condition: str = "mia_k1",
    ) -> Plan:
        """Return a Plan using category templates and retrieved memory metadata."""

        memories = [self._unwrap_memory(memory) for memory in retrieved_memories or []]
        memory_ids = [summary.task_id for summary, _score in memories]
        memory_categories = [summary.category for summary, _score in memories]
        selected_category = self._select_planning_category(question.category, memory_categories)
        steps = self._adapt_steps(selected_category, question.category, memories)
        rationale = self._planning_rationale(question, selected_category, memories, condition)

        return Plan(
            question_id=question.question_id,
            condition=condition,
            steps=steps,
            retrieved_memory_ids=memory_ids,
            retrieved_memory_categories=memory_categories,
            rationale=rationale,
        )

    @staticmethod
    def _unwrap_memory(memory: RetrievedMemory) -> tuple[WorkflowSummary, float | None]:
        if isinstance(memory, tuple):
            summary, score = memory
            return summary, float(score)
        return memory, None

    @staticmethod
    def _select_planning_category(question_category: str, memory_categories: list[str]) -> str:
        if question_category in memory_categories:
            return question_category
        if memory_categories:
            return memory_categories[0]
        return question_category

    @staticmethod
    def _adapt_steps(
        selected_category: str,
        question_category: str,
        memories: list[tuple[WorkflowSummary, float | None]],
    ) -> list[str]:
        steps = list(CATEGORY_PLAN_STEPS.get(selected_category, DEFAULT_PLAN_STEPS))

        matching_memories = [summary for summary, _score in memories if summary.category == question_category]
        if matching_memories:
            memory = matching_memories[0]
            if memory.successful_strategy:
                steps.insert(0, f"Apply retrieved workflow: {memory.successful_strategy[0]}")
            if memory.failure_modes:
                steps.insert(-1, f"Check retrieved caution: {memory.failure_modes[0]}")
        elif memories:
            steps.insert(
                0,
                "Treat retrieved memory as weak context because its category does not match the question.",
            )

        return steps

    @staticmethod
    def _planning_rationale(
        question: ResearchQuestion,
        selected_category: str,
        memories: list[tuple[WorkflowSummary, float | None]],
        condition: str,
    ) -> str:
        if not memories:
            return (
                f"No memory was supplied for {condition}; using the question category "
                f"'{question.category}' to choose a template plan."
            )

        matching_count = sum(1 for summary, _score in memories if summary.category == question.category)
        scored_memory = [
            f"{summary.task_id}:{summary.category}"
            + (f":{score:.3f}" if score is not None else "")
            for summary, score in memories
        ]
        if matching_count:
            return (
                f"Retrieved {matching_count} memory item(s) matching '{question.category}'. "
                f"Using the '{selected_category}' planning template with memory cues from "
                f"{', '.join(scored_memory)}."
            )
        return (
            f"Retrieved memories did not match '{question.category}'. Using the closest "
            f"available template '{selected_category}' cautiously from {', '.join(scored_memory)}."
        )


def _load_demo_question() -> ResearchQuestion:
    from src.utils.io import read_jsonl

    project_root = Path(__file__).resolve().parents[2]
    record = read_jsonl(project_root / "data" / "eval_tasks.jsonl")[0]
    return ResearchQuestion.from_dict(record)


def main() -> None:
    from src.memory.vector_store import build_index, load_summaries

    question = _load_demo_question()
    store = build_index(load_summaries())
    retrieved = store.retrieve(question.question, k=3)
    plan = Planner().create_plan(question, retrieved, condition="mia_k3")

    print(f"Question: {question.question}")
    print(f"Retrieved memory IDs: {', '.join(plan.retrieved_memory_ids)}")
    print(f"Retrieved categories: {', '.join(plan.retrieved_memory_categories)}")
    print("Plan steps:")
    for index, step in enumerate(plan.steps, start=1):
        print(f"{index}. {step}")
    print(f"Rationale: {plan.rationale}")


if __name__ == "__main__":
    main()
