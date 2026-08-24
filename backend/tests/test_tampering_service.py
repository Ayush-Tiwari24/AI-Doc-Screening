"""
Tests for basic tampering detection.

Step 8:
- Error Level Analysis (ELA)
- Metadata / EXIF forensics
"""

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from ml.tampering_service import (
    error_level_analysis,
    metadata_forensics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_clean_image(path: Path):
    """
    Create a simple JPEG image for testing.
    """

    image = Image.new(
        "RGB",
        (800, 500),
        "white",
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (100, 100, 700, 400),
        outline="black",
        width=4,
    )

    draw.text(
        (150, 200),
        "TEST DOCUMENT",
        fill="black",
    )

    image.save(
        path,
        "JPEG",
        quality=95,
    )


def _create_edited_image(path: Path):
    """
    Create an image with a locally modified region.
    """

    image = Image.new(
        "RGB",
        (800, 500),
        "white",
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (100, 100, 700, 400),
        outline="black",
        width=4,
    )

    draw.text(
        (150, 200),
        "TEST DOCUMENT",
        fill="black",
    )

    # Simulate a locally altered area.
    draw.rectangle(
        (450, 180, 650, 280),
        fill="gray",
    )

    draw.text(
        (480, 215),
        "EDITED",
        fill="black",
    )

    image.save(
        path,
        "JPEG",
        quality=75,
    )


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

def test_metadata_forensics_returns_expected_structure(tmp_path):
    image_path = tmp_path / "clean.jpg"

    _create_clean_image(image_path)

    result = metadata_forensics(
        str(image_path)
    )

    assert "score" in result
    assert "flags" in result
    assert "metadata" in result
    assert "image" in result

    assert 0.0 <= result["score"] <= 1.0

    assert result["image"]["width"] == 800
    assert result["image"]["height"] == 500


def test_metadata_detects_missing_exif(tmp_path):
    image_path = tmp_path / "no_exif.jpg"

    _create_clean_image(image_path)

    result = metadata_forensics(
        str(image_path)
    )

    assert any(
        "No EXIF metadata found" in flag
        for flag in result["flags"]
    )

    assert result["score"] > 0


def test_metadata_detects_editing_software(tmp_path):
    image_path = tmp_path / "photoshop.jpg"

    image = Image.new(
        "RGB",
        (800, 500),
        "white",
    )

    exif = Image.Exif()

    # EXIF tag 305 = Software
    exif[305] = "Adobe Photoshop"

    image.save(
        image_path,
        "JPEG",
        exif=exif,
    )

    result = metadata_forensics(
        str(image_path)
    )

    assert any(
        "Editing software detected" in flag
        for flag in result["flags"]
    )

    assert result["score"] >= 0.5


def test_metadata_flags_low_resolution(tmp_path):
    image_path = tmp_path / "small.jpg"

    image = Image.new(
        "RGB",
        (200, 100),
        "white",
    )

    image.save(
        image_path,
        "JPEG",
    )

    result = metadata_forensics(
        str(image_path)
    )

    assert any(
        "Very low image resolution" in flag
        for flag in result["flags"]
    )


# ---------------------------------------------------------------------------
# ELA tests
#
# MinIO upload is mocked because these are unit tests. We only want to
# verify the ELA algorithm here, not MinIO connectivity.
# ---------------------------------------------------------------------------

def test_ela_returns_valid_result(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "clean.jpg"

    _create_clean_image(image_path)

    uploaded = {}

    def fake_upload_file(
        local_path,
        object_name,
    ):
        uploaded["local_path"] = local_path
        uploaded["object_name"] = object_name

    monkeypatch.setattr(
        "ml.tampering_service.upload_file",
        fake_upload_file,
    )

    result = error_level_analysis(
        str(image_path)
    )

    assert "score" in result
    assert "heatmap_path" in result
    assert "details" in result

    assert 0.0 <= result["score"] <= 1.0

    assert result["heatmap_path"].startswith(
        "tampering/ela/"
    )

    assert result["heatmap_path"].endswith(
        ".png"
    )

    assert uploaded["object_name"] == (
        result["heatmap_path"]
    )


def test_ela_details_contain_analysis_metrics(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "clean.jpg"

    _create_clean_image(image_path)

    monkeypatch.setattr(
        "ml.tampering_service.upload_file",
        lambda local_path, object_name: None,
    )

    result = error_level_analysis(
        str(image_path)
    )

    details = result["details"]

    assert "mean_difference" in details
    assert "std_difference" in details
    assert "max_difference" in details
    assert "hotspot_ratio" in details

    assert details["mean_difference"] >= 0
    assert details["std_difference"] >= 0
    assert details["max_difference"] >= 0
    assert 0 <= details["hotspot_ratio"] <= 1


def test_ela_edited_image_returns_valid_score(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "edited.jpg"

    _create_edited_image(image_path)

    monkeypatch.setattr(
        "ml.tampering_service.upload_file",
        lambda local_path, object_name: None,
    )

    result = error_level_analysis(
        str(image_path)
    )

    assert 0.0 <= result["score"] <= 1.0
    assert result["heatmap_path"]