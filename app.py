"""Streamlit chat interface for the SafeBite typed-label prototype."""

from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st

from safebite_agent.agent import ask
from safebite_agent.allergen_reference import EU_ALLERGEN_CATALOG
from safebite_agent.config import MONGODB_DATABASE, MONGODB_URI
from safebite_agent.email_auth import AccountStoreError, EmailAccount, MongoAccountStore
from safebite_agent.profile_store import MongoProfileStore, ProfileStoreError, identity_key
from safebite_agent.schemas import AllergenProfile, LabelExtraction, RiskAssessment

_STATE_LABELS = {
    "risk_found": "Risk found",
    "possible_risk": "Possible risk",
    "no_match_found_in_readable_text": "No match found in readable text",
    "cannot_assess": "Cannot assess",
}
_ALLERGENS_BY_ID = {item.allergen_id: item for item in EU_ALLERGEN_CATALOG.allergens}
_LOGO_PATH = Path(__file__).resolve().parent / "assets" / "safebite-logo.png"


@st.cache_resource
def _profile_store() -> MongoProfileStore:
    store = MongoProfileStore(MONGODB_URI, MONGODB_DATABASE)
    store.ping()
    return store


@st.cache_resource
def _account_store() -> MongoAccountStore:
    return MongoAccountStore(MONGODB_URI, MONGODB_DATABASE)


def _email_login_callback() -> None:
    st.session_state.pop("_safebite_auth_error", None)
    try:
        account = _account_store().authenticate(
            st.session_state.get("login_email", ""),
            st.session_state.get("login_password", ""),
        )
        if account is None:
            st.session_state["_safebite_auth_error"] = (
                "Email or password is incorrect, or sign-in is temporarily locked."
            )
        else:
            st.session_state["_safebite_email_account_id"] = account.account_id
    except AccountStoreError as exc:
        st.session_state["_safebite_auth_error"] = str(exc)
    st.session_state["login_password"] = ""


def _email_register_callback() -> None:
    st.session_state.pop("_safebite_auth_error", None)
    email = st.session_state.get("register_email", "")
    password = st.session_state.get("register_password", "")
    password_confirm = st.session_state.get("register_password_confirm", "")
    if password != password_confirm:
        st.session_state["_safebite_auth_error"] = "The passwords do not match."
    else:
        try:
            account = _account_store().create_account(email, password)
            st.session_state["_safebite_email_account_id"] = account.account_id
        except AccountStoreError as exc:
            st.session_state["_safebite_auth_error"] = str(exc)
    st.session_state["register_password"] = ""
    st.session_state["register_password_confirm"] = ""


def _guest_login_callback() -> None:
    st.session_state.pop("_safebite_auth_error", None)
    st.session_state.pop("_safebite_email_account_id", None)
    st.session_state["_safebite_guest_id"] = uuid4().hex


def _render_login_page(auth_configured: bool) -> None:
    st.image(str(_LOGO_PATH), width=224)
    st.subheader("Sign in or create an account")
    st.caption(
        "Use the same sign-in method each time. Google and email/password accounts are separate."
    )
    if auth_error := st.session_state.pop("_safebite_auth_error", None):
        st.error(auth_error)

    google_tab, sign_in_tab, register_tab = st.tabs(
        ["Google", "Email sign-in", "Create account"]
    )
    with google_tab:
        st.write("Continue with Google. SafeBite does not receive or store your Google password.")
        if not auth_configured:
            st.info("Google sign-in is not configured yet. See docs/LOGIN_AND_MONGODB.md.")
        elif st.button("Continue with Google", type="primary", key="google_login"):
            st.login()

    with sign_in_tab, st.form("email_login_form"):
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_password")
        st.form_submit_button("Sign in", type="primary", on_click=_email_login_callback)

    with register_tab:
        st.caption(
            "Course prototype: email ownership is not verified and password reset is not configured. "
            "Use a demo password with at least 12 characters."
        )
        with st.form("email_register_form"):
            st.text_input("Email", key="register_email")
            st.text_input("Password", type="password", key="register_password")
            st.text_input(
                "Confirm password", type="password", key="register_password_confirm"
            )
            st.form_submit_button(
                "Create account", type="primary", on_click=_email_register_callback
            )

    st.divider()
    st.caption(
        "Guest mode does not create an account or save your profile. "
        "Your session data is cleared when the session ends."
    )
    st.button(
        "Continue as guest",
        use_container_width=True,
        on_click=_guest_login_callback,
    )


def _clear_session() -> None:
    st.session_state.pop("label_data", None)
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Your chat and label session have been cleared. Add a label when you are ready.",
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


