"""Training and inference helpers for the code-origin classifier."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from .features import LANGUAGES, detect_language, normalize_language, style_features

MODEL_VERSION = 1


def _code_column(samples: list[dict[str, str]]) -> list[str]:
    return [sample["code"] for sample in samples]


def _style_column(samples: list[dict[str, str]]) -> list[dict[str, float]]:
    return [style_features(sample) for sample in samples]


def normalize_sample(code: str, language: str | None = None) -> dict[str, str]:
    lang = normalize_language(language) if language else detect_language(code)
    return {"code": code, "language": lang}


def build_model() -> Pipeline:
    features = FeatureUnion([
        ("char_ngrams", Pipeline([
            ("select", FunctionTransformer(_code_column, validate=False)),
            ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=1,
                                      max_features=120_000, sublinear_tf=True, dtype=np.float32)),
        ])),
        ("tokens", Pipeline([
            ("select", FunctionTransformer(_code_column, validate=False)),
            ("tfidf", TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\b\w+\b|[^\w\s]",
                                      ngram_range=(1, 2), min_df=1, max_features=80_000,
                                      sublinear_tf=True, dtype=np.float32)),
        ])),
        ("style", Pipeline([
            ("select", FunctionTransformer(_style_column, validate=False)),
            ("dict", DictVectorizer(sparse=True)),
        ])),
    ], transformer_weights={"char_ngrams": 1.0, "tokens": 0.8, "style": 0.35})
    return Pipeline([
        ("features", features),
        ("classifier", LogisticRegression(C=1.0, class_weight="balanced", max_iter=1500,
                                           solver="liblinear", random_state=42)),
    ])


def read_dataset(path: str | Path) -> tuple[list[dict[str, str]], list[int]]:
    """Read UTF-8 CSV with required code,label and optional language columns."""
    samples: list[dict[str, str]] = []
    labels: list[int] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        if not {"code", "label"}.issubset(fields):
            raise ValueError("Training CSV must have 'code' and 'label' columns; 'language' is optional")
        for row_number, row in enumerate(reader, start=2):
            code = row.get("code") or ""
            raw_label = (row.get("label") or "").strip().lower()
            if not code.strip():
                raise ValueError(f"CSV row {row_number}: code is empty")
            if raw_label in {"human", "human-written", "human_written", "0"}:
                label = 0
            elif raw_label in {"ai", "ai-generated", "ai_generated", "generated", "1"}:
                label = 1
            else:
                raise ValueError(f"CSV row {row_number}: label must be human or ai, got {raw_label!r}")
            language = (row.get("language") or "").strip()
            samples.append(normalize_sample(code, language or None))
            labels.append(label)
    if len(samples) < 10 or min(labels.count(0), labels.count(1)) < 4:
        raise ValueError("Need at least 10 examples and at least 4 examples from each class")
    return samples, labels


def train_model(data_path: str | Path, model_path: str | Path) -> dict[str, Any]:
    samples, labels = read_dataset(data_path)
    model = build_model()
    model.fit(samples, labels)
    artifact = {
        "model_version": MODEL_VERSION,
        "model": model,
        "languages": list(LANGUAGES),
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


def predict(artifact: dict[str, Any], code: str, language: str | None = None) -> dict[str, Any]:
    if not code.strip():
        raise ValueError("Code is empty")
    sample = normalize_sample(code, language)
    probabilities = artifact["model"].predict_proba([sample])[0]
    classes = artifact["model"].named_steps["classifier"].classes_
    scores = {"human": 0.0, "ai": 0.0}
    for class_id, probability in zip(classes, probabilities):
        scores["ai" if int(class_id) == 1 else "human"] = float(probability)
    label = "ai-like" if scores["ai"] >= scores["human"] else "human-like"
    return {
        "prediction": label,
        "scores": scores,
        "language": sample["language"],
        "warning": "This is a dataset-dependent statistical signal, not proof of authorship. Validate on representative, held-out data before relying on it.",
    }
