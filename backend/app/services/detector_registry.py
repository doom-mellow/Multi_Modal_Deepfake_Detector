
from typing import Callable, Awaitable, Any


DetectorFunction = Callable[..., Awaitable[Any]]


class DetectorRegistry:
    def __init__(self):
        self._detectors: dict[str, DetectorFunction] = {}

    def register(self, modality: str, detector: DetectorFunction):
        self._detectors[modality] = detector

    def get(self, modality: str):
        return self._detectors.get(modality)

    def available_modalities(self):
        return list(self._detectors.keys())


detector_registry = DetectorRegistry()
