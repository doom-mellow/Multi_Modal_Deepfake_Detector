"""A small independently trainable image watermark detector."""

from __future__ import annotations

import torch
from torch import nn


class ResidualBlock(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.GELU(),
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.activation = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.activation(x + self.block(x))


class CustomImageDetector(nn.Module):
    """Binary detector for one target image watermark, not generic deepfakes.

    A high-pass residual stem emphasizes local forensic traces. This compact
    architecture is a baseline; validate it against the intended watermark and
    realistic transforms before drawing conclusions from its output.
    """

    def __init__(self, width: int = 32, blocks: int = 3) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(6, width, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(width),
            nn.GELU(),
            nn.Conv2d(width, width, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(width),
            nn.GELU(),
            *[ResidualBlock(width) for _ in range(blocks)],
            nn.Conv2d(width, width * 2, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(width * 2),
            nn.GELU(),
            nn.Conv2d(width * 2, width * 2, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(width * 2),
            nn.GELU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
        )
        self.classifier = nn.Linear(width * 2, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Concatenate a fixed high-pass residual with RGB so the model can
        # prioritize subtle local traces as well as image-level context.
        residual = x - torch.nn.functional.avg_pool2d(x, kernel_size=3, stride=1, padding=1, count_include_pad=False)
        return self.classifier(self.features(torch.cat((x, residual), dim=1))).squeeze(-1)


def load_custom_checkpoint(path: str, device: torch.device) -> tuple[CustomImageDetector, dict]:
    """Load a checkpoint written by the provided training pipeline."""
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    if checkpoint.get("format") != "wmforensics.custom.v1":
        raise ValueError("Unsupported custom checkpoint format")
    config = checkpoint["config"]
    model = CustomImageDetector(width=int(config["width"]), blocks=int(config["blocks"]))
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device).eval()
    return model, checkpoint