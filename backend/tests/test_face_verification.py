"""
Tests for Step 10 face verification logic.

These tests mock face detection so they do not run InsightFace.
"""

import numpy as np
import pytest

from ml.face_service import verify_faces


def _fake_face(
    embedding,
    bbox=None,
    detection_score=0.95,
    crop_value=100,
):
    if bbox is None:
        bbox = {
            "x1": 10,
            "y1": 20,
            "x2": 110,
            "y2": 140,
        }

    crop = np.full(
        (120, 100, 3),
        crop_value,
        dtype=np.uint8,
    )

    return {
        "bbox": bbox,
        "crop": crop,
        "embedding": np.asarray(
            embedding,
            dtype=np.float32,
        ),
        "detection_score": detection_score,
    }


def test_verify_faces_matches_similar_embeddings(
    monkeypatch,
):
    document_face = _fake_face(
        [1.0, 2.0, 3.0]
    )

    live_face = _fake_face(
        [1.0, 2.0, 3.0]
    )

    calls = []

    def fake_detect(path):
        calls.append(path)

        if "document" in path:
            return document_face

        return live_face

    monkeypatch.setattr(
        "ml.face_service.detect_and_crop_face",
        fake_detect,
    )

    monkeypatch.setattr(
        "ml.face_service.check_liveness_fft",
        lambda _crop: {
            "passed": True,
            "score": 0.90,
            "high_frequency_ratio": 0.27,
            "details": {
                "threshold": 0.20,
                "method": "fft_high_frequency",
                "message": "Mock liveness passed",
            },
        },
    )

    result = verify_faces(
        "document.jpg",
        "live.jpg",
    )

    assert result["similarity_score"] == pytest.approx(
        1.0
    )

    assert result["match"] is True
    assert result["threshold"] == 0.60
    assert result["liveness_passed"] is True
    assert result["liveness_score"] == 0.90

    assert calls == [
        "document.jpg",
        "live.jpg",
    ]


def test_verify_faces_rejects_different_embeddings(
    monkeypatch,
):
    document_face = _fake_face(
        [1.0, 0.0]
    )

    live_face = _fake_face(
        [-1.0, 0.0]
    )

    detections = iter(
        [
            document_face,
            live_face,
        ]
    )

    monkeypatch.setattr(
        "ml.face_service.detect_and_crop_face",
        lambda _path: next(detections),
    )

    monkeypatch.setattr(
        "ml.face_service.check_liveness_fft",
        lambda _crop: {
            "passed": True,
            "score": 0.80,
            "high_frequency_ratio": 0.24,
            "details": {
                "threshold": 0.20,
                "method": "fft_high_frequency",
                "message": "Mock",
            },
        },
    )

    result = verify_faces(
        "document.jpg",
        "live.jpg",
    )

    assert result["similarity_score"] == pytest.approx(
        -1.0
    )

    assert result["match"] is False


def test_verify_faces_respects_custom_threshold(
    monkeypatch,
):
    document_face = _fake_face(
        [1.0, 0.0]
    )

    live_face = _fake_face(
        [0.8, 0.6]
    )

    detections = iter(
        [
            document_face,
            live_face,
        ]
    )

    monkeypatch.setattr(
        "ml.face_service.detect_and_crop_face",
        lambda _path: next(detections),
    )

    monkeypatch.setattr(
        "ml.face_service.check_liveness_fft",
        lambda _crop: {
            "passed": True,
            "score": 0.75,
            "high_frequency_ratio": 0.22,
            "details": {
                "threshold": 0.20,
                "method": "fft_high_frequency",
                "message": "Mock",
            },
        },
    )

    result = verify_faces(
        "document.jpg",
        "live.jpg",
        threshold=0.90,
    )

    assert result["similarity_score"] == pytest.approx(
        0.8
    )

    assert result["match"] is False
    assert result["threshold"] == 0.90


def test_verify_faces_reports_failed_liveness(
    monkeypatch,
):
    document_face = _fake_face(
        [1.0, 2.0, 3.0]
    )

    live_face = _fake_face(
        [1.0, 2.0, 3.0]
    )

    detections = iter(
        [
            document_face,
            live_face,
        ]
    )

    monkeypatch.setattr(
        "ml.face_service.detect_and_crop_face",
        lambda _path: next(detections),
    )

    monkeypatch.setattr(
        "ml.face_service.check_liveness_fft",
        lambda _crop: {
            "passed": False,
            "score": 0.10,
            "high_frequency_ratio": 0.03,
            "details": {
                "threshold": 0.20,
                "method": "fft_high_frequency",
                "message": "Mock liveness failed",
            },
        },
    )

    result = verify_faces(
        "document.jpg",
        "live.jpg",
    )

    assert result["match"] is True

    assert result[
        "liveness_passed"
    ] is False

    assert result[
        "liveness_score"
    ] == 0.10


def test_verify_faces_returns_detection_information(
    monkeypatch,
):
    document_face = _fake_face(
        [1.0, 2.0, 3.0],
        bbox={
            "x1": 1,
            "y1": 2,
            "x2": 101,
            "y2": 202,
        },
        detection_score=0.91,
    )

    live_face = _fake_face(
        [1.0, 2.0, 3.0],
        bbox={
            "x1": 5,
            "y1": 6,
            "x2": 105,
            "y2": 206,
        },
        detection_score=0.97,
    )

    detections = iter(
        [
            document_face,
            live_face,
        ]
    )

    monkeypatch.setattr(
        "ml.face_service.detect_and_crop_face",
        lambda _path: next(detections),
    )

    monkeypatch.setattr(
        "ml.face_service.check_liveness_fft",
        lambda _crop: {
            "passed": True,
            "score": 0.85,
            "high_frequency_ratio": 0.255,
            "details": {
                "threshold": 0.20,
                "method": "fft_high_frequency",
                "message": "Mock",
            },
        },
    )

    result = verify_faces(
        "document.jpg",
        "live.jpg",
    )

    assert result[
        "document_face"
    ]["bbox"] == document_face["bbox"]

    assert result[
        "live_face"
    ]["bbox"] == live_face["bbox"]

    assert result[
        "document_face"
    ]["detection_score"] == pytest.approx(
        0.91
    )

    assert result[
        "live_face"
    ]["detection_score"] == pytest.approx(
        0.97
    )


def test_verify_faces_rejects_threshold_below_zero():
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        verify_faces(
            "document.jpg",
            "live.jpg",
            threshold=-0.1,
        )


def test_verify_faces_rejects_threshold_above_one():
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        verify_faces(
            "document.jpg",
            "live.jpg",
            threshold=1.1,
        )