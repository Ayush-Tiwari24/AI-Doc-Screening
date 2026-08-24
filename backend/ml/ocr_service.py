"""
OCR extraction service.

NOTE ON ENGINE CHOICE: PaddleOCR offers better multilingual accuracy but its
Windows/CPU-only install is heavy and fragile (large model downloads, GPU-
oriented defaults, dependency conflicts). We use pytesseract (wrapping the
Tesseract OCR engine) instead — simpler to install, well-supported on
Windows CPU-only environments, and sufficiently accurate for MRZ/passport-
style monospaced text at this stage. If OCR accuracy on real-world scanned
documents proves insufficient later, PaddleOCR remains a drop-in upgrade
path for extract_text().
"""

import re
from dataclasses import dataclass, field

import pytesseract
from PIL import Image

from config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


@dataclass
class OcrLine:
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]  # left, top, width, height


def extract_text(image_path: str) -> list[OcrLine]:
    """Run OCR on an image and return per-line text with confidence and bounding box."""
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    lines: dict[tuple[int, int, int], list[int]] = {}
    for i, text in enumerate(data["text"]):
        if not text.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(i)

    results = []
    for indices in lines.values():
        words = [data["text"][i] for i in indices]
        confs = [float(data["conf"][i]) for i in indices if data["conf"][i] != "-1"]
        lefts = [data["left"][i] for i in indices]
        tops = [data["top"][i] for i in indices]
        rights = [data["left"][i] + data["width"][i] for i in indices]
        bottoms = [data["top"][i] + data["height"][i] for i in indices]

        results.append(
            OcrLine(
                text=" ".join(words),
                confidence=sum(confs) / len(confs) if confs else 0.0,
                bbox=(min(lefts), min(tops), max(rights) - min(lefts), max(bottoms) - min(tops)),
            )
        )
    return results


# ---------------------------------------------------------------------------
# MRZ parsing (ICAO 9303, TD3 format — passports and visas: 2 lines x 44 chars)
# ---------------------------------------------------------------------------

_MRZ_CHARSET = re.compile(r"^[A-Z0-9<]+$")


def _char_value(c: str) -> int:
    if c.isdigit():
        return int(c)
    if c == "<":
        return 0
    return ord(c) - ord("A") + 10


def _compute_check_digit(s: str) -> int:
    weights = [7, 3, 1]
    total = sum(_char_value(c) * weights[i % 3] for i, c in enumerate(s))
    return total % 10


def _find_mrz_lines(raw_lines: list[str]) -> list[str] | None:
    """Find two consecutive 44-char lines matching the MRZ charset."""
    candidates = [
        line.strip().upper().replace(" ", "")
        for line in raw_lines
        if len(line.strip().replace(" ", "")) >= 40
    ]
    for i in range(len(candidates) - 1):
        l1, l2 = candidates[i], candidates[i + 1]
        l1 = l1.ljust(44, "<")[:44]
        l2 = l2.ljust(44, "<")[:44]
        if _MRZ_CHARSET.match(l1) and _MRZ_CHARSET.match(l2):
            return [l1, l2]
    return None


def parse_mrz(raw_lines: list[str]) -> dict | None:
    """
    Parse a TD3-format MRZ (passports/visas) from a list of raw OCR text lines.
    Returns None if no valid-looking MRZ block is found.
    """
    mrz = _find_mrz_lines(raw_lines)
    if mrz is None:
        return None
    line1, line2 = mrz

    # --- Line 1: document type, issuing country, name ---
    issuing_country = line1[2:5]
    names_field = line1[5:44]
    surname, _, given_names_raw = names_field.partition("<<")
    surname = surname.replace("<", " ").strip()
    given_names = given_names_raw.replace("<", " ").strip()

    # --- Line 2: doc number, nationality, DOB, sex, expiry, personal number ---
    doc_number_raw = line2[0:9]
    doc_number_check = line2[9]
    nationality = line2[10:13]
    dob_raw = line2[13:19]
    dob_check = line2[19]
    sex = line2[20]
    expiry_raw = line2[21:27]
    expiry_check = line2[27]
    personal_number_raw = line2[28:42]
    personal_number_check = line2[42]
    composite_check = line2[43]

    doc_number = doc_number_raw.replace("<", "")
    personal_number = personal_number_raw.replace("<", "")

    doc_number_valid = str(_compute_check_digit(doc_number_raw)) == doc_number_check
    dob_valid = str(_compute_check_digit(dob_raw)) == dob_check
    expiry_valid = str(_compute_check_digit(expiry_raw)) == expiry_check

    # Personal number check digit may legitimately be "<" if the field is unused
    if personal_number_raw.replace("<", "") == "":
        personal_number_valid = True
    else:
        personal_number_valid = str(_compute_check_digit(personal_number_raw)) == personal_number_check

    composite_input = (
        doc_number_raw + doc_number_check
        + dob_raw + dob_check
        + expiry_raw + expiry_check
        + personal_number_raw + personal_number_check
    )
    composite_valid = str(_compute_check_digit(composite_input)) == composite_check

    return {
        "full_name": f"{given_names} {surname}".strip(),
        "doc_number": doc_number,
        "nationality": nationality,
        "dob_raw": dob_raw,  # YYMMDD, caller resolves century
        "gender": sex,
        "doe_raw": expiry_raw,  # YYMMDD
        "issuing_country": issuing_country,
        "personal_number": personal_number,
        "mrz_raw": f"{line1}\n{line2}",
        "checksum_valid": {
            "doc_number": doc_number_valid,
            "dob": dob_valid,
            "expiry": expiry_valid,
            "personal_number": personal_number_valid,
            "composite": composite_valid,
        },
    }


# ---------------------------------------------------------------------------
# Non-MRZ field extraction (national ID / license / permit — no standard MRZ)
# ---------------------------------------------------------------------------

_LABEL_PATTERNS: dict[str, re.Pattern] = {
    "full_name": re.compile(r"(?:name|full name)\s*[:\-]?\s*(.+)", re.IGNORECASE),
    "doc_number": re.compile(r"(?:id\s*no\.?|license\s*no\.?|number)\s*[:\-]?\s*([A-Z0-9\-]+)", re.IGNORECASE),
    "dob": re.compile(r"(?:dob|date of birth)\s*[:\-]?\s*([\d/\-\.]+)", re.IGNORECASE),
    "nationality": re.compile(r"(?:nationality)\s*[:\-]?\s*([A-Za-z]+)", re.IGNORECASE),
}


def extract_non_mrz_fields(raw_lines: list[str], doc_type: str) -> dict:
    """
    Best-effort keyword/regex extraction for document types without a
    standard MRZ (national_id, license, permit). Far less reliable than
    MRZ parsing — flag low-confidence extractions to the caller.
    """
    fields: dict[str, str] = {}
    for line in raw_lines:
        for field_name, pattern in _LABEL_PATTERNS.items():
            if field_name in fields:
                continue
            match = pattern.search(line)
            if match:
                fields[field_name] = match.group(1).strip()

    return {
        "full_name": fields.get("full_name"),
        "doc_number": fields.get("doc_number"),
        "nationality": fields.get("nationality"),
        "dob_raw": fields.get("dob"),
        "mrz_raw": None,
        "extraction_method": "regex_fallback",
        "doc_type": doc_type,
    }