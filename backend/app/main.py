
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.status import router as status_router
from app.api.routes.detection import router as detection_router
from app.api.routes.features import router as features_router
from app.api.routes.media_features import router as media_features_router

from app.detectors.image.registration import register_image_detector


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


# Register trained detectors when their checkpoints are available.
register_image_detector()


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
