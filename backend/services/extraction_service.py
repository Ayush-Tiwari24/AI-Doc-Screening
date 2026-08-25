import os
import tempfile
import uuid
from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import Document, DocType, ExtractedData
from ml.ocr_service import (
    extract_non_mrz_fields,
    extract_text,
    parse_mrz,
)
from storage.client import get_s3_client


MRZ_ELIGIBLE_TYPES = {
    DocType.PASSPORT,
    DocType.VISA,
}


def _resolve_mrz_year(yy: str) -> int:
    year = int(yy)

    century_pivot = (
        datetime.utcnow().year % 100
    ) + 10

    if year <= century_pivot:
        return 2000 + year

    return 1900 + year


def _mrz_date_to_date(
    raw: str,
) -> date | None:

    if (
        not raw
        or len(raw) != 6
        or not raw.isdigit()
    ):
        return None

    yy = raw[0:2]
    mm = raw[2:4]
    dd = raw[4:6]

    try:
        return date(
            _resolve_mrz_year(yy),
            int(mm),
            int(dd),
        )

    except ValueError:
        return None


async def extract_document_data(
    db: AsyncSession,
    document_id: uuid.UUID,
) -> ExtractedData:
    """
    Run OCR and persist extracted document data.

    Used by both:
    - FastAPI extraction endpoint
    - Celery background pipeline
    """

    result = await db.execute(
        select(Document).where(
            Document.id == document_id
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise ValueError(
            "Document not found"
        )

    client = get_s3_client()

    suffix = (
        "."
        + document.file_path.rsplit(
            ".",
            1,
        )[-1]
    )

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as tmp:

            client.download_fileobj(
                settings.minio_bucket,
                document.file_path,
                tmp,
            )

            tmp_path = tmp.name

        ocr_lines = extract_text(
            tmp_path
        )

        raw_texts = [
            line.text
            for line in ocr_lines
        ]

        if ocr_lines:
            avg_confidence = (
                sum(
                    line.confidence
                    for line in ocr_lines
                )
                / len(ocr_lines)
            )
        else:
            avg_confidence = 0.0

        if (
            document.doc_type
            in MRZ_ELIGIBLE_TYPES
        ):
            parsed = parse_mrz(
                raw_texts
            )

            if parsed is None:
                parsed = (
                    extract_non_mrz_fields(
                        raw_texts,
                        document.doc_type.value,
                    )
                )

        else:
            parsed = (
                extract_non_mrz_fields(
                    raw_texts,
                    document.doc_type.value,
                )
            )

        dob = None
        doe = None

        if parsed.get("dob_raw"):
            dob = _mrz_date_to_date(
                parsed["dob_raw"]
            )

        if parsed.get("doe_raw"):
            doe = _mrz_date_to_date(
                parsed["doe_raw"]
            )

        # Make repeated pipeline execution safe.
        # ExtractedData has one row per document.
        await db.execute(
            delete(ExtractedData).where(
                ExtractedData.document_id
                == document.id
            )
        )

        excluded_fields = {
            "full_name",
            "doc_number",
            "nationality",
            "dob_raw",
            "doe_raw",
            "gender",
            "mrz_raw",
        }

        extracted = ExtractedData(
            document_id=document.id,
            full_name=parsed.get(
                "full_name"
            ),
            doc_number=parsed.get(
                "doc_number"
            ),
            nationality=parsed.get(
                "nationality"
            ),
            dob=(
                datetime.combine(
                    dob,
                    datetime.min.time(),
                )
                if dob
                else None
            ),
            doe=(
                datetime.combine(
                    doe,
                    datetime.min.time(),
                )
                if doe
                else None
            ),
            gender=parsed.get(
                "gender"
            ),
            mrz_raw=parsed.get(
                "mrz_raw"
            ),
            extra_fields={
                key: value
                for key, value
                in parsed.items()
                if key
                not in excluded_fields
            },
            ocr_confidence=(
                avg_confidence
            ),
        )

        db.add(
            extracted
        )

        await db.commit()

        await db.refresh(
            extracted
        )

        return extracted

    except Exception:
        await db.rollback()
        raise

    finally:
        if (
            tmp_path
            and os.path.exists(
                tmp_path
            )
        ):
            os.unlink(
                tmp_path
            )