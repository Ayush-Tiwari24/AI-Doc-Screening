"""
Basic document tampering detection endpoint.

Step 8:
- Error Level Analysis (ELA)
- Metadata / EXIF forensics
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
from ml.tampering_service import (
    error_level_analysis,
    metadata_forensics,
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
                "Basic tampering detection currently "
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

        ela_result = error_level_analysis(
            temp_path
        )

        metadata_result = metadata_forensics(
            temp_path
        )

        # Remove previous basic tampering results
        # so repeated calls don't duplicate rows.
        await session.execute(
            delete(TamperingResult).where(
                TamperingResult.document_id
                == document.id,
                TamperingResult.technique.in_(
                    [
                        TamperingTechnique.ELA,
                        TamperingTechnique.METADATA,
                    ]
                ),
            )
        )

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

        session.add_all(
            [
                ela_row,
                metadata_row,
            ]
        )

        await session.commit()

        await session.refresh(
            ela_row
        )

        await session.refresh(
            metadata_row
        )

        return [
            ela_row,
            metadata_row,
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