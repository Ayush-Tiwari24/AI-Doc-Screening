"""
Tests for Step 10 face verification API.

Covers:
- authentication required
- missing screening session
- missing document
- unsupported document type
- invalid live image extension
- successful face verification
- mismatch result
- database persistence
"""

import uuid

import pytest
from sqlalchemy import select

from auth.security import hash_password
from db.models import (
    Document,
    DocType,
    FaceVerification,
    ScreeningSession,
    User,
    UserRole,
)
from tests.conftest import TestSessionFactory


TEST_PASSWORD = "testpass123"


async def _seed_officer_and_session(db):
    officer = User(
        id=uuid.uuid4(),
        name="Face Test Officer",
        badge_id=f"FACE-{uuid.uuid4().hex[:8]}",
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
    file_path="documents/passport.jpg",
):
    return Document(
        id=uuid.uuid4(),
        session_id=session_id,
        file_path=file_path,
        doc_type=DocType.PASSPORT,
    )


@pytest.mark.asyncio
async def test_face_verification_requires_authentication(client):
    session_id = uuid.uuid4()

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        files={
            "live_image": (
                "live.jpg",
                b"fake-image-data",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_face_verification_session_not_found_404(client):
    async with TestSessionFactory() as db:
        _, badge_id = await _seed_officer_and_session(db)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/sessions/{uuid.uuid4()}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.jpg",
                b"fake-image-data",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_face_verification_requires_document(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.jpg",
                b"fake-image-data",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400

    assert (
        "No document available"
        in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_face_verification_rejects_non_image_document(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id,
            file_path="documents/passport.pdf",
        )

        db.add(document)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.jpg",
                b"fake-image-data",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400

    assert (
        "requires an image document"
        in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_face_verification_rejects_invalid_live_extension(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id
        )

        db.add(document)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.txt",
                b"fake-image-data",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    assert (
        "Live capture must be"
        in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_face_verification_success(
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

        document_path = document.file_path

    headers = await _auth_headers(
        client,
        badge_id,
    )

    def fake_download_file(
        object_name,
        destination_path,
    ):
        assert object_name == document_path

        with open(
            destination_path,
            "wb",
        ) as file:
            file.write(
                b"fake-document-image"
            )

        return destination_path

    def fake_verify_faces(
        document_image_path,
        live_image_path,
        threshold=0.60,
    ):
        return {
            "similarity_score": 0.91,
            "match": True,
            "threshold": threshold,
            "liveness_passed": True,
            "liveness_score": 0.88,
            "document_face": {
                "bbox": {
                    "x1": 1,
                    "y1": 2,
                    "x2": 100,
                    "y2": 120,
                },
                "detection_score": 0.97,
            },
            "live_face": {
                "bbox": {
                    "x1": 5,
                    "y1": 6,
                    "x2": 105,
                    "y2": 130,
                },
                "detection_score": 0.98,
            },
            "liveness": {
                "high_frequency_ratio": 0.26,
                "details": {
                    "method": "fft_high_frequency",
                },
            },
        }

    monkeypatch.setattr(
        "api.face_verification.download_file",
        fake_download_file,
    )

    monkeypatch.setattr(
        "api.face_verification.verify_faces",
        fake_verify_faces,
    )

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.jpg",
                b"fake-live-image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["session_id"] == str(session_id)

    assert data["doc_photo_path"] == document_path
    assert data["live_photo_path"] == "live.jpg"

    assert data["similarity_score"] == pytest.approx(
        0.91
    )

    assert data["match"] is True
    assert data["liveness_passed"] is True
    assert data["liveness_score"] == pytest.approx(
        0.88
    )


@pytest.mark.asyncio
async def test_face_verification_mismatch(
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

    headers = await _auth_headers(
        client,
        badge_id,
    )

    monkeypatch.setattr(
        "api.face_verification.download_file",
        lambda object_name, destination_path: destination_path,
    )

    monkeypatch.setattr(
        "api.face_verification.verify_faces",
        lambda document_path, live_path: {
            "similarity_score": 0.25,
            "match": False,
            "threshold": 0.60,
            "liveness_passed": True,
            "liveness_score": 0.80,
            "document_face": {
                "bbox": {},
                "detection_score": 0.90,
            },
            "live_face": {
                "bbox": {},
                "detection_score": 0.90,
            },
            "liveness": {
                "high_frequency_ratio": 0.20,
                "details": {},
            },
        },
    )

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.jpg",
                b"fake-live-image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["match"] is False
    assert data["similarity_score"] == pytest.approx(
        0.25
    )


@pytest.mark.asyncio
async def test_face_verification_is_persisted(
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

    headers = await _auth_headers(
        client,
        badge_id,
    )

    monkeypatch.setattr(
        "api.face_verification.download_file",
        lambda object_name, destination_path: destination_path,
    )

    monkeypatch.setattr(
        "api.face_verification.verify_faces",
        lambda document_path, live_path: {
            "similarity_score": 0.82,
            "match": True,
            "threshold": 0.60,
            "liveness_passed": True,
            "liveness_score": 0.77,
            "document_face": {
                "bbox": {},
                "detection_score": 0.91,
            },
            "live_face": {
                "bbox": {},
                "detection_score": 0.93,
            },
            "liveness": {
                "high_frequency_ratio": 0.22,
                "details": {},
            },
        },
    )

    response = await client.post(
        f"/sessions/{session_id}/verify-face",
        headers=headers,
        files={
            "live_image": (
                "live.jpg",
                b"fake-live-image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201, response.text

    row_id = uuid.UUID(
        response.json()["id"]
    )

    async with TestSessionFactory() as db:
        result = await db.execute(
            select(FaceVerification).where(
                FaceVerification.id == row_id
            )
        )

        row = result.scalar_one_or_none()

    assert row is not None

    assert row.session_id == session_id

    assert row.similarity_score == pytest.approx(
        0.82
    )

    assert row.match is True