
import torch

from app.detectors.image.model import DeepShieldImageClassifier


def test_image_classifier_output_shape():
    model = DeepShieldImageClassifier(pretrained=False)
    model.eval()

    sample = torch.randn(1, 3, 160, 160)

    with torch.no_grad():
        output = model(sample)

    assert output.shape == (1, 2)


def test_fine_tuning_configuration():
    model = DeepShieldImageClassifier(pretrained=False)
    model.configure_fine_tuning()

    feature_blocks = list(model.backbone.features.children())

    # Earlier feature blocks should remain frozen.
    for block in feature_blocks[:-2]:
        for parameter in block.parameters():
            assert parameter.requires_grad is False

    # Final two feature blocks should be trainable.
    for block in feature_blocks[-2:]:
        for parameter in block.parameters():
            assert parameter.requires_grad is True

    # Classification head should be trainable.
    for parameter in model.backbone.classifier.parameters():
        assert parameter.requires_grad is True
