"""
Tests for Step 8 tampering API.

Covers:
- authenticated endpoint access
- document not found
- unsupported file extension
- ELA + metadata persistence
- repeat call replaces previous basic-analysis rows
"""

import uuid

import pytest
from sqlalchemy import select

from auth.security import hash_password
from db.models import (
    Document,
    DocType,
    ScreeningSession,
    TamperingResult,
    TamperingTechnique,
    User,
    UserRole,
)
from tests.conftest import TestSessionFactory


TEST_PASSWORD = "testpass123"


async def _seed_officer_and_session(db):
    officer = User(
        id=uuid.uuid4(),
        name="Tampering Test Officer",
        badge_id=f"TAMP-{uuid.uuid4().hex[:8]}",
        role=UserRole.OFFICER,
        password_hash=hash_password(TEST_PASSWORD),
    )

    db.add(officer)
    await db.flush()

    screening_session = ScreeningSession(
        id=uuid.uuid4(),
        officer_id=officer.id,
    )

    db.add(screening_session)
    await db.flush()

    return screening_session.id, officer.badge_id


async def _auth_headers(client, badge_id):
    response = await client.post(
        "/auth/login",
        json={
            "badge_id": badge_id,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def _make_document(
    session_id,
    file_path="documents/test.jpg",
):
    return Document(
        id=uuid.uuid4(),
        session_id=session_id,
        file_path=file_path,
        doc_type=DocType.PASSPORT,
    )


@pytest.mark.asyncio
async def test_tampering_endpoint_requires_authentication(client):
    document_id = uuid.uuid4()

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampering_endpoint_document_not_found_404(client):
    async with TestSessionFactory() as db:
        _, badge_id = await _seed_officer_and_session(db)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/documents/{uuid.uuid4()}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tampering_rejects_unsupported_file_type(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id,
            file_path="documents/test.pdf",
        )

        db.add(document)
        await db.commit()

        document_id = document.id

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 400
    assert "supports JPG" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tampering_endpoint_creates_ela_and_metadata_rows(
    client,
    monkeypatch,
):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id,
            file_path="documents/test.jpg",
        )

        db.add(document)
        await db.commit()

        document_id = document.id

    headers = await _auth_headers(
        client,
        badge_id,
    )

    def fake_download_file(
        object_name,
        destination_path,
    ):
        with open(
            destination_path,
            "wb",
        ) as file:
            file.write(b"fake-image-data")

        return destination_path

    def fake_ela(_image_path):
        return {
            "score": 0.42,
            "heatmap_path": "tampering/ela/test.png",
            "details": {
                "mean_difference": 4.2,
                "std_difference": 9.1,
                "max_difference": 45.0,
                "hotspot_ratio": 0.03,
            },
        }

    def fake_metadata(_image_path):
        return {
            "score": 0.60,
            "flags": [
                "Editing software detected: Adobe Photoshop"
            ],
            "metadata": {
                "Software": "Adobe Photoshop"
            },
            "image": {
                "width": 800,
                "height": 500,
                "dpi": [300, 300],
                "format": "JPEG",
            },
        }

    monkeypatch.setattr(
        "api.tampering.download_file",
        fake_download_file,
    )

    monkeypatch.setattr(
        "api.tampering.error_level_analysis",
        fake_ela,
    )

    monkeypatch.setattr(
        "api.tampering.metadata_forensics",
        fake_metadata,
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert len(data) == 2

    techniques = {
        row["technique"]
        for row in data
    }

    assert techniques == {
        "ela",
        "metadata",
    }

    async with TestSessionFactory() as db:
        result = await db.execute(
            select(TamperingResult).where(
                TamperingResult.document_id
                == document_id
            )
        )

        rows = result.scalars().all()

    assert len(rows) == 2

    rows_by_technique = {
        row.technique: row
        for row in rows
    }

    ela_row = rows_by_technique[
        TamperingTechnique.ELA
    ]

    metadata_row = rows_by_technique[
        TamperingTechnique.METADATA
    ]

    assert ela_row.suspicious_score == 0.42
    assert ela_row.heatmap_path == (
        "tampering/ela/test.png"
    )

    assert metadata_row.suspicious_score == 0.60
    assert metadata_row.heatmap_path is None

    assert (
        "Editing software detected"
        in metadata_row.details["flags"][0]
    )


@pytest.mark.asyncio
async def test_repeated_tampering_call_replaces_old_basic_rows(
    client,
    monkeypatch,
):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id
        )

        db.add(document)
        await db.commit()

        document_id = document.id

    headers = await _auth_headers(
        client,
        badge_id,
    )

    def fake_download_file(
        object_name,
        destination_path,
    ):
        with open(
            destination_path,
            "wb",
        ) as file:
            file.write(b"fake-image-data")

        return destination_path

    monkeypatch.setattr(
        "api.tampering.download_file",
        fake_download_file,
    )

    monkeypatch.setattr(
        "api.tampering.error_level_analysis",
        lambda _path: {
            "score": 0.20,
            "heatmap_path": "tampering/ela/repeat.png",
            "details": {
                "mean_difference": 2.0,
                "std_difference": 4.0,
                "max_difference": 20.0,
                "hotspot_ratio": 0.01,
            },
        },
    )

    monkeypatch.setattr(
        "api.tampering.metadata_forensics",
        lambda _path: {
            "score": 0.10,
            "flags": [],
            "metadata": {},
            "image": {
                "width": 800,
                "height": 500,
                "dpi": None,
                "format": "JPEG",
            },
        },
    )

    first_response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert second_response.status_code == 201

    async with TestSessionFactory() as db:
        result = await db.execute(
            select(TamperingResult).where(
                TamperingResult.document_id
                == document_id
            )
        )

        rows = result.scalars().all()

    assert len(rows) == 2

    techniques = {
        row.technique
        for row in rows
    }

    assert techniques == {
        TamperingTechnique.ELA,
        TamperingTechnique.METADATA,
    }