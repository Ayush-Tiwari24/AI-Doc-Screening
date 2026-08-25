"""
Document tampering detection endpoint.

Runs:
- ELA
- Metadata forensics
- CNN tamper score
- Photo-swap analysis
- Aggregate tampering score
"""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import TamperingResultOut
from auth.dependencies import get_current_user
from db.models import User
from db.session import get_session
from services.tampering_analysis_service import (
    run_tampering_analysis,
)


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
    try:
        rows = await run_tampering_analysis(
            session,
            document_id,
        )

        return rows

    except ValueError as exc:
        message = str(exc)

        if message == "Document not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Tampering analysis failed: "
                f"{exc}"
            ),
        )