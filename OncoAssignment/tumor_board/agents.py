import time
from typing import Any

from config import (
    BOARD_CHAIR_API_KEY,
    BOARD_CHAIR_BASE_URL,
    BOARD_CHAIR_MODEL,
    MODEL_CALL_DELAY_SECONDS,
    ONCOLOGIST_API_KEY,
    ONCOLOGIST_BASE_URL,
    ONCOLOGIST_MODEL,
    PATHOLOGIST_API_KEY,
    PATHOLOGIST_BASE_URL,
    PATHOLOGIST_MODEL,
)
import tumor_board.logger as logger
from tumor_board.llm import chat_completion
from tumor_board.prompts import BOARD_CHAIR_SYSTEM_PROMPT, ONCOLOGIST_SYSTEM_PROMPT, PATHOLOGIST_SYSTEM_PROMPT

_last_call: dict[str, float] = {}


def ask(
    agent_name: str,
    prompt: str,
    images: list[dict[str, Any]] | None = None,
    *,
    node: str = "",
) -> str:
    # throttle
    elapsed = time.monotonic() - _last_call.get(agent_name, 0.0)
    if elapsed < MODEL_CALL_DELAY_SECONDS:
        time.sleep(MODEL_CALL_DELAY_SECONDS - elapsed)

    if agent_name == "oncologist":
        model = ONCOLOGIST_MODEL
        t0 = time.monotonic()
        result = chat_completion(
            model=model,
            system_prompt=ONCOLOGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
            images=images or [],
            base_url=ONCOLOGIST_BASE_URL,
            api_key=ONCOLOGIST_API_KEY,
        )
    elif agent_name == "pathologist":
        model = PATHOLOGIST_MODEL
        t0 = time.monotonic()
        result = chat_completion(
            model=model,
            system_prompt=PATHOLOGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
            base_url=PATHOLOGIST_BASE_URL,
            api_key=PATHOLOGIST_API_KEY,
        )
    elif agent_name == "board_chair":
        model = BOARD_CHAIR_MODEL
        t0 = time.monotonic()
        result = chat_completion(
            model=model,
            system_prompt=BOARD_CHAIR_SYSTEM_PROMPT,
            user_prompt=prompt,
            base_url=BOARD_CHAIR_BASE_URL,
            api_key=BOARD_CHAIR_API_KEY,
        )
    else:
        raise ValueError(f"Unknown agent: {agent_name!r}")

    duration_s = time.monotonic() - t0
    _last_call[agent_name] = time.monotonic()

    logger.log_call(
        agent=agent_name,
        node=node or agent_name,
        model=model,
        response=result,
        duration_s=duration_s,
    )

    return result
