"""
Tests for Step 11 risk scoring engine.

Covers:
- clean session -> LOW
- tampering score contribution
- blacklist hard override -> CRITICAL
- expired document hard override -> CRITICAL
- face mismatch contribution
"""

import uuid

import pytest

from db.models import (
    Document,
    DocType,
    FaceVerification,
    ScreeningSession,
    TamperingResult,
    TamperingTechnique,
    User,
    UserRole,
    ValidationResult,
    Severity,
)
from services.risk_engine import compute_risk
from tests.conftest import TestSessionFactory


async def _seed_session(db):
    officer = User(
        id=uuid.uuid4(),
        name="Risk Test Officer",
        badge_id=f"RISK-{uuid.uuid4().hex[:8]}",
        role=UserRole.OFFICER,
        password_hash="test-hash",
    )

    db.add(officer)
    await db.flush()

    session = ScreeningSession(
        id=uuid.uuid4(),
        officer_id=officer.id,
    )

    db.add(session)
    await db.flush()

    return session


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
async def test_clean_session_is_low_risk():
    async with TestSessionFactory() as db:
        session = await _seed_session(db)

        await db.commit()

        session_id = session.id

    async with TestSessionFactory() as db:
        result = await compute_risk(
            db,
            session_id,
        )

    assert result["risk_score"] == 0.0
    assert result["risk_level"] == "low"
    assert result["hard_override"] is False
    assert result["breakdown"] == []


@pytest.mark.asyncio
async def test_tampering_escalates_risk():
    async with TestSessionFactory() as db:
        session = await _seed_session(db)

        document = await _seed_document(
            db,
            session.id,
        )

        tampering = TamperingResult(
            document_id=document.id,
            technique=TamperingTechnique.ELA,
            suspicious_score=0.80,
            heatmap_path=None,
            details={
                "aggregate": {
                    "aggregate_score": 0.80,
                    "risk_level": "high",
                }
            },
        )

        db.add(tampering)

        await db.commit()

        session_id = session.id

    async with TestSessionFactory() as db:
        result = await compute_risk(
            db,
            session_id,
        )

    assert result["risk_score"] == pytest.approx(
        32.0
    )

    assert result["risk_level"] == "medium"

    assert any(
        item["factor"]
        == "Document tampering indicators"
        for item in result["breakdown"]
    )


@pytest.mark.asyncio
async def test_blacklist_match_forces_critical():
    async with TestSessionFactory() as db:
        session = await _seed_session(db)

        document = await _seed_document(
            db,
            session.id,
        )

        validation = ValidationResult(
            document_id=document.id,
            rule_name="blacklist_check",
            passed=False,
            severity=Severity.CRITICAL,
            details="Document number matched blacklist",
        )

        db.add(validation)

        await db.commit()

        session_id = session.id

    async with TestSessionFactory() as db:
        result = await compute_risk(
            db,
            session_id,
        )

    assert result["risk_level"] == "critical"
    assert result["hard_override"] is True
    assert result["risk_score"] >= 85.0

    assert any(
        item["factor"]
        == "Blacklist match detected"
        for item in result["breakdown"]
    )


@pytest.mark.asyncio
async def test_expired_document_forces_critical():
    async with TestSessionFactory() as db:
        session = await _seed_session(db)

        document = await _seed_document(
            db,
            session.id,
        )

        validation = ValidationResult(
            document_id=document.id,
            rule_name="date_logic",
            passed=False,
            severity=Severity.CRITICAL,
            details="Document expired on 2025-01-01",
        )

        db.add(validation)

        await db.commit()

        session_id = session.id

    async with TestSessionFactory() as db:
        result = await compute_risk(
            db,
            session_id,
        )

    assert result["risk_level"] == "critical"
    assert result["hard_override"] is True
    assert result["risk_score"] >= 85.0

    assert any(
        item["factor"]
        == "Document is expired"
        for item in result["breakdown"]
    )


@pytest.mark.asyncio
async def test_face_mismatch_contributes_to_risk():
    async with TestSessionFactory() as db:
        session = await _seed_session(db)

        face = FaceVerification(
            session_id=session.id,
            doc_photo_path="documents/passport.jpg",
            live_photo_path="live.jpg",
            similarity_score=0.20,
            match=False,
        )

        db.add(face)

        await db.commit()

        session_id = session.id

    async with TestSessionFactory() as db:
        result = await compute_risk(
            db,
            session_id,
        )

    assert result["risk_score"] == pytest.approx(
        35.0
    )

    assert result["risk_level"] == "medium"

    assert any(
        item["factor"]
        == "Face verification mismatch"
        for item in result["breakdown"]
    )


@pytest.mark.asyncio
async def test_multiple_factors_are_combined():
    async with TestSessionFactory() as db:
        session = await _seed_session(db)

        document = await _seed_document(
            db,
            session.id,
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

        db.add(
            ValidationResult(
                document_id=document.id,
                rule_name="format_validation",
                passed=False,
                severity=Severity.WARNING,
                details="Invalid document number format",
            )
        )

        db.add(
            FaceVerification(
                session_id=session.id,
                doc_photo_path="documents/passport.jpg",
                live_photo_path="live.jpg",
                similarity_score=0.25,
                match=False,
            )
        )

        await db.commit()

        session_id = session.id

    async with TestSessionFactory() as db:
        result = await compute_risk(
            db,
            session_id,
        )

    # 30 MRZ + 20 format + 35 face mismatch = 85
    assert result["risk_score"] == pytest.approx(
        85.0
    )

    assert result["risk_level"] == "critical"

    assert result["hard_override"] is False

    assert len(
        result["breakdown"]
    ) == 3


@pytest.mark.asyncio
async def test_missing_session_raises_error():
    async with TestSessionFactory() as db:
        with pytest.raises(
            ValueError,
            match="Screening session not found",
        ):
            await compute_risk(
                db,
                uuid.uuid4(),
            )