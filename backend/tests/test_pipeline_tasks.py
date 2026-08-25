"""
Tests for Step 12 Celery pipeline tasks.

Covers:
- health check
- OCR task wrapper
- validation task wrapper
- tampering task wrapper
- invalid session status
- parallel document pipeline success
- document pipeline failure
"""

import uuid

import pytest

from db.models import SessionStatus
from tasks.pipeline import (
    pipeline_health_check,
    process_document,
    run_ocr,
    run_tampering,
    run_validation,
    set_session_status,
)


# =========================================================
# Health check
# =========================================================

def test_pipeline_health_check():
    result = pipeline_health_check.run()

    assert result == {
        "status": "ok",
        "worker": "ai_doc_screening",
    }


# =========================================================
# OCR wrapper
# =========================================================

def test_run_ocr_calls_async_helper(
    monkeypatch,
):
    document_id = uuid.uuid4()

    fake_result = {
        "document_id": str(document_id),
        "extracted_data_id": str(uuid.uuid4()),
        "ocr_confidence": 91.5,
    }

    async def fake_run_ocr_async(
        doc_id,
    ):
        assert doc_id == document_id
        return fake_result

    monkeypatch.setattr(
        "tasks.pipeline._run_ocr_async",
        fake_run_ocr_async,
    )

    result = run_ocr.run(
        str(document_id)
    )

    assert result == fake_result


# =========================================================
# Validation wrapper
# =========================================================

def test_run_validation_calls_async_helper(
    monkeypatch,
):
    document_id = uuid.uuid4()

    fake_result = {
        "document_id": str(document_id),
        "validation_count": 5,
        "passed": 4,
        "failed": 1,
    }

    async def fake_run_validation_async(
        doc_id,
    ):
        assert doc_id == document_id
        return fake_result

    monkeypatch.setattr(
        "tasks.pipeline._run_validation_async",
        fake_run_validation_async,
    )

    result = run_validation.run(
        str(document_id)
    )

    assert result == fake_result


# =========================================================
# Tampering wrapper
# =========================================================

def test_run_tampering_calls_async_helper(
    monkeypatch,
):
    document_id = uuid.uuid4()

    fake_result = {
        "document_id": str(document_id),
        "techniques": 4,
        "results": [
            {
                "technique": "ela",
                "score": 0.10,
            },
            {
                "technique": "metadata",
                "score": 0.20,
            },
            {
                "technique": "cnn_classifier",
                "score": 0.30,
            },
            {
                "technique": "photo_swap",
                "score": 0.40,
            },
        ],
    }

    async def fake_run_tampering_async(
        doc_id,
    ):
        assert doc_id == document_id
        return fake_result

    monkeypatch.setattr(
        "tasks.pipeline._run_tampering_async",
        fake_run_tampering_async,
    )

    result = run_tampering.run(
        str(document_id)
    )

    assert result == fake_result


# =========================================================
# Invalid session status
# =========================================================

def test_set_session_status_rejects_invalid_status():
    with pytest.raises(
        ValueError,
        match="Invalid session status",
    ):
        set_session_status.run(
            str(uuid.uuid4()),
            "not-a-valid-status",
        )


# =========================================================
# Fake Celery group helpers
# =========================================================

class FakeGroupResult:
    """
    Fake result returned by Celery group.apply_async().
    """

    def __init__(
        self,
        results,
    ):
        self.results = results

    def get(
        self,
        timeout=None,
        disable_sync_subtasks=None,
    ):
        assert timeout == 300
        assert disable_sync_subtasks is False

        return self.results


class FakeGroup:
    """
    Fake Celery group used to avoid Redis/worker usage
    during unit tests.
    """

    def __init__(
        self,
        results,
    ):
        self.results = results

    def apply_async(self):
        return FakeGroupResult(
            self.results
        )


# =========================================================
# Full parallel pipeline success
# =========================================================

def test_process_document_parallel_success(
    monkeypatch,
):
    document_id = str(
        uuid.uuid4()
    )

    session_id = str(
        uuid.uuid4()
    )

    statuses = []

    validation_result = {
        "document_id": document_id,
        "validation_count": 5,
        "passed": 4,
        "failed": 1,
    }

    tampering_result = {
        "document_id": document_id,
        "techniques": 4,
        "results": [],
    }

    # -----------------------------------------------------
    # Mock session status updates
    # -----------------------------------------------------

    def fake_status(
        sid,
        status,
    ):
        assert sid == session_id

        statuses.append(
            status
        )

        return {
            "session_id": sid,
            "status": status,
        }

    monkeypatch.setattr(
        "tasks.pipeline.set_session_status.run",
        fake_status,
    )

    # -----------------------------------------------------
    # Mock OCR
    # -----------------------------------------------------

    def fake_ocr(
        doc_id,
    ):
        assert doc_id == document_id

        return {
            "document_id": doc_id,
            "ocr_confidence": 92.0,
        }

    monkeypatch.setattr(
        "tasks.pipeline.run_ocr.run",
        fake_ocr,
    )

    # -----------------------------------------------------
    # Mock Celery group
    # -----------------------------------------------------

    def fake_group(
        *tasks,
    ):
        # The orchestrator should create exactly:
        #
        # run_validation.s(document_id)
        # run_tampering.s(document_id)

        assert len(tasks) == 2

        return FakeGroup(
            [
                validation_result,
                tampering_result,
            ]
        )

    monkeypatch.setattr(
        "tasks.pipeline.group",
        fake_group,
    )

    # -----------------------------------------------------
    # Execute orchestrator
    # -----------------------------------------------------

    result = process_document.run(
        document_id,
        session_id,
    )

    # -----------------------------------------------------
    # Assertions
    # -----------------------------------------------------

    assert result[
        "status"
    ] == "awaiting_face"

    assert result[
        "document_id"
    ] == document_id

    assert result[
        "session_id"
    ] == session_id

    assert result[
        "validation"
    ] == validation_result

    assert result[
        "tampering"
    ] == tampering_result

    assert statuses == [
        SessionStatus.PROCESSING.value,
        SessionStatus.AWAITING_FACE.value,
    ]


# =========================================================
# Full pipeline failure
# =========================================================

def test_process_document_marks_failed_on_error(
    monkeypatch,
):
    document_id = str(
        uuid.uuid4()
    )

    session_id = str(
        uuid.uuid4()
    )

    statuses = []

    # -----------------------------------------------------
    # Status mock
    # -----------------------------------------------------

    def fake_status(
        sid,
        status,
    ):
        assert sid == session_id

        statuses.append(
            status
        )

        return {
            "session_id": sid,
            "status": status,
        }

    monkeypatch.setattr(
        "tasks.pipeline.set_session_status.run",
        fake_status,
    )

    # -----------------------------------------------------
    # Force OCR failure
    # -----------------------------------------------------

    def fail_ocr(
        _document_id,
    ):
        raise RuntimeError(
            "OCR failed"
        )

    monkeypatch.setattr(
        "tasks.pipeline.run_ocr.run",
        fail_ocr,
    )

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    with pytest.raises(
        Exception
    ):
        process_document.run(
            document_id,
            session_id,
        )

    # -----------------------------------------------------
    # Must enter processing first
    # and then mark the session failed.
    # -----------------------------------------------------

    assert statuses == [
        SessionStatus.PROCESSING.value,
        SessionStatus.FAILED.value,
    ]