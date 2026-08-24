"""
Module 2: Document validation engine.

Runs a fixed set of rules against a document's extracted_data (and, for
cross-document consistency, sibling documents in the same session), and
persists one ValidationResult row per rule. Each rule is intentionally
self-contained and returns a plain dict so run_validation() can just
collect and store them uniformly.
"""

from datetime import date, datetime, timezone

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BlacklistEntry, Document, ExtractedData, Severity, ValidationResult
from rules_config.doc_patterns import get_pattern

# Fuzzy-match thresholds (0-100 scale, rapidfuzz convention).
CROSS_DOC_NAME_MATCH_THRESHOLD = 85
BLACKLIST_NAME_MATCH_THRESHOLD = 90


def _mk_result(rule_name: str, passed: bool, severity: Severity, details: str) -> dict:
    return {"rule_name": rule_name, "passed": passed, "severity": severity, "details": details}


# ---------------------------------------------------------------------------
# Rule 1 — MRZ checksum
# ---------------------------------------------------------------------------

def rule_mrz_checksum(extracted: ExtractedData) -> dict:
    checksum_valid = (extracted.extra_fields or {}).get("checksum_valid")
    if checksum_valid is None:
        # No MRZ was found/parsed for this document (e.g. national ID, or
        # a passport where MRZ detection failed) — not applicable, not a failure.
        return _mk_result(
            "mrz_checksum",
            True,
            Severity.INFO,
            "No MRZ data present for this document; checksum rule not applicable.",
        )
    failed_fields = [k for k, v in checksum_valid.items() if v is False]
    if failed_fields:
        return _mk_result(
            "mrz_checksum",
            False,
            Severity.CRITICAL,
            f"MRZ checksum failed for: {', '.join(failed_fields)}.",
        )
    return _mk_result("mrz_checksum", True, Severity.INFO, "All MRZ checksums valid.")


# ---------------------------------------------------------------------------
# Rule 2 — Date logic
# ---------------------------------------------------------------------------

def rule_date_logic(extracted: ExtractedData, issue_date: date | None = None) -> dict:
    today = datetime.now(timezone.utc).date()
    problems = []

    dob = extracted.dob.date() if extracted.dob else None
    doe = extracted.doe.date() if extracted.doe else None

    if dob is None and doe is None:
        return _mk_result(
            "date_logic", True, Severity.INFO, "No date fields available to validate."
        )

    if dob is not None and dob >= today:
        problems.append("date of birth is not in the past")

    if doe is not None and doe < today:
        problems.append("document is expired")

    if doe is not None and issue_date is not None and doe <= issue_date:
        problems.append("expiry date is not after issue date")

    if problems:
        severity = Severity.CRITICAL if "document is expired" in problems else Severity.WARNING
        return _mk_result("date_logic", False, severity, "; ".join(problems).capitalize() + ".")

    return _mk_result("date_logic", True, Severity.INFO, "All date checks passed.")


# ---------------------------------------------------------------------------
# Rule 3 — Format validation
# ---------------------------------------------------------------------------

def rule_format(document: Document, extracted: ExtractedData) -> dict:
    # Document has no country_code field in this schema — use the MRZ-derived
    # issuing country from OCR instead. Note this means format validation is
    # only as reliable as the OCR/MRZ parse of `nationality` itself; garbage
    # in here just means the rule gets skipped, not a false failure.
    country_code = extracted.nationality
    pattern = get_pattern(document.doc_type.value, country_code)
    if pattern is None:
        return _mk_result(
            "format_validation",
            True,
            Severity.INFO,
            f"No format pattern configured for {document.doc_type.value}/{country_code}; skipped.",
        )
    if not extracted.doc_number:
        return _mk_result(
            "format_validation", False, Severity.WARNING, "No document number was extracted to validate."
        )
    if pattern.match(extracted.doc_number):
        return _mk_result(
            "format_validation", True, Severity.INFO, "Document number matches expected format."
        )
    return _mk_result(
        "format_validation",
        False,
        Severity.WARNING,
        f"Document number '{extracted.doc_number}' does not match the expected "
        f"{country_code}/{document.doc_type.value} format.",
    )


