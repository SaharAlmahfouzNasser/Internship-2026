"""Deterministic evaluation metrics for the MIA assignment."""

from __future__ import annotations

from src.memory.schemas import AgentResult, EvaluationSummary, ResearchQuestion


DEFAULT_CORRECTNESS_THRESHOLD = 0.61


def keyword_f1(answer: str, reference_keywords: list[str]) -> float:
    """Score answer quality by coverage of expected reference keywords.

    The assignment uses keyword-based deterministic judging. Because the
    expected terms are supplied as a compact reference set rather than extracted
    predictions, this metric treats keyword F1 as reference-keyword coverage.
    """

    if not reference_keywords:
        return 0.0

    answer_text = answer.lower()
    matched = sum(1 for keyword in reference_keywords if keyword.lower() in answer_text)
    return matched / len(reference_keywords)


def is_correct(keyword_score: float, threshold: float = DEFAULT_CORRECTNESS_THRESHOLD) -> bool:
    """Return whether a keyword score clears the correctness threshold."""

    return keyword_score >= threshold


def score_result(
    result: AgentResult,
    question: ResearchQuestion,
    *,
    threshold: float = DEFAULT_CORRECTNESS_THRESHOLD,
) -> AgentResult:
    """Update an AgentResult with deterministic keyword score and correctness."""

    score = keyword_f1(result.answer, question.reference_keywords)
    result.keyword_f1 = score
    result.is_correct = is_correct(score, threshold)
    return result


def accuracy(results: list[AgentResult]) -> float:
    """Compute fraction of correct results."""

    if not results:
        return 0.0
    return sum(1 for result in results if result.is_correct) / len(results)


def average_keyword_f1(results: list[AgentResult]) -> float:
    """Compute average keyword F1."""

    if not results:
        return 0.0
    return sum(result.keyword_f1 for result in results) / len(results)


def average_steps_to_answer(results: list[AgentResult]) -> float:
    """Compute average number of executor steps."""

    if not results:
        return 0.0
    return sum(result.steps_taken for result in results) / len(results)


def memory_hit_rate(results: list[AgentResult], questions: list[ResearchQuestion]) -> float | None:
    """Compute fraction of questions with at least one same-category memory hit."""

    if not results:
        return 0.0
    if results[0].condition == "baseline_no_memory":
        return None

    question_by_id = {question.question_id: question for question in questions}
    hits = 0
    total = 0
    for result in results:
        question = question_by_id.get(result.question_id)
        if question is None:
            continue
        total += 1
        if question.category in result.retrieved_memory_categories:
            hits += 1

    if total == 0:
        return 0.0
    return hits / total


def summarize_results(results: list[AgentResult], questions: list[ResearchQuestion]) -> EvaluationSummary:
    """Aggregate metrics for one condition."""

    condition = results[0].condition if results else "unknown"
    return EvaluationSummary(
        condition=condition,
        num_questions=len(results),
        accuracy=accuracy(results),
        average_keyword_f1=average_keyword_f1(results),
        average_steps_to_answer=average_steps_to_answer(results),
        memory_hit_rate=memory_hit_rate(results, questions),
    )
