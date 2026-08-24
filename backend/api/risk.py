"""
Risk report API.

Step 11:
- computes explainable risk
- updates screening session score/level
- returns full breakdown
"""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import RiskReportOut
from auth.dependencies import get_current_user
from db.models import (
    RiskLevel,
    ScreeningSession,
    User,
)
from db.session import get_session
from services.risk_engine import compute_risk


router = APIRouter(tags=["risk"])


@router.get(
    "/sessions/{session_id}/risk-report",
    response_model=RiskReportOut,
    status_code=status.HTTP_200_OK,
)
async def get_risk_report(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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

    try:
        report = await compute_risk(
            session,
            session_id,
        )

        screening_session.risk_score = report[
            "risk_score"
        ]

        screening_session.risk_level = RiskLevel(
            report["risk_level"]
        )

        await session.commit()

        return report

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
                "Risk calculation failed: "
                f"{exc}"
            ),
        )