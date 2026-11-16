"""Tool declarations and the single Python dispatch gateway."""

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from safebite_agent.allergen_checker import check_label
from safebite_agent.schemas import (
    AllergenProfile,
    LabelExtraction,
    RiskState,
    ToolResult,
)

CHECK_LABEL_NAME = "check_label"


class CheckLabelArguments(BaseModel):
    """This tool takes no model-controlled data; app state supplies profile and label."""

    model_config = ConfigDict(extra="forbid")


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": CHECK_LABEL_NAME,
        "description": (
            "Check the active user's reviewed label text against their selected allergens. "
            "Call this when the user asks whether the provided label matches their profile. "
            "The application supplies the profile and label; do not request or invent arguments."
        ),
        "parameters": CheckLabelArguments.model_json_schema(),
    }
]

TOOL_HANDLERS: dict[str, type[BaseModel]] = {CHECK_LABEL_NAME: CheckLabelArguments}


def run_tool(
    name: str,
    arguments: Any,
    *,
    active_profile: AllergenProfile,
    reviewed_label: LabelExtraction,
) -> ToolResult:
    """Validate and dispatch one model-requested tool through the allowlisted gateway."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return ToolResult(outcome="error", message="That tool is not available.")

    try:
        handler.model_validate(arguments)
    except (TypeError, ValueError, ValidationError):
        return ToolResult(outcome="error", message="The tool request had invalid arguments.")

    assessment = check_label(active_profile, reviewed_label)
    outcome: RiskState = assessment.state
    return ToolResult(
        outcome="needs_input" if outcome == "cannot_assess" else "ok",
        message=assessment.explanation,
        assessment=assessment,
    )
