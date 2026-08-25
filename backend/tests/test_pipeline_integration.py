"""
Integration-style test for Step 12 pipeline orchestration.

This test verifies that a screening session can progress through:
PROCESSING -> AWAITING_FACE -> SCORED -> COMPLETE

Heavy OCR / tampering / face work is mocked so the test stays fast.
"""

import uuid

import pytest
from sqlalchemy import select

from db.models import (
    ScreeningSession,
    SessionStatus,
    User,
    UserRole,
)
from tasks.pipeline import (
    finalize_session,
    process_document,
)
from tests.conftest import TestSessionFactory


async def _seed_session(db):
    officer = User(
        id=uuid.uuid4(),
        name="Pipeline Integration Officer",
        badge_id=f"PIPE-{uuid.uuid4().hex[:8]}",
        role=UserRole.OFFICER,
        password_hash="test-hash",
    )

    db.add(officer)
    await db.flush()

    screening_session = ScreeningSession(
        id=uuid.uuid4(),
        officer_id=officer.id,
        status=SessionStatus.PENDING,
    )

    db.add(screening_session)
    await db.commit()

    return screening_session.id


@pytest.mark.asyncio
async def test_full_pipeline_status_flow(
    monkeypatch,
):
    async with TestSessionFactory() as db:
        session_id = await _seed_session(db)

    document_id = str(
        uuid.uuid4()
    )

    statuses = []

    def fake_status(
        sid,
        status,
    ):
        assert sid == str(session_id)

        statuses.append(status)

        return {
            "session_id": sid,
            "status": status,
        }

    monkeypatch.setattr(
        "tasks.pipeline.set_session_status.run",
        fake_status,
    )

    monkeypatch.setattr(
        "tasks.pipeline.run_ocr.run",
        lambda _document_id: {
            "document_id": document_id,
            "ocr_confidence": 95.0,
        },
    )

    class FakeGroupResult:
        def get(
            self,
            timeout=None,
            disable_sync_subtasks=None,
        ):
            return [
                {
                    "validation_count": 5,
                    "passed": 5,
                    "failed": 0,
                },
                {
                    "techniques": 4,
                    "results": [],
                },
            ]

    class FakeGroup:
        def apply_async(self):
            return FakeGroupResult()

    monkeypatch.setattr(
        "tasks.pipeline.group",
        lambda *args: FakeGroup(),
    )

    monkeypatch.setattr(
        "tasks.pipeline.run_risk.run",
        lambda sid: {
            "session_id": sid,
            "risk_score": 10.0,
            "risk_level": "low",
            "breakdown": [],
            "hard_override": False,
        },
    )

    first_half = process_document.run(
        document_id,
        str(session_id),
    )

    assert first_half[
        "status"
    ] == "awaiting_face"

    second_half = finalize_session.run(
        str(session_id)
    )

    assert second_half[
        "status"
    ] == "complete"

    assert statuses == [
        SessionStatus.PROCESSING.value,
        SessionStatus.AWAITING_FACE.value,
        SessionStatus.SCORED.value,
        SessionStatus.COMPLETE.value,
    ]