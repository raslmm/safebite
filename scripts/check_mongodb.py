"""Check that configured MongoDB credentials can reach the selected cluster."""

from safebite_agent.config import MONGODB_DATABASE, MONGODB_URI
from safebite_agent.profile_store import MongoProfileStore, ProfileStoreError


def main() -> int:
    try:
        store = MongoProfileStore(MONGODB_URI, MONGODB_DATABASE)
        store.ping()
        store.close()
    except ProfileStoreError as exc:
        print(f"MongoDB connection failed: {exc}")
        return 1

    print("MongoDB connection OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
