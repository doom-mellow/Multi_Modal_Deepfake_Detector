"""Dataset loading, model training, and evaluation."""
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

from .features import FEATURE_VERSION, extract_video_features, feature_names

MODEL_VERSION = 1
LABELS = {"real": 0, "authentic": 0, "0": 0, "fake": 1, "deepfake": 1, "1": 1}


def read_manifest(path: str | Path) -> tuple[list[dict[str, str]], list[int]]:
    """Read CSV containing video,label and optional group, relative to manifest."""
    path = Path(path).resolve()
    records, labels = [], []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not {"video", "label"}.issubset(set(reader.fieldnames or [])):
            raise ValueError("Manifest CSV must have 'video' and 'label' columns; optional 'group' column supports leakage-safe splits")
        for row_number, row in enumerate(reader, start=2):
            video = (row.get("video") or "").strip()
            raw_label = (row.get("label") or "").strip().lower()
            if not video:
                raise ValueError(f"Manifest row {row_number}: video path is empty")
            if raw_label not in LABELS:
                raise ValueError(f"Manifest row {row_number}: label must be real or fake, got {raw_label!r}")
            video_path = Path(video)
            if not video_path.is_absolute():
                video_path = path.parent / video_path
            if not video_path.is_file():
                raise ValueError(f"Manifest row {row_number}: video not found: {video_path}")
            records.append({"video": str(video_path), "group": (row.get("group") or video).strip()})
            labels.append(LABELS[raw_label])
    if len(records) < 10 or min(labels.count(0), labels.count(1)) < 5:
        raise ValueError("Need at least 10 videos total and at least 5 from each class")
    return records, labels


def extract_records(records: list[dict[str, str]], sample_frames: int) -> np.ndarray:
    rows = []
    expected = feature_names()
    for index, record in enumerate(records, start=1):
        extracted = extract_video_features(record["video"], sample_frames=sample_frames)
        if list(extracted.keys()) != expected:
            raise RuntimeError("Extracted video feature schema does not match model schema")
        rows.append([extracted[name] for name in expected])
        print(f"Processed {index}/{len(records)}: {Path(record['video']).name}")
    return np.asarray(rows, dtype=np.float32)


def build_classifier(random_state: int = 42) -> VotingClassifier:
    # Two distinct tree ensembles capture nonlinear feature interactions without
    # requiring pretrained weights or GPU support. Both see the same tabular cues.
    forest = make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=2,
                               class_weight="balanced_subsample", random_state=random_state,
                               n_jobs=-1),
    )
    extra = make_pipeline(
        SimpleImputer(strategy="median"),
        ExtraTreesClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=2,
                             class_weight="balanced", random_state=random_state + 1,
                             n_jobs=-1),
    )
    return VotingClassifier([("forest", forest), ("extra", extra)], voting="soft", n_jobs=1)


def train_model(manifest: str | Path, model_path: str | Path, sample_frames: int = 16) -> dict[str, Any]:
    records, labels = read_manifest(manifest)
    groups_by_label = {label: {record["group"] for record, y in zip(records, labels) if y == label} for label in (0, 1)}
    if len(groups_by_label[0]) < 2 or len(groups_by_label[1]) < 2:
        raise ValueError("Training data needs at least 2 distinct real groups and 2 distinct fake groups (e.g. source video or identity)")
    matrix = extract_records(records, sample_frames)
    model = build_classifier()
    model.fit(matrix, labels)
    artifact = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": feature_names(),
        "model": model,
        "training_examples": len(labels),
        "class_counts": {"real": labels.count(0), "fake": labels.count(1)},
        "sample_frames": sample_frames,
    }
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, destination, compress=3)
    return {key: value for key, value in artifact.items() if key != "model" and key != "feature_names"} | {"model_path": str(destination)}


def load_model(path: str | Path) -> dict[str, Any]:
    artifact = joblib.load(path)
    if (not isinstance(artifact, dict) or artifact.get("model_version") != MODEL_VERSION
            or artifact.get("feature_version") != FEATURE_VERSION
            or artifact.get("feature_names") != feature_names()):
        raise ValueError("Unsupported or invalid model artifact/feature schema")
    return artifact


def predict(artifact: dict[str, Any], video_path: str | Path, sample_frames: int | None = None) -> dict[str, Any]:
    used_frames = sample_frames or int(artifact.get("sample_frames", 16))
    values = extract_video_features(video_path, sample_frames=used_frames)
    matrix = np.asarray([[values[name] for name in artifact["feature_names"]]], dtype=np.float32)
    classifier = artifact["model"]
    scores_raw = classifier.predict_proba(matrix)[0]
    scores = {"real": 0.0, "fake": 0.0}
    for class_id, probability in zip(classifier.classes_, scores_raw):
        scores["fake" if int(class_id) == 1 else "real"] = float(probability)
    return {
        "prediction": "likely-manipulated" if scores["fake"] >= scores["real"] else "likely-authentic",
        "scores": scores,
        "video": str(video_path),
        "frames_sampled": used_frames,
        "warning": "Research baseline only. Compression, editing, source identity, and unknown generators can change results; this score is not proof of manipulation or authenticity.",
    }


def evaluate(artifact: dict[str, Any], manifest: str | Path, sample_frames: int | None = None) -> dict[str, Any]:
    records, labels = read_manifest(manifest)
    matrix = extract_records(records, sample_frames or int(artifact.get("sample_frames", 16)))
    predictions = artifact["model"].predict(matrix)
    return {
        "examples": len(labels),
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "precision_fake": float(precision_score(labels, predictions, pos_label=1, zero_division=0)),
        "recall_fake": float(recall_score(labels, predictions, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
        "class_report": classification_report(labels, predictions, labels=[0, 1], target_names=["real", "fake"], output_dict=True, zero_division=0),
        "warning": "Only a held-out dataset split by source video and subject identity gives a defensible estimate; this utility computes scores but cannot verify that split design.",
    }
