
MODALITIES = {
    "image": {
        "name": "Image Detection",
        "input_type": "file_or_url",
        "detector_path": "app.detectors.image",
    },
    "video": {
        "name": "Video Detection",
        "input_type": "file_or_url",
        "detector_path": "app.detectors.video",
    },
    "audio": {
        "name": "Audio Detection",
        "input_type": "file",
        "detector_path": "app.detectors.audio",
    },
    "text": {
        "name": "Text Detection",
        "input_type": "text",
        "detector_path": "app.detectors.text",
    },
    "code": {
        "name": "Code Detection",
        "input_type": "text_or_file",
        "detector_path": "app.detectors.code",
    },
    "embedding": {
        "name": "Embedding Analysis",
        "input_type": "file_or_text",
        "detector_path": "app.detectors.embedding",
    },
    "watermark": {
        "name": "Watermark Analysis",
        "input_type": "file_or_url",
        "detector_path": "app.detectors.watermark",
    },
}
