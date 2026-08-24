"""
Face verification service.

Step 10:
- InsightFace model initialization
- Face detection
- Face cropping
- Embedding extraction

Later steps will add:
- cosine similarity
- basic FFT liveness heuristic
"""

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


@lru_cache(maxsize=1)
def get_face_app() -> FaceAnalysis:
    """
    Load InsightFace buffalo_l once and reuse it.

    CPU execution is used so the backend works
    without requiring a GPU.
    """

    app = FaceAnalysis(
        name="buffalo_l",
        providers=[
            "CPUExecutionProvider"
        ],
    )

    app.prepare(
        ctx_id=-1,
        det_size=(640, 640),
    )

    return app


def detect_and_crop_face(
    image_path: str,
) -> dict:
    """
    Detect the largest face in an image.

    Returns:
        {
            "bbox": {
                "x1": int,
                "y1": int,
                "x2": int,
                "y2": int
            },
            "crop": numpy.ndarray,
            "embedding": numpy.ndarray,
            "detection_score": float
        }

    Raises:
        FileNotFoundError:
            if image does not exist

        ValueError:
            if image cannot be read
            or no face is detected
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = cv2.imread(
        str(path)
    )

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    face_app = get_face_app()

    faces = face_app.get(
        image
    )

    if not faces:
        raise ValueError(
            "No face detected in image"
        )

    # Pick the largest detected face.
    face = max(
        faces,
        key=lambda f: (
            float(f.bbox[2] - f.bbox[0])
            * float(f.bbox[3] - f.bbox[1])
        ),
    )

    x1, y1, x2, y2 = [
        int(round(value))
        for value in face.bbox
    ]

    height, width = image.shape[:2]

    # Clamp bounding box to image dimensions.
    x1 = max(
        0,
        min(
            x1,
            width - 1,
        ),
    )

    y1 = max(
        0,
        min(
            y1,
            height - 1,
        ),
    )

    x2 = max(
        x1 + 1,
        min(
            x2,
            width,
        ),
    )

    y2 = max(
        y1 + 1,
        min(
            y2,
            height,
        ),
    )

    crop = image[
        y1:y2,
        x1:x2,
    ].copy()

    embedding = np.asarray(
        face.embedding,
        dtype=np.float32,
    )

    return {
        "bbox": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        },
        "crop": crop,
        "embedding": embedding,
        "detection_score": float(
            face.det_score
        ),
    }

def compute_similarity(
    embedding_a,
    embedding_b,
) -> float:
    """
    Compute cosine similarity between two face embeddings.

    Returns a value in the range [-1, 1].

    For normal InsightFace embeddings:
    - higher = more similar
    - lower = less similar
    """

    a = np.asarray(
        embedding_a,
        dtype=np.float32,
    )

    b = np.asarray(
        embedding_b,
        dtype=np.float32,
    )

    if a.shape != b.shape:
        raise ValueError(
            "Embeddings must have the same shape"
        )

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        raise ValueError(
            "Embedding vector cannot have zero magnitude"
        )

    similarity = np.dot(
        a,
        b,
    ) / (
        norm_a * norm_b
    )

    return float(similarity)

def check_liveness_fft(
    face_image,
) -> dict:
    """
    Basic FFT-based liveness heuristic.

    Measures high-frequency information in the face image.

    This is NOT a production-grade anti-spoofing system.
    It is a lightweight prototype heuristic that can help
    flag unusually smooth / low-detail face captures.

    Returns:
        {
            "passed": bool,
            "score": float,
            "high_frequency_ratio": float,
            "details": dict
        }
    """

    if face_image is None:
        raise ValueError(
            "Face image cannot be None"
        )

    image = np.asarray(
        face_image
    )

    if image.size == 0:
        raise ValueError(
            "Face image cannot be empty"
        )

    # Convert to grayscale when needed.
    if len(image.shape) == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )
    elif len(image.shape) == 2:
        gray = image
    else:
        raise ValueError(
            "Unsupported face image shape"
        )

    gray = gray.astype(
        np.float32
    )

    # ---------------------------------------------------------
    # 2D Fast Fourier Transform
    # ---------------------------------------------------------

    fft = np.fft.fft2(
        gray
    )

    fft_shifted = np.fft.fftshift(
        fft
    )

    magnitude = np.abs(
        fft_shifted
    )

    height, width = magnitude.shape

    center_y = height // 2
    center_x = width // 2

    # Low-frequency region around the FFT centre.
    radius = max(
        2,
        min(
            height,
            width,
        ) // 10,
    )

    low_frequency_mask = np.zeros(
        magnitude.shape,
        dtype=bool,
    )

    y1 = max(
        0,
        center_y - radius,
    )
    y2 = min(
        height,
        center_y + radius + 1,
    )

    x1 = max(
        0,
        center_x - radius,
    )
    x2 = min(
        width,
        center_x + radius + 1,
    )

    low_frequency_mask[
        y1:y2,
        x1:x2,
    ] = True

    total_energy = float(
        np.sum(magnitude)
    )

    if total_energy <= 0:
        return {
            "passed": False,
            "score": 0.0,
            "high_frequency_ratio": 0.0,
            "details": {
                "message": (
                    "No usable frequency information "
                    "found in face image"
                ),
            },
        }

    low_frequency_energy = float(
        np.sum(
            magnitude[
                low_frequency_mask
            ]
        )
    )

    high_frequency_energy = max(
        0.0,
        total_energy
        - low_frequency_energy,
    )

    high_frequency_ratio = (
        high_frequency_energy
        / total_energy
    )

    # Normalize the heuristic into 0..1.
    #
    # This threshold is deliberately conservative for the
    # prototype and should later be calibrated using real
    # camera captures and spoof samples.
    score = min(
        1.0,
        max(
            0.0,
            high_frequency_ratio / 0.30,
        ),
    )

    threshold = 0.20

    passed = (
        score >= threshold
    )

    return {
        "passed": passed,
        "score": round(
            float(score),
            4,
        ),
        "high_frequency_ratio": round(
            float(
                high_frequency_ratio
            ),
            6,
        ),
        "details": {
            "threshold": threshold,
            "method": "fft_high_frequency",
            "message": (
                "FFT-based texture heuristic completed"
            ),
        },
    }

DEFAULT_FACE_MATCH_THRESHOLD = 0.60


def verify_faces(
    document_image_path: str,
    live_image_path: str,
    threshold: float = DEFAULT_FACE_MATCH_THRESHOLD,
) -> dict:
    """
    Compare the document face with a live capture.

    Pipeline:
    1. Detect largest face in document image
    2. Detect largest face in live image
    3. Compare InsightFace embeddings using cosine similarity
    4. Run basic FFT liveness heuristic on the live face crop
    5. Return match + liveness breakdown

    Important:
    The liveness check is only a lightweight heuristic.
    It is NOT production-grade anti-spoofing.
    """

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            "Face-match threshold must be between 0 and 1"
        )

    document_face = detect_and_crop_face(
        document_image_path
    )

    live_face = detect_and_crop_face(
        live_image_path
    )

    similarity = compute_similarity(
        document_face["embedding"],
        live_face["embedding"],
    )

    match = (
        similarity >= threshold
    )

    liveness = check_liveness_fft(
        live_face["crop"]
    )

    return {
        "similarity_score": round(
            float(similarity),
            4,
        ),
        "match": bool(match),
        "threshold": float(threshold),
        "liveness_passed": bool(
            liveness["passed"]
        ),
        "liveness_score": float(
            liveness["score"]
        ),
        "document_face": {
            "bbox": document_face[
                "bbox"
            ],
            "detection_score": round(
                float(
                    document_face[
                        "detection_score"
                    ]
                ),
                4,
            ),
        },
        "live_face": {
            "bbox": live_face[
                "bbox"
            ],
            "detection_score": round(
                float(
                    live_face[
                        "detection_score"
                    ]
                ),
                4,
            ),
        },
        "liveness": {
            "high_frequency_ratio": (
                liveness[
                    "high_frequency_ratio"
                ]
            ),
            "details": liveness[
                "details"
            ],
        },
    }