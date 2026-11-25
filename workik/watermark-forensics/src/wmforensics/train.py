"""Training loop and datasets for the standalone custom image detector."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from torch import nn
from torch.utils.data import DataLoader, Dataset

from .custom_model import CustomImageDetector
from .media import load_image_tensor


class WatermarkImageDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Folder-layout or JSONL-labeled image dataset with train-only distortions."""

    VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    CLASS_LABELS = {"clean": 0, "negative": 0, "unmarked": 0, "real": 0, "marked": 1, "watermarked": 1, "positive": 1}

    def __init__(self, root: str | None = None, manifest: str | None = None, image_size: int = 224, augment: bool = False) -> None:
        if bool(root) == bool(manifest):
            raise ValueError("Provide exactly one of root or manifest")
        self.image_size = image_size
        self.augment = augment
        self.samples: list[tuple[Path, int]] = []
        if root:
            base = Path(root)
            if not base.is_dir():
                raise FileNotFoundError(f"Dataset directory does not exist: {base}")
            class_dirs = sorted(p for p in base.iterdir() if p.is_dir())
            if not class_dirs:
                raise ValueError(f"Expected clean/ and marked/ class folders inside {base}")
            for class_dir in class_dirs:
                label = self.CLASS_LABELS.get(class_dir.name.lower())
                if label is None:
                    raise ValueError(f"Unrecognized class directory {class_dir.name!r}; use clean/marked")
                self.samples.extend((p, label) for p in sorted(class_dir.rglob("*")) if p.is_file() and p.suffix.lower() in self.VALID_EXTENSIONS)
        else:
            manifest_path = Path(manifest).resolve()
            for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                label = int(record["label"])
                if label not in (0, 1):
                    raise ValueError(f"Manifest label at line {line_number} must be 0 or 1")
                image_path = Path(record["path"])
                if not image_path.is_absolute():
                    image_path = manifest_path.parent / image_path
                self.samples.append((image_path, label))
        if not self.samples:
            raise ValueError(f"No supported images found in {root or manifest}")
        labels = {label for _, label in self.samples}
        if labels != {0, 1}:
            raise ValueError("Dataset must contain both clean (0) and marked (1) examples")

    def __len__(self) -> int:
        return len(self.samples)

    def _load_augmented(self, path: Path) -> torch.Tensor:
        with Image.open(path) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
            if self.augment:
                if random.random() < 0.5:
                    image = ImageOps.mirror(image)
                if random.random() < 0.25:
                    image = image.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.1, 1.3)))
                if random.random() < 0.6:
                    image = ImageEnhance.Contrast(image).enhance(random.uniform(0.75, 1.25))
                if random.random() < 0.5:
                    quality = random.randint(45, 95)
                    import io
                    encoded = io.BytesIO()
                    image.save(encoded, format="JPEG", quality=quality)
                    encoded.seek(0)
                    with Image.open(encoded) as compressed:
                        image = compressed.convert("RGB")
                if random.random() < 0.2:
                    scale = random.uniform(0.55, 0.9)
                    small = max(16, int(self.image_size * scale))
                    image = image.resize((small, small), Image.Resampling.BILINEAR).resize((self.image_size, self.image_size), Image.Resampling.BILINEAR)
            image = ImageOps.fit(image, (self.image_size, self.image_size), method=Image.Resampling.BILINEAR)
            pixels = np.asarray(image, dtype=np.float32).copy() / 255.0
        return (torch.from_numpy(pixels).permute(2, 0, 1) - 0.5) / 0.5

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        path, label = self.samples[index]
        image = self._load_augmented(path)
        return image, torch.tensor(label, dtype=torch.float32)


def _evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, np.ndarray, np.ndarray]:
    loss_fn = nn.BCEWithLogitsLoss()
    total_loss = 0.0
    probabilities: list[torch.Tensor] = []
    labels: list[torch.Tensor] = []
    model.eval()
    with torch.inference_mode():
        for images, targets in loader:
            images, targets = images.to(device), targets.to(device)
            logits = model(images)
            total_loss += float(loss_fn(logits, targets).item()) * len(targets)
            probabilities.append(logits.sigmoid().cpu())
            labels.append(targets.cpu())
    return total_loss / max(len(loader.dataset), 1), torch.cat(probabilities).numpy(), torch.cat(labels).numpy()


