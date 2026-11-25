import os
from pathlib import Path
from threading import Lock

# .../backend/app/detectors/text/classifier.py -> parents[3] is backend/
MODEL_DIR = Path(
    os.getenv("TEXT_MODEL_DIR")
    or Path(__file__).resolve().parents[3] / "models" / "text_detector"
)
MAX_LEN = 512
CHUNK_WORDS = 300
MIN_WORDS_RELIABLE = 50

_lock = Lock()
_state: dict = {}


def is_available() -> bool:
    return (MODEL_DIR / "config.json").exists()


def _load() -> dict:
    with _lock:
        if "model" not in _state:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            device = "cuda" if torch.cuda.is_available() else "cpu"
            tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
            model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
            _state.update(tok=tokenizer, model=model.to(device).eval(), device=device)
    return _state


def _chunks(text: str) -> list[str]:
    words = text.split()
    chunks = [" ".join(words[i:i + CHUNK_WORDS]) for i in range(0, len(words), CHUNK_WORDS)]
    if len(chunks) > 1 and len(chunks[-1].split()) < CHUNK_WORDS // 4:
        chunks[-2] += " " + chunks.pop()
    return chunks


def classify_text(text: str) -> dict:
    """Blocking call. Run it with asyncio.to_thread() from async code."""
    import torch

    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text.")

    state = _load()
    chunks = _chunks(text)
    probs: list[float] = []
    with torch.no_grad():
        for i in range(0, len(chunks), 8):
            enc = state["tok"](
                chunks[i:i + 8],
                truncation=True,
                max_length=MAX_LEN,
                padding=True,
                return_tensors="pt",
            ).to(state["device"])
            logits = state["model"](**enc).logits
            probs.extend(torch.softmax(logits, dim=-1)[:, 1].cpu().tolist())

    word_count = len(text.split())
    return {
        "ai_probability": round(sum(probs) / len(probs), 4),
        "word_count": word_count,
        "chunks_analyzed": len(chunks),
        "reliable": word_count >= MIN_WORDS_RELIABLE,
    }