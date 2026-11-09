
MAX_FILE_SIZE = 100 * 1024 * 1024

ALLOWED_MODALITIES = {
    "image",
    "video",
    "audio",
    "text",
    "code",
    "embedding",
    "watermark",
}

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "video": {".mp4", ".avi", ".mov", ".webm"},
    "audio": {".mp3", ".wav", ".ogg", ".webm", ".m4a"},
    "code": {
        ".py", ".js", ".jsx", ".ts", ".tsx",
        ".cpp", ".c", ".h", ".hpp", ".java",
        ".go", ".rs", ".php", ".rb", ".swift",
        ".kt", ".cs", ".html", ".css", ".json",
    },
    "embedding": {
        ".jpg", ".jpeg", ".png", ".webp",
        ".mp4", ".wav", ".mp3", ".txt", ".json",
    },
    "watermark": {
        ".jpg", ".jpeg", ".png", ".webp",
        ".mp4", ".wav", ".mp3", ".pdf",
    },
}