def balanced_accuracy_threshold(probabilities: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """Choose a validation-set threshold by balanced accuracy (for development)."""
    candidates = np.unique(np.concatenate(([0.0, 0.5, 1.0], probabilities)))
    best_threshold, best_score = 0.5, -1.0
    for threshold in candidates:
        predicted = probabilities >= threshold
        positive = labels == 1
        negative = labels == 0
        tpr = float(predicted[positive].mean()) if positive.any() else 0.0
        tnr = float((~predicted[negative]).mean()) if negative.any() else 0.0
        score = (tpr + tnr) / 2
        if score > best_score or (score == best_score and abs(float(threshold) - 0.5) < abs(best_threshold - 0.5)):
            best_threshold, best_score = float(threshold), score
    return best_threshold, best_score


def train_custom(
    train_dir: str | None = None,
    val_dir: str | None = None,
    train_manifest: str | None = None,
    val_manifest: str | None = None,
    output: str = "checkpoints/custom_image.pt",
    epochs: int = 15,
    batch_size: int = 16,
    learning_rate: float = 3e-4,
    image_size: int = 224,
    width: int = 32,
    blocks: int = 3,
    workers: int = 0,
    seed: int = 17,
    device_name: str = "cpu",
    target: str = "custom_image_watermark",
) -> dict[str, Any]:
    """Fit the custom detector only and save the best validation-loss weights."""
    if epochs < 1 or batch_size < 1 or image_size < 32:
        raise ValueError("epochs/batch_size must be positive and image_size must be at least 32")
    if bool(train_dir) != bool(val_dir) or bool(train_manifest) != bool(val_manifest):
        raise ValueError("Provide both training and validation directories or both manifests")
    if not ((train_dir and val_dir) or (train_manifest and val_manifest)):
        raise ValueError("Provide training/validation directories or training/validation manifests")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device(device_name)
    train_data = WatermarkImageDataset(train_dir, train_manifest, image_size, augment=True)
    val_data = WatermarkImageDataset(val_dir, val_manifest, image_size, augment=False)
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True, num_workers=workers, pin_memory=device.type == "cuda")
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False, num_workers=workers, pin_memory=device.type == "cuda")
    model = CustomImageDetector(width=width, blocks=blocks).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    loss_fn = nn.BCEWithLogitsLoss()
    best_loss = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.detach().item()) * len(labels)
        val_loss, probabilities, labels_np = _evaluate(model, val_loader, device)
        threshold, balanced_accuracy = balanced_accuracy_threshold(probabilities, labels_np)
        record = {"epoch": float(epoch), "train_loss": running_loss / len(train_data), "val_loss": val_loss, "val_balanced_accuracy": balanced_accuracy, "val_threshold": threshold}
        history.append(record)
        if val_loss < best_loss:
            best_loss = val_loss
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        print(json.dumps(record))
    assert best_state is not None
    model.load_state_dict(best_state)
    _, best_probabilities, best_labels = _evaluate(model, val_loader, device)
    threshold, balanced_accuracy = balanced_accuracy_threshold(best_probabilities, best_labels)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "format": "wmforensics.custom.v1",
        "state_dict": best_state,
        "config": {"width": width, "blocks": blocks, "image_size": image_size, "mean": [0.5, 0.5, 0.5], "std": [0.5, 0.5, 0.5], "target": target},
        "threshold": threshold,
        "validation": {"best_epoch_val_loss": best_loss, "balanced_accuracy": balanced_accuracy, "num_examples": len(val_data), "history": history},
        "seed": seed,
    }
    torch.save(checkpoint, output_path)
    return {"output": str(output_path), "threshold": threshold, "validation_balanced_accuracy": balanced_accuracy, "validation_loss": best_loss, "epochs": epochs, "train_examples": len(train_data), "validation_examples": len(val_data)}