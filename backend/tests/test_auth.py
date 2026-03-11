"""Tests for user registration, authentication, and session management."""
from httpx import AsyncClient

from app.auth import hash_password, verify_password


# --- Password hashing unit tests ---

def test_hash_password_produces_salt_and_hash():
    result = hash_password("mypassword")
    assert "$" in result
    salt, h = result.split("$", 1)
    assert len(salt) == 32  # 16 bytes hex
    assert len(h) == 64  # sha256 hex


def test_verify_password_correct():
    stored = hash_password("secret123")
    assert verify_password("secret123", stored) is True


def test_verify_password_wrong():
    stored = hash_password("secret123")
    assert verify_password("wrong", stored) is False


def test_verify_password_invalid_hash():
    assert verify_password("anything", "nope") is False


def test_different_hashes_for_same_password():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # Different salts


# --- Registration endpoint tests ---

async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/register", json={"username": "newuser", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "newuser"
    assert "session" in resp.cookies


async def test_register_creates_board(client: AsyncClient):
    resp = await client.post("/api/register", json={"username": "boarduser", "password": "password123"})
    cookies = dict(resp.cookies)
    board_resp = await client.get("/api/board", cookies=cookies)
    assert board_resp.status_code == 200
    data = board_resp.json()
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 8


async def test_register_duplicate_username(client: AsyncClient):
    await client.post("/api/register", json={"username": "dupuser", "password": "password123"})
    resp = await client.post("/api/register", json={"username": "dupuser", "password": "password456"})
    assert resp.status_code == 409


async def test_register_short_username(client: AsyncClient):
    resp = await client.post("/api/register", json={"username": "ab", "password": "password123"})
    assert resp.status_code == 400


async def test_register_invalid_username_chars(client: AsyncClient):
    resp = await client.post("/api/register", json={"username": "bad user!", "password": "password123"})
    assert resp.status_code == 400


async def test_register_short_password(client: AsyncClient):
    resp = await client.post("/api/register", json={"username": "gooduser", "password": "short"})
    assert resp.status_code == 400


async def test_register_then_login(client: AsyncClient):
    await client.post("/api/register", json={"username": "logintest", "password": "mypassword1"})
    resp = await client.post("/api/login", json={"username": "logintest", "password": "mypassword1"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "logintest"


async def test_register_then_login_wrong_password(client: AsyncClient):
    await client.post("/api/register", json={"username": "logintest2", "password": "mypassword1"})
    resp = await client.post("/api/login", json={"username": "logintest2", "password": "wrongpass1"})
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/login", json={"username": "nonexistent", "password": "password123"})
    assert resp.status_code == 401


async def test_session_persists_after_login(client: AsyncClient):
    reg = await client.post("/api/register", json={"username": "sessuser", "password": "password123"})
    cookies = dict(reg.cookies)
    me = await client.get("/api/me", cookies=cookies)
    assert me.status_code == 200
    assert me.json()["username"] == "sessuser"


async def test_logout_invalidates_session(client: AsyncClient):
    reg = await client.post("/api/register", json={"username": "logouttest", "password": "password123"})
    cookies = dict(reg.cookies)
    await client.post("/api/logout", cookies=cookies)
    me = await client.get("/api/me", cookies=cookies)
    assert me.status_code == 401
