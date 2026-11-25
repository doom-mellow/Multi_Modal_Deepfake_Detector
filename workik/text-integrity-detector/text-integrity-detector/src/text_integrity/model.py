"""Training and evaluation for a supervised human-vs-AI text classifier."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from .features import style_features

MODEL_VERSION = 1


def _text_column(samples: list[dict[str, str]]) -> list[str]:
    return [sample["text"] for sample in samples]


def _style_column(samples: list[dict[str, str]]) -> list[dict[str, float]]:
    return [style_features(sample["text"]) for sample in samples]


def build_model() -> Pipeline:
    features = FeatureUnion([
        ("word_ngrams", Pipeline([
            ("select", FunctionTransformer(_text_column, validate=False)),
            ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 3), min_df=1,
                                      max_features=100_000, sublinear_tf=True, dtype=np.float32)),
        ])),
        ("char_ngrams", Pipeline([
            ("select", FunctionTransformer(_text_column, validate=False)),
            ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=1,
                                      max_features=150_000, sublinear_tf=True, dtype=np.float32)),
        ])),
        ("style", Pipeline([
            ("select", FunctionTransformer(_style_column, validate=False)),
            ("dict", DictVectorizer(sparse=True)),
        ])),
    ], transformer_weights={"word_ngrams": 0.9, "char_ngrams": 1.0, "style": 0.25})
    return Pipeline([
        ("features", features),
        ("classifier", LogisticRegression(C=1.0, class_weight="balanced", max_iter=1500,
                                           solver="liblinear", random_state=42)),
    ])


def read_dataset(path: str | Path) -> tuple[list[dict[str, str]], list[int]]:
    """Read CSV with `text,label`; labels accept human/ai and common aliases."""
    samples: list[dict[str, str]] = []
    labels: list[int] = []
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fields = set(reader.fieldnames or [])
        if not {"text", "label"}.issubset(fields):
            raise ValueError("CSV must have 'text' and 'label' columns")
        for row_number, row in enumerate(reader, start=2):
            text = (row.get("text") or "").strip()
            raw_label = (row.get("label") or "").strip().lower()
            if not text:
                raise ValueError(f"CSV row {row_number}: text is empty")
            if raw_label in {"human", "human-written", "human_written", "0"}:
                label = 0
            elif raw_label in {"ai", "ai-generated", "ai_generated", "generated", "1"}:
                label = 1
            else:
                raise ValueError(f"CSV row {row_number}: label must be human or ai, got {raw_label!r}")
            samples.append({"text": text})
            labels.append(label)
    if len(samples) < 20 or min(labels.count(0), labels.count(1)) < 10:
        raise ValueError("Need at least 20 examples and at least 10 examples from each class")
    return samples, labels


def train_model(data_path: str | Path, model_path: str | Path) -> dict[str, Any]:
    samples, labels = read_dataset(data_path)
    model = build_model()
    model.fit(samples, labels)
    artifact = {
        "model_version": MODEL_VERSION,
        "model": model,
        "training_examples": len(labels),
        "class_counts": {"human": labels.count(0), "ai": labels.count(1)},
    }
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, destination, compress=3)
    return {key: value for key, value in artifact.items() if key != "model"} | {"model_path": str(destination)}


def load_model(path: str | Path) -> dict[str, Any]:
    artifact = joblib.load(path)
    if not isinstance(artifact, dict) or artifact.get("model_version") != MODEL_VERSION:
        raise ValueError("Unsupported or invalid model artifact")
    return artifact


def predict(artifact: dict[str, Any], text: str) -> dict[str, Any]:
    if not text.strip():
        raise ValueError("Text is empty")
    probabilities = artifact["model"].predict_proba([{"text": text}])[0]
    classes = artifact["model"].named_steps["classifier"].classes_
    scores = {"human": 0.0, "ai": 0.0}
    for class_id, probability in zip(classes, probabilities):
        scores["ai" if int(class_id) == 1 else "human"] = float(probability)
    return {
        "prediction": "ai-like" if scores["ai"] >= scores["human"] else "human-like",
        "scores": scores,
        "warning": "A model score is not proof of authorship; accuracy depends on representative, independently held-out training data.",
    }


def evaluate(artifact: dict[str, Any], data_path: str | Path) -> dict[str, Any]:
    samples, labels = read_dataset(data_path)
    predictions = artifact["model"].predict(samples)
    return {
        "examples": len(labels),
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "precision_ai": float(precision_score(labels, predictions, pos_label=1, zero_division=0)),
        "recall_ai": float(recall_score(labels, predictions, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
        "class_report": classification_report(labels, predictions, labels=[0, 1],
                                               target_names=["human", "ai"], output_dict=True, zero_division=0),
        "warning": "Evaluation is meaningful only when this CSV is an untouched holdout with no source overlap or duplicates from training data.",
    }
