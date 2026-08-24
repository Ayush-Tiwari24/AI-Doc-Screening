"""
Tests for Step 10 face verification service.

Covers:
- cosine similarity
- invalid embeddings
- FFT liveness heuristic
- invalid liveness inputs
"""

import numpy as np
import pytest

from ml.face_service import (
    check_liveness_fft,
    compute_similarity,
)


def test_similarity_identical_embeddings():
    embedding = np.array(
        [1.0, 2.0, 3.0],
        dtype=np.float32,
    )

    result = compute_similarity(
        embedding,
        embedding,
    )

    assert result == pytest.approx(1.0)


def test_similarity_opposite_embeddings():
    embedding_a = np.array(
        [1.0, 0.0],
        dtype=np.float32,
    )

    embedding_b = np.array(
        [-1.0, 0.0],
        dtype=np.float32,
    )

    result = compute_similarity(
        embedding_a,
        embedding_b,
    )

    assert result == pytest.approx(-1.0)


def test_similarity_orthogonal_embeddings():
    embedding_a = np.array(
        [1.0, 0.0],
        dtype=np.float32,
    )

    embedding_b = np.array(
        [0.0, 1.0],
        dtype=np.float32,
    )

    result = compute_similarity(
        embedding_a,
        embedding_b,
    )

    assert result == pytest.approx(0.0)


def test_similarity_rejects_different_shapes():
    embedding_a = np.array(
        [1.0, 2.0],
        dtype=np.float32,
    )

    embedding_b = np.array(
        [1.0, 2.0, 3.0],
        dtype=np.float32,
    )

    with pytest.raises(
        ValueError,
        match="same shape",
    ):
        compute_similarity(
            embedding_a,
            embedding_b,
        )


def test_similarity_rejects_zero_vector():
    embedding_a = np.array(
        [0.0, 0.0],
        dtype=np.float32,
    )

    embedding_b = np.array(
        [1.0, 2.0],
        dtype=np.float32,
    )

    with pytest.raises(
        ValueError,
        match="zero magnitude",
    ):
        compute_similarity(
            embedding_a,
            embedding_b,
        )


def test_liveness_blank_image_fails():
    image = np.zeros(
        (200, 200, 3),
        dtype=np.uint8,
    )

    result = check_liveness_fft(
        image
    )

    assert result["passed"] is False
    assert result["score"] == 0.0
    assert result["high_frequency_ratio"] == 0.0


def test_liveness_textured_image_returns_valid_score():
    rng = np.random.default_rng(
        seed=42
    )

    image = rng.integers(
        low=0,
        high=256,
        size=(200, 200, 3),
        dtype=np.uint8,
    )

    result = check_liveness_fft(
        image
    )

    assert 0.0 <= result["score"] <= 1.0
    assert 0.0 <= result["high_frequency_ratio"] <= 1.0

    assert (
        result["details"]["method"]
        == "fft_high_frequency"
    )


def test_liveness_rejects_none():
    with pytest.raises(
        ValueError,
        match="cannot be None",
    ):
        check_liveness_fft(
            None
        )


def test_liveness_rejects_empty_array():
    image = np.array(
        [],
        dtype=np.uint8,
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        check_liveness_fft(
            image
        )


def test_liveness_rejects_unsupported_shape():
    image = np.zeros(
        (2, 2, 2, 2),
        dtype=np.uint8,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported face image shape",
    ):
        check_liveness_fft(
            image
        )