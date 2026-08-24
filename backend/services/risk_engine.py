"""
Risk scoring engine.

Step 11:
- Loads configurable risk weights from JSON
- Combines validation, tampering and face-verification signals
- Produces explainable risk contributions
"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    FaceVerification,
    RiskLevel,
    ScreeningSession,
    TamperingResult,
    ValidationResult,
)


RISK_WEIGHTS_PATH = Path(
    "config/risk_weights.json"
)


def load_risk_weights() -> dict:
    """
    Load risk weights at request time.

    This keeps the configuration hot-reloadable:
    changes to risk_weights.json are picked up without
    restarting the backend.
    """

    if not RISK_WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Risk weights config not found: "
            f"{RISK_WEIGHTS_PATH}"
        )

    with RISK_WEIGHTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        weights = json.load(file)

    required = {
        "blacklist_match",
        "expired_document",
        "mrz_checksum_fail",
        "format_invalid",
        "cross_doc_mismatch",
        "tampering_score",
        "face_mismatch",
        "liveness_flag",
    }

    missing = required - set(
        weights.keys()
    )

    if missing:
        raise ValueError(
            "Risk weight config missing keys: "
            + ", ".join(
                sorted(missing)
            )
        )

    return weights


def _map_risk_level(
    score: float,
) -> RiskLevel:
    """
    Map numeric score to project risk level.
    """

    if score < 30:
        return RiskLevel.LOW

    if score < 60:
        return RiskLevel.MEDIUM

    if score < 85:
        return RiskLevel.HIGH

    return RiskLevel.CRITICAL


async def compute_risk(
    db: AsyncSession,
    session_id,
) -> dict:
    """
    Compute risk for one screening session.

    Returns:
        {
            "session_id": ...,
            "risk_score": float,
            "risk_level": str,
            "breakdown": [...],
            "hard_override": bool
        }
    """

    weights = load_risk_weights()

    # ---------------------------------------------------------
    # Load screening session
    # ---------------------------------------------------------

    result = await db.execute(
        select(ScreeningSession).where(
            ScreeningSession.id
            == session_id
        )
    )

    screening_session = (
        result.scalar_one_or_none()
    )

    if screening_session is None:
        raise ValueError(
            "Screening session not found"
        )

    # ---------------------------------------------------------
    # Load validation results for all documents
    # in this session
    # ---------------------------------------------------------

    validation_result = await db.execute(
        select(ValidationResult).where(
            ValidationResult.document_id.in_(
                select_document_ids_for_session(
                    session_id
                )
            )
        )
    )

    validation_rows = (
        validation_result.scalars().all()
    )

    # ---------------------------------------------------------
    # Load tampering results
    # ---------------------------------------------------------

    tampering_result = await db.execute(
        select(TamperingResult).where(
            TamperingResult.document_id.in_(
                select_document_ids_for_session(
                    session_id
                )
            )
        )
    )

    tampering_rows = (
        tampering_result.scalars().all()
    )

    # ---------------------------------------------------------
    # Load latest face verification
    # ---------------------------------------------------------

    face_result = await db.execute(
        select(FaceVerification).where(
            FaceVerification.session_id
            == session_id
        )
    )

    face_rows = (
        face_result.scalars().all()
    )

    latest_face = (
        face_rows[-1]
        if face_rows
        else None
    )

    breakdown = []

    score = 0.0
    hard_override = False

    # ---------------------------------------------------------
    # Validation factors
    # ---------------------------------------------------------

    for row in validation_rows:
        if row.passed:
            continue

        rule = row.rule_name.lower()

        details = (
            row.details or ""
        ).lower()

        if rule == "blacklist_check":
            points = float(
                weights[
                    "blacklist_match"
                ]
            )

            breakdown.append(
                {
                    "factor": (
                        "Blacklist match detected"
                    ),
                    "points": points,
                }
            )

            score += points
            hard_override = True

        elif rule == "date_logic":
            if "expired" in details:
                points = float(
                    weights[
                        "expired_document"
                    ]
                )

                breakdown.append(
                    {
                        "factor": (
                            "Document is expired"
                        ),
                        "points": points,
                    }
                )

                score += points
                hard_override = True

        elif rule == "mrz_checksum":
            points = float(
                weights[
                    "mrz_checksum_fail"
                ]
            )

            breakdown.append(
                {
                    "factor": (
                        "MRZ checksum failed"
                    ),
                    "points": points,
                }
            )

            score += points

        elif rule == "format_validation":
            points = float(
                weights[
                    "format_invalid"
                ]
            )

            breakdown.append(
                {
                    "factor": (
                        "Document format is invalid"
                    ),
                    "points": points,
                }
            )

            score += points

        elif (
            rule
            == "cross_document_consistency"
        ):
            points = float(
                weights[
                    "cross_doc_mismatch"
                ]
            )

            breakdown.append(
                {
                    "factor": (
                        "Cross-document mismatch"
                    ),
                    "points": points,
                }
            )

            score += points

    # ---------------------------------------------------------
    # Tampering factor
    #
    # Aggregate tampering score is attached in
    # details["aggregate"]["aggregate_score"].
    # Use the highest aggregate found.
    # ---------------------------------------------------------

    aggregate_scores = []

    for row in tampering_rows:
        details = row.details or {}

        aggregate = details.get(
            "aggregate"
        )

        if not aggregate:
            continue

        aggregate_score = aggregate.get(
            "aggregate_score"
        )

        if aggregate_score is not None:
            aggregate_scores.append(
                float(
                    aggregate_score
                )
            )

    if aggregate_scores:
        highest_tampering = max(
            aggregate_scores
        )

        points = (
            highest_tampering
            * float(
                weights[
                    "tampering_score"
                ]
            )
        )

        if points > 0:
            breakdown.append(
                {
                    "factor": (
                        "Document tampering indicators"
                    ),
                    "points": round(
                        points,
                        2,
                    ),
                    "raw_score": round(
                        highest_tampering,
                        4,
                    ),
                }
            )

            score += points

    # ---------------------------------------------------------
    # Face mismatch
    # ---------------------------------------------------------

    if (
        latest_face is not None
        and latest_face.match is False
    ):
        points = float(
            weights[
                "face_mismatch"
            ]
        )

        breakdown.append(
            {
                "factor": (
                    "Face verification mismatch"
                ),
                "points": points,
            }
        )

        score += points

    # ---------------------------------------------------------
    # Liveness
    #
    # Current FaceVerification table does not yet persist
    # liveness, so this will be integrated once that field is
    # stored. The risk factor remains in config now so the
    # architecture is ready for it.
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Cap score and apply hard override
    # ---------------------------------------------------------

    score = min(
        100.0,
        score,
    )

    if hard_override:
        final_level = (
            RiskLevel.CRITICAL
        )

        # A hard override should also present a critical
        # numeric score to keep UI behaviour intuitive.
        score = max(
            85.0,
            score,
        )

    else:
        final_level = _map_risk_level(
            score
        )

    breakdown.sort(
        key=lambda item: item[
            "points"
        ],
        reverse=True,
    )

    return {
        "session_id": session_id,
        "risk_score": round(
            score,
            2,
        ),
        "risk_level": (
            final_level.value
        ),
        "breakdown": breakdown,
        "hard_override": hard_override,
    }


def select_document_ids_for_session(
    session_id,
):
    """
    Return a selectable containing document IDs
    belonging to a screening session.
    """

    from db.models import Document

    return select(
        Document.id
    ).where(
        Document.session_id
        == session_id
    )