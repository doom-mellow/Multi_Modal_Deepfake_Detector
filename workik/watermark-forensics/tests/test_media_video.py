from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wmforensics.media import decode_video_frames


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_video_decode_samples_frames(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    # Use ffmpeg's lavfi test pattern to make a tiny deterministic fixture.
    completed = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=64x64:r=4:d=2", "-pix_fmt", "yuv420p", "-y", str(source)],
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        pytest.skip("ffmpeg build does not provide the lavfi color source")
    frames = decode_video_frames(source, count=3)
    assert 1 <= len(frames) <= 3
    assert all(frame.mode == "RGB" for frame in frames)
