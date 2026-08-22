"""Security unit tests that do not require a database connection."""
from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing_and_jwt_round_trip():
    password_hash = hash_password("DemoPass!123")
    assert password_hash != "DemoPass!123"
    assert verify_password("DemoPass!123", password_hash)
    token = create_access_token("507f1f77bcf86cd799439011", "patient")
    payload = decode_access_token(token)
    assert payload["sub"] == "507f1f77bcf86cd799439011"
    assert payload["role"] == "patient"
