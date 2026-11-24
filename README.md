# SafeBite Agent

An agent that checks packaged-food labels against a user's selected allergens.

## Setup

Install uv, then run:

~~~powershell
uv sync --locked
Copy-Item .env.example .env
~~~

Set `GOOGLE_API_KEY`, `MONGODB_URI`, and `MONGODB_DATABASE` in the local `.env` file. Keep `.env` private. App settings are loaded from process environment/`.env` first, and use Streamlit Community Cloud secrets only when `SAFEBITE_USE_CLOUD_SECRETS = true` is set in Cloud Secrets.

Local Google OpenID Connect settings for `st.login()` belong in the ignored `.streamlit/secrets.toml` under `[auth]`. That file configures the login redirect and OIDC client; SafeBite does not use it as a fallback for model, database, or tracing settings. See [Local and Cloud Configuration](docs/CONFIGURATION.md) for setup details.

Streamlit Community Cloud does not receive the local `.env` or local `.streamlit/secrets.toml`. Add app settings and the deployed `[auth]` configuration to **App → Settings → Secrets**, then register the deployed `redirect_uri` with Google.

The app offers Google OIDC and a course-demo email/password option. Email/password accounts use Argon2id hashes in MongoDB; those accounts are separate from Google accounts, and email verification and password recovery are not implemented.

Check the Google connection with one short live request when a key is configured:

~~~powershell
uv run python hello_ai.py
~~~

Run the app:

~~~powershell
uv run streamlit run app.py
~~~
