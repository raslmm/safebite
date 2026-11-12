"""Project settings; the only module that reads environment variables.

GOOGLE_API_KEY: Google GenAI key; required for live model requests.
MODEL: optional Google model ID; defaults to gemini-3.5-flash-lite.
LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY: optional tracing credentials.
LANGFUSE_BASE_URL: Langfuse server; defaults to the EU Cloud endpoint.
LANGFUSE_TRACING_ENABLED: disable remote tracing with "false".
TRACE_CONTENT: record input/output content only when explicitly enabled.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE, override=False)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
MODEL = os.getenv("MODEL", "").strip() or "gemini-3.5-flash-lite"

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
LANGFUSE_BASE_URL = (
    os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").strip()
    or "https://cloud.langfuse.com"
)
TRACING_ENABLED = (
    bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)
    and os.getenv("LANGFUSE_TRACING_ENABLED", "true").strip().lower() != "false"
)
TRACE_CONTENT = os.getenv("TRACE_CONTENT", "false").strip().lower() == "true"
