
from fastapi import APIRouter

from app.core.modalities import MODALITIES
from app.services.detector_registry import detector_registry

router = APIRouter(prefix="/status", tags=["System Status"])


@router.get("/detectors")
async def detector_status():
    available = detector_registry.available_modalities()

    detectors = {}

    for modality, configuration in MODALITIES.items():
        detectors[modality] = {
            "name": configuration["name"],
            "input_type": configuration["input_type"],
            "connected": modality in available,
            "status": (
                "connected"
                if modality in available
                else "not_connected"
            ),
        }

    return {
        "total": len(detectors),
        "connected": len(available),
        "pending": len(detectors) - len(available),
        "detectors": detectors,
    }
