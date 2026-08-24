import pytest
from sqlalchemy import select

from auth.security import hash_password
from db.models import User, UserRole
from tests.conftest import TestSessionFactory


async def create_admin_user(
    badge_id: str, password: str = "adminpass123"
):
    async with TestSessionFactory() as session:
        admin = User(
            name="Test Admin",
            badge_id=badge_id,
            role=UserRole.ADMIN,
            password_hash=hash_password(password),
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin


async def get_admin_token(
    client, badge_id: str, password: str = "adminpass123"
):
    response = await client.post(
        "/auth/login",
        json={
            "badge_id": badge_id,
            "password": password,
        },
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_register_requires_admin(client, unique_badge_id):
    # No token at all -> should be rejected
    response = await client.post(
        "/auth/register",
        json={
            "name": "New Officer",
            "badge_id": unique_badge_id,
            "password": "somepass123",
            "role": "officer",
        },
    )

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_register_success_as_admin(client, unique_badge_id):
    admin_badge = unique_badge_id + "-admin"

    await create_admin_user(admin_badge)
    token = await get_admin_token(client, admin_badge)

    response = await client.post(
        "/auth/register",
        json={
            "name": "New Officer",
            "badge_id": unique_badge_id,
            "password": "somepass123",
            "role": "officer",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    body = response.json()

    assert body["badge_id"] == unique_badge_id
    assert body["role"] == "officer"
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_rejects_non_admin(client, unique_badge_id):
    async with TestSessionFactory() as session:
        officer = User(
            name="Regular Officer",
            badge_id=unique_badge_id + "-officer",
            role=UserRole.OFFICER,
            password_hash=hash_password("pass123"),
        )

        session.add(officer)
        await session.commit()

    login_resp = await client.post(
        "/auth/login",
        json={
            "badge_id": unique_badge_id + "-officer",
            "password": "pass123",
        },
    )

    token = login_resp.json()["access_token"]

    response = await client.post(
        "/auth/register",
        json={
            "name": "Sneaky New User",
            "badge_id": unique_badge_id + "-new",
            "password": "pass123",
            "role": "officer",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login_success(client, unique_badge_id):
    await create_admin_user(unique_badge_id)

    response = await client.post(
        "/auth/login",
        json={
            "badge_id": unique_badge_id,
            "password": "adminpass123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, unique_badge_id):
    await create_admin_user(unique_badge_id)

    response = await client.post(
        "/auth/login",
        json={
            "badge_id": unique_badge_id,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/auth/login",
        json={
            "badge_id": "does-not-exist",
            "password": "whatever",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client, unique_badge_id):
    await create_admin_user(unique_badge_id)

    token = await get_admin_token(client, unique_badge_id)

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["badge_id"] == unique_badge_id


@pytest.mark.asyncio
async def test_me_without_token(client):
    response = await client.get("/auth/me")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_with_invalid_token(client):
    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer garbage.invalid.token"
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(client, unique_badge_id):
    await create_admin_user(unique_badge_id)

    login_resp = await client.post(
        "/auth/login",
        json={
            "badge_id": unique_badge_id,
            "password": "adminpass123",
        },
    )

    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client, unique_badge_id):
    await create_admin_user(unique_badge_id)

    access_token = await get_admin_token(
        client,
        unique_badge_id,
    )

    # Using an access token where a refresh token is expected should fail
    response = await client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token
        },
    )

    assert response.status_code == 401