
import torch.nn as nn
from torchvision.models import (
    MobileNet_V3_Small_Weights,
    mobilenet_v3_small,
)


class DeepShieldImageClassifier(nn.Module):
    """
    Binary image classifier:
    0 = AI-generated
    1 = Real
    """

    def __init__(self, pretrained: bool = False):
        super().__init__()

        weights = (
            MobileNet_V3_Small_Weights.DEFAULT
            if pretrained
            else None
        )

        self.backbone = mobilenet_v3_small(weights=weights)

        input_features = self.backbone.classifier[0].in_features

        self.backbone.classifier = nn.Sequential(
            nn.Linear(input_features, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.35),
            nn.Linear(128, 2),
        )

    def configure_fine_tuning(self):
        # Freeze the pretrained feature extractor first.
        for parameter in self.backbone.features.parameters():
            parameter.requires_grad = False

        # Unfreeze the final two feature blocks.
        for block in list(self.backbone.features.children())[-2:]:
            for parameter in block.parameters():
                parameter.requires_grad = True

        # Train the complete classification head.
        for parameter in self.backbone.classifier.parameters():
            parameter.requires_grad = True

    def forward(self, images):
        return self.backbone(images)
