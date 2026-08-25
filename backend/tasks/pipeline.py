"""
Celery screening pipeline.

Pipeline flow:

document upload
    -> PROCESSING
    -> OCR
    -> validation + tampering in parallel
    -> AWAITING_FACE
    -> face verification
    -> risk scoring
    -> SCORED
    -> COMPLETE

Celery uses a short-lived AsyncEngine with NullPool so asyncpg
connections are not reused across separate asyncio.run() loops.

Step 12 also:
- publishes live status updates through Redis
- records every status transition in audit_logs
"""

import asyncio
import uuid
from contextlib import asynccontextmanager

from celery import group
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from config import settings
from db.models import (
    AuditLog,
    Document,
    RiskLevel,
    ScreeningSession,
    SessionStatus,
)
from services.extraction_service import (
    extract_document_data,
)
from services.risk_engine import (
    compute_risk,
)
from services.status_events import (
    publish_session_event,
)
from services.tampering_analysis_service import (
    run_tampering_analysis,
)
from services.validation_service import (
    run_validation as run_validation_service,
)
from tasks.celery_app import celery_app


# =========================================================
# ASYNC / DATABASE HELPERS
# =========================================================


def run_async(coro):
    """
    Execute async backend code from a synchronous Celery task.
    """

    return asyncio.run(coro)


@asynccontextmanager
async def task_db_session():
    """
    Create a Celery-local database session.

    NullPool prevents asyncpg connections from being reused
    across different asyncio event loops.
    """

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    try:
        async with session_factory() as db:
            yield db

    finally:
        await engine.dispose()


# =========================================================
# SESSION STATUS + AUDIT + REDIS
# =========================================================


async def _update_session_status(
    session_id: uuid.UUID,
    status: SessionStatus,
):
    async with task_db_session() as db:
        result = await db.execute(
            select(ScreeningSession).where(
                ScreeningSession.id == session_id
            )
        )

        screening_session = (
            result.scalar_one_or_none()
        )

        if screening_session is None:
            raise ValueError(
                f"Screening session not found: {session_id}"
            )

        # -------------------------------------------------
        # Update status
        # -------------------------------------------------

        screening_session.status = status

        # -------------------------------------------------
        # Audit log
        # -------------------------------------------------

        audit_row = AuditLog(
            session_id=session_id,
            officer_id=screening_session.officer_id,
            action=(
                f"session_status_changed:"
                f"{status.value}"
            ),
            metadata_={
                "status": status.value,
                "source": "celery_pipeline",
            },
        )

        db.add(
            audit_row
        )

        await db.commit()

        # -------------------------------------------------
        # Publish WebSocket/Redis event
        # -------------------------------------------------

        publish_session_event(
            str(session_id),
            "status_changed",
            {
                "status": status.value,
            },
        )

        return {
            "session_id": str(session_id),
            "status": status.value,
        }


# =========================================================
# OCR
# =========================================================


async def _run_ocr_async(
    document_id: uuid.UUID,
):
    async with task_db_session() as db:
        extracted = await extract_document_data(
            db,
            document_id,
        )

        return {
            "document_id": str(document_id),
            "extracted_data_id": str(
                extracted.id
            ),
            "ocr_confidence": (
                extracted.ocr_confidence
            ),
        }


# =========================================================
# VALIDATION
# =========================================================


async def _run_validation_async(
    document_id: uuid.UUID,
):
    async with task_db_session() as db:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        document = (
            result.scalar_one_or_none()
        )

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        validation_results = (
            await run_validation_service(
                db,
                document,
            )
        )

        return {
            "document_id": str(document_id),
            "validation_count": len(
                validation_results
            ),
            "passed": sum(
                1
                for item in validation_results
                if item.passed
            ),
            "failed": sum(
                1
                for item in validation_results
                if not item.passed
            ),
        }


# =========================================================
# TAMPERING
# =========================================================


async def _run_tampering_async(
    document_id: uuid.UUID,
):
    async with task_db_session() as db:
        rows = await run_tampering_analysis(
            db,
            document_id,
        )

        return {
            "document_id": str(document_id),
            "techniques": len(
                rows
            ),
            "results": [
                {
                    "technique": (
                        row.technique.value
                    ),
                    "score": (
                        row.suspicious_score
                    ),
                }
                for row in rows
            ],
        }


# =========================================================
# RISK SCORING
# =========================================================


async def _run_risk_async(
    session_id: uuid.UUID,
):
    async with task_db_session() as db:
        report = await compute_risk(
            db,
            session_id,
        )

        result = await db.execute(
            select(ScreeningSession).where(
                ScreeningSession.id == session_id
            )
        )

        screening_session = (
            result.scalar_one_or_none()
        )

        if screening_session is None:
            raise ValueError(
                f"Screening session not found: {session_id}"
            )

        screening_session.risk_score = (
            report["risk_score"]
        )

        screening_session.risk_level = RiskLevel(
            report["risk_level"]
        )

        await db.commit()

        return report


