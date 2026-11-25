import csv

import pytest

from text_integrity.model import load_model, predict, read_dataset, train_model


def write_data(path):
    rows = []
    for i in range(10):
        rows.append({"text": f"I remember walking along the quiet river after work number {i}. The air felt cool, and I stopped to watch a small boat drift beneath the bridge.", "label": "human"})
        rows.append({"text": f"This comprehensive overview {i} examines several important aspects. Furthermore, it is essential to consider the broader implications. In conclusion, these factors demonstrate the significance of the topic.", "label": "ai"})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=("text", "label"))
        writer.writeheader()
        writer.writerows(rows)


def test_train_predict_round_trip(tmp_path):
    data = tmp_path / "train.csv"
    model_path = tmp_path / "model.joblib"
    write_data(data)
    summary = train_model(data, model_path)
    result = predict(load_model(model_path), "I walked home in the rain and forgot my umbrella.")
    assert summary["training_examples"] == 20
    assert result["prediction"] in {"ai-like", "human-like"}
    assert sum(result["scores"].values()) == pytest.approx(1)


def test_rejects_unbalanced_small_data(tmp_path):
    data = tmp_path / "tiny.csv"
    data.write_text("text,label\nhello world,human\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least 20"):
        read_dataset(data)


def test_empty_text_rejected():
    with pytest.raises(ValueError, match="empty"):
        predict({}, " ")
