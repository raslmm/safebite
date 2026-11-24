"""Streamlit chat interface for the SafeBite typed-label prototype."""

import base64
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
_WORDMARK_PATH = Path(__file__).resolve().parent / "assets" / "safebite-wordmark.png"
_GOOGLE_ICON_PATH = Path(__file__).resolve().parent / "assets" / "google-g.svg"


@st.cache_resource(show_spinner=False)
def _profile_store() -> MongoProfileStore:
    store = MongoProfileStore(MONGODB_URI, MONGODB_DATABASE)
    store.ping()
    return store


@st.cache_resource(show_spinner=False)
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


def _auth_styles() -> None:
    google_icon_data = base64.b64encode(_GOOGLE_ICON_PATH.read_bytes()).decode("ascii")
    st.markdown(
        """<style>
        [data-testid="stAppViewContainer"] {
            --auth-bg: #f4f6fa;
            --auth-surface: #ffffff;
            --auth-text: #282d38;
            --auth-muted: #687486;
            --auth-border: #e1e6ee;
            --auth-input: #ffffff;
            --auth-input-text: #303642;
            --auth-input-border: #d8dde6;
            --auth-shadow: rgba(24, 39, 75, .08);
            background:
                radial-gradient(circle at 12% 18%, rgba(56, 121, 248, .10), transparent 23rem),
                radial-gradient(circle at 88% 84%, rgba(45, 170, 115, .10), transparent 25rem),
                var(--auth-bg);
            color: var(--auth-text);
        }
        @media (prefers-color-scheme: dark) {
            [data-testid="stAppViewContainer"] {
                --auth-bg: #0b1118;
                --auth-surface: #151d27;
                --auth-text: #eef3f8;
                --auth-muted: #a7b2c1;
                --auth-border: #2b394a;
                --auth-input: #0f1720;
                --auth-input-text: #edf3fa;
                --auth-input-border: #344355;
                --auth-shadow: rgba(0, 0, 0, .34);
                background:
                    radial-gradient(circle at 12% 18%, rgba(56, 121, 248, .16), transparent 23rem),
                    radial-gradient(circle at 88% 84%, rgba(45, 170, 115, .12), transparent 25rem),
                    var(--auth-bg);
                color: var(--auth-text);
            }
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stImage"] { display: flex; justify-content: center; }
        [data-testid="stImage"] img { margin-left: auto; margin-right: auto; }
        .main .block-container {
            max-width: 1100px;
            padding-top: 3.5rem;
            padding-bottom: 4rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--auth-surface);
            border: 1px solid var(--auth-border);
            border-radius: 14px;
            box-shadow: 0 16px 42px var(--auth-shadow);
        }
        .main .block-container,
        .main .block-container p,
        .main .block-container label,
        .main .block-container [data-testid="stMarkdownContainer"] {
            color: var(--auth-text);
        }
        .main .block-container [data-testid="stCaptionContainer"] {
            color: var(--auth-muted);
        }
        [data-testid="stTextInput"] input {
            min-height: 2.7rem;
            border-radius: 7px;
            background: var(--auth-input);
            color: var(--auth-input-text);
            border-color: var(--auth-input-border);
        }
        [data-testid="stTextInput"] input::placeholder {
            color: var(--auth-muted);
            opacity: 1;
        }
        [data-testid="stTextInput"] label { color: var(--auth-muted); }
        [data-testid="stFormSubmitButton"] button[kind="primary"],
        div.stButton > button[kind="primary"] {
            min-height: 2.8rem;
            border-radius: 7px;
            background: #3978f6;
            border-color: #3978f6;
            color: #ffffff;
            font-weight: 600;
        }
        [data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
        div.stButton > button[kind="primary"]:hover {
            background: #2867e5;
            border-color: #2867e5;
        }
        div.stButton > button[kind="secondary"] {
            min-height: 2.7rem;
            border-radius: 7px;
            background: var(--auth-surface);
            border-color: var(--auth-input-border);
            color: var(--auth-text);
        }
        div.stButton > button[kind="tertiary"] {
            color: var(--auth-muted);
        }
        .st-key-google_login button [data-testid="stMarkdownContainer"] {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: .6rem;
        }
        .st-key-google_login button [data-testid="stMarkdownContainer"] p { margin: 0; }
        .st-key-google_login button [data-testid="stMarkdownContainer"]::before {
            content: "";
            display: inline-block;
            width: 19px;
            height: 19px;
            flex: 0 0 19px;
            background: center / contain no-repeat url("__GOOGLE_ICON__");
        }
        .auth-eyebrow {
            color: var(--auth-muted);
            font-size: .9rem;
            margin-bottom: .1rem;
        }
        .auth-title {
            color: var(--auth-text);
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -.035em;
            line-height: 1.2;
            margin: 0 0 1.4rem 0;
        }
        .auth-muted { color: var(--auth-muted); font-size: .9rem; }
        .landing-copy {
            max-width: 660px;
            margin: .5rem auto 1.6rem auto;
            color: var(--auth-muted);
            font-size: 1.15rem;
            line-height: 1.65;
            text-align: center;
        }
        .landing-eyebrow {
            color: #3978f6;
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .16em;
            text-align: center;
            margin-top: 0.6rem;
        }
        </style>""".replace("__GOOGLE_ICON__", f"data:image/svg+xml;base64,{google_icon_data}"),
        unsafe_allow_html=True,
    )


