"""
Tests for Step 11 risk-report API.

Covers:
- authentication required
- missing session -> 404
- clean session -> LOW
- blacklist hard override -> CRITICAL
- persistence of risk_score / risk_level
"""

import uuid

import pytest
from sqlalchemy import select

from auth.security import hash_password
from db.models import (
    Document,
    DocType,
    RiskLevel,
    ScreeningSession,
    Severity,
    User,
    UserRole,
    ValidationResult,
)
from tests.conftest import TestSessionFactory


TEST_PASSWORD = "testpass123"


async def _seed_officer_and_session(db):
    officer = User(
        id=uuid.uuid4(),
        name="Risk API Officer",
        badge_id=f"RISKAPI-{uuid.uuid4().hex[:8]}",
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


async def _seed_document(db, session_id):
    document = Document(
        id=uuid.uuid4(),
        session_id=session_id,
        file_path="documents/test.jpg",
        doc_type=DocType.PASSPORT,
    )

    db.add(document)
    await db.flush()

    return document


@pytest.mark.asyncio
async def test_risk_report_requires_authentication(client):
    response = await client.get(
        f"/sessions/{uuid.uuid4()}/risk-report"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_risk_report_missing_session_404(client):
    async with TestSessionFactory() as db:
        _, badge_id = await _seed_officer_and_session(db)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.get(
        f"/sessions/{uuid.uuid4()}/risk-report",
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_clean_session_returns_low_risk(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)
        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.get(
        f"/sessions/{session_id}/risk-report",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["session_id"] == str(session_id)
    assert data["risk_score"] == 0.0
    assert data["risk_level"] == "low"
    assert data["hard_override"] is False
    assert data["breakdown"] == []


@pytest.mark.asyncio
async def test_blacklist_forces_critical(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = await _seed_document(
            db,
            session_id,
        )

        db.add(
            ValidationResult(
                document_id=document.id,
                rule_name="blacklist_check",
                passed=False,
                severity=Severity.CRITICAL,
                details="Document matched blacklist",
            )
        )

        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.get(
        f"/sessions/{session_id}/risk-report",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["risk_level"] == "critical"
    assert data["hard_override"] is True
    assert data["risk_score"] >= 85.0

    assert any(
        item["factor"] == "Blacklist match detected"
        for item in data["breakdown"]
    )


@pytest.mark.asyncio
async def test_risk_report_persists_score_and_level(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = await _seed_document(
            db,
            session_id,
        )

        db.add(
            ValidationResult(
                document_id=document.id,
                rule_name="mrz_checksum",
                passed=False,
                severity=Severity.WARNING,
                details="MRZ checksum failed",
            )
        )

        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.get(
        f"/sessions/{session_id}/risk-report",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["risk_score"] == pytest.approx(
        30.0
    )

    assert data["risk_level"] == "medium"

    async with TestSessionFactory() as db:
        result = await db.execute(
            select(ScreeningSession).where(
                ScreeningSession.id == session_id
            )
        )

        row = result.scalar_one()

    assert row.risk_score == pytest.approx(
        30.0
    )

    assert row.risk_level == RiskLevel.MEDIUM