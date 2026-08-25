import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ExtractedDataOut
from auth.dependencies import get_current_user
from db.models import User
from db.session import get_session
from services.extraction_service import (
    extract_document_data,
)


router = APIRouter(tags=["extraction"])


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
    try:
        extracted = await extract_document_data(
            session,
            document_id,
        )

        return extracted

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "OCR extraction failed: "
                f"{exc}"
            ),
        )