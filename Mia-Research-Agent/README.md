# Memory-Augmented Oncology Research Agent

This is a small Python project on a simplified Memory Intelligence Agent (MIA). It builds an offline oncology research-agent prototype that stores compressed workflow memories from past runs and retrieves them for new questions.

The oncology examples are synthetic and used only for controlled evaluation. This project is an engineering demonstration only and not clinical decision support.

## Objective

The assignment goal is to compare a memory-free research agent with memory-augmented versions. Instead of putting full raw trajectories into the prompt, the system compresses prior runs into short workflow summaries and retrieves those summaries for future planning.

This implementation does not use live web search, external LLM calls, or parametric memory training. It is meant to test the memory-agent pipeline end to end.

## Why the prototype is offline

I kept this version offline so it is easy to run and compare. The assignment is mainly about the memory pipeline and the ablation setup, not about tuning prompts for a specific LLM API. A live LLM would add randomness, API keys, cost, and rate limits. For this submission, deterministic components make the baseline, MIA k=1, MIA k=3, and random retrieval results easier to reproduce.

## Architecture

| Component | What it does |
|---|---|
| Manager | Reads raw trajectories and compresses them into `WorkflowSummary` records. |
| MemoryStore | Indexes `compressed_summary_text` and retrieves relevant summaries with TF-IDF cosine similarity. |
| Planner | Builds a category-aware plan from the question and retrieved summaries. |
| Executor | Produces deterministic offline answers for each evaluation condition. |

The five question categories are treatment guidelines, biomarker matching, drug mechanisms, adverse effects, and clinical trial interpretation.

## Install

From the project directory:

```bash
pip install -r requirements.txt
```

`scikit-learn` is listed for TF-IDF retrieval. If it is not available, the vector store has a simple local TF-IDF fallback so the demo can still run.

## Run

Generate workflow summaries:

```bash
python -m src.agents.manager
```

Check memory retrieval:

```bash
python -m src.memory.vector_store
```

Run the full evaluation:

```bash
python -m src.evaluation.run_eval --condition all
```

Run one condition:

```bash
python -m src.evaluation.run_eval --condition baseline_no_memory
python -m src.evaluation.run_eval --condition mia_k1
python -m src.evaluation.run_eval --condition mia_k3
python -m src.evaluation.run_eval --condition random_k3
```

## Evaluation Conditions

| Condition | Description |
|---|---|
| `baseline_no_memory` | Executor answers directly without retrieved memory or a plan. |
| `mia_k1` | Retrieves the top 1 workflow summary, then plans and answers. |
| `mia_k3` | Retrieves the top 3 workflow summaries, then plans and answers. |
| `random_k3` | Retrieves 3 random summaries to test whether relevance matters. |

## Metrics

| Metric | Meaning |
|---|---|
| Accuracy | Fraction of answers whose keyword F1 clears the deterministic threshold. |
| Keyword F1 | Coverage of reference keywords in the generated answer. |
| Average steps to answer | Mean number of simulated Executor steps. |
| Memory hit rate | Fraction of questions with at least one retrieved memory from the same category. |

## Results

| Condition | Accuracy | Keyword F1 | Avg. Steps | Memory Hit Rate |
|---|---:|---:|---:|---:|
| `baseline_no_memory` | 0.333 | 0.550 | 5.00 | N/A |
| `mia_k1` | 0.750 | 0.767 | 3.50 | 1.000 |
| `mia_k3` | 1.000 | 1.000 | 3.50 | 1.000 |
| `random_k3` | 0.333 | 0.583 | 4.67 | 0.333 |

## Interpretation

The memory conditions perform better than the baseline. `mia_k1` improves answer completeness and reduces the simulated number of steps. `mia_k3` does best on this small dataset because it usually has more relevant workflow context.

The random retrieval condition stays close to the baseline. That is useful because it shows that adding memory text is not enough by itself; the retrieved summaries need to match the question category.

## Possible production extensions

The same structure could be upgraded with LLM-backed components. The Manager could use an LLM to compress raw trajectories, the Planner could use an LLM to generate plans from retrieved memories, and the Executor could call search tools with citation checks. The TF-IDF memory store could also be replaced with embeddings and a vector database. I kept these out of the submitted version to keep the assignment reproducible.

## Limitations

- The data is synthetic and small. Some sample content may have been generated or assisted, and it is used only to exercise the pipeline.
- The Executor is a deterministic simulator, not a real biomedical search agent.
- The evaluation uses reference-keyword coverage, not clinical expert review.
- The Manager uses heuristic compression.
- The MemoryStore uses TF-IDF retrieval or a simple TF-IDF fallback, not a validated biomedical retriever.
- There is no real LLM reasoning, clinical search, or parametric memory training.

## Safety Note

This project is an engineering demonstration only and not clinical decision support. It is not medical advice or a diagnostic tool. Real oncology decisions require qualified clinicians and authoritative medical references.
