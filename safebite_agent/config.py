"""Project settings; the only module that reads environment variables/secrets.

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


def _setting(name: str, default: str = "") -> str:
    """Read process/.env settings, then explicitly enabled Community Cloud secrets.

    Local ``.streamlit/secrets.toml`` is reserved for Streamlit's OIDC ``[auth]``
    configuration. App/API settings must come from ``.env`` locally or from the
    Community Cloud secret store after its opt-in switch has been set.
    """
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        import streamlit as st

        secrets: Any = st.secrets
    except FileNotFoundError:
        return default

    cloud_fallback_enabled = str(
        secrets.get("SAFEBITE_USE_CLOUD_SECRETS", "")
    ).strip().lower() == "true"
    if not cloud_fallback_enabled:
        return default
    return str(secrets.get(name, default)).strip()


GOOGLE_API_KEY = _setting("GOOGLE_API_KEY")
MODEL = _setting("MODEL") or "gemini-3.5-flash-lite"

LANGFUSE_PUBLIC_KEY = _setting("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = _setting("LANGFUSE_SECRET_KEY")
LANGFUSE_BASE_URL = (
    _setting("LANGFUSE_BASE_URL", "https://cloud.langfuse.com") or "https://cloud.langfuse.com"
)
TRACING_ENABLED = (
    bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)
    and _setting("LANGFUSE_TRACING_ENABLED", "true").lower() != "false"
)
TRACE_CONTENT = _setting("TRACE_CONTENT", "false").lower() == "true"

MONGODB_URI = _setting("MONGODB_URI")
MONGODB_DATABASE = _setting("MONGODB_DATABASE", "safebite") or "safebite"
