"""
Configuration for aggregate document tampering score.

Step 9 combines:
- ELA
- Metadata forensics
- CNN tamper classifier
- Photo-swap inconsistency check

Weights must add up to 1.0.
"""

TAMPERING_WEIGHTS = {
    "ela": 0.30,
    "metadata": 0.15,
    "cnn": 0.35,
    "photo_swap": 0.20,
}


def validate_weights():
    total = sum(TAMPERING_WEIGHTS.values())

    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Tampering weights must sum to 1.0, got {total}"
        )

    return True