st.set_page_config(
    page_title="SafeBite",
    page_icon=str(_LOGO_PATH),
    layout="wide",
)

try:
    auth_configured = bool(st.secrets.get("auth"))
except FileNotFoundError:
    auth_configured = False

google_logged_in = bool(getattr(st.user, "is_logged_in", False))
guest_id = st.session_state.get("_safebite_guest_id")
email_account: EmailAccount | None = None
email_account_id = st.session_state.get("_safebite_email_account_id")
if not guest_id and email_account_id:
    try:
        email_account = _account_store().get_account(str(email_account_id))
    except AccountStoreError as exc:
        st.error(str(exc))
        st.stop()
    if email_account is None:
        st.session_state.pop("_safebite_email_account_id", None)

if not guest_id and email_account is None and not google_logged_in:
    _render_login_page(auth_configured)
    st.stop()

if guest_id:
    user_key = f"guest:{guest_id}"
    user_email = "Guest"
    auth_method = "guest"
elif email_account is not None:
    user_key = identity_key("safebite-email-password", email_account.account_id)
    user_email = email_account.email
    auth_method = "email"
else:
    user_claims = st.user.to_dict()
    user_key = identity_key(str(user_claims.get("iss", "")), str(user_claims.get("sub", "")))
    user_email = str(user_claims.get("email", "signed in"))
    auth_method = "google"

stored_profile = None
store: MongoProfileStore | None = None
if auth_method != "guest":
    try:
        store = _profile_store()
        stored_profile = store.load(user_key)
    except ProfileStoreError as exc:
        st.error(str(exc))
        st.info("Check docs/LOGIN_AND_MONGODB.md for login and database setup.")
        st.stop()

if st.session_state.get("active_user_key") != user_key:
    st.session_state.active_user_key = user_key
    st.session_state.profile_widget = (
        [item.value for item in stored_profile.allergens.selected_allergens]
        if stored_profile else []
    )
    st.session_state.profile_language = stored_profile.preferred_language if stored_profile else "en"
    st.session_state.profile_consent = stored_profile is not None
    st.session_state.pop("label_data", None)
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Choose your allergens and add a label, then ask me to check it.",
    }]
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
    st.image(str(_LOGO_PATH), width=190)
    st.caption(f"Food-label screening · {user_email} · {auth_method}")
    signout_label = "Exit guest session" if auth_method == "guest" else "Sign out"
    if st.button(signout_label, use_container_width=True):
        st.session_state.clear()
        if auth_method == "google":
            st.logout()
            st.stop()
        else:
            st.rerun()

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
    st.selectbox(
        "Preferred language",
        options=["en", "pt"],
        format_func=lambda code: "English" if code == "en" else "Português",
        key="profile_language",
    )
    if auth_method == "guest":
        st.caption(
            "Guest mode: your allergy selections and label stay in this session only. "
            "They are not saved to an account or MongoDB."
        )
    else:
        st.checkbox(
            "I agree to save my allergy selections to my account for future sessions.",
            key="profile_consent",
            help="Allergy information is sensitive health data. Save only if you want this feature.",
        )
        if st.button("Save profile", type="primary", use_container_width=True):
            if not st.session_state.profile_consent:
                st.warning("Agree to profile storage before saving.")
            elif not selected_allergens:
                st.warning("Choose at least one allergen before saving.")
            else:
                try:
                    assert store is not None
                    store.save(
                        user_key,
                        AllergenProfile(selected_allergens=selected_allergens),
                        st.session_state.profile_language,
                    )
                    st.success("Allergy profile saved to your account.")
                except ProfileStoreError as exc:
                    st.error(str(exc))

        with st.expander("Delete saved profile"):
            st.caption("This permanently removes your saved allergy selections from the database.")
            confirm_delete = st.checkbox(
                "I understand this cannot be undone.", key="confirm_delete_profile"
            )
            if st.button(
                "Delete my saved profile", key="delete_profile", disabled=not confirm_delete
            ):
                try:
                    assert store is not None
                    store.delete(user_key)
                    st.session_state.profile_widget = []
                    st.session_state.profile_consent = False
                    st.session_state.confirm_delete_profile = False
                    st.success("Saved profile deleted.")
                    st.rerun()
                except ProfileStoreError as exc:
                    st.error(str(exc))

    st.divider()
    st.subheader("Label text")
    st.caption("Paste the complete ingredients section. Review it before saving; label text stays in this session.")

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
        "Chat and label text are sent to the configured Google model. Avoid identifying details. "
        "Only your allergy profile is saved when you opt in; label text stays session-only."
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
