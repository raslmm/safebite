"""MongoDB persistence for a user's explicit allergy profile."""

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from safebite_agent.schemas import AllergenId, AllergenProfile

COLLECTION_NAME = "user_profiles"
CONSENT_VERSION = "allergy-profile-v1"


class ProfileStoreError(RuntimeError):
    """User-safe MongoDB profile storage error."""


@dataclass(frozen=True)
class StoredProfile:
    allergens: AllergenProfile
    preferred_language: str
    consented_at: datetime


def identity_key(issuer: str, subject: str) -> str:
    """Return a stable, pseudonymous key for one authentication issuer/subject pair."""
    issuer = issuer.strip()
    subject = subject.strip()
    if not issuer or not subject:
        raise ProfileStoreError("The login provider did not supply a stable user identity.")
    return sha256(f"{issuer}\0{subject}".encode()).hexdigest()


class MongoProfileStore:
    """Server-side profile repository scoped to an authenticated application identity."""

    def __init__(self, uri: str, database: str) -> None:
        if not uri.strip():
            raise ProfileStoreError("MONGODB_URI is not configured in app secrets.")
        if not database.strip():
            raise ProfileStoreError("MONGODB_DATABASE is not configured in app secrets.")
        try:
            self._client: MongoClient[dict[str, Any]] = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
            )
            self._profiles: Collection[dict[str, Any]] = self._client[database][COLLECTION_NAME]
        except PyMongoError:
            raise ProfileStoreError("Could not configure the MongoDB connection.") from None

    def ping(self) -> None:
        try:
            self._client.admin.command("ping")
        except PyMongoError:
            raise ProfileStoreError(
                "Could not connect to MongoDB. Check the URI, database user, and Atlas network access list."
            ) from None

    def load(self, user_key: str) -> StoredProfile | None:
        try:
            document = self._profiles.find_one({"_id": user_key})
        except PyMongoError:
            raise ProfileStoreError("Could not load the saved allergy profile.") from None

        if document is None:
            return None

        try:
            allergens = AllergenProfile(
                selected_allergens=[AllergenId(value) for value in document["allergens"]]
            )
            consented_at = document["consented_at"]
            if not isinstance(consented_at, datetime):
                raise TypeError("consent timestamp missing")
            language = str(document.get("preferred_language", "en"))
            if language not in {"en", "pt"}:
                raise ValueError("unsupported preferred language")
            return StoredProfile(
                allergens=allergens,
                preferred_language=language,
                consented_at=consented_at,
            )
        except (KeyError, TypeError, ValueError):
            raise ProfileStoreError(
                "The saved allergy profile is invalid. Delete it and create it again."
            ) from None

    def save(
        self,
        user_key: str,
        profile: AllergenProfile,
        preferred_language: str,
    ) -> None:
        if preferred_language not in {"en", "pt"}:
            raise ProfileStoreError("Preferred language must be English or Portuguese.")
        now = datetime.now(UTC)
        try:
            self._profiles.update_one(
                {"_id": user_key},
                {
                    "$set": {
                        "allergens": [item.value for item in profile.selected_allergens],
                        "preferred_language": preferred_language,
                        "consent_version": CONSENT_VERSION,
                        "consented_at": now,
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
        except PyMongoError:
            raise ProfileStoreError("Could not save the allergy profile.") from None

    def delete(self, user_key: str) -> None:
        try:
            self._profiles.delete_one({"_id": user_key})
        except PyMongoError:
            raise ProfileStoreError("Could not delete the saved allergy profile.") from None

    def close(self) -> None:
        self._client.close()
