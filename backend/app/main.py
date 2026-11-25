
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.detectors.text.registration import register_text_detector
from app.api.routes.status import router as status_router
from app.api.routes.detection import router as detection_router
from app.api.routes.features import router as features_router
from app.api.routes.media_features import router as media_features_router
from app.detectors.code.registration import register_code_detector
from app.detectors.image.registration import register_image_detector
from app.detectors.video.registration import register_video_detector
from app.detectors.audio.registration import register_audio_detector
from app.detectors.watermark.registration import register_watermark_detector

app = FastAPI(
    title="DeepShield AI API",
    description="Multimodal digital content analysis and forensic API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register available detectors.
register_image_detector()
register_video_detector()
register_audio_detector()
register_text_detector()
register_code_detector()
register_watermark_detector()

app.include_router(detection_router, prefix="/api/v1")
app.include_router(status_router, prefix="/api/v1")
app.include_router(features_router, prefix="/api/v1")
app.include_router(media_features_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "DeepShield AI",
        "message": "Backend is running.",
        "documentation": "/docs",
    }


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DeepShield AI API",
        "version": "1.0.0",
    }
