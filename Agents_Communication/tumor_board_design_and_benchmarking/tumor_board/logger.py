"""Run-scoped logger for tumor board sessions.

Call init() once at the start of a run.  Every ask() call then records itself
via log_call().  finalize() writes the closing footer and persists the run.

Each run is written three ways:
  * logs/runs/<stamp>_<case_id>.log   - human-readable transcript
  * logs/runs/<stamp>_<case_id>.json  - structured transcript for the frontend
  * logs/latest/<case_id>.json        - copy of the most recent run for that case

The live FastAPI server (server.py) collects its own events and calls
persist_run() directly, so live streams also refresh logs/latest.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Node -> (speaker, title) mapping (single source of truth).
# Imported by server.py so the live stream and the saved transcript use identical
# labels.
NODE_META: dict[str, tuple[str, str]] = {
    "pathologist_independent_assessment": ("Pathologist", "Independent Assessment"),
    "oncologist_independent_assessment":  ("Oncologist",  "Independent Assessment"),
    "pathologist_opening":                ("Pathologist", "Round 1 — Opening"),
    "oncologist_response":                ("Oncologist",  "Round 2 — Response"),
    "pathologist_reply":                  ("Pathologist", "Round 3 — Reply"),
    "oncologist_revision":                ("Oncologist",  "Summary Contribution"),
    "pathologist_final_contribution":     ("Pathologist", "Summary Contribution"),
    "consistency_check":                  ("Board Chair", "Consistency Check"),
    "final_summary":                      ("Board",       "Final Summary"),
}

DIVIDER = "=" * 80
SUBDIV = "-" * 80

# Module state for the CLI (graph.invoke) path.
_log_file: Path | None = None
_log_dir: Path = Path("logs")
_run_start: float = 0.0
_started_iso: str = ""
_stamp: str = ""
_case_id: str = ""
_events: list[dict[str, Any]] = []


def meta_for(node: str) -> tuple[str, str]:
    return NODE_META.get(node, ("Board", node))


def init(case_id: str, log_dir: str | Path = "logs") -> Path:
    global _log_file, _log_dir, _run_start, _started_iso, _stamp, _case_id, _events
    _run_start = time.monotonic()
    _case_id = case_id
    _log_dir = Path(log_dir)
    _events = []

    runs_dir = _log_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _started_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log_file = runs_dir / f"{_stamp}_{case_id}.log"

    header = (
        f"{DIVIDER}\n"
        f"TUMOR BOARD RUN: {case_id}\n"
        f"Started: {_started_iso}\n"
        f"{DIVIDER}\n"
    )
    _log_file.write_text(header)
    _emit(header, newline=False)
    return _log_file


def log_call(
    *,
    agent: str,
    node: str,
    model: str,
    response: str,
    duration_s: float,
) -> None:
    elapsed = time.monotonic() - _run_start
    speaker, title = meta_for(node)
    _events.append(
        {
            "agent": agent,
            "node": node,
            "speaker": speaker,
            "title": title,
            "model": model,
            "duration_s": round(duration_s, 1),
            "elapsed_s": round(elapsed, 1),
            "content": response,
        }
    )
    block = (
        f"\n[+{elapsed:.1f}s]  {agent.upper()} | {node}\n"
        f"Model: {model}  |  Duration: {duration_s:.1f}s\n"
        f"{SUBDIV}\n"
        f"{response}\n"
    )
    _append(block)
    _emit(block, newline=False)


def finalize() -> None:
    elapsed = time.monotonic() - _run_start
    footer = f"\n{DIVIDER}\nRUN COMPLETE  Total: {elapsed:.1f}s\n{DIVIDER}\n"
    _append(footer)
    _emit(footer, newline=False)

    if _log_file is not None:
        persist_run(
            case_id=_case_id,
            stamp=_stamp,
            started_iso=_started_iso,
            total_seconds=round(elapsed, 1),
            events=_events,
            log_dir=_log_dir,
            write_text=False,  # the .log was already written incrementally
        )
        print(f"\n[logger] log saved → {_log_file}", file=sys.stderr, flush=True)


def persist_run(
    *,
    case_id: str,
    stamp: str,
    started_iso: str,
    total_seconds: float,
    events: list[dict[str, Any]],
    log_dir: str | Path = "logs",
    write_text: bool = True,
) -> dict[str, Path]:
    """Write the JSON transcript + refresh logs/latest. Optionally write text too.

    Used by finalize() (CLI path) and by server.py (live-stream path).
    Returns the paths written.
    """
    log_dir = Path(log_dir)
    runs_dir = log_dir / "runs"
    latest_dir = log_dir / "latest"
    runs_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "case_id": case_id,
        "stamp": stamp,
        "started": started_iso,
        "total_seconds": total_seconds,
        "events": events,
    }
    serialized = json.dumps(payload, indent=2, ensure_ascii=False)

    json_path = runs_dir / f"{stamp}_{case_id}.json"
    json_path.write_text(serialized)

    latest_path = latest_dir / f"{case_id}.json"
    latest_path.write_text(serialized)

    written = {"json": json_path, "latest": latest_path}

    if write_text:
        text = _render_text(case_id, started_iso, total_seconds, events)
        log_path = runs_dir / f"{stamp}_{case_id}.log"
        log_path.write_text(text)
        written["log"] = log_path

    return written


# Internal helpers.

def _render_text(
    case_id: str, started_iso: str, total_seconds: float, events: list[dict[str, Any]]
) -> str:
    parts = [
        f"{DIVIDER}\n"
        f"TUMOR BOARD RUN: {case_id}\n"
        f"Started: {started_iso}\n"
        f"{DIVIDER}\n"
    ]
    for e in events:
        parts.append(
            f"\n[+{e['elapsed_s']:.1f}s]  {e['agent'].upper()} | {e['node']}\n"
            f"Model: {e['model']}  |  Duration: {e['duration_s']:.1f}s\n"
            f"{SUBDIV}\n"
            f"{e['content']}\n"
        )
    parts.append(f"\n{DIVIDER}\nRUN COMPLETE  Total: {total_seconds:.1f}s\n{DIVIDER}\n")
    return "".join(parts)


def _append(text: str) -> None:
    if _log_file:
        with _log_file.open("a") as f:
            f.write(text)


def _emit(text: str, *, newline: bool = True) -> None:
    print(text, file=sys.stderr, flush=True, end="\n" if newline else "")
