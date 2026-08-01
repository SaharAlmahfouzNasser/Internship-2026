# Song Music Theory Analysis — Agent Skill

An agent skill that gives an LLM the behavioral guidance, API resource pointers, and step-by-step workflow needed to reliably turn a song name into a structured music theory profile. Built to test the "Science Skills" approach from Google DeepMind's *Science Skills for Antigravity* (2026) paper: does a plain-text skill file actually make an agent more reliable and efficient?

## What it does

Given a song name (and optionally an artist), the agent:

1. Searches **Spotify** for the track ID and basic metadata
2. Calls **ReccoBeats** with that track ID to get audio features (tempo, key, mode, valence, energy, danceability, instrumentalness)
3. Searches **MusicBrainz** for release date and genre tags
4. Synthesizes everything into a structured music theory profile — including a mood label (Euphoric/Upbeat, Peaceful/Calm, Angry/Intense, Sad/Melancholic) derived from a valence + energy matrix

## Why music theory

- Domain I know well (choir, a cappella, guitar, piano, music theory)
- A repeatable, multi-step workflow that touches 2+ external APIs
- Outputs are verifiable — I can check whether the key and mood are actually correct

## Repo contents

| File | Description |
|---|---|
| `skill_file.md` | The agent skill itself: behavioral guidance, resource pointers (endpoints, auth, response shapes), and the 6-step workflow the agent follows |
| `test_suite.md` (or `.pdf`) | 3 tests — Unit, Workflow, and Capability — with prompts, expected outputs, and pass criteria |
| `results_table.md` (or `.pdf`) | Full baseline-vs-skill results: turn counts, pass/fail per test, and summary metrics |
| `ScienceSkills_Simran_Mallik.pdf` | Slide deck summarizing the project, methodology, and findings |

## The skill file's 3 components

1. **Behavioral Guidance** — how to approach the task, including the mood synthesis table (valence × energy → mood label) and explicit high/low thresholds (< 0.5 vs ≥ 0.5) so agent behavior stays consistent and testable.
2. **Resource Pointers** — exact API endpoints, auth methods, and response structures for Spotify, ReccoBeats, and MusicBrainz, so the agent never has to search for these.
3. **Step-by-Step Workflow** — 6 numbered steps: authenticate → search Spotify → query ReccoBeats → query MusicBrainz → convert key integer + synthesize mood → output in the exact structured format.

## Experiment setup

- **Model:** `llama-3.3-70b-versatile` (Groq)
- **Framework:** custom ReAct loop in Python
- **Baseline condition:** system prompt = *"You are a helpful music analysis assistant."* Agent is given the same 3 tools and figures out its own approach.
- **Skill condition:** full skill file injected as system-level context, same tools as baseline.

### Test types

| Test | Prompt | Tests |
|---|---|---|
| Unit | "What is the Spotify track ID for 'Shape of You' by Ed Sheeran?" | One step in isolation |
| Workflow | "Give me a full music theory analysis of 'Blinding Lights' by The Weeknd" | Full end-to-end; all 3 APIs called and interpreted |
| Capability | "I'm building an upbeat playlist. Can you analyze 'Happy' by Pharrell Williams and tell me if it fits the mood?" | Open-ended — does the agent apply the skill without being told to? |

## Results

| Test | Baseline Turns | Baseline Result | Skill Turns | Skill Result |
|---|---|---|---|---|
| Unit | 1 | Pass | 3 | Pass (Partial — over-applied the workflow for a simple ID lookup) |
| Workflow | 3 | Pass | 3 | Pass |
| Capability | 2 | Pass | 3 | Pass |

**Summary metrics:**

| Metric | Baseline | With Skill |
|---|---|---|
| Total turns (all 3 tests) | 6 | 9 |
| Tests passed | 3/3 | 3/3 (1 partial) |
| Used structured output format | 0/3 | 3/3 |
| Called all 3 APIs | 1/3 | 3/3 |
| Gave explicit mood label | 0/3 | 3/3 |

### Comparison to the paper

| Metric | Paper Reports | This Result | Match? |
|---|---|---|---|
| Reliability | 49% → 93% with skill | Both conditions passed all 3 tests | Partial — baseline was stronger than expected |
| Efficiency (turns) | Skill reduces token usage | Skill used more turns (9 vs 6) | Opposite — skill was over-applied |
| Consistency | Skill enforces repeatable workflow | Skill used structured format in 3/3 tests; baseline in 0/3 | Confirmed |

**Bottom line:** the skill's real contribution was *consistency and completeness*, not correctness. The baseline model was capable but unpredictable — it sometimes skipped tools or answered in free-form prose. The skill enforced a repeatable structure across every run, at the cost of some efficiency on trivial lookups.

## What was hardest to get right

| Component | Difficulty | Notes |
|---|---|---|
| Behavioral Guidance | Medium | Straightforward once the domain was clear; the mood synthesis table with binary thresholds was the key design decision |
| Resource Pointers | Hardest | Not hard to *write*, but API reliability was outside the skill's control — Spotify returned covers/remixes, ReccoBeats had missing songs. A skill can't fix bad upstream data |
| Workflow Steps | Hard | A parallel tool call bug showed that step ordering matters a lot — the skill said "search Spotify first," but the agent called all tools simultaneously until sequential calls were forced at the framework level |

## Takeaways

1. Skills enforce structure and honesty — even when APIs fail, the agent behaved more predictably with the skill than without.
2. The hardest part isn't writing the skill — it's knowing which APIs are reliable enough to build a workflow on.
3. Step ordering should be enforced at the framework level, not just described in prose.
4. Music theory ground truth is inherently ambiguous (e.g., C# major, Db major, and C minor can describe overlapping harmonic content), which limits how "correct" any automated analysis can claim to be.

## Attribution

Based on: *Science Skills for Antigravity* (Google DeepMind, 2026)
