import hashlib

from app.services import window_storage


def test_sha256_hex_matches_hashlib():
    data = b"entropia-window-payload"
    expected = hashlib.sha256(data).hexdigest()
    assert window_storage.sha256_hex(data) == expected


def test_sha256_hex_empty_string():
    assert window_storage.sha256_hex(b"") == hashlib.sha256(b"").hexdigest()


def test_sha256_hex_binary_deterministic():
    data = bytes(range(256))
    assert window_storage.sha256_hex(data) == window_storage.sha256_hex(data)
