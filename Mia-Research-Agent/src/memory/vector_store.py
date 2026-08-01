"""Lightweight vector store for workflow-summary memory retrieval."""

from __future__ import annotations

import random
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ModuleNotFoundError:
    TfidfVectorizer = None
    cosine_similarity = None

from src.memory.schemas import WorkflowSummary
from src.utils.io import read_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMMARIES_PATH = PROJECT_ROOT / "data" / "workflow_summaries.jsonl"


def load_summaries(path: str | Path = DEFAULT_SUMMARIES_PATH) -> list[WorkflowSummary]:
    """Load workflow summaries from JSONL."""

    return [WorkflowSummary.from_dict(record) for record in read_jsonl(path)]


class MemoryStore:
    """Vector-based retrieval over compressed workflow summaries.

    TF-IDF cosine similarity is the default retrieval backend because it is
    deterministic, lightweight, and sufficient for the assignment demo.
    """

    def __init__(self, *, random_seed: int = 7) -> None:
        self.summaries: list[WorkflowSummary] = []
        self.vectorizer: Any = None
        self.matrix: Any = None
        self.random = random.Random(random_seed)
        self.backend = "sklearn-tfidf"

    def build_index(self, summaries: list[WorkflowSummary]) -> None:
        """Build a TF-IDF index over compressed summary text."""

        self.summaries = summaries
        texts = [summary.compressed_summary_text for summary in summaries]
        if TfidfVectorizer is not None:
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self.matrix = self.vectorizer.fit_transform(texts) if texts else None
            self.backend = "sklearn-tfidf"
            return

        self.vectorizer = SimpleTfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(texts)
        self.backend = "simple-tfidf-fallback"

    def retrieve(self, query: str, k: int = 3) -> list[tuple[WorkflowSummary, float]]:
        """Return the top-k summaries and cosine similarity scores."""

        if not self.summaries or self.vectorizer is None or self.matrix is None:
            return []

        safe_k = max(0, min(k, len(self.summaries)))
        if safe_k == 0:
            return []

        query_vector = self.vectorizer.transform([query])
        if cosine_similarity is not None:
            scores = cosine_similarity(query_vector, self.matrix).ravel()
        else:
            scores = simple_cosine_similarity(query_vector[0], self.matrix)
        ranked_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)

        return [(self.summaries[index], float(scores[index])) for index in ranked_indices[:safe_k]]

    def retrieve_random(self, k: int = 3) -> list[tuple[WorkflowSummary, float]]:
        """Return k random summaries with a neutral score for ablation tests."""

        if not self.summaries:
            return []

        safe_k = max(0, min(k, len(self.summaries)))
        sampled = self.random.sample(self.summaries, safe_k)
        return [(summary, 0.0) for summary in sampled]


def build_index(summaries: list[WorkflowSummary]) -> MemoryStore:
    """Convenience function that returns a built MemoryStore."""

    store = MemoryStore()
    store.build_index(summaries)
    return store


class SimpleTfidfVectorizer:
    """Small fallback used only when scikit-learn is not installed."""

    def __init__(self) -> None:
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}

    def fit_transform(self, texts: list[str]) -> list[list[float]]:
        tokenized = [self._tokens(text) for text in texts]
        terms = sorted({token for tokens in tokenized for token in tokens})
        self.vocabulary = {term: index for index, term in enumerate(terms)}

        doc_count = len(texts)
        document_frequency = Counter()
        for tokens in tokenized:
            document_frequency.update(set(tokens))

        self.idf = {
            term: math.log((1 + doc_count) / (1 + document_frequency[term])) + 1
            for term in terms
        }
        return [self._vectorize_tokens(tokens) for tokens in tokenized]

    def transform(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize_tokens(self._tokens(text)) for text in texts]

    def _vectorize_tokens(self, tokens: list[str]) -> list[float]:
        vector = [0.0] * len(self.vocabulary)
        if not tokens:
            return vector

        counts = Counter(tokens)
        total = sum(counts.values())
        for token, count in counts.items():
            index = self.vocabulary.get(token)
            if index is not None:
                vector[index] = (count / total) * self.idf[token]
        return vector

    @staticmethod
    def _tokens(text: str) -> list[str]:
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        bigrams = [f"{left} {right}" for left, right in zip(words, words[1:])]
        return words + bigrams


def simple_cosine_similarity(query_vector: list[float], matrix: list[list[float]]) -> list[float]:
    """Compute cosine similarity for fallback dense vectors."""

    query_norm = math.sqrt(sum(value * value for value in query_vector))
    scores: list[float] = []
    for row in matrix:
        row_norm = math.sqrt(sum(value * value for value in row))
        if query_norm == 0.0 or row_norm == 0.0:
            scores.append(0.0)
            continue
        dot_product = sum(left * right for left, right in zip(query_vector, row))
        scores.append(dot_product / (query_norm * row_norm))
    return scores


def _preview(text: str, max_chars: int = 220) -> str:
    clean_text = " ".join(text.split())
    if len(clean_text) <= max_chars:
        return clean_text
    return clean_text[: max_chars - 3] + "..."


def main() -> None:
    summaries = load_summaries()
    store = build_index(summaries)
    query = "What is a first-line targeted therapy for metastatic EGFR-mutated NSCLC?"
    results = store.retrieve(query, k=3)

    print(f"Loaded {len(summaries)} workflow summaries.")
    print(f"Backend: {store.backend}")
    print(f"Query: {query}")
    print("Top 3 results:")
    for rank, (summary, score) in enumerate(results, start=1):
        print(f"{rank}. task_id={summary.task_id} category={summary.category} score={score:.4f}")
        print(f"   preview={_preview(summary.compressed_summary_text)}")


if __name__ == "__main__":
    main()
