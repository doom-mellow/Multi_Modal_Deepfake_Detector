"""Manifest loading, training, and evaluation for image manipulation detection."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .features import FEATURE_VERSION, extract_image_features, feature_names

MODEL_VERSION = 1
LABELS = {"real": 0, "authentic": 0, "0": 0, "fake": 1, "deepfake": 1, "synthetic": 1, "generated": 1, "1": 1}


def read_manifest(path: str | Path) -> tuple[list[dict[str, str]], list[int]]:
    """Read CSV with image,label and optional group; relative paths are manifest-relative."""
    path = Path(path).resolve()
    records: list[dict[str, str]] = []
    labels: list[int] = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not {"image", "label"}.issubset(set(reader.fieldnames or [])):
            raise ValueError("Manifest CSV must have 'image' and 'label' columns; optional 'group' helps prevent data leakage")
        for row_number, row in enumerate(reader, start=2):
            image = (row.get("image") or "").strip()
            raw_label = (row.get("label") or "").strip().lower()
            if not image:
                raise ValueError(f"Manifest row {row_number}: image path is empty")
            if raw_label not in LABELS:
                raise ValueError(f"Manifest row {row_number}: label must be real or fake, got {raw_label!r}")
            image_path = Path(image)
            if not image_path.is_absolute():
                image_path = path.parent / image_path
            if not image_path.is_file():
                raise ValueError(f"Manifest row {row_number}: image not found: {image_path}")
            records.append({"image": str(image_path), "group": (row.get("group") or image).strip()})
            labels.append(LABELS[raw_label])
    if len(records) < 20 or min(labels.count(0), labels.count(1)) < 10:
        raise ValueError("Need at least 20 images total and at least 10 from each class")
    return records, labels


def extract_records(records: list[dict[str, str]]) -> np.ndarray:
    rows = []
    expected = feature_names()
    for index, record in enumerate(records, start=1):
        features = extract_image_features(record["image"])
        if list(features.keys()) != expected:
            raise RuntimeError("Image feature schema does not match model schema")
        rows.append([features[name] for name in expected])
        print(f"Processed {index}/{len(records)}: {Path(record['image']).name}")
    return np.asarray(rows, dtype=np.float32)


def build_classifier(random_state: int = 42) -> VotingClassifier:
    svm = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                        SVC(C=2.0, kernel="rbf", class_weight="balanced", probability=True,
                            random_state=random_state))
    forest = make_pipeline(SimpleImputer(strategy="median"),
                           RandomForestClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=2,
                                                  class_weight="balanced_subsample", random_state=random_state + 1,
                                                  n_jobs=-1))
    extra = make_pipeline(SimpleImputer(strategy="median"),
                          ExtraTreesClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=2,
                                               class_weight="balanced", random_state=random_state + 2,
                                               n_jobs=-1))
    return VotingClassifier([("svm", svm), ("forest", forest), ("extra", extra)], voting="soft", n_jobs=1)


def train_model(manifest: str | Path, model_path: str | Path) -> dict[str, Any]:
    records, labels = read_manifest(manifest)
    groups_by_label = {label: {record["group"] for record, y in zip(records, labels) if y == label}
                       for label in (0, 1)}
    if len(groups_by_label[0]) < 2 or len(groups_by_label[1]) < 2:
        raise ValueError("Training data needs at least 2 distinct source groups in each class")
    matrix = extract_records(records)
    model = build_classifier()
    model.fit(matrix, labels)
    artifact = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": feature_names(),
        "model": model,
        "training_examples": len(labels),
        "class_counts": {"real": labels.count(0), "fake": labels.count(1)},
    }
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, destination, compress=3)
    return {key: value for key, value in artifact.items() if key not in {"model", "feature_names"}} | {"model_path": str(destination)}


def load_model(path: str | Path) -> dict[str, Any]:
    artifact = joblib.load(path)
    if (not isinstance(artifact, dict) or artifact.get("model_version") != MODEL_VERSION
            or artifact.get("feature_version") != FEATURE_VERSION
            or artifact.get("feature_names") != feature_names()):
        raise ValueError("Unsupported or invalid model artifact/feature schema")
    return artifact


def predict(artifact: dict[str, Any], image_path: str | Path) -> dict[str, Any]:
    values = extract_image_features(image_path)
    matrix = np.asarray([[values[name] for name in artifact["feature_names"]]], dtype=np.float32)
    classifier = artifact["model"]
    probabilities = classifier.predict_proba(matrix)[0]
    scores = {"real": 0.0, "fake": 0.0}
    for class_id, probability in zip(classifier.classes_, probabilities):
        scores["fake" if int(class_id) == 1 else "real"] = float(probability)
    return {
        "prediction": "likely-manipulated-or-generated" if scores["fake"] >= scores["real"] else "likely-authentic",
        "scores": scores,
        "image": str(image_path),
        "warning": "Research baseline only. Resizing, recompression, edits, subject matter, and unknown generation methods can change results; this is not proof of authenticity or manipulation.",
    }


def evaluate(artifact: dict[str, Any], manifest: str | Path) -> dict[str, Any]:
    records, labels = read_manifest(manifest)
    matrix = extract_records(records)
    predictions = artifact["model"].predict(matrix)
    return {
        "examples": len(labels),
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "precision_fake": float(precision_score(labels, predictions, pos_label=1, zero_division=0)),
        "recall_fake": float(recall_score(labels, predictions, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
        "class_report": classification_report(labels, predictions, labels=[0, 1],
                                               target_names=["real", "fake"], output_dict=True, zero_division=0),
        "warning": "Only an untouched, representative test set split by source image, subject identity, and generation method provides a useful estimate; this command cannot verify split independence.",
    }
