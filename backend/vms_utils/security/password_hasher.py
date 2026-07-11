import base64
import hashlib
import hmac
import os


class PasswordHasher:
    """
    PBKDF2-HMAC password hashing.
    No plain-text password is stored.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120_000,
        )

        return (
            base64.urlsafe_b64encode(salt).decode("utf-8")
            + "."
            + base64.urlsafe_b64encode(digest).decode("utf-8")
        )

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt_text, digest_text = stored_hash.split(".", 1)

            salt = base64.urlsafe_b64decode(salt_text.encode("utf-8"))
            expected_digest = base64.urlsafe_b64decode(digest_text.encode("utf-8"))

            actual_digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                120_000,
            )

            return hmac.compare_digest(actual_digest, expected_digest)

        except Exception:
            return False