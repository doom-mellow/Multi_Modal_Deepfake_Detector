
import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from app.detectors.image.model import DeepShieldImageClassifier


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data" / "image_dataset"
MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"

CLASS_NAMES = ["ai_generated", "real"]

IMAGE_SIZE = 160

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def create_dataloaders(batch_size, num_workers):
    train_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    evaluation_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    train_dataset = datasets.ImageFolder(
        DATA_DIR / "train",
        transform=train_transform,
    )

    val_dataset = datasets.ImageFolder(
        DATA_DIR / "val",
        transform=evaluation_transform,
    )

    test_dataset = datasets.ImageFolder(
        DATA_DIR / "test",
        transform=evaluation_transform,
    )

    expected_mapping = {
        "ai_generated": 0,
        "real": 1,
    }

    if train_dataset.class_to_idx != expected_mapping:
        raise ValueError(
            f"Unexpected training class mapping: "
            f"{train_dataset.class_to_idx}"
        )

    if val_dataset.class_to_idx != expected_mapping:
        raise ValueError("Validation class mapping does not match.")

    if test_dataset.class_to_idx != expected_mapping:
        raise ValueError("Test class mapping does not match.")

    if not train_dataset or not val_dataset or not test_dataset:
        raise ValueError("One or more dataset splits are empty.")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    return train_loader, val_loader, test_loader


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)

    total_loss = 0.0
    all_labels = []
    all_predictions = []

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        if training:
            optimizer.zero_grad()

        with torch.set_grad_enabled(training):
            outputs = model(images)
            loss = criterion(outputs, labels)

            if training:
                loss.backward()
                optimizer.step()

        total_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)

        all_labels.extend(labels.detach().cpu().numpy())
        all_predictions.extend(predictions.detach().cpu().numpy())

    average_loss = total_loss / len(loader.dataset)

    accuracy = accuracy_score(
        all_labels,
        all_predictions,
    )

    return average_loss, accuracy


def evaluate_model(model, loader, device):
    model.eval()

    labels_all = []
    predictions_all = []
    probabilities_all = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)

            outputs = model(images)
            probabilities = torch.softmax(outputs, dim=1)

            predictions = outputs.argmax(dim=1)

            labels_all.extend(labels.numpy())
            predictions_all.extend(predictions.cpu().numpy())
            probabilities_all.extend(
                probabilities[:, 0].cpu().numpy()
            )

    labels_all = np.asarray(labels_all)
    predictions_all = np.asarray(predictions_all)
    probabilities_all = np.asarray(probabilities_all)

    metrics = {
        "accuracy": float(
            accuracy_score(labels_all, predictions_all)
        ),
        "precision_macro": float(
            precision_score(
                labels_all,
                predictions_all,
                average="macro",
                zero_division=0,
            )
        ),
        "recall_macro": float(
            recall_score(
                labels_all,
                predictions_all,
                average="macro",
                zero_division=0,
            )
        ),
        "f1_macro": float(
            f1_score(
                labels_all,
                predictions_all,
                average="macro",
                zero_division=0,
            )
        ),
        "confusion_matrix": confusion_matrix(
            labels_all,
            predictions_all,
        ).tolist(),
        "classification_report": classification_report(
            labels_all,
            predictions_all,
            target_names=CLASS_NAMES,
            zero_division=0,
            output_dict=True,
        ),
    }

    if len(np.unique(labels_all)) == 2:
        metrics["ai_roc_auc"] = float(
            roc_auc_score(
                labels_all == 0,
                probabilities_all,
            )
        )

    return metrics


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    if args.epochs < 1 or args.batch_size < 1:
        raise ValueError("Epochs and batch size must be positive.")

    set_seed(args.seed)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Training device: {device}")

    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("No CUDA GPU detected. Training on CPU.")

    if device.type == "cpu":
        torch.set_num_threads(2)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    train_loader, val_loader, test_loader = create_dataloaders(
        args.batch_size,
        args.workers,
    )

    print(f"Training images: {len(train_loader.dataset)}")
    print(f"Validation images: {len(val_loader.dataset)}")
    print(f"Testing images: {len(test_loader.dataset)}")

    model = DeepShieldImageClassifier(pretrained=True)
    model.configure_fine_tuning()
    model.to(device)

    feature_parameters = [
        parameter
        for parameter in model.backbone.features.parameters()
        if parameter.requires_grad
    ]

    classifier_parameters = [
        parameter
        for parameter in model.backbone.classifier.parameters()
        if parameter.requires_grad
    ]

    optimizer = torch.optim.AdamW(
        [
            {
                "params": feature_parameters,
                "lr": args.learning_rate * 0.1,
            },
            {
                "params": classifier_parameters,
                "lr": args.learning_rate,
            },
        ],
        weight_decay=1e-4,
    )

    criterion = nn.CrossEntropyLoss()

    best_accuracy = -1.0
    best_epoch = 0

    checkpoint_path = MODEL_DIR / "image_detector.pt"

    for epoch in range(args.epochs):
        train_loss, train_accuracy = run_epoch(
            model,
            train_loader,
            criterion,
            device,
            optimizer,
        )

        val_loss, val_accuracy = run_epoch(
            model,
            val_loader,
            criterion,
            device,
        )

        print(
            f"Epoch {epoch + 1}/{args.epochs} | "
            f"Train loss: {train_loss:.4f} | "
            f"Train accuracy: {train_accuracy:.4f} | "
            f"Val loss: {val_loss:.4f} | "
            f"Val accuracy: {val_accuracy:.4f}"
        )

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_epoch = epoch + 1

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_to_idx": {
                        "ai_generated": 0,
                        "real": 1,
                    },
                    "input_size": IMAGE_SIZE,
                    "mean": IMAGENET_MEAN,
                    "std": IMAGENET_STD,
                    "threshold": 0.5,
                    "epoch": best_epoch,
                    "validation_accuracy": best_accuracy,
                    "model_name": "DeepShield MobileNetV3-Small",
                    "architecture": "mobilenet_v3_small",
                },
                checkpoint_path,
            )

            print("Best checkpoint saved.")

    # Evaluate the best validation checkpoint on the held-out test set.
    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics = evaluate_model(
        model,
        test_loader,
        device,
    )

    report = {
        "model": checkpoint["model_name"],
        "architecture": checkpoint["architecture"],
        "best_epoch": best_epoch,
        "validation_accuracy": best_accuracy,
        "test_metrics": test_metrics,
        "training_device": str(device),
        "epochs_requested": args.epochs,
        "batch_size": args.batch_size,
    }

    report_path = REPORT_DIR / "image_detector_metrics.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nFinal test metrics:")
    print(json.dumps(test_metrics, indent=4))

    print(f"\nModel saved to: {checkpoint_path}")
    print(f"Metrics saved to: {report_path}")


if __name__ == "__main__":
    main()
