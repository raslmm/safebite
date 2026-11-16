"""Streamlit chat interface for the SafeBite typed-label prototype."""

from typing import Any

import streamlit as st

from safebite_agent.agent import ask
from safebite_agent.allergen_reference import EU_ALLERGEN_CATALOG
from safebite_agent.schemas import AllergenProfile, LabelExtraction, RiskAssessment

_STATE_LABELS = {
    "risk_found": "Risk found",
    "possible_risk": "Possible risk",
    "no_match_found_in_readable_text": "No match found in readable text",
    "cannot_assess": "Cannot assess",
}
_ALLERGENS_BY_ID = {item.allergen_id: item for item in EU_ALLERGEN_CATALOG.allergens}


def _clear_session() -> None:
    st.session_state.profile_widget = []
    st.session_state.pop("label_data", None)
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Your session has been cleared. Choose allergens and add a label when you are ready.",
        }
    ]


def _show_assessment(data: dict[str, Any] | None) -> None:
    if data is None:
        return

    assessment = RiskAssessment.model_validate(data)
    state = assessment.state
    with st.container(border=True):
        if state == "risk_found":
            st.error(f"**{_STATE_LABELS[state]}**")
        elif state == "possible_risk":
            st.warning(f"**{_STATE_LABELS[state]}**")
        elif state == "cannot_assess":
            st.info(f"**{_STATE_LABELS[state]}**")
        else:
            st.info(f"**{_STATE_LABELS[state]}**")

        st.write(assessment.explanation)
        for evidence in assessment.evidence:
            allergen = _ALLERGENS_BY_ID[evidence.allergen_id]
            st.markdown(f"> {evidence.quote}")
            st.caption(
                f"{allergen.name_en} / {allergen.name_pt} · "
                f"{evidence.evidence_type.replace('_', ' ')} · "
                f"Annex II ({evidence.source_version})"
            )


def _save_label() -> None:
    ingredients = st.session_state.get("ingredients_input", "").strip()
    if not ingredients:
        st.session_state.label_error = "Enter the full ingredient list before saving the label."
        return

    extraction = LabelExtraction(
        language=st.session_state.label_language,
        ingredients_text=ingredients,
        contains_text=st.session_state.get("contains_input", "").strip() or None,
        may_contain_text=st.session_state.get("may_contain_input", "").strip() or None,
        is_complete=True,
        human_reviewed=True,
    )
    st.session_state.label_data = extraction.model_dump(mode="json")
    st.session_state.pop("label_error", None)


st.set_page_config(page_title="SafeBite", page_icon="🥗", layout="wide")
st.markdown(
    """<style>
    .block-container {max-width: 1120px; padding-top: 2rem; padding-bottom: 2rem;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.18);}
    </style>""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi, I’m SafeBite. Choose your allergens and add a label in the sidebar, "
                "then ask me to check it. I’ll show the checker’s result and supporting text here."
            ),
        }
    ]

with st.sidebar:
    st.title("🥗 SafeBite")
    st.caption("Food-label screening prototype")

    st.subheader("Your profile")
    selected_allergens = st.multiselect(
        "Select the allergens you want to check",
        options=list(_ALLERGENS_BY_ID),
        format_func=lambda allergen_id: (
            f"{_ALLERGENS_BY_ID[allergen_id].name_en} / {_ALLERGENS_BY_ID[allergen_id].name_pt}"
        ),
        key="profile_widget",
        placeholder="Choose one or more",
    )
    st.caption("This selection is kept in this session and used by the Python checker.")

    st.divider()
    st.subheader("Label text")
    st.caption("Paste the complete ingredients section. Review it before saving.")

    with st.form("label_form"):
        st.selectbox(
            "Label language",
            options=["en", "pt"],
            format_func=lambda code: "English" if code == "en" else "Português",
            key="label_language",
        )
        st.text_area(
            "Ingredients",
            key="ingredients_input",
            height=130,
            placeholder="e.g. wheat flour, milk powder, salt",
        )
        with st.expander("Add allergen statements (optional)"):
            st.text_input("Contains", key="contains_input", placeholder="e.g. milk")
            st.text_input(
                "May contain",
                key="may_contain_input",
                placeholder="e.g. peanuts",
            )
        st.form_submit_button("Save label", type="primary", on_click=_save_label)

    if st.session_state.get("label_error"):
        st.warning(st.session_state.label_error)
    elif st.session_state.get("label_data"):
        st.success("Label saved for this session.")

    with st.container(border=True):
        st.markdown("**📷 Photo scanner**")
        st.button(
            "Coming soon",
            disabled=True,
            use_container_width=True,
            help="Photo upload and label scanning are planned for an upcoming update.",
        )

    st.divider()
    st.caption(
        "Chat, pasted label text, and tool results are sent to the configured Google model. "
        "Avoid identifying information. Session data is not saved as account history."
    )
    st.button("Clear session", on_click=_clear_session, use_container_width=True)

st.title("Check a food label")
st.write(
    "Ask a question about the label you saved. The assessment comes from the deterministic checker."
)

profile_ready = bool(selected_allergens)
label_data = st.session_state.get("label_data")
label_ready = bool(label_data)

profile_col, label_col = st.columns(2)
with profile_col, st.container(border=True):
    st.markdown("**Active profile**")
    st.write(
        ", ".join(_ALLERGENS_BY_ID[item].name_en for item in selected_allergens)
        if profile_ready
        else "No allergens selected yet."
    )
with label_col, st.container(border=True):
    st.markdown("**Current label**")
    if label_ready:
        saved_label = LabelExtraction.model_validate(label_data)
        st.write(f"Saved · {saved_label.language.upper()} · ingredient text ready")
    else:
        st.write("No label saved yet.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        _show_assessment(message.get("assessment"))

prompt = st.chat_input("Ask SafeBite to check this label")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    assessment_data: dict[str, Any] | None = None
    if not profile_ready or not label_ready:
        response = (
            "Choose at least one allergen and save the complete label text in the sidebar first."
        )
    else:
        active_profile = AllergenProfile(selected_allergens=selected_allergens)
        active_label = LabelExtraction.model_validate(label_data)
        with st.spinner("Checking the label…"):
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
