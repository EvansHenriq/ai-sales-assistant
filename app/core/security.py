"""API-key generation, hashing and verification.

API keys are high-entropy random tokens (256 bits), so a fast cryptographic
hash (SHA-256) is the right choice for storage — unlike low-entropy user
passwords, they do not need a slow KDF (bcrypt/argon2). Only the hash is stored;
the raw key is shown to the operator once at creation time.
"""

import hashlib
import hmac
import secrets

# Number of random bytes behind a generated key (urlsafe-encoded).
_KEY_BYTES = 32


def generate_api_key() -> str:
    """Return a new random, URL-safe API key."""
    return secrets.token_urlsafe(_KEY_BYTES)


def hash_api_key(raw_key: str) -> str:
    """Return the hex SHA-256 digest of an API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    """Constant-time comparison of a raw key against a stored hash."""
    return hmac.compare_digest(hash_api_key(raw_key), key_hash)
