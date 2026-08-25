"""
Face verification API.

Step 10:
- accepts live capture upload
- compares against document image
- stores result in face_verification table

Step 12:
- after successful face verification persistence,
  triggers final risk scoring + session completion
"""

import os
import tempfile
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import FaceVerificationOut
from auth.dependencies import get_current_user
from db.models import (
    Document,
    FaceVerification,
    ScreeningSession,
    User,
)
from db.session import get_session
from ml.face_service import verify_faces
from storage.client import download_file
from tasks.pipeline import finalize_session


router = APIRouter(tags=["face-verification"])


@router.post(
    "/sessions/{session_id}/verify-face",
    response_model=FaceVerificationOut,
    status_code=status.HTTP_201_CREATED,
)
async def verify_session_face(
    session_id: uuid.UUID,
    live_image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # ---------------------------------------------------------
    # Load screening session
    # ---------------------------------------------------------

    result = await session.execute(
        select(ScreeningSession).where(
            ScreeningSession.id == session_id
        )
    )

    screening_session = result.scalar_one_or_none()

    if screening_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening session not found",
        )

    # ---------------------------------------------------------
    # Load first document for the session
    # ---------------------------------------------------------

    result = await session.execute(
        select(Document).where(
            Document.session_id == session_id
        )
    )

    document = result.scalars().first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document available for face verification",
        )

    # ---------------------------------------------------------
    # Validate document image extension
    # ---------------------------------------------------------

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
                "Face verification requires an image document "
                "(JPG, JPEG or PNG)"
            ),
        )

    # ---------------------------------------------------------
    # Validate live image extension
    # ---------------------------------------------------------

    live_extension = os.path.splitext(
        live_image.filename or ""
    )[1].lower()

    if live_extension not in {
        ".jpg",
        ".jpeg",
        ".png",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Live capture must be JPG, JPEG or PNG"
            ),
        )

    document_temp_path = None
    live_temp_path = None

    try:
        # -----------------------------------------------------
        # Download document from MinIO
        # -----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            document_temp_path = (
                temp_file.name
            )

        download_file(
            document.file_path,
            document_temp_path,
        )

        # -----------------------------------------------------
        # Save uploaded live capture temporarily
        # -----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=live_extension,
        ) as temp_file:
            live_temp_path = (
                temp_file.name
            )

            content = await live_image.read()

            temp_file.write(
                content
            )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Live capture is empty",
            )

        # -----------------------------------------------------
        # Run InsightFace + liveness verification
        # -----------------------------------------------------

        verification = verify_faces(
            document_temp_path,
            live_temp_path,
        )

        # -----------------------------------------------------
        # Persist face verification
        # -----------------------------------------------------

        row = FaceVerification(
            session_id=session_id,
            doc_photo_path=(
                document.file_path
            ),
            live_photo_path=(
                live_image.filename
            ),
            similarity_score=(
                verification[
                    "similarity_score"
                ]
            ),
            match=verification[
                "match"
            ],
        )

        session.add(
            row
        )

        await session.commit()

        await session.refresh(
            row
        )

        # -----------------------------------------------------
        # Trigger final asynchronous pipeline
        #
        # Face Verification
        #        ↓
        #      SCORED
        #        ↓
        #   Risk Engine
        #        ↓
        #     COMPLETE
        # -----------------------------------------------------

        finalize_session.delay(
            str(session_id)
        )

        # -----------------------------------------------------
        # Return immediately while Celery calculates risk
        # -----------------------------------------------------

        return {
            "id": row.id,
            "session_id": (
                row.session_id
            ),
            "doc_photo_path": (
                row.doc_photo_path
            ),
            "live_photo_path": (
                row.live_photo_path
            ),
            "similarity_score": (
                row.similarity_score
            ),
            "match": row.match,
            "liveness_passed": (
                verification[
                    "liveness_passed"
                ]
            ),
            "liveness_score": (
                verification[
                    "liveness_score"
                ]
            ),
        }

    except HTTPException:
        raise

    except ValueError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Face verification failed: "
                f"{exc}"
            ),
        )

    finally:
        # -----------------------------------------------------
        # Clean temporary document image
        # -----------------------------------------------------

        if (
            document_temp_path
            and os.path.exists(
                document_temp_path
            )
        ):
            os.unlink(
                document_temp_path
            )

        # -----------------------------------------------------
        # Clean temporary live image
        # -----------------------------------------------------

        if (
            live_temp_path
            and os.path.exists(
                live_temp_path
            )
        ):
            os.unlink(
                live_temp_path
            )