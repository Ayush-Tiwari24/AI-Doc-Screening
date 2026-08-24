"""
Tests for Step 9 advanced tampering components.

Covers:
- CNN inference wrapper fallback
- missing-image handling
- photo-swap analysis
- photo-swap score bounds
- small-image handling
"""

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from ml.cnn_tamper_service import cnn_tamper_score
from ml.tampering_service import photo_swap_analysis


def _create_document_image(path: Path):
    image = Image.new(
        "RGB",
        (1000, 650),
        "white",
    )

    draw = ImageDraw.Draw(image)

    # Document boundary
    draw.rectangle(
        (20, 20, 980, 630),
        outline="black",
        width=4,
    )

    # Simulated portrait region
    draw.rectangle(
        (80, 130, 350, 520),
        fill="gray",
        outline="black",
        width=3,
    )

    # Simulated text
    draw.text(
        (430, 180),
        "NAME: TEST USER",
        fill="black",
    )

    draw.text(
        (430, 240),
        "DOCUMENT: Z1234567",
        fill="black",
    )

    image.save(
        path,
        "JPEG",
        quality=95,
    )


def test_cnn_wrapper_returns_neutral_without_model(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "document.jpg"

    _create_document_image(
        image_path
    )

    fake_model_path = (
        tmp_path
        / "missing_model.pt"
    )

    monkeypatch.setattr(
        "ml.cnn_tamper_service.MODEL_PATH",
        fake_model_path,
    )

    result = cnn_tamper_score(
        str(image_path)
    )

    assert result["score"] == 0.0
    assert result["model_loaded"] is False

    assert (
        "not configured"
        in result["details"]["message"].lower()
    )


def test_cnn_wrapper_rejects_missing_image():
    with pytest.raises(
        FileNotFoundError
    ):
        cnn_tamper_score(
            "this-file-does-not-exist.jpg"
        )


def test_photo_swap_returns_expected_structure(
    tmp_path,
):
    image_path = (
        tmp_path
        / "document.jpg"
    )

    _create_document_image(
        image_path
    )

    result = photo_swap_analysis(
        str(image_path)
    )

    assert "score" in result
    assert "details" in result

    assert 0.0 <= result["score"] <= 1.0

    assert (
        "portrait_region"
        in result["details"]
    )


def test_photo_swap_score_is_bounded(
    tmp_path,
):
    image_path = (
        tmp_path
        / "document.jpg"
    )

    _create_document_image(
        image_path
    )

    result = photo_swap_analysis(
        str(image_path)
    )

    assert result["score"] >= 0.0
    assert result["score"] <= 1.0


def test_photo_swap_handles_small_image(
    tmp_path,
):
    image_path = (
        tmp_path
        / "small.jpg"
    )

    image = Image.new(
        "RGB",
        (80, 80),
        "white",
    )

    image.save(
        image_path,
        "JPEG",
    )

    result = photo_swap_analysis(
        str(image_path)
    )

    assert result["score"] == 0.0

    assert (
        "too small"
        in result["details"]["message"].lower()
    )