"""Shared dataclass schemas for MIA artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RawTrajectory:
    """Verbose record of one agent run before compression."""

    task_id: str
    question: str
    category: str
    condition: str
    steps: list[str] = field(default_factory=list)
    searches: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    final_answer: str = ""
    was_successful: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawTrajectory":
        return cls(**data)


@dataclass(slots=True)
class WorkflowSummary:
    """Compressed reusable memory extracted from a raw trajectory."""

    task_id: str
    category: str
    question_type: str
    original_question: str
    successful_strategy: list[str] = field(default_factory=list)
    useful_queries: list[str] = field(default_factory=list)
    key_evidence_patterns: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    compressed_summary_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowSummary":
        return cls(**data)


@dataclass(slots=True)
class ResearchQuestion:
    """Evaluation question with reference answer information."""

    question_id: str
    question: str
    category: str
    reference_answer: str
    reference_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchQuestion":
        return cls(**data)


@dataclass(slots=True)
class Plan:
    """Planner output for a single research question."""

    question_id: str
    condition: str
    steps: list[str] = field(default_factory=list)
    retrieved_memory_ids: list[str] = field(default_factory=list)
    retrieved_memory_categories: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Plan":
        return cls(**data)


@dataclass(slots=True)
class AgentResult:
    """Final answer and evaluation fields from one agent run."""

    question_id: str
    condition: str
    answer: str
    steps_taken: int
    retrieved_memory_ids: list[str] = field(default_factory=list)
    retrieved_memory_categories: list[str] = field(default_factory=list)
    plan_steps: list[str] = field(default_factory=list)
    is_correct: bool = False
    keyword_f1: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentResult":
        return cls(**data)


@dataclass(slots=True)
class EvaluationSummary:
    """Aggregate metrics for one experiment condition."""

    condition: str
    num_questions: int
    accuracy: float
    average_keyword_f1: float
    average_steps_to_answer: float
    memory_hit_rate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationSummary":
        return cls(**data)
