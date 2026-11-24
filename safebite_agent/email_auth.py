"""MongoDB-backed email/password accounts for the SafeBite course prototype."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

ACCOUNT_COLLECTION = "user_accounts"
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128
MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION = timedelta(minutes=15)
_PASSWORD_HASHER = PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1)
_DUMMY_PASSWORD_HASH = _PASSWORD_HASHER.hash("SafeBite dummy hash for timing equalization")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccountStoreError(RuntimeError):
    """Safe message for an account operation that could not complete."""


@dataclass(frozen=True)
class EmailAccount:
    account_id: str
    email: str


class MongoAccountStore:
    """Store account identifiers and Argon2id hashes; never store passwords."""

    def __init__(self, uri: str, database: str) -> None:
        if not uri.strip():
            raise AccountStoreError("MONGODB_URI is not configured.")
        if not database.strip():
            raise AccountStoreError("MONGODB_DATABASE is not configured.")
        try:
            self._client: MongoClient[dict[str, Any]] = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
            )
            self._accounts: Collection[dict[str, Any]] = self._client[database][ACCOUNT_COLLECTION]
            self._accounts.create_index(
                [("email_normalized", ASCENDING)],
                unique=True,
                name="unique_email_normalized",
            )
        except PyMongoError:
            raise AccountStoreError("Could not configure the MongoDB account collection.") from None

    @staticmethod
    def _normalize_email(email: str) -> str:
        normalized = email.strip().casefold()
        if len(normalized) > 254 or not _EMAIL_PATTERN.fullmatch(normalized):
            raise AccountStoreError("Enter a valid email address.")
        return normalized

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AccountStoreError("Use a password with at least 6 characters.")
        if len(password) > MAX_PASSWORD_LENGTH:
            raise AccountStoreError("Password must be 128 characters or fewer.")

    def ping(self) -> None:
        try:
            self._client.admin.command("ping")
        except PyMongoError:
            raise AccountStoreError("Could not connect to MongoDB.") from None

    def create_account(self, email: str, password: str) -> EmailAccount:
        normalized = self._normalize_email(email)
        self._validate_password(password)
        now = datetime.now(UTC)
        document = {
            "email_normalized": normalized,
            "email": email.strip(),
            "password_hash": _PASSWORD_HASHER.hash(password),
            "created_at": now,
            "failed_logins": 0,
            "locked_until": None,
        }
        try:
            result = self._accounts.insert_one(document)
        except DuplicateKeyError:
            raise AccountStoreError(
                "An account may already exist for this email. Try signing in instead."
            ) from None
        except PyMongoError:
            raise AccountStoreError("Could not create the account in MongoDB.") from None
        return EmailAccount(str(result.inserted_id), str(document["email"]))

    def authenticate(self, email: str, password: str) -> EmailAccount | None:
        try:
            normalized = self._normalize_email(email)
        except AccountStoreError:
            normalized = email.strip().casefold()[:254]

        try:
            account = self._accounts.find_one({"email_normalized": normalized})
        except PyMongoError:
            raise AccountStoreError("Could not check the account in MongoDB.") from None

        if account is None:
            self._burn_password_check(password)
            return None

        now = datetime.now(UTC)
        locked_until = account.get("locked_until")
        if isinstance(locked_until, datetime):
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=UTC)
            if locked_until > now:
                self._burn_password_check(password)
                return None

        try:
            _PASSWORD_HASHER.verify(str(account["password_hash"]), password)
        except (VerificationError, InvalidHashError, ValueError, TypeError):
            self._record_failed_login(account, now)
            return None

        try:
            self._accounts.update_one(
                {"_id": account["_id"]},
                {"$set": {"failed_logins": 0, "locked_until": None}},
            )
        except PyMongoError:
            raise AccountStoreError("Could not update the account login state.") from None
        return EmailAccount(str(account["_id"]), str(account["email"]))

    def get_account(self, account_id: str) -> EmailAccount | None:
        if not ObjectId.is_valid(account_id):
            return None
        try:
            account = self._accounts.find_one({"_id": ObjectId(account_id)})
        except PyMongoError:
            raise AccountStoreError("Could not load the signed-in account.") from None
        if account is None:
            return None
        return EmailAccount(str(account["_id"]), str(account["email"]))

    def close(self) -> None:
        self._client.close()

    def _record_failed_login(self, account: dict[str, Any], now: datetime) -> None:
        previous_lock = account.get("locked_until")
        reset_expired_lock = False
        if isinstance(previous_lock, datetime):
            if previous_lock.tzinfo is None:
                previous_lock = previous_lock.replace(tzinfo=UTC)
            if previous_lock <= now:
                account["failed_logins"] = 0
                reset_expired_lock = True
        failed_logins = int(account.get("failed_logins", 0)) + 1
        update: dict[str, Any] = {"failed_logins": failed_logins}
        if reset_expired_lock:
            update["locked_until"] = None
        if failed_logins >= MAX_FAILED_LOGINS:
            update["locked_until"] = now + LOCKOUT_DURATION
        try:
            self._accounts.update_one({"_id": account["_id"]}, {"$set": update})
        except PyMongoError:
            raise AccountStoreError("Could not update the account login state.") from None

    @staticmethod
    def _burn_password_check(password: str) -> None:
        try:
            _PASSWORD_HASHER.verify(_DUMMY_PASSWORD_HASH, password[:MAX_PASSWORD_LENGTH])
        except (VerificationError, InvalidHashError, ValueError, TypeError):
            pass
