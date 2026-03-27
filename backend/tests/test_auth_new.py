"""
Tests for authentication utilities and the new /auth/* endpoints.

Covers:
- verify_password / get_password_hash
- create_access_token
- POST /auth/register
- POST /auth/token
- GET /auth/me
"""
import pytest
from datetime import timedelta

from backend.auth import verify_password, get_password_hash, create_access_token


# ---------------------------------------------------------------------------
# Unit tests – pure auth utility functions (no DB, no HTTP)
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_and_verify_roundtrip(self):
        """A hashed password can be verified with the original plain text."""
        plain = "SuperSecret42!"
        hashed = get_password_hash(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_wrong_password_rejected(self):
        """A different plain text does not match the hash."""
        hashed = get_password_hash("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_bcrypt(self):
        """Hash starts with the bcrypt prefix $2b$."""
        hashed = get_password_hash("password123")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


class TestCreateAccessToken:
    def test_token_is_string(self):
        """create_access_token returns a non-empty string."""
        token = create_access_token(data={"sub": "1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_with_custom_expiry(self):
        """Token is created successfully with a custom expiry delta."""
        token = create_access_token(
            data={"sub": "99"}, expires_delta=timedelta(minutes=5)
        )
        assert isinstance(token, str)

    def test_token_payload_roundtrip(self):
        """Decoded token contains the same ``sub`` value that was encoded."""
        from jose import jwt
        from backend.config import settings

        token = create_access_token(data={"sub": "42"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "42"


# ---------------------------------------------------------------------------
# Integration tests – HTTP endpoints (use in-memory SQLite via auth_client)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_new_user(test_client):
    """POST /auth/register creates a user and returns user data."""
    resp = await test_client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@auth.test",
            "password": "AlicePass1!",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == "alice@auth.test"
    assert data["username"] == "alice"
    assert "id" in data
    # Hashed password must NOT appear in the response
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(test_client):
    """Registering with an already-used e-mail returns 400."""
    payload = {
        "username": "bob",
        "email": "bob_dup@auth.test",
        "password": "BobPass1!",
    }
    first = await test_client.post("/auth/register", json=payload)
    assert first.status_code == 200

    second = await test_client.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert "already registered" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_returns_token(test_client):
    """POST /auth/token returns a bearer token for valid credentials."""
    # Register first
    await test_client.post(
        "/auth/register",
        json={
            "username": "carol",
            "email": "carol@auth.test",
            "password": "CarolPass1!",
        },
    )

    resp = await test_client.post(
        "/auth/token",
        data={"username": "carol@auth.test", "password": "CarolPass1!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "expires_at" in body


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(test_client):
    """POST /auth/token with wrong password returns 401."""
    await test_client.post(
        "/auth/register",
        json={
            "username": "dan",
            "email": "dan@auth.test",
            "password": "DanPass1!",
        },
    )

    resp = await test_client.post(
        "/auth/token",
        data={"username": "dan@auth.test", "password": "wrong!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user_rejected(test_client):
    """POST /auth/token for an unknown e-mail returns 401."""
    resp = await test_client.post(
        "/auth/token",
        data={"username": "nobody@auth.test", "password": "anything"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(auth_client):
    """GET /auth/me returns the current user's profile when authenticated."""
    resp = await auth_client.get("/auth/me")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "id" in data
    assert "email" in data
    assert "username" in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(test_client):
    """GET /auth/me without a token returns 401."""
    resp = await test_client.get("/auth/me")
    assert resp.status_code == 401
