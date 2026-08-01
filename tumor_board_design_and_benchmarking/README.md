# Tumor Board

A two-agent tumor board. An oncologist agent and a pathologist agent read the
same case packet, assess it independently, discuss it over a few rounds, and
each write a summary. A board chair agent then checks both summaries against the
case packet for unsupported or contradictory claims.

It runs as a LangGraph pipeline. A FastAPI server streams each step over SSE, and
a Next.js frontend shows the case packet alongside the live (or replayed) board
discussion.

## How it works

The graph (`tumor_board/graph.py`) runs these steps:

1. Pathologist and oncologist each write an independent assessment (in parallel).
2. Three discussion rounds: pathologist opens, oncologist responds, pathologist replies.
3. Each specialist writes their summary contribution (in parallel, so neither sees the other's).
4. The board chair runs a consistency check against the case packet.
5. The final summary concatenates both contributions and the chair's check.

The oncologist runs on a vision model and receives any case images; the
pathologist and board chair run on a text model. Models are set per agent in
`.env` (see Configuration).

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- Node.js 18+ (for the frontend)
- API keys for the model providers you point the agents at

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and add at least OPENROUTER_API_KEY
```

## Usage

### Run a case from the CLI

```bash
uv run tb-run --case cases/nsclc_egfr_l858r_advanced/case.json
uv run tb-all        # run all three cases in sequence
uv run tb-diagram    # render the graph to diagram.png
```

Each run prints to the terminal and writes a transcript to `logs/runs/`, plus a
copy at `logs/latest/<case_id>.json` that the frontend's Replay mode reads.

### Run the server + frontend

```bash
# terminal 1: streaming API on http://localhost:8000
uv run tb-serve --reload

# terminal 2: UI on http://localhost:3000
cd frontend
npm install
npm run dev
```

In the UI, **Live** mode streams a fresh run from the server; **Replay** mode
loads the latest saved run from `logs/latest/` without calling any model.

## Configuration

All config lives in `config.py`. It reads secrets and model choices from `.env`
and hard-codes the rest (token limits, timeouts, retries). The only required
variable is `OPENROUTER_API_KEY`; every agent falls back to OpenRouter if its own
model/provider isn't set. See `.env.example` for the full list.

The frontend has two optional environment variables:

- `FASTAPI_URL` — backend URL (default `http://localhost:8000`)
- `LOGS_DIR` — where Replay mode reads transcripts (default `../logs`)

## Layout

```
config.py              Config and secret loading
server.py              FastAPI SSE server (POST /stream/{case_id})
tumor_board/
  graph.py             LangGraph wiring (nodes and edges)
  nodes.py             One function per board step
  agents.py            ask() - picks the model per agent, throttles, logs
  llm.py               HTTP chat-completion call with retry/backoff
  prompts.py           System prompts and case-fidelity rules
  state.py             Shared graph state (TypedDict)
  loader.py            Loads case.json and base64-encodes images
  logger.py            Writes run transcripts (.log + .json)
  cli/                 Entry points: run, run_all, serve, diagram
cases/                 Case packets (case.json) and images
logs/                  Saved run transcripts
frontend/              Next.js app (case panel + streaming/replay transcript)
```
