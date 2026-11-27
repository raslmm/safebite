"""MongoDB persistence for a user's explicit allergy profile."""

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from safebite_agent.schemas import AllergenId, AllergenProfile

COLLECTION_NAME = "user_profiles"
SCANNED_GOODS_COLLECTION_NAME = "user_scanned_goods"
CONSENT_VERSION = "allergy-profile-v1"


class ProfileStoreError(RuntimeError):
    """User-safe MongoDB profile storage error."""


@dataclass(frozen=True)
class StoredProfile:
    allergens: AllergenProfile
    preferred_language: str
    consented_at: datetime


@dataclass(frozen=True)
class StoredGood:
    good_id: str
    name: str
    product_code: str
    ingredients_text: str
    contains_text: str
    may_contain_text: str
    language: str
    source: str
    saved_at: datetime


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
            self._goods: Collection[dict[str, Any]] = self._client[database][
                SCANNED_GOODS_COLLECTION_NAME
            ]
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

    def list_scanned_goods(self, user_key: str) -> list[StoredGood]:
        """Return a user's saved product summaries, newest first."""
        try:
            documents = list(
                self._goods.find({"user_key": user_key}).sort("saved_at", -1).limit(100)
            )
        except PyMongoError:
            raise ProfileStoreError("Could not load your previously scanned goods.") from None
        try:
            return [
                StoredGood(
                    good_id=str(document["_id"]),
                    name=str(document.get("name", "Scanned product")),
                    product_code=str(document.get("product_code", "")),
                    ingredients_text=str(document.get("ingredients_text", "")),
                    contains_text=str(document.get("contains_text", "")),
                    may_contain_text=str(document.get("may_contain_text", "")),
                    language=str(document.get("language", "en")),
                    source=str(document.get("source", "photo")),
                    saved_at=document["saved_at"],
                )
                for document in documents
                if isinstance(document.get("saved_at"), datetime)
            ]
        except (KeyError, TypeError, ValueError):
            raise ProfileStoreError("A saved product record is invalid.") from None

    def save_scanned_good(
        self,
        user_key: str,
        *,
        name: str,
        product_code: str,
        ingredients_text: str,
        contains_text: str,
        may_contain_text: str,
        language: str,
        source: str,
    ) -> None:
        """Save reviewed label text, not the uploaded image, to one user's history."""
        now = datetime.now(UTC)
        code = product_code.strip()
        good_id = sha256(f"{user_key}\0{code}".encode()).hexdigest() if code else uuid4().hex
        try:
            self._goods.update_one(
                {"_id": good_id, "user_key": user_key},
                {
                    "$set": {
                        "user_key": user_key,
                        "name": name.strip() or "Scanned product",
                        "product_code": code,
                        "ingredients_text": ingredients_text,
                        "contains_text": contains_text,
                        "may_contain_text": may_contain_text,
                        "language": language,
                        "source": source,
                        "saved_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
        except PyMongoError:
            raise ProfileStoreError("Could not save this scanned good to your profile.") from None

    def delete_scanned_good(self, user_key: str, good_id: str) -> None:
        try:
            self._goods.delete_one({"_id": good_id, "user_key": user_key})
        except PyMongoError:
            raise ProfileStoreError("Could not remove this scanned good.") from None

    def close(self) -> None:
        self._client.close()
