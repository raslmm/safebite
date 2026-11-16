# SafeBite Agent

An agent that checks packaged-food labels against a user's selected allergens.

## Setup

Install uv, then run:

~~~powershell
uv sync --locked
Copy-Item .env.example .env
~~~

Set GOOGLE_API_KEY in the local .env file. Do not commit .env or put keys in source, notebooks, or documentation.

Check the local environment without making an API request:

~~~powershell
uv run python check_setup.py
~~~

Make one short live request when a key is configured:

~~~powershell
uv run python check_setup.py --api
uv run python hello_ai.py
~~~