import io

import pytest

from auth.security import hash_password
from db.models import User, UserRole
from tests.conftest import TestSessionFactory
from unittest.mock import Mock


async def create_officer_and_token(
    client,
    badge_id: str,
    password: str = "officerpass123",
):
    async with TestSessionFactory() as session:
        officer = User(
            name="Test Officer",
            badge_id=badge_id,
            role=UserRole.OFFICER,
            password_hash=hash_password(password),
        )

        session.add(officer)
        await session.commit()

    response = await client.post(
        "/auth/login",
        json={
            "badge_id": badge_id,
            "password": password,
        },
    )

    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_session_requires_auth(
    client,
):
    response = await client.post(
        "/sessions",
        json={},
    )

    assert response.status_code in (
        401,
        403,
    )


@pytest.mark.asyncio
async def test_create_session_success(
    client,
    unique_badge_id,
):
    token = await create_officer_and_token(
        client,
        unique_badge_id,
    )

    response = await client.post(
        "/sessions",
        json={
            "traveler_ref_id": "TRAV-001"
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body[
        "traveler_ref_id"
    ] == "TRAV-001"

    assert body[
        "status"
    ] == "pending"


@pytest.mark.asyncio
async def test_upload_document_success(
    client,
    unique_badge_id,
    sample_jpeg_bytes,
    monkeypatch,
):
    token = await create_officer_and_token(
        client,
        unique_badge_id,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    session_resp = await client.post(
        "/sessions",
        json={},
        headers=headers,
    )

    session_id = session_resp.json()[
        "id"
    ]

    mock_delay = Mock()

    monkeypatch.setattr(
        "api.documents.process_document.delay",
        mock_delay,
    )

    files = {
        "file": (
            "passport.jpg",
            io.BytesIO(
                sample_jpeg_bytes
            ),
            "image/jpeg",
        )
    }

    response = await client.post(
        f"/sessions/{session_id}/documents?doc_type=passport",
        files=files,
        headers=headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body[
        "doc_type"
    ] == "passport"

    assert body[
        "session_id"
    ] == session_id

    assert (
        "sessions/"
        in body["file_path"]
    )

    mock_delay.assert_called_once_with(
        body["id"],
        str(session_id),
    )


@pytest.mark.asyncio
async def test_upload_document_rejects_bad_content_type(
    client,
    unique_badge_id,
    monkeypatch,
):
    token = await create_officer_and_token(
        client,
        unique_badge_id,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    session_resp = await client.post(
        "/sessions",
        json={},
        headers=headers,
    )

    session_id = session_resp.json()[
        "id"
    ]

    mock_delay = Mock()

    monkeypatch.setattr(
        "api.documents.process_document.delay",
        mock_delay,
    )

    files = {
        "file": (
            "notes.txt",
            io.BytesIO(
                b"just some text"
            ),
            "text/plain",
        )
    }

    response = await client.post(
        f"/sessions/{session_id}/documents?doc_type=passport",
        files=files,
        headers=headers,
    )

    assert response.status_code == 400

    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_upload_document_session_not_found(
    client,
    unique_badge_id,
    sample_jpeg_bytes,
    monkeypatch,
):
    token = await create_officer_and_token(
        client,
        unique_badge_id,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    fake_session_id = (
        "00000000-0000-0000-0000-000000000000"
    )

    mock_delay = Mock()

    monkeypatch.setattr(
        "api.documents.process_document.delay",
        mock_delay,
    )

    files = {
        "file": (
            "passport.jpg",
            io.BytesIO(
                sample_jpeg_bytes
            ),
            "image/jpeg",
        )
    }

    response = await client.post(
        f"/sessions/{fake_session_id}/documents?doc_type=passport",
        files=files,
        headers=headers,
    )

    assert response.status_code == 404

    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_list_documents(
    client,
    unique_badge_id,
    sample_jpeg_bytes,
    monkeypatch,
):
    token = await create_officer_and_token(
        client,
        unique_badge_id,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    session_resp = await client.post(
        "/sessions",
        json={},
        headers=headers,
    )

    session_id = session_resp.json()[
        "id"
    ]

    mock_delay = Mock()

    monkeypatch.setattr(
        "api.documents.process_document.delay",
        mock_delay,
    )

    files = {
        "file": (
            "passport.jpg",
            io.BytesIO(
                sample_jpeg_bytes
            ),
            "image/jpeg",
        )
    }

    upload_response = await client.post(
        f"/sessions/{session_id}/documents?doc_type=passport",
        files=files,
        headers=headers,
    )

    assert upload_response.status_code == 201

    response = await client.get(
        f"/sessions/{session_id}/documents",
        headers=headers,
    )

    assert response.status_code == 200

    docs = response.json()

    assert len(docs) == 1

    assert docs[0][
        "doc_type"
    ] == "passport"

    assert docs[0][
        "view_url"
    ].startswith(
        "http"
    )

    mock_delay.assert_called_once()