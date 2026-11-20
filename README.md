# SafeBite Agent

An agent that checks packaged-food labels against a user's selected allergens.

## Setup

Install uv, then run:

~~~powershell
uv sync --locked
Copy-Item .env.example .env
~~~

Set GOOGLE_API_KEY in the local .env file. Do not commit .env or put keys in source, notebooks, or documentation.

To configure sign-in and persistent allergy profiles, follow [Login and MongoDB setup](docs/LOGIN_AND_MONGODB.md). Local Google OIDC credentials belong in the ignored `.streamlit/secrets.toml`; MongoDB and model keys can be in the ignored `.env` or Streamlit secrets. Never commit either secrets file.

Streamlit Community Cloud does not receive the ignored local `.env`. The app reads MongoDB and model settings from **App → Settings → Secrets** when environment variables are absent. Google sign-in also needs the `[auth]` table in those Cloud secrets, with the deployed `redirect_uri`.

The app offers Google OIDC and a course-demo email/password option. Email/password accounts use Argon2id hashes in MongoDB; those accounts are separate from Google accounts, and email verification and password recovery are not implemented.

Check the Google connection with one short live request when a key is configured:

~~~powershell
uv run python hello_ai.py
~~~

Run the app:

~~~powershell
uv run streamlit run app.py
~~~
