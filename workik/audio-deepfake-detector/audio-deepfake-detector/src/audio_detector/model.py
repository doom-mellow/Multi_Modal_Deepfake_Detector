"""Dataset loading, training, and evaluation for audio manipulation signals."""
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

from .features import FEATURE_VERSION, extract_audio_features, feature_names

MODEL_VERSION = 1
LABELS = {"real": 0, "authentic": 0, "bonafide": 0, "0": 0,
          "fake": 1, "deepfake": 1, "spoof": 1, "synthetic": 1, "1": 1}


def read_manifest(path: str | Path) -> tuple[list[dict[str, str]], list[int]]:
    """Read CSV with audio,label and optional group columns; paths relative to CSV."""
    path = Path(path).resolve()
    records: list[dict[str, str]] = []
    labels: list[int] = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not {"audio", "label"}.issubset(set(reader.fieldnames or [])):
            raise ValueError("Manifest CSV must have 'audio' and 'label' columns; optional 'group' helps avoid split leakage")
        for row_number, row in enumerate(reader, start=2):
            audio = (row.get("audio") or "").strip()
            raw_label = (row.get("label") or "").strip().lower()
            if not audio:
                raise ValueError(f"Manifest row {row_number}: audio path is empty")
            if raw_label not in LABELS:
                raise ValueError(f"Manifest row {row_number}: label must be real or fake, got {raw_label!r}")
            audio_path = Path(audio)
            if not audio_path.is_absolute():
                audio_path = path.parent / audio_path
            if not audio_path.is_file():
                raise ValueError(f"Manifest row {row_number}: audio file not found: {audio_path}")
            records.append({"audio": str(audio_path), "group": (row.get("group") or audio).strip()})
            labels.append(LABELS[raw_label])
    if len(records) < 20 or min(labels.count(0), labels.count(1)) < 10:
        raise ValueError("Need at least 20 audio clips and at least 10 from each class")
    return records, labels


def extract_records(records: list[dict[str, str]], max_duration: float = 10.0) -> np.ndarray:
    rows = []
    expected = feature_names()
    for index, record in enumerate(records, start=1):
        features = extract_audio_features(record["audio"], max_duration=max_duration)
        if list(features.keys()) != expected:
            raise RuntimeError("Audio feature schema does not match model schema")
        rows.append([features[name] for name in expected])
        print(f"Processed {index}/{len(records)}: {Path(record['audio']).name}")
    return np.asarray(rows, dtype=np.float32)


def build_classifier(random_state: int = 42) -> VotingClassifier:
    # Acoustic spoofing and voice-conversion artifacts may be subtle and nonlinear.
    # A scaled RBF SVM complements ensemble trees on the summary features.
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


def train_model(manifest: str | Path, model_path: str | Path,
                max_duration: float = 10.0) -> dict[str, Any]:
    records, labels = read_manifest(manifest)
    groups_by_label = {label: {record["group"] for record, y in zip(records, labels) if y == label}
                       for label in (0, 1)}
    if len(groups_by_label[0]) < 2 or len(groups_by_label[1]) < 2:
        raise ValueError("Training data needs at least 2 distinct source groups in each class")
    matrix = extract_records(records, max_duration=max_duration)
    model = build_classifier()
    model.fit(matrix, labels)
    artifact = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": feature_names(),
        "model": model,
        "training_examples": len(labels),
        "class_counts": {"real": labels.count(0), "fake": labels.count(1)},
        "max_duration": max_duration,
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


def predict(artifact: dict[str, Any], audio_path: str | Path,
            max_duration: float | None = None) -> dict[str, Any]:
    duration = max_duration or float(artifact.get("max_duration", 10.0))
    values = extract_audio_features(audio_path, max_duration=duration)
    matrix = np.asarray([[values[name] for name in artifact["feature_names"]]], dtype=np.float32)
    classifier = artifact["model"]
    probabilities = classifier.predict_proba(matrix)[0]
    scores = {"real": 0.0, "fake": 0.0}
    for class_id, probability in zip(classifier.classes_, probabilities):
        scores["fake" if int(class_id) == 1 else "real"] = float(probability)
    return {
        "prediction": "likely-spoofed-or-synthetic" if scores["fake"] >= scores["real"] else "likely-authentic",
        "scores": scores,
        "audio": str(audio_path),
        "analyzed_duration_seconds": values["audio_duration"],
        "warning": "Research baseline only. Unknown speakers, codecs, edits, languages, and generators can change results; this score is not proof of authenticity or spoofing.",
    }


def evaluate(artifact: dict[str, Any], manifest: str | Path,
             max_duration: float | None = None) -> dict[str, Any]:
    records, labels = read_manifest(manifest)
    matrix = extract_records(records, max_duration=max_duration or float(artifact.get("max_duration", 10.0)))
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
        "warning": "Only an untouched test set split by speaker identity, recording session, and source/generation method yields a useful estimate; this command cannot verify split independence.",
    }
