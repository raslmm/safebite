"""Offline tests for the SafeBite tool gateway and bounded agent loop."""

from typing import Any

from safebite_agent.agent import ask
from safebite_agent.llm import FunctionCall, ModelTurn
from safebite_agent.schemas import AllergenId, AllergenProfile, LabelExtraction
from safebite_agent.tools import TOOL_DECLARATIONS, run_tool


def sample_profile() -> AllergenProfile:
    return AllergenProfile(selected_allergens=[AllergenId.PEANUTS])


def sample_label() -> LabelExtraction:
    return LabelExtraction(language="en", ingredients_text="Sugar, peanuts", is_complete=True)


class ScriptedModel:
    def __init__(self, *responses: ModelTurn) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def respond(self, **request: Any) -> ModelTurn:
        self.requests.append(request)
        return self.responses.pop(0)


def test_gateway_runs_only_registered_tool_and_uses_active_profile() -> None:
    result = run_tool(
        "check_label", {}, active_profile=sample_profile(), reviewed_label=sample_label()
    )

    assert result.outcome == "ok"
    assert result.assessment is not None
    assert result.assessment.state == "risk_found"


def test_gateway_rejects_extra_model_arguments() -> None:
    result = run_tool(
        "check_label",
        {"selected_allergens": ["milk"], "ingredients_text": "milk"},
        active_profile=sample_profile(),
        reviewed_label=sample_label(),
    )

    assert result.outcome == "error"
    assert result.assessment is None


def test_gateway_rejects_unknown_tool() -> None:
    result = run_tool(
        "delete_scan", {}, active_profile=sample_profile(), reviewed_label=sample_label()
    )

    assert result.outcome == "error"
    assert result.assessment is None


def test_tool_schema_has_no_model_controlled_arguments() -> None:
    declaration = TOOL_DECLARATIONS[0]

    assert declaration["name"] == "check_label"
    assert declaration["parameters"]["properties"] == {}
    assert declaration["parameters"]["additionalProperties"] is False


def test_agent_runs_checker_then_returns_model_answer_and_assessment() -> None:
    model = ScriptedModel(
        ModelTurn(
            interaction_id="interaction-1",
            status="requires_action",
            text="",
            function_calls=(FunctionCall("call-1", "check_label", {}),),
        ),
        ModelTurn(
            interaction_id="interaction-2",
            status="completed",
            text="The label lists peanuts, which match your selected allergen.",
        ),
    )

    turn = ask("Check this label", sample_profile(), sample_label(), model=model)

    assert turn.outcome == "answered"
    assert turn.answer.startswith("The label lists peanuts")
    assert turn.assessment is not None
    assert turn.assessment.state == "risk_found"
    assert len(turn.tool_results) == 1
    assert model.requests[0]["message"] is not None
    assert model.requests[1]["previous_interaction_id"] == "interaction-1"
    assert model.requests[1]["function_results"][0]["call_id"] == "call-1"


def test_agent_caps_repeated_tool_calls() -> None:
    call_response = ModelTurn(
        interaction_id="interaction",
        status="requires_action",
        text="",
        function_calls=(FunctionCall("call", "check_label", {}),),
    )
    model = ScriptedModel(call_response, call_response, call_response)

    turn = ask("Check this label", sample_profile(), sample_label(), model=model, max_rounds=2)

    assert turn.outcome == "round_limit"
    assert len(turn.tool_results) == 2
    assert len(model.requests) == 2
