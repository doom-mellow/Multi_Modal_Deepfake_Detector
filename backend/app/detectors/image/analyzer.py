from io import BytesIO

from PIL import Image, UnidentifiedImageError


def analyze_image(content: bytes) -> dict:
    if not content:
        raise ValueError("Image file is empty.")

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()

        with Image.open(BytesIO(content)) as image:
            return {
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "color_mode": image.mode,
                "frame_count": getattr(image, "n_frames", 1),
                "file_size_bytes": len(content),
                "is_animated": getattr(image, "n_frames", 1) > 1,
            }

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValueError(
            "The uploaded file is not a valid or supported image."
        ) from exc