# =========================================================
# CELERY TASKS
# =========================================================


@celery_app.task(
    name="pipeline.set_session_status",
)
def set_session_status(
    session_id: str,
    status: str,
):
    session_uuid = uuid.UUID(
        session_id
    )

    try:
        session_status = SessionStatus(
            status
        )

    except ValueError as exc:
        raise ValueError(
            f"Invalid session status: {status}"
        ) from exc

    return run_async(
        _update_session_status(
            session_uuid,
            session_status,
        )
    )


@celery_app.task(
    name="pipeline.health_check",
)
def pipeline_health_check():
    return {
        "status": "ok",
        "worker": "ai_doc_screening",
    }


@celery_app.task(
    bind=True,
    name="pipeline.run_ocr",
)
def run_ocr(
    self,
    document_id: str,
):
    document_uuid = uuid.UUID(
        document_id
    )

    try:
        return run_async(
            _run_ocr_async(
                document_uuid
            )
        )

    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=3,
            max_retries=2,
        )


@celery_app.task(
    bind=True,
    name="pipeline.run_validation",
)
def run_validation(
    self,
    document_id: str,
):
    document_uuid = uuid.UUID(
        document_id
    )

    try:
        return run_async(
            _run_validation_async(
                document_uuid
            )
        )

    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=3,
            max_retries=2,
        )


@celery_app.task(
    bind=True,
    name="pipeline.run_tampering",
)
def run_tampering(
    self,
    document_id: str,
):
    document_uuid = uuid.UUID(
        document_id
    )

    try:
        return run_async(
            _run_tampering_async(
                document_uuid
            )
        )

    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=3,
            max_retries=2,
        )


@celery_app.task(
    bind=True,
    name="pipeline.run_risk",
)
def run_risk(
    self,
    session_id: str,
):
    session_uuid = uuid.UUID(
        session_id
    )

    try:
        return run_async(
            _run_risk_async(
                session_uuid
            )
        )

    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=3,
            max_retries=2,
        )


@celery_app.task(
    bind=True,
    name="pipeline.finalize_session",
)
def finalize_session(
    self,
    session_id: str,
):
    """
    Finish screening after face verification.

    Flow:

        SCORED
          ↓
      risk scoring
          ↓
       COMPLETE
    """

    try:
        # -------------------------------------------------
        # SCORED
        # -------------------------------------------------

        set_session_status.run(
            session_id,
            SessionStatus.SCORED.value,
        )

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        risk_report = run_risk.run(
            session_id
        )

        # -------------------------------------------------
        # COMPLETE
        # -------------------------------------------------

        set_session_status.run(
            session_id,
            SessionStatus.COMPLETE.value,
        )

        return {
            "session_id": session_id,
            "status": "complete",
            "risk": risk_report,
        }

    except Exception as exc:
        try:
            set_session_status.run(
                session_id,
                SessionStatus.FAILED.value,
            )

        except Exception:
            pass

        raise self.retry(
            exc=exc,
            countdown=5,
            max_retries=1,
        )


@celery_app.task(
    bind=True,
    name="pipeline.process_document",
)
def process_document(
    self,
    document_id: str,
    session_id: str,
):
    """
    First half of screening.

    Flow:

        PROCESSING
            ↓
           OCR
            ↓
      Validation + Tampering
            ↓
       AWAITING_FACE
    """

    try:
        # -------------------------------------------------
        # PROCESSING
        # -------------------------------------------------

        set_session_status.run(
            session_id,
            SessionStatus.PROCESSING.value,
        )

        # -------------------------------------------------
        # OCR
        # -------------------------------------------------

        ocr_result = run_ocr.run(
            document_id
        )

        # -------------------------------------------------
        # VALIDATION + TAMPERING
        # -------------------------------------------------

        analysis_group = group(
            run_validation.s(
                document_id
            ),
            run_tampering.s(
                document_id
            ),
        )

        group_result = (
            analysis_group.apply_async()
        )

        analysis_results = (
            group_result.get(
                timeout=300,
                disable_sync_subtasks=False,
            )
        )

        validation_result = (
            analysis_results[0]
        )

        tampering_result = (
            analysis_results[1]
        )

        # -------------------------------------------------
        # WAIT FOR FACE
        # -------------------------------------------------

        set_session_status.run(
            session_id,
            SessionStatus.AWAITING_FACE.value,
        )

        return {
            "status": "awaiting_face",
            "session_id": session_id,
            "document_id": document_id,
            "ocr": ocr_result,
            "validation": validation_result,
            "tampering": tampering_result,
        }

    except Exception as exc:
        try:
            set_session_status.run(
                session_id,
                SessionStatus.FAILED.value,
            )

        except Exception:
            pass

        raise self.retry(
            exc=exc,
            countdown=5,
            max_retries=1,
        )