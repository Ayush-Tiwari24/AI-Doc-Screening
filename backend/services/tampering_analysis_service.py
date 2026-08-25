import os
import tempfile
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Document,
    TamperingResult,
    TamperingTechnique,
)
from ml.aggregate_tampering import (
    calculate_aggregate_tampering_score,
)
from ml.cnn_tamper_service import (
    cnn_tamper_score,
)
from ml.tampering_service import (
    error_level_analysis,
    metadata_forensics,
    photo_swap_analysis,
)
from storage.client import download_file


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


async def run_tampering_analysis(
    db: AsyncSession,
    document_id: uuid.UUID,
) -> list[TamperingResult]:
    """
    Run complete tampering analysis for one document.

    Signals:
    - ELA
    - metadata forensics
    - CNN classifier
    - photo-swap analysis
    - aggregate tampering score

    Used by both FastAPI and Celery.
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

    extension = os.path.splitext(
        document.file_path
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Tampering detection currently supports "
            "JPG, JPEG and PNG images only"
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_path = temp_file.name

        download_file(
            document.file_path,
            temp_path,
        )

        # -------------------------------------------------
        # Run all tampering detectors
        # -------------------------------------------------

        ela_result = error_level_analysis(
            temp_path
        )

        metadata_result = metadata_forensics(
            temp_path
        )

        cnn_result = cnn_tamper_score(
            temp_path
        )

        photo_swap_result = photo_swap_analysis(
            temp_path
        )

        # -------------------------------------------------
        # Aggregate score
        # -------------------------------------------------

        aggregate_result = (
            calculate_aggregate_tampering_score(
                ela_score=ela_result["score"],
                metadata_score=metadata_result["score"],
                cnn_score=cnn_result["score"],
                photo_swap_score=photo_swap_result["score"],
            )
        )

        aggregate_details = {
            "aggregate_score": aggregate_result[
                "score"
            ],
            "risk_level": aggregate_result[
                "risk_level"
            ],
            "components": aggregate_result[
                "components"
            ],
            "weights": aggregate_result[
                "weights"
            ],
        }

        # -------------------------------------------------
        # Make execution retry-safe
        # -------------------------------------------------

        await db.execute(
            delete(TamperingResult).where(
                TamperingResult.document_id
                == document.id
            )
        )

        # -------------------------------------------------
        # ELA
        # -------------------------------------------------

        ela_row = TamperingResult(
            document_id=document.id,
            technique=TamperingTechnique.ELA,
            suspicious_score=ela_result[
                "score"
            ],
            heatmap_path=ela_result[
                "heatmap_path"
            ],
            details={
                **(
                    ela_result.get(
                        "details"
                    )
                    or {}
                ),
                "aggregate": aggregate_details,
            },
        )

        # -------------------------------------------------
        # Metadata
        # -------------------------------------------------

        metadata_row = TamperingResult(
            document_id=document.id,
            technique=TamperingTechnique.METADATA,
            suspicious_score=metadata_result[
                "score"
            ],
            heatmap_path=None,
            details={
                "flags": metadata_result[
                    "flags"
                ],
                "metadata": metadata_result[
                    "metadata"
                ],
                "image": metadata_result[
                    "image"
                ],
                "aggregate": aggregate_details,
            },
        )

        # -------------------------------------------------
        # CNN
        # -------------------------------------------------

        cnn_row = TamperingResult(
            document_id=document.id,
            technique=(
                TamperingTechnique.CNN_CLASSIFIER
            ),
            suspicious_score=cnn_result[
                "score"
            ],
            heatmap_path=None,
            details={
                "model_loaded": cnn_result[
                    "model_loaded"
                ],
                **(
                    cnn_result.get(
                        "details"
                    )
                    or {}
                ),
                "aggregate": aggregate_details,
            },
        )

        # -------------------------------------------------
        # Photo swap
        # -------------------------------------------------

        photo_swap_row = TamperingResult(
            document_id=document.id,
            technique=(
                TamperingTechnique.PHOTO_SWAP
            ),
            suspicious_score=photo_swap_result[
                "score"
            ],
            heatmap_path=None,
            details={
                **(
                    photo_swap_result.get(
                        "details"
                    )
                    or {}
                ),
                "aggregate": aggregate_details,
            },
        )

        rows = [
            ela_row,
            metadata_row,
            cnn_row,
            photo_swap_row,
        ]

        db.add_all(
            rows
        )

        await db.commit()

        for row in rows:
            await db.refresh(
                row
            )

        return rows

    except Exception:
        await db.rollback()
        raise

    finally:
        if (
            temp_path
            and os.path.exists(
                temp_path
            )
        ):
            os.unlink(
                temp_path
            )