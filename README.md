# SafeBite Agent

An agent that checks packaged-food labels against a user's selected allergens.

## Setup

Install uv, then run:

~~~powershell
uv sync --locked
Copy-Item .env.example .env
~~~

Set GOOGLE_API_KEY in the local .env file. Do not commit .env or put keys in source, notebooks, or documentation.

Check the Google connection with one short live request when a key is configured:

~~~powershell
uv run python hello_ai.py
~~~

Run the chat-only prototype:

~~~powershell
uv run streamlit run app.py
~~~
