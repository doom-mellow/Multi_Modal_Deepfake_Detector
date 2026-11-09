
from io import BytesIO
from pathlib import Path
from threading import Lock

import torch
from PIL import Image, ImageOps, UnidentifiedImageError
from torchvision import transforms

from fastapi import HTTPException

from app.detectors.image.model import DeepShieldImageClassifier


BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "models" / "image_detector.pt"

_model = None
_checkpoint = None
_model_lock = Lock()

MAX_IMAGE_PIXELS = 40_000_000


def load_model():
    global _model, _checkpoint

    if _model is not None:
        return _model, _checkpoint

    with _model_lock:
        if _model is not None:
            return _model, _checkpoint

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Trained image model not found: {MODEL_PATH}"
            )

        checkpoint = torch.load(
            MODEL_PATH,
            map_location="cpu",
            weights_only=True,
        )

        expected_mapping = {
            "ai_generated": 0,
            "real": 1,
        }

        if checkpoint.get("class_to_idx") != expected_mapping:
            raise ValueError(
                "The model checkpoint has an unexpected class mapping."
            )

        model = DeepShieldImageClassifier(pretrained=False)

        model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        model.eval()

        _model = model
        _checkpoint = checkpoint

    return _model, _checkpoint


def predict_image_bytes(content: bytes):
    if not content:
        raise ValueError("Image file is empty.")

    try:
        with Image.open(BytesIO(content)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError(
                    "Image dimensions exceed the supported limit."
                )

            image = ImageOps.exif_transpose(source).convert("RGB")

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValueError(
            "The uploaded file is not a valid supported image."
        ) from exc

    model, checkpoint = load_model()

    image_size = checkpoint["input_size"]

    mean = checkpoint["mean"]
    std = checkpoint["std"]

    preprocessing = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    tensor = preprocessing(image).unsqueeze(0)

    with torch.inference_mode():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0]

    ai_score = float(probabilities[0].item())
    real_score = float(probabilities[1].item())

    threshold = float(checkpoint.get("threshold", 0.5))

    result = (
        "ai-generated"
        if ai_score >= threshold
        else "real"
    )

    confidence = max(ai_score, real_score)

    uncertain = abs(ai_score - threshold) <= 0.10

    indicators = [
        {
            "name": "AI-generated probability",
            "value": round(ai_score, 4),
        },
        {
            "name": "Real-image probability",
            "value": round(real_score, 4),
        },
        {
            "name": "Decision threshold",
            "value": threshold,
        },
    ]

    explanation = (
        "The model's prediction is close to its decision threshold. "
        "Treat this result as uncertain."
        if uncertain
        else
        "Prediction generated using the trained DeepShield "
        "image classification model."
    )

    return {
        "modality": "image",
        "result": result,
        "confidence": round(confidence, 4),
        "explanation": explanation,
        "indicators": indicators,
        "metadata": {
            "model": checkpoint.get(
                "model_name",
                "DeepShield Image Classifier",
            ),
            "architecture": checkpoint.get(
                "architecture",
                "mobilenet_v3_small",
            ),
            "ai_score": round(ai_score, 4),
            "real_score": round(real_score, 4),
            "threshold": threshold,
            "uncertain": uncertain,
            "training_epoch": checkpoint.get("epoch"),
        },
    }


async def detect_image(
    content=None,
    url=None,
    file=None,
    file_metadata=None,
    language_hint=None,
    embedding_model=None,
):
    if url:
        raise HTTPException(
            status_code=501,
            detail=(
                "Image URL inference is not implemented yet. "
                "Please upload the image directly."
            ),
        )

    if file is None:
        raise HTTPException(
            status_code=400,
            detail="An image file is required.",
        )

    try:
        image_bytes = await file.read()

        return predict_image_bytes(image_bytes)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The trained image detector is not installed yet. "
                "Please install the model checkpoint."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
