# Tool Contract: `check_label`

## Purpose

Compare the active user's selected EU allergen groups with label text they supplied and reviewed.
Python performs the comparison and returns a `RiskAssessment`; the model does not choose or alter
its risk state.

## Model-facing schema

`check_label` accepts an empty JSON object. It has no model-controlled arguments. The application
provides the active profile and reviewed label to the Python tool gateway, so the model cannot
change the profile or replace the text being checked.

## Python input and result

- Input: `AllergenProfile` and `LabelExtraction`, held by the current app turn.
- Validation: `CheckLabelArguments` rejects extra or malformed arguments; `run_tool` only dispatches
  registered names.
- Result: `ToolResult` contains an outcome, user-safe message, and optional deterministic assessment
  with evidence, source ID, and reference version.
- Unavailable tools and invalid arguments return an error result; they never produce a risk state.

## Safety behavior

- The profile is supplied by application code, not model arguments.
- Label text is untrusted data and is included in the agent context as quoted label content.
- Incomplete, unsupported, or unreviewed uncertain input cannot be assessed.
- “May contain”, unresolved terms, unknown sulphite quantity, and exception phrases stay possible
  risks or require review.
- A no-match result must retain the caveat that it is not a safety guarantee.

## Example call

```json
{
  "name": "check_label",
  "arguments": {}
}
```
