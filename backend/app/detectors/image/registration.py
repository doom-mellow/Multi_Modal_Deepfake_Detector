
from pathlib import Path

from app.services.detector_registry import detector_registry


BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "models" / "image_detector.pt"


def register_image_detector() -> bool:
    """
    Register the image detector only when its trained
    checkpoint is available.
    """

    if not MODEL_PATH.is_file():
        return False

    from app.detectors.image.predictor import detect_image

    detector_registry.register(
        "image",
        detect_image,
    )

    return True
