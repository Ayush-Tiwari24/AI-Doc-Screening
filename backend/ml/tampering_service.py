"""
Basic tampering detection service.

Step 8:
- Error Level Analysis (ELA)
"""

import os
import tempfile
import uuid
from datetime import datetime

from PIL import ExifTags, Image, ImageChops, ImageEnhance, ImageStat

from storage.client import upload_file


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def error_level_analysis(image_path: str) -> dict:
    """
    Perform Error Level Analysis on an image.

    Returns:
        {
            "score": float,
            "heatmap_path": str,
            "details": {...}
        }
    """

    original = Image.open(image_path).convert("RGB")

    temp_jpeg = None
    temp_heatmap = None

    try:
        # Re-save image as JPEG
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg",
        ) as tmp:
            temp_jpeg = tmp.name

        original.save(
            temp_jpeg,
            "JPEG",
            quality=90,
        )

        recompressed = Image.open(
            temp_jpeg
        ).convert("RGB")

        # Difference between original and recompressed image
        difference = ImageChops.difference(
            original,
            recompressed,
        )

        grayscale = difference.convert("L")

        stats = ImageStat.Stat(grayscale)

        mean_difference = float(
            stats.mean[0]
        )

        std_difference = float(
            stats.stddev[0]
        )

        extrema = grayscale.getextrema()

        max_difference = float(
            extrema[1]
        )

        # Detect concentrated high-error regions
        threshold = max(
            12.0,
            mean_difference
            + (2.0 * std_difference),
        )

        histogram = grayscale.histogram()

        threshold_index = min(
            255,
            max(
                0,
                int(threshold),
            ),
        )

        hotspot_pixels = sum(
            histogram[
                threshold_index:
            ]
        )

        total_pixels = (
            grayscale.width
            * grayscale.height
        )

        hotspot_ratio = (
            hotspot_pixels / total_pixels
            if total_pixels
            else 0.0
        )

        # Build normalized suspicion score
        mean_score = _clamp(
            mean_difference / 30.0
        )

        variance_score = _clamp(
            std_difference / 40.0
        )

        hotspot_score = _clamp(
            hotspot_ratio / 0.10
        )

        suspicion_score = (
            (0.30 * mean_score)
            + (0.40 * variance_score)
            + (0.30 * hotspot_score)
        )

        suspicion_score = round(
            _clamp(
                suspicion_score
            ),
            4,
        )

        # Generate visible ELA heatmap
        if max_difference > 0:
            scale = min(
                20.0,
                255.0
                / max_difference,
            )
        else:
            scale = 1.0

        heatmap = ImageEnhance.Brightness(
            difference
        ).enhance(
            scale
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".png",
        ) as tmp:
            temp_heatmap = tmp.name

        heatmap.save(
            temp_heatmap,
            "PNG",
        )

        object_name = (
            "tampering/ela/"
            f"{uuid.uuid4().hex}.png"
        )

        upload_file(
            temp_heatmap,
            object_name,
        )

        return {
            "score": suspicion_score,
            "heatmap_path": object_name,
            "details": {
                "mean_difference": round(
                    mean_difference,
                    4,
                ),
                "std_difference": round(
                    std_difference,
                    4,
                ),
                "max_difference": round(
                    max_difference,
                    4,
                ),
                "hotspot_ratio": round(
                    hotspot_ratio,
                    6,
                ),
            },
        }

    finally:
        if (
            temp_jpeg
            and os.path.exists(
                temp_jpeg
            )
        ):
            os.unlink(
                temp_jpeg
            )

        if (
            temp_heatmap
            and os.path.exists(
                temp_heatmap
            )
        ):
            os.unlink(
                temp_heatmap
            )
EDITING_SOFTWARE_KEYWORDS = {
    "photoshop",
    "adobe photoshop",
    "gimp",
    "lightroom",
    "paint.net",
    "affinity",
    "pixlr",
    "canva",
    "snapseed",
}


def _parse_exif_datetime(value):
    if not value:
        return None

    try:
        return datetime.strptime(
            str(value),
            "%Y:%m:%d %H:%M:%S",
        )
    except (ValueError, TypeError):
        return None


def metadata_forensics(image_path: str) -> dict:
    """
    Inspect image metadata for possible signs of editing.

    Checks:
    - missing EXIF metadata
    - known editing-software tags
    - original/modified date mismatch
    - unusual DPI
    - very low image resolution
    """

    image = Image.open(image_path)

    exif = image.getexif()

    metadata = {}

    if exif:
        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(
                tag_id,
                str(tag_id),
            )

            if isinstance(
                value,
                (str, int, float, bool),
            ):
                metadata[tag_name] = value
            else:
                metadata[tag_name] = str(value)

    flags = []
    score = 0.0

    # ---------------------------------------------------------
    # 1. Missing EXIF
    # ---------------------------------------------------------

    if not metadata:
        flags.append(
            "No EXIF metadata found"
        )

        # Scans and exported images often legitimately lose EXIF,
        # so this should only contribute a small suspicion score.
        score += 0.10

    # ---------------------------------------------------------
    # 2. Editing software
    # ---------------------------------------------------------

    software = str(
        metadata.get(
            "Software",
            "",
        )
    ).lower()

    if software:
        for keyword in EDITING_SOFTWARE_KEYWORDS:
            if keyword in software:
                flags.append(
                    "Editing software detected: "
                    f"{metadata.get('Software')}"
                )

                score += 0.50
                break

    # ---------------------------------------------------------
    # 3. EXIF date mismatch
    # ---------------------------------------------------------

    original_date = _parse_exif_datetime(
        metadata.get(
            "DateTimeOriginal"
        )
    )

    modified_date = _parse_exif_datetime(
        metadata.get(
            "DateTime"
        )
    )

    if original_date and modified_date:
        difference_seconds = abs(
            (
                modified_date
                - original_date
            ).total_seconds()
        )

        if difference_seconds > 86400:
            flags.append(
                "EXIF original and modified dates "
                "differ by more than 24 hours"
            )

            score += 0.25

    # ---------------------------------------------------------
    # 4. DPI check
    # ---------------------------------------------------------

    dpi = image.info.get("dpi")

    if dpi:
        try:
            dpi_x = float(dpi[0])
            dpi_y = float(dpi[1])

            if (
                dpi_x < 72
                or dpi_y < 72
                or dpi_x > 1200
                or dpi_y > 1200
            ):
                flags.append(
                    "Unusual DPI detected: "
                    f"{dpi_x:.1f} x {dpi_y:.1f}"
                )

                score += 0.15

        except (
            TypeError,
            ValueError,
            IndexError,
        ):
            flags.append(
                "Unable to interpret image DPI"
            )

            score += 0.05

    # ---------------------------------------------------------
    # 5. Resolution check
    # ---------------------------------------------------------

    width, height = image.size

    if width < 300 or height < 200:
        flags.append(
            "Very low image resolution: "
            f"{width}x{height}"
        )

        score += 0.10

    # ---------------------------------------------------------
    # 6. Missing original timestamp
    # ---------------------------------------------------------

    if (
        metadata
        and not metadata.get(
            "DateTimeOriginal"
        )
    ):
        flags.append(
            "DateTimeOriginal EXIF field is missing"
        )

        score += 0.05

    score = round(
        _clamp(score),
        4,
    )

    return {
        "score": score,
        "flags": flags,
        "metadata": metadata,
        "image": {
            "width": width,
            "height": height,
            "dpi": (
                list(dpi)
                if dpi
                else None
            ),
            "format": image.format,
        },
    }