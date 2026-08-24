"""
Aggregate tampering scoring service.

Step 9 combines:
- Error Level Analysis (ELA)
- Metadata forensics
- CNN classifier
- Photo-swap analysis

The final score is calculated using configurable weights
from ml/tampering_config.py.
"""

from ml.tampering_config import (
    TAMPERING_WEIGHTS,
    validate_weights,
)


def _clamp(value: float) -> float:
    return max(
        0.0,
        min(
            1.0,
            float(value),
        ),
    )


def calculate_aggregate_tampering_score(
    ela_score: float,
    metadata_score: float,
    cnn_score: float,
    photo_swap_score: float,
) -> dict:
    """
    Combine all tampering signals into one final score.

    Returns:
        {
            "score": float,
            "risk_level": str,
            "components": dict,
            "weights": dict
        }
    """

    validate_weights()

    scores = {
        "ela": _clamp(
            ela_score
        ),
        "metadata": _clamp(
            metadata_score
        ),
        "cnn": _clamp(
            cnn_score
        ),
        "photo_swap": _clamp(
            photo_swap_score
        ),
    }

    weighted_components = {
        name: (
            scores[name]
            * TAMPERING_WEIGHTS[name]
        )
        for name in scores
    }

    final_score = sum(
        weighted_components.values()
    )

    final_score = round(
        _clamp(final_score),
        4,
    )

    # ---------------------------------------------------------
    # Human-readable risk classification
    # ---------------------------------------------------------

    if final_score < 0.25:
        risk_level = "low"

    elif final_score < 0.50:
        risk_level = "medium"

    elif final_score < 0.75:
        risk_level = "high"

    else:
        risk_level = "critical"

    return {
        "score": final_score,
        "risk_level": risk_level,
        "components": {
            name: {
                "score": scores[name],
                "weight": TAMPERING_WEIGHTS[
                    name
                ],
                "weighted_score": round(
                    weighted_components[
                        name
                    ],
                    4,
                ),
            }
            for name in scores
        },
        "weights": dict(
            TAMPERING_WEIGHTS
        ),
    }