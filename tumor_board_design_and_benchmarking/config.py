"""Centralized configuration for the tumor board.

Env vars are used only for external secrets and model specification.
Everything else is a hardcoded constant here.
"""

import os

from dotenv import load_dotenv

load_dotenv(override=True)

# External secrets (fail fast if missing)
OPENROUTER_API_KEY: str = os.environ["OPENROUTER_API_KEY"]
DOO_V1_API_KEY: str | None = os.getenv("DOO_V1_API_KEY")

# Fixed configuration
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
DIGITALOCEAN_INFERENCE_BASE_URL: str = "https://inference.do-ai.run/v1"

# Per-agent model + provider (env-overridable)
ONCOLOGIST_MODEL: str = os.getenv("ONCOLOGIST_MODEL", "qwen/qwen3-vl-32b-instruct")
ONCOLOGIST_BASE_URL: str = os.getenv("ONCOLOGIST_BASE_URL", OPENROUTER_BASE_URL)
ONCOLOGIST_API_KEY: str = os.getenv("ONCOLOGIST_API_KEY", OPENROUTER_API_KEY)

_pathologist_model = os.getenv("PATHOLOGIST_MODEL") or os.getenv("PATHOLOGIST_MODEL_DOO")
PATHOLOGIST_MODEL: str = _pathologist_model or "deepseek/deepseek-v3.2"
PATHOLOGIST_BASE_URL: str = os.getenv("PATHOLOGIST_BASE_URL", OPENROUTER_BASE_URL)
PATHOLOGIST_API_KEY: str = os.getenv(
    "PATHOLOGIST_API_KEY",
    DOO_V1_API_KEY or OPENROUTER_API_KEY,
)

# Board chair runs the consistency check. Defaults to the pathologist provider.
BOARD_CHAIR_MODEL: str = os.getenv("BOARD_CHAIR_MODEL", PATHOLOGIST_MODEL)
BOARD_CHAIR_BASE_URL: str = os.getenv("BOARD_CHAIR_BASE_URL", PATHOLOGIST_BASE_URL)
BOARD_CHAIR_API_KEY: str = os.getenv("BOARD_CHAIR_API_KEY", PATHOLOGIST_API_KEY)

MODEL_MAX_TOKENS: int = 2000
MODEL_TIMEOUT_SECONDS: float = 60.0
MODEL_MAX_RETRIES: int = 3
# Fallback retry delay when the server omits a Retry-After header.
MODEL_RETRY_DELAY_SECONDS: float = 5.0
# Inter-call delay (0 = no intentional throttling; adjust if needed).
MODEL_CALL_DELAY_SECONDS: float = 0.0

QUIET_PROGRESS: bool = False
