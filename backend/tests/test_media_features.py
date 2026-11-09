from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app
import numpy as np
import app.detectors.video.analyzer as video_analyzer


client = TestClient(app)


def create_test_image() -> bytes:
    buffer = BytesIO()

    image = Image.new("RGB", (120, 80), color="white")
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def test_image_feature_analysis():
    image_bytes = create_test_image()

    response = client.post(
        "/api/v1/features/image",
        files={
            "file": (
                "test.png",
                image_bytes,
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["format"] == "PNG"
    assert data["width"] == 120
    assert data["height"] == 80
    assert data["color_mode"] == "RGB"


def test_invalid_image_rejected():
    response = client.post(
        "/api/v1/features/image",
        files={
            "file": (
                "fake.png",
                b"this is not an image",
                "image/png",
            )
        },
    )

    assert response.status_code == 400



def test_video_frame_extraction(monkeypatch):
    class FakeVideoCapture:
        def __init__(self, path):
            self.properties = {
                video_analyzer.cv2.CAP_PROP_FPS: 30.0,
                video_analyzer.cv2.CAP_PROP_FRAME_COUNT: 30,
                video_analyzer.cv2.CAP_PROP_FRAME_WIDTH: 1280,
                video_analyzer.cv2.CAP_PROP_FRAME_HEIGHT: 720,
            }

        def isOpened(self):
            return True

        def get(self, property_id):
            return self.properties[property_id]

        def set(self, property_id, value):
            return True

        def read(self):
            frame = np.full(
                (720, 1280, 3),
                128,
                dtype=np.uint8,
            )
            return True, frame

        def release(self):
            pass

    monkeypatch.setattr(
        video_analyzer.cv2,
        "VideoCapture",
        FakeVideoCapture,
    )

    video_header = (
        b"\x00\x00\x00\x18"
        + b"ftyp"
        + b"isom"
        + b"\x00\x00\x02\x00"
        + b"isom"
    )

    result = video_analyzer.analyze_video(
        video_header,
        "test.mp4",
    )

    assert result["container"] == "isobmff"
    assert result["header_valid"] is True
    assert result["fps"] == 30.0
    assert result["duration_seconds"] == 1.0
    assert result["total_frames"] == 30
    assert result["frames_extracted"] == 12
    assert len(result["sampled_frames"]) == 12

    first_frame = result["sampled_frames"][0]

    assert first_frame["frame_index"] == 0
    assert first_frame["width"] == 640
    assert first_frame["height"] == 360



def test_invalid_video_rejected():
    response = client.post(
        "/api/v1/features/video",
        files={
            "file": (
                "fake.mp4",
                b"this is not a video",
                "video/mp4",
            )
        },
    )

    assert response.status_code == 400