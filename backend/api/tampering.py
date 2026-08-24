"""
Document tampering detection endpoint.

Step 8:
- Error Level Analysis (ELA)
- Metadata / EXIF forensics

Step 9:
- CNN tampering score
- Photo-swap analysis
- Aggregate tampering score
"""

import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import TamperingResultOut
from auth.dependencies import get_current_user
from db.models import (
    Document,
    TamperingResult,
    TamperingTechnique,
    User,
)
from db.session import get_session
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


router = APIRouter(tags=["tampering"])


@router.post(
    "/documents/{document_id}/detect-tampering/basic",
    response_model=list[TamperingResultOut],
    status_code=status.HTTP_201_CREATED,
)
async def detect_basic_tampering(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Document).where(
            Document.id == document_id
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    extension = os.path.splitext(
        document.file_path
    )[1].lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tampering detection currently "
                "supports JPG, JPEG and PNG images only"
            ),
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

        # ---------------------------------------------------------
        # Step 8 signals
        # ---------------------------------------------------------

        ela_result = error_level_analysis(
            temp_path
        )

        metadata_result = metadata_forensics(
            temp_path
        )

        # ---------------------------------------------------------
        # Step 9 signals
        # ---------------------------------------------------------

        cnn_result = cnn_tamper_score(
            temp_path
        )

        photo_swap_result = photo_swap_analysis(
            temp_path
        )

        aggregate_result = (
            calculate_aggregate_tampering_score(
                ela_score=ela_result["score"],
                metadata_score=metadata_result["score"],
                cnn_score=cnn_result["score"],
                photo_swap_score=photo_swap_result["score"],
            )
        )

        # ---------------------------------------------------------
        # Remove previous tampering rows
        # ---------------------------------------------------------

        await session.execute(
            delete(TamperingResult).where(
                TamperingResult.document_id
                == document.id,
                TamperingResult.technique.in_(
                    [
                        TamperingTechnique.ELA,
                        TamperingTechnique.METADATA,
                        TamperingTechnique.CNN_CLASSIFIER,
                        TamperingTechnique.PHOTO_SWAP,
                    ]
                ),
            )
        )

        # ---------------------------------------------------------
        # Create ELA row
        # ---------------------------------------------------------

        ela_row = TamperingResult(
            document_id=document.id,
            technique=TamperingTechnique.ELA,
            suspicious_score=ela_result[
                "score"
            ],
            heatmap_path=ela_result[
                "heatmap_path"
            ],
            details=ela_result[
                "details"
            ],
        )

        # ---------------------------------------------------------
        # Create metadata row
        # ---------------------------------------------------------

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
            },
        )

        # ---------------------------------------------------------
        # Create CNN row
        # ---------------------------------------------------------

        cnn_row = TamperingResult(
            document_id=document.id,
            technique=TamperingTechnique.CNN_CLASSIFIER,
            suspicious_score=cnn_result[
                "score"
            ],
            heatmap_path=None,
            details={
                "model_loaded": cnn_result[
                    "model_loaded"
                ],
                **cnn_result[
                    "details"
                ],
            },
        )

        # ---------------------------------------------------------
        # Create photo-swap row
        # ---------------------------------------------------------

        photo_swap_row = TamperingResult(
            document_id=document.id,
            technique=TamperingTechnique.PHOTO_SWAP,
            suspicious_score=photo_swap_result[
                "score"
            ],
            heatmap_path=None,
            details=photo_swap_result[
                "details"
            ],
        )

        # ---------------------------------------------------------
        # Attach aggregate score to each row's details
        #
        # No new database column is required for the prototype.
        # ---------------------------------------------------------

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

        ela_row.details = {
            **(
                ela_row.details
                or {}
            ),
            "aggregate": aggregate_details,
        }

        metadata_row.details = {
            **(
                metadata_row.details
                or {}
            ),
            "aggregate": aggregate_details,
        }

        cnn_row.details = {
            **(
                cnn_row.details
                or {}
            ),
            "aggregate": aggregate_details,
        }

        photo_swap_row.details = {
            **(
                photo_swap_row.details
                or {}
            ),
            "aggregate": aggregate_details,
        }

        session.add_all(
            [
                ela_row,
                metadata_row,
                cnn_row,
                photo_swap_row,
            ]
        )

        await session.commit()

        await session.refresh(
            ela_row
        )
        await session.refresh(
            metadata_row
        )
        await session.refresh(
            cnn_row
        )
        await session.refresh(
            photo_swap_row
        )

        return [
            ela_row,
            metadata_row,
            cnn_row,
            photo_swap_row,
        ]

    except HTTPException:
        raise

    except Exception as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Tampering analysis failed: "
                f"{exc}"
            ),
        )

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