"""The only module that imports Google's model SDK."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from google import genai
from google.genai import errors
from google.genai import interactions as gi

from safebite_agent import config, tracing


class SafeBiteModelError(RuntimeError):
    """A user-safe model or configuration failure."""


class MissingAPIKey(SafeBiteModelError):
    """No Google API key is configured."""


@dataclass(frozen=True)
class ModelReply:
    text: str
    model: str
    interaction_id: str
    status: str


@dataclass(frozen=True)
class FunctionCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelTurn:
    interaction_id: str
    status: str
    text: str
    function_calls: tuple[FunctionCall, ...] = ()


def _api_status(error: Exception) -> int | None:
    value = getattr(error, "status_code", None) or getattr(error, "code", None)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _is_connection_error(error: Exception) -> bool:
    name = type(error).__name__.lower()
    return (
        isinstance(error, (TimeoutError, ConnectionError))
        or "connection" in name
        or "timeout" in name
        or "connecterror" in name
    )


def _explain_api_error(error: Exception) -> SafeBiteModelError:
    status = _api_status(error)
    if status in (401, 403):
        return SafeBiteModelError(
            f"Google rejected the API key or its access ({status}). Check the key and project."
        )
    if status == 429:
        return SafeBiteModelError("Google rate limit or quota reached. Wait, then try again.")
    if status == 404:
        return SafeBiteModelError("The configured model was not found or is not available.")
    if status is not None and status >= 500:
        return SafeBiteModelError(f"Google's service returned {status}. Try again shortly.")
    if status is not None:
        return SafeBiteModelError(f"Google rejected the request ({status}). Check its settings.")
    return SafeBiteModelError("Could not reach Google. Check the network, then try again.")


class GoogleInteractionsModel:
    """Small provider adapter for one function-calling agent turn."""

    def __init__(self) -> None:
        if not config.GOOGLE_API_KEY:
            raise MissingAPIKey(
                "GOOGLE_API_KEY is missing. Copy .env.example to this repository's .env and add your key."
            )
        self._client = genai.Client(api_key=config.GOOGLE_API_KEY)

    def respond(
        self,
        *,
        message: str | None,
        previous_interaction_id: str | None,
        function_results: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_instruction: str,
    ) -> ModelTurn:
        """Send a user turn or tool results and return typed model function calls."""
        request_input: Any = message
        if function_results:
            request_input = [
                {
                    "type": "function_result",
                    "name": result["name"],
                    "call_id": result["call_id"],
                    "result": [{"type": "text", "text": result["result"]}],
                }
                for result in function_results
            ]

        try:
            interaction = self._client.interactions.create(
                model=config.MODEL,
                input=request_input,
                previous_interaction_id=previous_interaction_id,
                tools=tools,
                system_instruction=system_instruction,
            )
        except Exception as error:
            if isinstance(error, errors.APIError) or _is_connection_error(error):
                raise _explain_api_error(error) from None
            raise

        if not isinstance(interaction, gi.Interaction):
            raise SafeBiteModelError("Google returned an unexpected streaming response.")

        calls: list[FunctionCall] = []
        for step in interaction.steps or []:
            if getattr(step, "type", None) != "function_call":
                continue
            raw_arguments = getattr(step, "arguments", None)
            if isinstance(raw_arguments, Mapping):
                arguments = dict(raw_arguments)
            elif raw_arguments is not None and hasattr(raw_arguments, "model_dump"):
                arguments = raw_arguments.model_dump()
            else:
                arguments = {}
            calls.append(
                FunctionCall(
                    call_id=str(getattr(step, "id", "") or ""),
                    name=str(getattr(step, "name", "") or ""),
                    arguments=arguments,
                )
            )

        return ModelTurn(
            interaction_id=interaction.id or "",
            status=str(interaction.status or ""),
            text=(interaction.output_text or "").strip(),
            function_calls=tuple(calls),
        )


def first_hello() -> ModelReply:
    """Make one short Interactions API call and trace it"""
    if not config.GOOGLE_API_KEY:
        raise MissingAPIKey(
            "GOOGLE_API_KEY is missing. Copy .env.example to this repository's .env and add your key."
        )

    prompt = "Say hello in one short sentence."
    session_id = uuid4().hex
    tracing.setup()
    with tracing.agent_turn(prompt, session_id) as turn:
        generation = None
        try:
            client = genai.Client(api_key=config.GOOGLE_API_KEY)
            with tracing.model_call(config.MODEL, prompt) as generation:
                try:
                    interaction = client.interactions.create(
                        model=config.MODEL,
                        input=prompt,
                    )
                    if not isinstance(interaction, gi.Interaction):
                        raise SafeBiteModelError(
                            "Google returned an unexpected streaming response."
                        )
                except Exception as error:
                    tracing.failed(generation, error)
                    if (
                        isinstance(error, errors.APIError)
                        or _is_connection_error(error)
                        or _api_status(error) is not None
                    ):
                        raise _explain_api_error(error) from None
                    raise

                status = str(interaction.status or "")
                text = (interaction.output_text or "").strip()
                actual_model = interaction.model or config.MODEL
                usage = interaction.usage
                input_tokens = int(getattr(usage, "total_input_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "total_output_tokens", 0) or 0)
                output_tokens += int(getattr(usage, "total_thought_tokens", 0) or 0)

                tracing.model_result(generation, actual_model, text, input_tokens, output_tokens)

            if status != "completed":
                raise SafeBiteModelError(
                    f"The model did not complete its reply (status: {status or 'unknown'})."
                )
            if not text:
                raise SafeBiteModelError("The model returned an empty reply. Try again.")

            tracing.turn_result(turn, "answered", text)
            return ModelReply(
                text=text,
                model=actual_model,
                interaction_id=interaction.id or "",
                status=status,
            )
        except SafeBiteModelError as error:
            tracing.failed(turn, error)
            raise
        except (TimeoutError, ConnectionError) as error:
            tracing.failed(turn, error)
            raise SafeBiteModelError(
                "Could not reach Google. Check the network, then try again."
            ) from None
