"""One trace per request; this module alone imports the Langfuse SDK."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langfuse import get_client, propagate_attributes

from safebite_agent import config

_Client = Any
_Span = Any
_client: _Client | None = None


def setup() -> _Client | None:
    """Return the process client, or None when tracing credentials are not configured."""
    global _client
    if not config.TRACING_ENABLED:
        return None
    if _client is None:
        _client = get_client()
    return _client


def _maybe_content(value: str) -> str | None:
    return value if config.TRACE_CONTENT else None


@contextmanager
def agent_turn(message: str, session_id: str) -> Iterator[_Span | None]:
    """Open one root observation for a request, with a random conversation/session ID."""
    client = setup()
    if client is None:
        yield None
        return

    with (
        propagate_attributes(session_id=session_id),
        client.start_as_current_observation(
            as_type="agent",
            name="safebite_agent",
            input=_maybe_content(message),
        ) as span,
    ):
        yield span


@contextmanager
def model_call(model_name: str, prompt: str) -> Iterator[_Span | None]:
    """Open a generation span for one provider request."""
    client = setup()
    if client is None:
        yield None
        return

    with client.start_as_current_observation(
        as_type="generation",
        name="interactions.create",
        input=_maybe_content(prompt),
    ) as span:
        yield span


def model_result(
    span: _Span | None,
    actual_model: str,
    output: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    if span is None:
        return
    update: dict[str, Any] = {
        "model": actual_model,
        "usage_details": {"input": input_tokens, "output": output_tokens},
    }
    if config.TRACE_CONTENT:
        update["output"] = output
    span.update(**update)


def turn_result(span: _Span | None, outcome: str, output: str | None = None) -> None:
    if span is None:
        return
    update: dict[str, Any] = {"metadata": {"outcome": outcome}}
    if config.TRACE_CONTENT and output is not None:
        update["output"] = output
    span.update(**update)


def failed(span: _Span | None, error: Exception) -> None:
    if span is not None:
        span.update(level="ERROR", status_message=type(error).__name__)
