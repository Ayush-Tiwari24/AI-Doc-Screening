import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ValidationResultOut
from auth.dependencies import get_current_user
from db.models import Document, User
from db.session import get_session
from services.validation_service import run_validation

router = APIRouter(tags=["validation"])


@router.post(
    "/documents/{document_id}/validate",
    response_model=list[ValidationResultOut],
    status_code=status.HTTP_201_CREATED,
)
async def validate_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        rows = await run_validation(session, document)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return rows