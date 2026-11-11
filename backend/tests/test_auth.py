"""
tests/test_auth.py - Pengujian Autentikasi dan JWT
"""
import pytest
from app.auth import (
    verify_password,
    hash_password,
    create_access_token,
    decode_access_token,
    authenticate_user
)


def test_password_hashing():
    raw = "testpassword123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_token_creation_and_decoding():
    data = {"sub": "admin", "role": "super_admin"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "super_admin"


def test_authenticate_default_admin():
    user = authenticate_user("admin", "adminukk2026")
    assert user is not None
    assert user["username"] == "admin"
    assert user["role"] == "super_admin"

    failed = authenticate_user("admin", "wrong_password")
    assert failed is None
