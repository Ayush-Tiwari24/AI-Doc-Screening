"""
Mocked tests for InsightFace-based face detection.

These tests do not download or run buffalo_l.
They verify our wrapper logic around InsightFace.
"""

from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from ml.face_service import detect_and_crop_face


def _write_test_image(path):
    image = np.full(
        (300, 400, 3),
        255,
        dtype=np.uint8,
    )

    cv2.rectangle(
        image,
        (50, 50),
        (180, 220),
        (0, 0, 0),
        2,
    )

    cv2.imwrite(
        str(path),
        image,
    )


class FakeFaceApp:
    def __init__(self, faces):
        self.faces = faces

    def get(self, image):
        return self.faces


def test_detect_and_crop_face_returns_expected_structure(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "face.jpg"

    _write_test_image(
        image_path
    )

    fake_face = SimpleNamespace(
        bbox=np.array(
            [50.0, 60.0, 180.0, 220.0]
        ),
        embedding=np.arange(
            512,
            dtype=np.float32,
        ),
        det_score=0.98,
    )

    fake_app = FakeFaceApp(
        [fake_face]
    )

    monkeypatch.setattr(
        "ml.face_service.get_face_app",
        lambda: fake_app,
    )

    result = detect_and_crop_face(
        str(image_path)
    )

    assert "bbox" in result
    assert "crop" in result
    assert "embedding" in result
    assert "detection_score" in result

    assert result["bbox"] == {
        "x1": 50,
        "y1": 60,
        "x2": 180,
        "y2": 220,
    }

    assert result["embedding"].shape == (
        512,
    )

    assert result["detection_score"] == pytest.approx(
        0.98
    )

    assert result["crop"].size > 0


def test_detect_and_crop_face_selects_largest_face(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "faces.jpg"

    _write_test_image(
        image_path
    )

    small_face = SimpleNamespace(
        bbox=np.array(
            [20.0, 20.0, 80.0, 80.0]
        ),
        embedding=np.ones(
            512,
            dtype=np.float32,
        ),
        det_score=0.80,
    )

    large_face = SimpleNamespace(
        bbox=np.array(
            [100.0, 50.0, 300.0, 260.0]
        ),
        embedding=np.full(
            512,
            2.0,
            dtype=np.float32,
        ),
        det_score=0.95,
    )

    fake_app = FakeFaceApp(
        [
            small_face,
            large_face,
        ]
    )

    monkeypatch.setattr(
        "ml.face_service.get_face_app",
        lambda: fake_app,
    )

    result = detect_and_crop_face(
        str(image_path)
    )

    assert result["bbox"] == {
        "x1": 100,
        "y1": 50,
        "x2": 300,
        "y2": 260,
    }

    assert result["detection_score"] == pytest.approx(
        0.95
    )


def test_detect_and_crop_face_clamps_bbox(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "face.jpg"

    _write_test_image(
        image_path
    )

    fake_face = SimpleNamespace(
        bbox=np.array(
            [-50.0, -20.0, 500.0, 400.0]
        ),
        embedding=np.ones(
            512,
            dtype=np.float32,
        ),
        det_score=0.90,
    )

    fake_app = FakeFaceApp(
        [fake_face]
    )

    monkeypatch.setattr(
        "ml.face_service.get_face_app",
        lambda: fake_app,
    )

    result = detect_and_crop_face(
        str(image_path)
    )

    assert result["bbox"] == {
        "x1": 0,
        "y1": 0,
        "x2": 400,
        "y2": 300,
    }


def test_detect_and_crop_face_raises_when_no_face(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "no_face.jpg"

    _write_test_image(
        image_path
    )

    fake_app = FakeFaceApp(
        []
    )

    monkeypatch.setattr(
        "ml.face_service.get_face_app",
        lambda: fake_app,
    )

    with pytest.raises(
        ValueError,
        match="No face detected",
    ):
        detect_and_crop_face(
            str(image_path)
        )


def test_detect_and_crop_face_rejects_missing_file():
    with pytest.raises(
        FileNotFoundError
    ):
        detect_and_crop_face(
            "missing-face-image.jpg"
        )


def test_detect_and_crop_face_rejects_unreadable_file(
    tmp_path,
):
    image_path = (
        tmp_path
        / "invalid.jpg"
    )

    image_path.write_bytes(
        b"not-an-image"
    )

    with pytest.raises(
        ValueError,
        match="Unable to read image",
    ):
        detect_and_crop_face(
            str(image_path)
        )