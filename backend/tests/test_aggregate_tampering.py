"""
Tests for Step 9 aggregate tampering score.
"""

import pytest

from ml.aggregate_tampering import (
    calculate_aggregate_tampering_score,
)
from ml.tampering_config import (
    TAMPERING_WEIGHTS,
    validate_weights,
)


def test_weights_sum_to_one():
    assert validate_weights() is True

    assert abs(
        sum(TAMPERING_WEIGHTS.values()) - 1.0
    ) < 1e-6


def test_aggregate_score_calculation():
    result = calculate_aggregate_tampering_score(
        ela_score=0.4,
        metadata_score=0.2,
        cnn_score=0.6,
        photo_swap_score=0.3,
    )

    assert result["score"] == pytest.approx(
        0.42
    )

    assert result["risk_level"] == "medium"


def test_low_risk():
    result = calculate_aggregate_tampering_score(
        ela_score=0.1,
        metadata_score=0.1,
        cnn_score=0.1,
        photo_swap_score=0.1,
    )

    assert result["risk_level"] == "low"


def test_medium_risk():
    result = calculate_aggregate_tampering_score(
        ela_score=0.4,
        metadata_score=0.4,
        cnn_score=0.4,
        photo_swap_score=0.4,
    )

    assert result["risk_level"] == "medium"


def test_high_risk():
    result = calculate_aggregate_tampering_score(
        ela_score=0.6,
        metadata_score=0.6,
        cnn_score=0.6,
        photo_swap_score=0.6,
    )

    assert result["risk_level"] == "high"


def test_critical_risk():
    result = calculate_aggregate_tampering_score(
        ela_score=0.9,
        metadata_score=0.9,
        cnn_score=0.9,
        photo_swap_score=0.9,
    )

    assert result["risk_level"] == "critical"


def test_scores_are_clamped():
    result = calculate_aggregate_tampering_score(
        ela_score=-5,
        metadata_score=2,
        cnn_score=10,
        photo_swap_score=-3,
    )

    components = result["components"]

    assert components["ela"]["score"] == 0.0
    assert components["metadata"]["score"] == 1.0
    assert components["cnn"]["score"] == 1.0
    assert components["photo_swap"]["score"] == 0.0

    assert 0.0 <= result["score"] <= 1.0


def test_components_are_returned():
    result = calculate_aggregate_tampering_score(
        ela_score=0.2,
        metadata_score=0.3,
        cnn_score=0.4,
        photo_swap_score=0.5,
    )

    assert set(
        result["components"].keys()
    ) == {
        "ela",
        "metadata",
        "cnn",
        "photo_swap",
    }

    for component in result[
        "components"
    ].values():
        assert "score" in component
        assert "weight" in component
        assert "weighted_score" in component


def test_weights_are_in_response():
    result = calculate_aggregate_tampering_score(
        ela_score=0.2,
        metadata_score=0.2,
        cnn_score=0.2,
        photo_swap_score=0.2,
    )

    assert result["weights"] == (
        TAMPERING_WEIGHTS
    )