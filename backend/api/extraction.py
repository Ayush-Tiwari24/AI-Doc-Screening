import tempfile
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ExtractedDataOut
from auth.dependencies import get_current_user
from db.models import Document, DocType, ExtractedData, User
from db.session import get_session
from ml.ocr_service import extract_non_mrz_fields, extract_text, parse_mrz
from storage.client import get_s3_client
from config import settings

router = APIRouter(tags=["extraction"])

_MRZ_ELIGIBLE_TYPES = {DocType.PASSPORT, DocType.VISA}


def _resolve_mrz_year(yy: str) -> int:
    """MRZ dates are 2-digit years. ICAO convention: pivot at current year + ~10."""
    year = int(yy)
    century_pivot = (datetime.utcnow().year % 100) + 10
    return 2000 + year if year <= century_pivot else 1900 + year


def _mrz_date_to_date(raw: str) -> date | None:
    if not raw or len(raw) != 6 or not raw.isdigit():
        return None
    yy, mm, dd = raw[0:2], raw[2:4], raw[4:6]
    try:
        return date(_resolve_mrz_year(yy), int(mm), int(dd))
    except ValueError:
        return None


@router.post(
    "/documents/{document_id}/extract",
    response_model=ExtractedDataOut,
    status_code=status.HTTP_201_CREATED,
)
async def extract_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Download the file from MinIO to a temp path for OCR processing
    client = get_s3_client()
    suffix = "." + document.file_path.rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        client.download_fileobj(settings.minio_bucket, document.file_path, tmp)
        tmp_path = tmp.name

    ocr_lines = extract_text(tmp_path)
    raw_texts = [line.text for line in ocr_lines]
    avg_confidence = (
        sum(line.confidence for line in ocr_lines) / len(ocr_lines) if ocr_lines else 0.0
    )

    parsed: dict
    if document.doc_type in _MRZ_ELIGIBLE_TYPES:
        mrz_result = parse_mrz(raw_texts)
        if mrz_result is not None:
            parsed = mrz_result
        else:
            parsed = extract_non_mrz_fields(raw_texts, document.doc_type.value)
    else:
        parsed = extract_non_mrz_fields(raw_texts, document.doc_type.value)

    dob = _mrz_date_to_date(parsed.get("dob_raw", "")) if parsed.get("dob_raw") else None
    doe = _mrz_date_to_date(parsed.get("doe_raw", "")) if parsed.get("doe_raw") else None

    extracted = ExtractedData(
        document_id=document.id,
        full_name=parsed.get("full_name"),
        doc_number=parsed.get("doc_number"),
        nationality=parsed.get("nationality"),
        dob=datetime.combine(dob, datetime.min.time()) if dob else None,
        doe=datetime.combine(doe, datetime.min.time()) if doe else None,
        gender=parsed.get("gender"),
        mrz_raw=parsed.get("mrz_raw"),
        extra_fields={
            k: v
            for k, v in parsed.items()
            if k not in {"full_name", "doc_number", "nationality", "dob_raw", "doe_raw", "gender", "mrz_raw"}
        },
        ocr_confidence=avg_confidence,
    )
    session.add(extracted)
    await session.commit()
    await session.refresh(extracted)
    return extracted