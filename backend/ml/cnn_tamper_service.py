"""
CNN-based tampering classifier wrapper.

Step 9:
- Provides a single inference interface
- Keeps model loading isolated from the API layer
- Allows a trained model to be plugged in later

For now, if no model is configured, the service returns
a neutral score instead of crashing the pipeline.
"""

from pathlib import Path


MODEL_PATH = Path(
    "ml/models/tamper_classifier.pt"
)


def cnn_tamper_score(
    image_path: str,
) -> dict:
    """
    Return a CNN tampering suspicion score.

    Expected result:
        {
            "score": float between 0 and 1,
            "model_loaded": bool,
            "details": dict
        }

    A trained CNN model can be connected here later.
    """

    image = Path(image_path)

    if not image.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    if not MODEL_PATH.exists():
        return {
            "score": 0.0,
            "model_loaded": False,
            "details": {
                "message": (
                    "CNN model not configured; "
                    "neutral score returned"
                ),
                "model_path": str(MODEL_PATH),
            },
        }

    # ---------------------------------------------------------
    # Placeholder for trained model inference.
    #
    # Later this block will:
    # 1. load PyTorch model
    # 2. preprocess image
    # 3. run model prediction
    # 4. convert output to probability
    # ---------------------------------------------------------

    return {
        "score": 0.0,
        "model_loaded": False,
        "details": {
            "message": (
                "CNN model file exists, but inference "
                "implementation has not been connected yet"
            ),
            "model_path": str(MODEL_PATH),
        },
    }