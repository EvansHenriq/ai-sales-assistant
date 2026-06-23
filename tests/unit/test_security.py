from app.core.security import generate_api_key, hash_api_key, verify_api_key


def test_generate_api_key_is_random_and_long() -> None:
    first, second = generate_api_key(), generate_api_key()
    assert first != second
    assert len(first) >= 32


def test_hash_is_stable_and_hex() -> None:
    digest = hash_api_key("my-key")
    assert digest == hash_api_key("my-key")
    assert len(digest) == 64
    int(digest, 16)  # raises if not valid hex


def test_verify_api_key_matches_and_rejects() -> None:
    raw = generate_api_key()
    digest = hash_api_key(raw)
    assert verify_api_key(raw, digest) is True
    assert verify_api_key("wrong-key", digest) is False
