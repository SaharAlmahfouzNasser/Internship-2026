"""Run the required MIA assignment evaluation conditions."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.agents.executor import Executor
from src.agents.planner import Planner
from src.evaluation.metrics import score_result, summarize_results
from src.memory.schemas import AgentResult, EvaluationSummary, ResearchQuestion
from src.memory.vector_store import MemoryStore, build_index, load_summaries
from src.utils.io import read_jsonl, write_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
EVAL_TASKS_PATH = DATA_DIR / "eval_tasks.jsonl"
WORKFLOW_SUMMARIES_PATH = DATA_DIR / "workflow_summaries.jsonl"

CONDITIONS = ("baseline_no_memory", "mia_k1", "mia_k3", "random_k3")


def load_eval_questions(path: str | Path = EVAL_TASKS_PATH) -> list[ResearchQuestion]:
    """Load evaluation questions from JSONL."""

    return [ResearchQuestion.from_dict(record) for record in read_jsonl(path)]


def run_condition(
    condition: str,
    questions: list[ResearchQuestion],
    memory_store: MemoryStore,
    planner: Planner,
    executor: Executor,
) -> list[AgentResult]:
    """Run one evaluation condition over all questions."""

    results: list[AgentResult] = []
    for question in questions:
        if condition == "baseline_no_memory":
            result = executor.run(question, plan=None, condition=condition)
        else:
            retrieved = retrieve_for_condition(memory_store, question.question, condition)
            plan = planner.create_plan(question, retrieved, condition=condition)
            result = executor.run(question, plan=plan, condition=condition)

        results.append(score_result(result, question))
    return results


def retrieve_for_condition(memory_store: MemoryStore, query: str, condition: str):
    """Retrieve memories according to the requested condition."""

    if condition == "mia_k1":
        return memory_store.retrieve(query, k=1)
    if condition == "mia_k3":
        return memory_store.retrieve(query, k=3)
    if condition == "random_k3":
        return memory_store.retrieve_random(k=3)
    raise ValueError(f"Unsupported memory condition: {condition}")


def save_condition_results(condition: str, results: list[AgentResult]) -> Path:
    """Write detailed per-question results for one condition."""

    path = RESULTS_DIR / f"{condition}_results.json"
    write_json(path, [result.to_dict() for result in results])
    return path


def save_summary_table(summaries: list[EvaluationSummary]) -> Path:
    """Write summary metrics to CSV."""

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "summary_table.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "condition",
                "num_questions",
                "accuracy",
                "average_keyword_f1",
                "average_steps_to_answer",
                "memory_hit_rate",
            ],
        )
        writer.writeheader()
        for summary in summaries:
            row = summary.to_dict()
            row["memory_hit_rate"] = "N/A" if summary.memory_hit_rate is None else summary.memory_hit_rate
            writer.writerow(row)
    return path


def print_summary_table(summaries: list[EvaluationSummary]) -> None:
    """Print a readable summary table."""

    headers = [
        "condition",
        "n",
        "accuracy",
        "keyword_f1",
        "avg_steps",
        "memory_hit_rate",
    ]
    rows = []
    for summary in summaries:
        rows.append(
            [
                summary.condition,
                str(summary.num_questions),
                f"{summary.accuracy:.3f}",
                f"{summary.average_keyword_f1:.3f}",
                f"{summary.average_steps_to_answer:.2f}",
                "N/A" if summary.memory_hit_rate is None else f"{summary.memory_hit_rate:.3f}",
            ]
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    header_line = " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    separator = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def selected_conditions(condition: str) -> list[str]:
    """Resolve CLI condition selection."""

    if condition == "all":
        return list(CONDITIONS)
    if condition not in CONDITIONS:
        valid = ", ".join(("all", *CONDITIONS))
        raise ValueError(f"Unknown condition '{condition}'. Valid options: {valid}")
    return [condition]


def run_evaluation(condition: str = "all") -> list[EvaluationSummary]:
    """Run selected evaluation condition(s) end to end."""

    questions = load_eval_questions()
    summaries = load_summaries(WORKFLOW_SUMMARIES_PATH)
    memory_store = build_index(summaries)
    planner = Planner()
    executor = Executor()

    summary_rows: list[EvaluationSummary] = []
    for condition_name in selected_conditions(condition):
        results = run_condition(condition_name, questions, memory_store, planner, executor)
        save_condition_results(condition_name, results)
        summary_rows.append(summarize_results(results, questions))

    save_summary_table(summary_rows)
    return summary_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run simplified MIA evaluation.")
    parser.add_argument(
        "--condition",
        default="all",
        choices=("all", *CONDITIONS),
        help="Evaluation condition to run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = run_evaluation(args.condition)
    print_summary_table(summaries)
    print(f"\nSaved results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
