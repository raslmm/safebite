<p align="center">
  <img src="assets/safebite-wordmark.png" alt="SafeBite" width="300">
</p>

<p align="center"><strong>A cautious food-label assistant for your allergy profile.</strong></p>

<p align="center">Check packaged-food ingredients and allergen warnings, with clear evidence behind each result.</p>
<p align="center">
  <a href="https://safebite-ai.streamlit.app/">Open the live app</a>
<br/> <br/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"></a>
</p>

## What it does so far

- Check ingredient and label text against the 14 EU allergen groups, both in English or Portuguese.
- Show a cautious result with matching label evidence.
- Sign in with Google or email/password, or try the app as a guest.
- Optionally save an allergy profile to your account.

Photo scanning and barcode lookup are not available yet. A “no match” result is not a guarantee that a product is safe; always verify the package.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

Main packages: Streamlit and its auth extra for the app and Google sign-in, `pymongo` for MongoDB, `google-genai` for Gemini, and `argon2-cffi` for password hashing. Optional Langfuse tracing uses `langfuse`. Exact versions and transitive dependencies are recorded in `pyproject.toml` and `uv.lock`.

## Set up locally

Open a terminal in this folder and create the project virtual environment. `uv sync` installs the locked dependencies into `.venv`.

```powershell
uv venv --python 3.12
uv sync --locked
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Activate the environment if you want to run Python commands directly:

```powershell
.\.venv\Scripts\Activate.ps1
```


Edit `.env` and add the settings you use. The setup command only copies the example when `.env` is absent, so it won't overwrite an existing local configuration.

```dotenv
GOOGLE_API_KEY=your_google_genai_key
MONGODB_URI=mongodb+srv://username:password@cluster/...
MONGODB_DATABASE=safebite
```

`MONGODB_URI` must include the database username and password. URL-encode special characters in the password. Keep `.env` private and out of Git.

For local Google sign-in, create `.streamlit/secrets.toml` with your Google OAuth client settings. Its `[auth]` section is for Streamlit sign-in; model and database settings belong in `.env`.

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Add the same local callback URL to the OAuth client's authorized redirect URIs. The `secrets.toml` file is local-only and ignored by Git.

## Run

```powershell
uv run streamlit run app.py
```

Optional checks:

```powershell
uv run python hello_ai.py
uv run python scripts/check_mongodb.py
uv run pytest
```

## Streamlit Community Cloud

Add your app settings in **App → Settings → Secrets**. Set the fallback switch so SafeBite reads those values when the Cloud environment has no process environment value:

```toml
SAFEBITE_USE_CLOUD_SECRETS = true
GOOGLE_API_KEY = "your_google_genai_key"
MONGODB_URI = "mongodb+srv://username:password@cluster/..."
MONGODB_DATABASE = "safebite"

[auth]
redirect_uri = "https://your-app-name.streamlit.app/oauth2callback"
cookie_secret = "a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Replace the example values. Register the deployed callback URL exactly as shown in the Google OAuth client. Cloud Secrets are separate from local `.env` and `.streamlit/secrets.toml` files.

## Notes

- Email/password accounts require MongoDB, use a six-character minimum password, and are separate from Google accounts. Email verification and password reset are not configured.
- Allergy profiles are saved only after the user opts in. Pasted label text stays in the current session.
- Product data and model output can be incomplete. SafeBite is not medical advice and does not replace checking the physical package.
- See [safety and data handling](docs/SAFETY.md) and the [tool contract](docs/TOOLS.md).

## License

[MIT](LICENSE)
