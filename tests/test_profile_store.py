from typing import Any

from safebite_agent import profile_store
from safebite_agent.profile_store import MongoProfileStore, ProfileStoreError, identity_key
from safebite_agent.schemas import AllergenId, AllergenProfile


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}

    def find_one(self, query: dict[str, str]) -> dict[str, Any] | None:
        return self.documents.get(query["_id"])

    def update_one(self, query: dict[str, str], update: dict[str, Any], upsert: bool) -> None:
        assert upsert
        document = self.documents.setdefault(query["_id"], {"_id": query["_id"]})
        document.update(update["$set"])
        for key, value in update["$setOnInsert"].items():
            document.setdefault(key, value)

    def delete_one(self, query: dict[str, str]) -> None:
        self.documents.pop(query["_id"], None)


class FakeDatabase:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection = collection

    def __getitem__(self, _name: str) -> FakeCollection:
        return self.collection


class FakeClient:
    def __init__(self, _uri: str, **_kwargs: Any) -> None:
        self.collection = FakeCollection()
        self.admin = self

    def __getitem__(self, _name: str) -> FakeDatabase:
        return FakeDatabase(self.collection)

    def command(self, _name: str) -> dict[str, int]:
        return {"ok": 1}

    def close(self) -> None:
        pass


def test_identity_key_is_stable_for_same_oidc_identity() -> None:
    assert identity_key("issuer", "subject") == identity_key("issuer", "subject")


def test_identity_key_separates_issuer_and_subject() -> None:
    base = identity_key("issuer-a", "subject-a")
    assert base != identity_key("issuer-b", "subject-a")
    assert base != identity_key("issuer-a", "subject-b")


def test_identity_key_rejects_missing_claims() -> None:
    try:
        identity_key("issuer", " ")
    except ProfileStoreError:
        pass
    else:
        raise AssertionError("Missing identity claims must not produce a database key.")


def test_profile_round_trip_and_delete_are_scoped_by_user(monkeypatch: Any) -> None:
    monkeypatch.setattr(profile_store, "MongoClient", FakeClient)
    store = MongoProfileStore("mongodb://fake", "safebite")
    user_a = identity_key("issuer", "user-a")
    user_b = identity_key("issuer", "user-b")
    profile = AllergenProfile(selected_allergens=[AllergenId.MILK, AllergenId.EGGS])

    store.save(user_a, profile, "pt")

    saved = store.load(user_a)
    assert saved is not None
    assert saved.allergens == profile
    assert saved.preferred_language == "pt"
    assert store.load(user_b) is None
    store.delete(user_a)
    assert store.load(user_a) is None
