import csv

import pytest

from code_origin_detector.model import load_model, predict, read_dataset, train_model


def make_dataset(path):
    rows = []
    for i in range(6):
        rows.append({"code": f"# human example {i}\ndef add_{i}(left, right):\n    return left + right\n", "label": "human", "language": "python"})
        rows.append({"code": f"# generated solution {i}\ndef calculate_{i}(first_value, second_value):\n    result = first_value + second_value\n    return result\n", "label": "ai", "language": "python"})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=("code", "label", "language"))
        writer.writeheader()
        writer.writerows(rows)


def test_training_round_trip(tmp_path):
    data = tmp_path / "examples.csv"
    model_path = tmp_path / "model.joblib"
    make_dataset(data)
    summary = train_model(data, model_path)
    artifact = load_model(model_path)
    result = predict(artifact, "def sum_values(a, b):\n    return a + b\n", "python")
    assert summary["training_examples"] == 12
    assert result["prediction"] in {"ai-like", "human-like"}
    assert set(result["scores"]) == {"ai", "human"}
    assert sum(result["scores"].values()) == pytest.approx(1.0)


def test_dataset_requires_both_classes(tmp_path):
    path = tmp_path / "small.csv"
    path.write_text("code,label\nprint(1),human\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least 10"):
        read_dataset(path)


def test_prediction_rejects_empty_code(tmp_path):
    data = tmp_path / "examples.csv"
    model_path = tmp_path / "model.joblib"
    make_dataset(data)
    train_model(data, model_path)
    with pytest.raises(ValueError, match="empty"):
        predict(load_model(model_path), "  ", "python")
