
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_text_features_endpoint():
    response = client.post(
        "/api/v1/features/text",
        data={"content": "Python is useful. Python is versatile."},
    )

    assert response.status_code == 200
    assert response.json()["word_count"] == 6


def test_code_features_endpoint():
    source = "def greet():\n    print('Hello')"

    response = client.post(
        "/api/v1/features/code",
        data={
            "content": source,
            "language_hint": "python",
        },
    )

    assert response.status_code == 200
    assert response.json()["language_hint"] == "python"


def test_empty_text_endpoint():
    response = client.post(
        "/api/v1/features/text",
        data={"content": "   "},
    )

    assert response.status_code == 400
