# Assignment Report: Simplified Memory-Augmented Oncology Research Agent

## 1. Motivation

The assignment is based on the MIA idea that raw trajectory retrieval can create attention dilution. A full trajectory may contain useful experience, but it also includes repeated searches, intermediate observations, and details that are not useful for the next question. If the whole log is retrieved, the agent has to sort through that noise before it can plan.

This prototype uses a smaller memory unit: a compressed workflow summary. The summary keeps the parts that seem reusable, such as the successful strategy, useful queries, evidence patterns, and failure modes. The goal is not to build a clinical system, but to test whether structured memory can improve a simple research-agent workflow.

The oncology tasks in this project are synthetic and used for controlled offline evaluation. Some sample data may have been generated or assisted. The purpose is to evaluate the memory pipeline, not to validate medical performance.

## 2. System Design

The system has four main pieces:

| Component | Role |
|---|---|
| Manager | Compresses raw trajectories into workflow summaries. |
| MemoryStore | Indexes workflow summaries and retrieves them for new questions. |
| Planner | Creates a category-specific plan using retrieved memories. |
| Executor | Produces deterministic offline answers for evaluation. |

The data covers five oncology question categories: treatment guidelines, biomarker matching, drug mechanisms, adverse effects, and clinical trial interpretation. The implementation is intentionally offline. It does not use live search, external LLM APIs, clinical databases, or parametric memory training.

## 3. Memory Compression Design

The Manager reads `data/raw_trajectories.jsonl`. Each raw trajectory contains a question, category, search steps, final answer, and reflection. The Manager then writes `WorkflowSummary` records to `data/workflow_summaries.jsonl`.

Each summary stores the original question, category, question type, successful strategy, useful queries, evidence patterns, failure modes, and a compact `compressed_summary_text` field. Compression is heuristic. Category templates provide common strategies and cautions, while queries and observations are extracted from the raw trajectory.

This is a practical approximation of memory compression. It removes the bulk of the raw trajectory while preserving the information that should help a future Planner.

## 4. Retrieval And Planning Design

The MemoryStore indexes `compressed_summary_text`. The default retrieval method is TF-IDF cosine similarity from scikit-learn. If scikit-learn is not installed, the code uses a small local TF-IDF fallback so the project can still run in a lightweight environment.

The Planner takes a `ResearchQuestion` and retrieved summaries. It uses deterministic category templates rather than an LLM. If retrieved memory matches the question category, the plan includes memory-derived strategy and caution steps. If memory is random or irrelevant, the plan treats it as weak context.

This approximates MIA's memory use through in-context retrieved workflow summaries. It does not implement the full paper's reinforcement-learning approach for internalizing strategies into model weights.

## 5. Evaluation Setup

The evaluation compares four conditions:

| Condition | Description |
|---|---|
| `baseline_no_memory` | Executor answers directly without a plan or memory. |
| `mia_k1` | Retrieves the top 1 relevant memory and uses it for planning. |
| `mia_k3` | Retrieves the top 3 relevant memories and uses them for planning. |
| `random_k3` | Retrieves 3 random memories as an ablation. |

The metrics are:

- **Accuracy:** whether keyword F1 clears the deterministic correctness threshold.
- **Keyword F1:** coverage of expected reference keywords.
- **Average steps to answer:** mean simulated Executor steps.
- **Memory hit rate:** whether retrieved memory includes at least one summary from the same category as the question.

This setup is deliberately simple. It checks whether the components interact correctly and whether relevant memory retrieval changes the outcome.

## 6. Results And Interpretation

| Condition | Accuracy | Keyword F1 | Avg. Steps | Memory Hit Rate |
|---|---:|---:|---:|---:|
| `baseline_no_memory` | 0.333 | 0.550 | 5.00 | N/A |
| `mia_k1` | 0.750 | 0.767 | 3.50 | 1.000 |
| `mia_k3` | 1.000 | 1.000 | 3.50 | 1.000 |
| `random_k3` | 0.333 | 0.583 | 4.67 | 0.333 |

The results show the intended pattern. The baseline answers some questions partially, but it misses more reference concepts and takes more simulated steps. `mia_k1` improves both accuracy and keyword F1 because the Planner receives one relevant workflow summary. `mia_k3` performs best on this dataset because it has more relevant memory context.

The random retrieval condition stays close to the baseline. It retrieves three summaries, but only some match the question category. This supports the main design assumption: memory helps when retrieval is relevant, not simply because more text is added.

## 7. Trade-Offs

Compressed summaries are easier to retrieve and use than raw trajectories. They reduce prompt noise and keep the planning signal focused. The trade-off is that compression can lose details that might matter for unusual cases.

Relevant retrieval clearly matters. In this setup, random retrieval sometimes helps by chance, but it does not match the performance of category-relevant memory.

The `k=1` setting is concise and already improves over baseline. The `k=3` setting gives broader context and performs best here, although a larger `k` could add noise in a larger or messier memory store.

The project uses non-parametric memory: explicit summaries stored outside the model. This is easy to inspect and update. The full MIA paper also discusses parametric memory, where planning strategies are internalized through training. That approach is outside the scope of this offline prototype.

## 8. Limitations And Future Work

The main limitation is that this is a controlled engineering prototype, not a clinical research tool. The data is synthetic, the Executor is deterministic, and the evaluation uses keyword coverage rather than expert review. There is no real document retrieval, no source attribution, no live literature search, and no validated medical performance.

The Manager's heuristic compression is also limited. A stronger version could compare LLM-based summaries, structured evidence extraction, and human-written workflow memories. Retrieval could also be improved with biomedical embeddings or hybrid search.

Future work could add a larger evaluation set, real source documents, citation tracking, LLM-as-judge scoring, and more realistic executor behavior. A more complete MIA implementation could also explore how procedural memory is learned or distilled into the Planner rather than only retrieved in context.

## 9. Safety Note

This project is an engineering demonstration only and not clinical decision support. It is not medical advice or a diagnostic system. The oncology examples are synthetic and should not be used to guide patient care.
