"""One direct model call; useful for checking the provider connection."""

from safebite_agent.llm import SafeBiteModelError, first_hello


def main() -> int:
    try:
        reply = first_hello()
    except SafeBiteModelError as error:
        print(f"FAIL: {error}")
        return 1

    print(reply.text)
    print(f"Answered by: {reply.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