def _auth_error() -> None:
    if auth_error := st.session_state.pop("_safebite_auth_error", None):
        st.error(auth_error)


def _render_centered_wordmark(width: int = 340) -> None:
    image_data = base64.b64encode(_WORDMARK_PATH.read_bytes()).decode("ascii")
    st.markdown(
        f'<div style="width:100%;display:flex;justify-content:center;align-items:center">'
        f'<img src="data:image/png;base64,{image_data}" alt="SafeBite" '
        f'style="display:block;width:min({width}px,100%);height:auto;margin:0 auto"></div>',
        unsafe_allow_html=True,
    )


def _render_landing_page() -> None:
    _auth_styles()
    st.markdown(
        """<style>
        .main .block-container {
            min-height: calc(100vh - 5rem);
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    _, center, _ = st.columns([1, 2, 1])
    with center:
        _render_centered_wordmark()
        st.markdown(
            '<div class="landing-eyebrow">FOOD LABELS, MADE CLEAR</div>', unsafe_allow_html=True
        )
        st.markdown(
            '<div class="landing-copy">Check packaged-food labels against your allergy profile, '
            "with clear evidence and results.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Get started", type="primary", use_container_width=True, key="landing_start"):
            st.session_state["_safebite_auth_view"] = "login"
            st.rerun()
        st.markdown(
            '<p class="auth-muted" style="text-align:center;margin-top:1rem">'
            "Save your information by logging in, or continue as guest!</p>",
            unsafe_allow_html=True,
        )


def _render_login_page(auth_configured: bool) -> None:
    _auth_styles()
    _, center, _ = st.columns([1.1, 1.35, 1.1])
    with center, st.container(border=True):
        st.markdown(
            '<div class="auth-eyebrow">Please enter your details</div>', unsafe_allow_html=True
        )
        st.markdown('<div class="auth-title">Welcome back</div>', unsafe_allow_html=True)
        _auth_error()
        if st.session_state.pop("_safebite_forgot_notice", False):
            st.info(
                "Sorry, but we don't really do that... :/"
                "Try Google sign-in or contact the app administrator."
            )

        with st.form("email_login_form"):
            st.text_input(
                "Email address",
                key="login_email",
                placeholder="Email address",
                label_visibility="collapsed",
            )
            st.text_input(
                "Password",
                type="password",
                key="login_password",
                placeholder="Password",
                label_visibility="collapsed",
            )
            st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
                on_click=_email_login_callback,
            )

        _, forgot_col = st.columns([1.3, 1])
        with forgot_col:
            if st.button("Forgot password?", key="forgot_password", type="tertiary"):
                st.session_state["_safebite_forgot_notice"] = True
                st.rerun()

        st.markdown(
            '<div class="auth-muted" style="text-align:center;margin:.6rem 0">or</div>',
            unsafe_allow_html=True,
        )
        if not auth_configured:
            st.info("Google sign-in is not configured yet.")
        elif st.button("Sign in with Google", use_container_width=True, key="google_login"):
            st.login()

        st.markdown(
            '<div class="auth-muted" style="text-align:center;margin-top:1.1rem">'
            "Don’t have an account?</div>",
            unsafe_allow_html=True,
        )
        if st.button("Sign up", use_container_width=True, key="show_signup"):
            st.session_state["_safebite_auth_view"] = "signup"
            st.session_state.pop("_safebite_auth_error", None)
            st.rerun()

        if st.button("Continue as guest", use_container_width=True, key="guest_login"):
            _guest_login_callback()
            st.rerun()


def _render_signup_page() -> None:
    _auth_styles()
    _, center, _ = st.columns([1.1, 1.35, 1.1])
    with center, st.container(border=True):
        st.markdown(
            '<div class="auth-eyebrow">Create your SafeBite account</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="auth-title">Sign up</div>', unsafe_allow_html=True)
        _auth_error()
        st.caption("Use a password with at least 6 characters.")
        with st.form("email_register_form"):
            st.text_input(
                "Email address",
                key="register_email",
                placeholder="Email address",
                label_visibility="collapsed",
            )
            st.text_input(
                "Password",
                type="password",
                key="register_password",
                placeholder="Password",
                label_visibility="collapsed",
            )
            st.text_input(
                "Confirm password",
                type="password",
                key="register_password_confirm",
                placeholder="Confirm password",
                label_visibility="collapsed",
            )
            st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
                on_click=_email_register_callback,
            )
        st.caption("Don't worry, we won't be asking you to verify email ownership :)")
        if st.button("Back to sign in", key="back_to_login", type="tertiary"):
            st.session_state["_safebite_auth_view"] = "login"
            st.session_state.pop("_safebite_auth_error", None)
            st.rerun()


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
    auth_view = st.session_state.setdefault("_safebite_auth_view", "landing")
    if auth_view == "landing":
        _render_landing_page()
    elif auth_view == "signup":
        _render_signup_page()
    else:
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
        if stored_profile
        else []
    )
    st.session_state.profile_language = (
        stored_profile.preferred_language if stored_profile else "en"
    )
    st.session_state.profile_consent = stored_profile is not None
    st.session_state.pop("label_data", None)
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Choose your allergens and add a label, then ask me to check it.",
        }
    ]
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
    st.image(str(_WORDMARK_PATH), width=190)
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
    st.caption(
        "Paste the complete ingredients section. Review it before saving; label text stays in this session."
    )

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
