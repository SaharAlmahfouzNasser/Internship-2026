"""FastAPI streaming server for the tumor board.

Run:
    uv run tb-serve --reload

Each POST to /stream/{case_id} runs the LangGraph pipeline and streams
one SSE event per completed node, in real time.
"""

import asyncio
import json
import queue
import threading
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import tumor_board.logger as logger
from tumor_board import tumor_board_graph
from tumor_board.loader import format_case_packet, load_case, load_oncologist_images
from tumor_board.logger import NODE_META

app = FastAPI(title="Tumor Board API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

CASES_DIR = Path("cases")

_SENTINEL = object()


def sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def stream_board(case_id: str) -> AsyncIterator[str]:
    case_dir = CASES_DIR / case_id
    case_file = case_dir / "case.json"
    if not case_file.exists():
        yield sse({"type": "error", "content": f"Case not found: {case_id}"})
        return

    case = load_case(str(case_file))
    oncologist_images = load_oncologist_images(case, case_dir)
    yield sse({"type": "status", "title": "Running", "content": f"Starting tumor board for {case_id}…"})

    initial_state = {
        "case_id": case["id"],
        "case_packet": format_case_packet(case),
        "oncologist_images": oncologist_images,
        "pathologist_independent_assessment": "",
        "oncologist_independent_assessment": "",
        "pathologist_opening": "",
        "oncologist_response": "",
        "pathologist_reply": "",
        "oncologist_revision": "",
        "pathologist_final_contribution": "",
        "consistency_check": "",
        "final_summary": "",
    }

    # Bridge: sync LangGraph generator → async SSE stream via a queue.
    # The graph runs in a background thread and puts each node event onto
    # the queue; the async loop drains it and yields SSE chunks in real time.
    q: queue.Queue = queue.Queue()

    def run_graph() -> None:
        # init/finalize the run-scoped logger so each live stream is also saved
        # to logs/runs/ and refreshes logs/latest/<case_id>.json (for Replay mode).
        logger.init(case_id)
        try:
            for node_event in tumor_board_graph.stream(initial_state):
                q.put(node_event)
            logger.finalize()
        except Exception as exc:
            q.put(exc)
        finally:
            q.put(_SENTINEL)

    thread = threading.Thread(target=run_graph, daemon=True)
    thread.start()

    loop = asyncio.get_event_loop()
    while True:
        node_event = await loop.run_in_executor(None, q.get)

        if node_event is _SENTINEL:
            break
        if isinstance(node_event, Exception):
            yield sse({"type": "error", "content": str(node_event)})
            break

        for node_name, output in node_event.items():
            speaker, title = NODE_META.get(node_name, ("Board", node_name))
            content = next(iter(output.values())) if isinstance(output, dict) else str(output)
            yield sse({"type": "section", "speaker": speaker, "title": title, "content": content})

    yield sse({"type": "done", "content": "Presentation complete."})


@app.post("/stream/{case_id}")
async def stream_endpoint(case_id: str) -> StreamingResponse:
    return StreamingResponse(
        stream_board(case_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
