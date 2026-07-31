# Manager Notes

This project is an engineering demo for a memory-augmented oncology research agent. It is not clinical decision support, and the synthetic examples should not be used to make patient-care decisions.

## What The Manager Does

The Manager reads raw past agent trajectories from `data/raw_trajectories.jsonl`, compresses each trajectory into a structured `WorkflowSummary`, and writes the resulting summaries to `data/workflow_summaries.jsonl`.

Each workflow summary preserves the reusable lesson from a prior run rather than the full verbose interaction history. The summary includes the task category, question type, original question, useful search queries, successful strategy, evidence patterns, likely failure modes, and a compact text version suitable for retrieval.

## How Compression Works

Compression is heuristic only. The Manager does not call an external LLM API.

The current implementation:

- Copies `task_id`, `category`, and `original_question` from the raw trajectory.
- Uses the raw trajectory `question_type` when present, otherwise falls back to a category-based question type.
- Extracts `useful_queries` from each search step's `query` field.
- Infers `key_evidence_patterns` by matching observation text against oncology and trial-interpretation keywords.
- Builds `successful_strategy` from category-specific workflow templates plus the first sentence of the trajectory reflection.
- Builds `failure_modes` from category-specific caution templates plus any reflection sentence beginning with "Avoid".
- Creates `compressed_summary_text` by combining the strategy, evidence patterns, and failure modes into one retrieval-friendly paragraph.

## Why This Reduces Attention Dilution

Raw trajectories contain repeated searches, intermediate observations, false starts, and wording that may not help the next task. Passing those full logs into a planner can dilute attention because the model must separate durable lessons from incidental details.

Compressed workflow summaries keep the reusable parts: what kind of question it was, which search strategy worked, which evidence patterns mattered, and what mistakes to avoid. This gives the future Planner a smaller and more targeted memory context, making retrieval more useful and reducing irrelevant prompt tokens.

## Current Limitations

- The raw trajectory format includes `search_steps` and `reflection`, but the existing `RawTrajectory` dataclass in `src/memory/schemas.py` uses different field names. To honor the instruction not to change shared schemas, the Manager reads raw trajectories as dictionaries and only emits the existing `WorkflowSummary` schema.
- Compression quality is rule-based and brittle compared with an LLM summarizer.
- Evidence pattern extraction uses keyword matching, so it may miss paraphrases.
- The synthetic dataset is concise and designed for software testing, not clinical completeness.
- The Manager does not score whether the original trajectory was correct before summarizing it.
- No vector store insertion is performed yet; this step only writes workflow summaries to JSONL.
