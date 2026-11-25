from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wmforensics.custom_model import CustomImageDetector, load_custom_checkpoint
from wmforensics.media import load_image_tensor, read_wav_mono
from wmforensics.schemes import analyze, selected_schemes
from wmforensics.train import WatermarkImageDataset, balanced_accuracy_threshold


def _write_image(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (48, 48), color).save(path)


def test_custom_model_logits_shape_and_gradients() -> None:
    model = CustomImageDetector(width=8, blocks=1)
    images = torch.randn(2, 3, 64, 64)
    logits = model(images)
    assert logits.shape == (2,)
    logits.sum().backward()
    assert model.classifier.weight.grad is not None


def test_training_dataset_folder_classes_and_normalization(tmp_path: Path) -> None:
    for split in ("clean", "marked"):
        (tmp_path / split).mkdir()
    _write_image(tmp_path / "clean" / "negative.png", (32, 40, 50))
    _write_image(tmp_path / "marked" / "positive.png", (220, 190, 170))
    dataset = WatermarkImageDataset(root=str(tmp_path), image_size=32, augment=False)
    image, label = dataset[0]
    assert image.shape == (3, 32, 32)
    assert -1 <= image.min() <= image.max() <= 1
    assert {int(dataset[i][1]) for i in range(len(dataset))} == {0, 1}


def test_manifest_relative_paths_and_labels(tmp_path: Path) -> None:
    (tmp_path / "imgs").mkdir()
    _write_image(tmp_path / "imgs" / "a.png", (10, 20, 30))
    _write_image(tmp_path / "imgs" / "b.png", (200, 210, 220))
    manifest = tmp_path / "train.jsonl"
    manifest.write_text('{"path":"imgs/a.png","label":0}\n{"path":"imgs/b.png","label":1}\n')
    dataset = WatermarkImageDataset(manifest=str(manifest), image_size=32)
    assert len(dataset) == 2


def test_balanced_accuracy_threshold() -> None:
    threshold, score = balanced_accuracy_threshold(np.array([0.1, 0.25, 0.75, 0.9]), np.array([0, 0, 1, 1]))
    assert 0.25 <= threshold <= 0.75
    assert score == pytest.approx(1.0)


def test_train_custom_one_epoch_and_safe_checkpoint_reload(tmp_path: Path) -> None:
    from wmforensics.train import train_custom

    train_root, val_root = tmp_path / "train", tmp_path / "val"
    for root in (train_root, val_root):
        (root / "clean").mkdir(parents=True)
        (root / "marked").mkdir(parents=True)
        for i in range(2):
            _write_image(root / "clean" / f"{i}.png", (20 + i, 40, 60))
            _write_image(root / "marked" / f"{i}.png", (220 - i, 180, 160))
    checkpoint = tmp_path / "model.pt"
    stats = train_custom(
        train_dir=str(train_root), val_dir=str(val_root), output=str(checkpoint),
        epochs=1, batch_size=2, image_size=32, width=8, blocks=1,
    )
    model, payload = load_custom_checkpoint(str(checkpoint), torch.device("cpu"))
    assert stats["train_examples"] == 4
    assert payload["format"] == "wmforensics.custom.v1"
    assert isinstance(model, CustomImageDetector)


def test_image_loader_and_default_scheme_selection(tmp_path: Path) -> None:
    image = tmp_path / "asset.png"
    _write_image(image, (100, 120, 140))
    assert load_image_tensor(image, 40).shape == (3, 40, 40)
    assert selected_schemes(image, None, has_custom=False) == ["c2pa"]
    video = tmp_path / "asset.mp4"
    assert selected_schemes(video, None, has_custom=True) == ["video", "custom"]


def test_manifest_jsonl_training_smoke(tmp_path: Path) -> None:
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _write_image(image_a, (10, 20, 30))
    _write_image(image_b, (230, 210, 190))
    train_manifest = tmp_path / "train.jsonl"
    val_manifest = tmp_path / "val.jsonl"
    contents = f'{json.dumps({"path": "a.png", "label": 0})}\n{json.dumps({"path": "b.png", "label": 1})}\n'
    train_manifest.write_text(contents)
    val_manifest.write_text(contents)
    from wmforensics.train import train_custom

    result = train_custom(
        train_manifest=str(train_manifest), val_manifest=str(val_manifest),
        output=str(tmp_path / "manifest.pt"), epochs=1, batch_size=2,
        image_size=32, width=8, blocks=1,
    )
    assert Path(result["output"]).is_file()


def test_analyze_keeps_scheme_results_separate_and_reports_missing_checkpoint(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    _write_image(image, (120, 110, 100))
    outcomes = analyze(image, ["custom", "not-a-scheme"], torch.device("cpu"))
    assert [item.scheme for item in outcomes] == ["custom", "not-a-scheme"]
    assert outcomes[0].status == "unavailable"
    assert outcomes[1].status == "error"


def test_wav_reader_resamples(tmp_path: Path) -> None:
    from scipy.io import wavfile

    path = tmp_path / "tone.wav"
    wavfile.write(path, 8000, (np.sin(np.arange(800, dtype=np.float32) / 10) * 0.5).astype(np.float32))
    audio, rate = read_wav_mono(path, 16000)
    assert rate == 16000
    assert len(audio) == 1600


def test_cli_reports_missing_asset(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "wmforensics.cli", "inspect", str(tmp_path / "missing.png"), "--json"],
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "does not exist" in completed.stderr


def test_c2pa_missing_manifest_is_a_non_error(tmp_path: Path) -> None:
    pytest.importorskip("c2pa")
    from wmforensics.schemes import detect_c2pa

    image = tmp_path / "plain.jpg"
    _write_image(image, (10, 20, 30))
    outcome = detect_c2pa(image)
    assert outcome.scheme == "c2pa"
    assert outcome.status == "not_detected"
    assert outcome.evidence["manifest_present"] is False


def test_c2pa_missing_manifest_on_video(tmp_path: Path) -> None:
    pytest.importorskip("c2pa")
    from wmforensics.schemes import detect_c2pa
    import shutil
    import subprocess

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is not installed")
    video = tmp_path / "plain.mp4"
    completed = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=64x64:r=2:d=1", "-pix_fmt", "yuv420p", "-y", str(video)],
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        pytest.skip("ffmpeg cannot generate the synthetic fixture")
    outcome = detect_c2pa(video)
    assert outcome.status == "not_detected"