# ---------------------------------------------------------------------------
# Rule 4 — Cross-document consistency
# ---------------------------------------------------------------------------

def rule_cross_document(extracted: ExtractedData, sibling_extracted: list[ExtractedData]) -> dict:
    if not sibling_extracted:
        return _mk_result(
            "cross_document_consistency",
            True,
            Severity.INFO,
            "Only one document in this session; nothing to cross-check.",
        )

    mismatches = []
    for sibling in sibling_extracted:
        if extracted.full_name and sibling.full_name:
            score = fuzz.token_sort_ratio(extracted.full_name.upper(), sibling.full_name.upper())
            if score < CROSS_DOC_NAME_MATCH_THRESHOLD:
                mismatches.append(
                    f"name mismatch vs document {sibling.document_id} "
                    f"('{extracted.full_name}' vs '{sibling.full_name}', similarity {score:.0f}%)"
                )
        if extracted.dob and sibling.dob and extracted.dob.date() != sibling.dob.date():
            mismatches.append(
                f"DOB mismatch vs document {sibling.document_id} "
                f"({extracted.dob.date()} vs {sibling.dob.date()})"
            )

    if mismatches:
        return _mk_result(
            "cross_document_consistency", False, Severity.CRITICAL, "; ".join(mismatches) + "."
        )
    return _mk_result(
        "cross_document_consistency", True, Severity.INFO, "Consistent with other documents in session."
    )


# ---------------------------------------------------------------------------
# Rule 5 — Blacklist check
# ---------------------------------------------------------------------------

async def rule_blacklist(session: AsyncSession, extracted: ExtractedData) -> dict:
    result = await session.execute(select(BlacklistEntry))
    entries = result.scalars().all()

    for entry in entries:
        if entry.doc_number and extracted.doc_number and entry.doc_number.upper() == extracted.doc_number.upper():
            return _mk_result(
                "blacklist_check",
                False,
                Severity.CRITICAL,
                f"Document number matches a blacklist entry (exact match). Reason on file: {entry.reason or 'unspecified'}.",
            )

    for entry in entries:
        if entry.name and extracted.full_name:
            score = fuzz.token_sort_ratio(entry.name.upper(), extracted.full_name.upper())
            if score >= BLACKLIST_NAME_MATCH_THRESHOLD:
                return _mk_result(
                    "blacklist_check",
                    False,
                    Severity.CRITICAL,
                    f"Name closely matches a blacklist entry ('{entry.name}', similarity {score:.0f}%). Reason on file: {entry.reason or 'unspecified'}.",
                )

    return _mk_result("blacklist_check", True, Severity.INFO, "No blacklist match found.")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def run_validation(session: AsyncSession, document: Document) -> list[ValidationResult]:
    result = await session.execute(
        select(ExtractedData).where(ExtractedData.document_id == document.id)
    )
    extracted = result.scalar_one_or_none()
    if extracted is None:
        raise ValueError(f"No extracted_data found for document {document.id}; run OCR extraction first.")

    siblings: list[ExtractedData] = []
    sib_result = await session.execute(
        select(ExtractedData)
        .join(Document, Document.id == ExtractedData.document_id)
        .where(Document.session_id == document.session_id, Document.id != document.id)
    )
    siblings = list(sib_result.scalars().all())

    rule_outputs = [
        rule_mrz_checksum(extracted),
        rule_date_logic(extracted),
        rule_format(document, extracted),
        rule_cross_document(extracted, siblings),
        await rule_blacklist(session, extracted),
    ]

    rows = []
    for r in rule_outputs:
        row = ValidationResult(
            document_id=document.id,
            rule_name=r["rule_name"],
            passed=r["passed"],
            severity=r["severity"],
            details=r["details"],
        )
        session.add(row)
        rows.append(row)

    await session.commit()
    for row in rows:
        await session.refresh(row)
    return rows