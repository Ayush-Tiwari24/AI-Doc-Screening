"""
Document-number format patterns, keyed by (country_code, doc_type).

These are deliberately conservative, well-known public formats (ICAO/
government-published specs), NOT derived from any real document sample.
Treat these as a starting seed — expand per-country as real format specs
are confirmed. A doc_number that doesn't match its expected format is a
signal, not proof of forgery (legitimate format variants exist), so this
rule should stay WARNING severity rather than CRITICAL on its own.
"""

import re

# Passport number formats (post-ICAO-9303-compliant countries).
PASSPORT_PATTERNS: dict[str, re.Pattern] = {
    "IND": re.compile(r"^[A-Z][0-9]{7}$"),  # India: 1 letter + 7 digits
    "USA": re.compile(r"^[0-9]{9}$"),  # US: 9 digits (modern format)
    "GBR": re.compile(r"^[0-9]{9}$"),  # UK: 9 digits
    "DEU": re.compile(r"^[CFGHJKLMNPRTVWXYZ0-9]{9}$"),  # Germany: alphanumeric, excludes ambiguous letters
    "FRA": re.compile(r"^[0-9]{2}[A-Z]{2}[0-9]{5}$"),  # France: NNLLNNNNN
    "CHN": re.compile(r"^[EGPS][0-9]{8}$"),  # China: letter prefix + 8 digits
    "JPN": re.compile(r"^[A-Z]{2}[0-9]{7}$"),  # Japan: 2 letters + 7 digits
    "AUS": re.compile(r"^[A-Z][0-9]{7}$"),  # Australia: 1 letter + 7 digits
    "CAN": re.compile(r"^[A-Z]{2}[0-9]{6}$"),  # Canada: 2 letters + 6 digits
    "SCHENGEN": re.compile(r"^[A-Z0-9]{6,9}$"),  # generic fallback for Schengen-format states
}

# National ID number formats.
NATIONAL_ID_PATTERNS: dict[str, re.Pattern] = {
    "IND": re.compile(r"^[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}$"),  # Aadhaar-style: 12 digits
    "USA": re.compile(r"^[0-9]{3}-?[0-9]{2}-?[0-9]{4}$"),  # SSN-style
    "GBR": re.compile(r"^[A-Z]{2}[0-9]{6}[A-Z]$"),  # NI number style
}

DRIVING_LICENSE_PATTERNS: dict[str, re.Pattern] = {
    "IND": re.compile(r"^[A-Z]{2}[0-9]{2}\s?[0-9]{11}$"),
    "USA": re.compile(r"^[A-Z0-9]{5,12}$"),  # varies heavily by state, generic fallback
}

_PATTERN_TABLES = {
    "passport": PASSPORT_PATTERNS,
    "visa": PASSPORT_PATTERNS,  # visas commonly share the issuing country's passport-style numbering
    "national_id": NATIONAL_ID_PATTERNS,
    "license": DRIVING_LICENSE_PATTERNS,
}


def get_pattern(doc_type: str, country_code: str | None) -> re.Pattern | None:
    """Look up the expected format regex for a (doc_type, country_code) pair.
    Returns None if no pattern is configured — callers should treat that as
    'cannot validate format', not as a failure.
    """
    table = _PATTERN_TABLES.get(doc_type)
    if table is None or not country_code:
        return None
    return table.get(country_code.upper())