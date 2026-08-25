"""
Tests for Step 9 advanced tampering API.

Covers:
- authentication
- document not found
- unsupported file extension
- ELA persistence
- metadata persistence
- CNN persistence
- photo-swap persistence
- aggregate score persistence
- repeated call replaces previous rows
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


def _patch_tampering_services(monkeypatch):
    """
    Patch tampering functions where they are now used:
    services.tampering_analysis_service
    """

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
        "services.tampering_analysis_service.download_file",
        fake_download_file,
    )

    monkeypatch.setattr(
        "services.tampering_analysis_service.error_level_analysis",
        lambda _path: {
            "score": 0.40,
            "heatmap_path": "tampering/ela/test.png",
            "details": {
                "mean_difference": 4.0,
                "std_difference": 8.0,
                "max_difference": 40.0,
                "hotspot_ratio": 0.03,
            },
        },
    )

    monkeypatch.setattr(
        "services.tampering_analysis_service.metadata_forensics",
        lambda _path: {
            "score": 0.20,
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
        },
    )

    monkeypatch.setattr(
        "services.tampering_analysis_service.cnn_tamper_score",
        lambda _path: {
            "score": 0.60,
            "model_loaded": True,
            "details": {
                "message": "Mock CNN prediction",
                "model_path": "mock-model.pt",
            },
        },
    )

    monkeypatch.setattr(
        "services.tampering_analysis_service.photo_swap_analysis",
        lambda _path: {
            "score": 0.30,
            "details": {
                "portrait_region": {
                    "left": 10,
                    "top": 20,
                    "right": 200,
                    "bottom": 400,
                },
                "mean_difference": 2.0,
                "std_difference": 5.0,
                "max_difference": 25.0,
                "message": (
                    "Photo region analyzed for "
                    "compression inconsistencies"
                ),
            },
        },
    )


@pytest.mark.asyncio
async def test_tampering_endpoint_requires_authentication(client):
    response = await client.post(
        f"/documents/{uuid.uuid4()}/detect-tampering/basic"
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

    assert (
        "supports JPG"
        in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_tampering_endpoint_creates_four_technique_rows(
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

    _patch_tampering_services(
        monkeypatch
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert len(data) == 4

    techniques = {
        row["technique"]
        for row in data
    }

    assert techniques == {
        "ela",
        "metadata",
        "cnn_classifier",
        "photo_swap",
    }

    async with TestSessionFactory() as db:
        result = await db.execute(
            select(TamperingResult).where(
                TamperingResult.document_id
                == document_id
            )
        )

        rows = result.scalars().all()

    assert len(rows) == 4


@pytest.mark.asyncio
async def test_tampering_scores_are_persisted(
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

    _patch_tampering_services(
        monkeypatch
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    async with TestSessionFactory() as db:
        result = await db.execute(
            select(TamperingResult).where(
                TamperingResult.document_id
                == document_id
            )
        )

        rows = result.scalars().all()

    rows_by_technique = {
        row.technique: row
        for row in rows
    }

    assert (
        rows_by_technique[
            TamperingTechnique.ELA
        ].suspicious_score
        == 0.40
    )

    assert (
        rows_by_technique[
            TamperingTechnique.METADATA
        ].suspicious_score
        == 0.20
    )

    assert (
        rows_by_technique[
            TamperingTechnique.CNN_CLASSIFIER
        ].suspicious_score
        == 0.60
    )

    assert (
        rows_by_technique[
            TamperingTechnique.PHOTO_SWAP
        ].suspicious_score
        == 0.30
    )


@pytest.mark.asyncio
async def test_aggregate_score_is_attached_to_details(
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

    _patch_tampering_services(
        monkeypatch
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    for row in data:
        aggregate = row["details"][
            "aggregate"
        ]

        assert aggregate[
            "aggregate_score"
        ] == pytest.approx(
            0.42
        )

        assert aggregate[
            "risk_level"
        ] == "medium"

        assert set(
            aggregate[
                "components"
            ].keys()
        ) == {
            "ela",
            "metadata",
            "cnn",
            "photo_swap",
        }


@pytest.mark.asyncio
async def test_cnn_details_are_saved(
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

    _patch_tampering_services(
        monkeypatch
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    rows = {
        row["technique"]: row
        for row in response.json()
    }

    cnn = rows[
        "cnn_classifier"
    ]

    assert cnn[
        "details"
    ]["model_loaded"] is True

    assert (
        cnn["details"]["message"]
        == "Mock CNN prediction"
    )


@pytest.mark.asyncio
async def test_photo_swap_details_are_saved(
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

    _patch_tampering_services(
        monkeypatch
    )

    response = await client.post(
        f"/documents/{document_id}/detect-tampering/basic",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    rows = {
        row["technique"]: row
        for row in response.json()
    }

    photo_swap = rows[
        "photo_swap"
    ]

    assert (
        "portrait_region"
        in photo_swap["details"]
    )


@pytest.mark.asyncio
async def test_repeated_tampering_call_keeps_only_four_rows(
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

    _patch_tampering_services(
        monkeypatch
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

    assert len(rows) == 4

    assert {
        row.technique
        for row in rows
    } == {
        TamperingTechnique.ELA,
        TamperingTechnique.METADATA,
        TamperingTechnique.CNN_CLASSIFIER,
        TamperingTechnique.PHOTO_SWAP,
    }