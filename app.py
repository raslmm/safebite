"""Chat-only Streamlit interface for the SafeBite prototype."""

import re
from typing import Any

import streamlit as st

from safebite_agent.agent import ask
from safebite_agent.allergen_reference import EU_ALLERGEN_CATALOG
from safebite_agent.schemas import AllergenId, AllergenProfile, LabelExtraction, RiskAssessment

_WELCOME = """Welcome to the SafeBite prototype.

Set your profile with `/profile peanuts, milk` (English or Portuguese names work), then paste the
full ingredient list with `/label en: sugar, milk powder`. You can include statements with pipes:
`/label en: sugar, cocoa | contains: milk | may contain: peanuts`. Use `pt` for Portuguese.

Then ask me to check the label. Use `/reset` to clear the session profile and label. This prototype
does not determine whether a product is safe. Chat text, label text, and tool results are sent to the
configured Google model; do not include identifying information.
"""

_STATE_LABELS = {
    "risk_found": "Risk found",
    "possible_risk": "Possible risk",
    "no_match_found_in_readable_text": "No match found in readable text",
    "cannot_assess": "Cannot assess",
}


def _profile_aliases() -> dict[str, AllergenId]:
    aliases: dict[str, AllergenId] = {}
    for item in EU_ALLERGEN_CATALOG.allergens:
        values = (
            item.allergen_id.value,
            item.name_en,
            item.name_pt,
            *item.match_terms_en,
            *item.match_terms_pt,
        )
        for value in values:
            aliases[value.casefold().strip()] = item.allergen_id
    return aliases


def _set_profile(command: str) -> str:
    raw = command[len("/profile") :].strip()
    if raw.casefold() in ("clear", "none"):
        st.session_state.pop("profile_ids", None)
        return "Your allergen profile was cleared for this session."

    aliases = _profile_aliases()
    selected: list[AllergenId] = []
    unknown: list[str] = []
    for part in raw.split(","):
        name = part.strip().casefold()
        if not name:
            continue
        allergen_id = aliases.get(name)
        if allergen_id is None:
            unknown.append(part.strip())
        elif allergen_id not in selected:
            selected.append(allergen_id)

    if unknown or not selected:
        return "I couldn't set that profile. Use comma-separated names such as `/profile peanuts, milk`."

    st.session_state.profile_ids = [item.value for item in selected]
    return f"Saved {len(selected)} selected allergen group(s) for this session."


def _parse_label(command: str) -> LabelExtraction | None:
    match = re.match(r"^/label\s+(pt|en)\s*:\s*(.+)$", command, re.IGNORECASE | re.DOTALL)
    if match is None:
        return None

    language = match.group(1).lower()
    parts = [part.strip() for part in match.group(2).split("|")]
    ingredients: list[str] = []
    contains: list[str] = []
    may_contain: list[str] = []

    for index, part in enumerate(parts):
        section = re.match(
            r"^(contains|contém|may\s+contain|pode\s+conter)\s*:\s*(.*)$",
            part,
            re.IGNORECASE,
        )
        if index == 0 and section is None:
            ingredients.append(part)
        elif section is not None:
            section_name = re.sub(r"\s+", " ", section.group(1).casefold())
            target = may_contain if section_name in ("may contain", "pode conter") else contains
            target.append(section.group(2).strip())
        elif part:
            ingredients.append(part)

    ingredient_text = " | ".join(ingredients).strip()
    if not ingredient_text:
        return None

    extraction = LabelExtraction(
        language=language,  # type: ignore[arg-type]
        ingredients_text=ingredient_text,
        contains_text=" | ".join(contains) or None,
        may_contain_text=" | ".join(may_contain) or None,
        is_complete=True,
        human_reviewed=True,
    )
    st.session_state.label_data = extraction.model_dump(mode="json")
    return extraction


def _show_assessment(data: dict[str, Any] | None) -> None:
    if data is None:
        return
    assessment = RiskAssessment.model_validate(data)
    st.markdown(f"**Assessment: {_STATE_LABELS[assessment.state]}**")
    st.write(assessment.explanation)
    for item in assessment.evidence:
        st.markdown(f"> {item.quote}")
        st.caption(
            f"{item.allergen_id.value} · {item.evidence_type.replace('_', ' ')} · "
            f"{item.source_id} ({item.source_version})"
        )


st.set_page_config(page_title="SafeBite", page_icon="🥗")
st.title("SafeBite")
st.caption("Chat-only prototype · session data is cleared when this session ends")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": _WELCOME}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        _show_assessment(message.get("assessment"))

prompt = st.chat_input("Set a profile, paste a label, or ask a question")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    assessment_data: dict[str, Any] | None = None
    if prompt.strip().casefold().startswith("/profile"):
        response = _set_profile(prompt.strip())
    elif prompt.strip().casefold().startswith("/label"):
        label = _parse_label(prompt.strip())
        response = (
            "Saved the label text for this session. Ask me to check it against your profile."
            if label is not None
            else "Use `/label en: full ingredient list` or `/label pt: lista completa de ingredientes`."
        )
    elif prompt.strip().casefold() == "/reset":
        st.session_state.pop("profile_ids", None)
        st.session_state.pop("label_data", None)
        response = "Cleared the profile and label from this session."
    elif not st.session_state.get("profile_ids") or not st.session_state.get("label_data"):
        response = "First set a profile with `/profile ...` and paste a full label with `/label en: ...` or `/label pt: ...`."
    else:
        active_profile = AllergenProfile(
            selected_allergens=[AllergenId(value) for value in st.session_state.profile_ids]
        )
        active_label = LabelExtraction.model_validate(st.session_state.label_data)
        turn = ask(prompt, active_profile, active_label)
        response = turn.answer
        if turn.assessment is not None:
            assessment_data = turn.assessment.model_dump(mode="json")

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "assessment": assessment_data}
    )
    with st.chat_message("assistant"):
        st.markdown(response)
        _show_assessment(assessment_data)
