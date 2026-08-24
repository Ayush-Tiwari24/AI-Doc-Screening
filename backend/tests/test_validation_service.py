"""
Tests for the document validation engine (Step 7).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from auth.security import hash_password
from db.models import (
    BlacklistEntry,
    Document,
    DocType,
    ExtractedData,
    ScreeningSession,
    User,
    UserRole,
)
from services.validation_service import (
    rule_cross_document,
    rule_date_logic,
    rule_format,
    rule_mrz_checksum,
)
from tests.conftest import TestSessionFactory


def _make_extracted(**overrides) -> ExtractedData:
    defaults = dict(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        full_name="ANNA MARIA ERIKSSON",
        doc_number="L898902C3",
        nationality="UTO",
        dob=datetime(1974, 8, 12, tzinfo=timezone.utc),
        doe=datetime.now(timezone.utc) + timedelta(days=365),
        gender="F",
        mrz_raw="dummy",
        extra_fields={
            "checksum_valid": {
                "doc_number": True,
                "dob": True,
                "expiry": True,
                "personal_number": True,
                "composite": True,
            }
        },
        ocr_confidence=90.0,
    )

    defaults.update(overrides)
    return ExtractedData(**defaults)


def _make_document(**overrides) -> Document:
    defaults = dict(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        file_path="passports/sample.png",
        doc_type=DocType.PASSPORT,
    )

    defaults.update(overrides)
    return Document(**defaults)


# ---------------------------------------------------------------------------
# Rule 1: MRZ checksum
# ---------------------------------------------------------------------------

def test_mrz_checksum_passes_when_all_valid():
    extracted = _make_extracted()

    assert rule_mrz_checksum(extracted)["passed"] is True


def test_mrz_checksum_fails_when_any_invalid():
    extracted = _make_extracted(
        extra_fields={
            "checksum_valid": {
                "doc_number": False,
                "dob": True,
                "expiry": True,
                "personal_number": True,
                "composite": True,
            }
        }
    )

    result = rule_mrz_checksum(extracted)

    assert result["passed"] is False
    assert "doc_number" in result["details"]


def test_mrz_checksum_not_applicable_when_no_mrz_data():
    extracted = _make_extracted(extra_fields={})

    result = rule_mrz_checksum(extracted)

    assert result["passed"] is True
    assert "not applicable" in result["details"]


# ---------------------------------------------------------------------------
# Rule 2: Date logic
# ---------------------------------------------------------------------------

def test_date_logic_passes_for_valid_dates():
    result = rule_date_logic(_make_extracted())

    assert result["passed"] is True


def test_date_logic_fails_when_expired():
    extracted = _make_extracted(
        doe=datetime.now(timezone.utc) - timedelta(days=10)
    )

    result = rule_date_logic(extracted)

    assert result["passed"] is False
    assert "expired" in result["details"].lower()


def test_date_logic_fails_when_dob_in_future():
    extracted = _make_extracted(
        dob=datetime.now(timezone.utc) + timedelta(days=10)
    )

    result = rule_date_logic(extracted)

    assert result["passed"] is False


def test_date_logic_fails_when_expiry_before_issue():
    now = datetime.now(timezone.utc)

    extracted = _make_extracted(
        doe=now + timedelta(days=1)
    )

    result = rule_date_logic(
        extracted,
        issue_date=(now + timedelta(days=2)).date(),
    )

    assert result["passed"] is False
    assert "issue date" in result["details"].lower()


# ---------------------------------------------------------------------------
# Rule 3: Format validation
#
# Document has no country_code field in this schema.
# rule_format reads the issuing country from extracted.nationality.
# ---------------------------------------------------------------------------

def test_format_passes_for_valid_indian_passport_number():
    document = _make_document(
        doc_type=DocType.PASSPORT
    )

    extracted = _make_extracted(
        nationality="IND",
        doc_number="Z1234567",
    )

    result = rule_format(document, extracted)

    assert result["passed"] is True


def test_format_fails_for_invalid_number():
    document = _make_document(
        doc_type=DocType.PASSPORT
    )

    extracted = _make_extracted(
        nationality="IND",
        doc_number="NOTAVALIDNUMBER",
    )

    result = rule_format(document, extracted)

    assert result["passed"] is False


def test_format_skips_when_no_pattern_configured():
    document = _make_document(
        doc_type=DocType.PASSPORT
    )

    extracted = _make_extracted(
        nationality="ZZZ",
        doc_number="ANYTHING",
    )

    result = rule_format(document, extracted)

    assert result["passed"] is True
    assert "no format pattern" in result["details"].lower()


# ---------------------------------------------------------------------------
# Rule 4: Cross-document consistency
# ---------------------------------------------------------------------------

def test_cross_document_passes_with_no_siblings():
    extracted = _make_extracted()

    result = rule_cross_document(
        extracted,
        [],
    )

    assert result["passed"] is True


def test_cross_document_fails_on_name_mismatch():
    extracted = _make_extracted(
        full_name="ANNA MARIA ERIKSSON"
    )

    sibling = _make_extracted(
        full_name="COMPLETELY DIFFERENT PERSON"
    )

    result = rule_cross_document(
        extracted,
        [sibling],
    )

    assert result["passed"] is False
    assert "name mismatch" in result["details"]


def test_cross_document_fails_on_dob_mismatch():
    extracted = _make_extracted(
        dob=datetime(
            1974,
            8,
            12,
            tzinfo=timezone.utc,
        )
    )

    sibling = _make_extracted(
        full_name=extracted.full_name,
        dob=datetime(
            1990,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

    result = rule_cross_document(
        extracted,
        [sibling],
    )

    assert result["passed"] is False
    assert "dob mismatch" in result["details"].lower()


def test_cross_document_tolerates_minor_ocr_noise_in_name():
    extracted = _make_extracted(
        full_name="ANNA MARIA ERIKSSON"
    )

    sibling = _make_extracted(
        full_name="ANNA MARIA ER1KSS0N"
    )

    result = rule_cross_document(
        extracted,
        [sibling],
    )

    assert result["passed"] is True


# ---------------------------------------------------------------------------
# DB-backed tests:
# Rule 5 blacklist + full validation endpoint
#
# Uses the project's existing PostgreSQL test infrastructure from
# tests/conftest.py.
# ---------------------------------------------------------------------------

TEST_PASSWORD = "testpass123"


async def _seed_officer_and_session(db):
    """
    Create a real test officer with a hashed password,
    then create the ScreeningSession required by Document.session_id.

    Returns:
        (screening_session_id, badge_id)
    """

    officer = User(
        id=uuid.uuid4(),
        name="Test Officer",
        badge_id=f"BADGE-{uuid.uuid4().hex[:8]}",
        role=UserRole.OFFICER,
        password_hash=hash_password(TEST_PASSWORD),
    )

    db.add(officer)
    await db.flush()

    screening_session = ScreeningSession(
        id=uuid.uuid4(),
        officer_id=officer.id,
    )

    db.add(screening_session)
    await db.flush()

    return screening_session.id, officer.badge_id


async def _auth_headers(client, badge_id):
    """
    Log the seeded officer in through the real auth endpoint
    and return Authorization headers.
    """

    response = await client.post(
        "/auth/login",
        json={
            "badge_id": badge_id,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# ---------------------------------------------------------------------------
# Endpoint: all rules pass
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_endpoint_all_rules_pass(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id
        )

        db.add(document)

        extracted = _make_extracted(
            document_id=document.id,
            nationality="IND",
            doc_number="Z1234567",
        )

        db.add(extracted)

        await db.commit()

        document_id = document.id

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/documents/{document_id}/validate",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    results = {
        row["rule_name"]: row
        for row in response.json()
    }

    assert set(results) == {
        "mrz_checksum",
        "date_logic",
        "format_validation",
        "cross_document_consistency",
        "blacklist_check",
    }

    assert all(
        result["passed"]
        for result in results.values()
    )


# ---------------------------------------------------------------------------
# Endpoint: blacklist hit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_endpoint_blacklist_hit_is_critical(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id
        )

        db.add(document)

        extracted = _make_extracted(
            document_id=document.id,
            nationality="IND",
            doc_number="Z1234567",
        )

        db.add(extracted)

        blacklist_entry = BlacklistEntry(
            doc_number="Z1234567",
            name=None,
            reason="reported stolen",
        )

        db.add(blacklist_entry)

        await db.commit()

        document_id = document.id

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/documents/{document_id}/validate",
        headers=headers,
    )

    assert response.status_code == 201, response.text

    results = {
        row["rule_name"]: row
        for row in response.json()
    }

    blacklist_result = results["blacklist_check"]

    assert blacklist_result["passed"] is False
    assert blacklist_result["severity"] == "critical"
    assert "stolen" in blacklist_result["details"].lower()


# ---------------------------------------------------------------------------
# Endpoint: document not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_endpoint_document_not_found_404(client):
    async with TestSessionFactory() as db:
        _, badge_id = await _seed_officer_and_session(db)

        await db.commit()

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/documents/{uuid.uuid4()}/validate",
        headers=headers,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint: document has no extracted data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_endpoint_no_extracted_data_400(client):
    async with TestSessionFactory() as db:
        session_id, badge_id = await _seed_officer_and_session(db)

        document = _make_document(
            session_id=session_id
        )

        db.add(document)

        await db.commit()

        document_id = document.id

    headers = await _auth_headers(
        client,
        badge_id,
    )

    response = await client.post(
        f"/documents/{document_id}/validate",
        headers=headers,
    )

    assert response.status_code == 400