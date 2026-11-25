"""CLI for AI-text classification and local-corpus similarity checks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .model import evaluate, load_model, predict, train_model
from .plagiarism import compare_corpus


def _read_text(value: str | None, file_name: str | None) -> str:
    return Path(file_name).read_text(encoding="utf-8") if file_name else (value or "")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="text-integrity", description="AI-text classification and corpus similarity search")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Train AI-vs-human classifier from labeled CSV")
    train.add_argument("--data", required=True, help="CSV with text,label columns")
    train.add_argument("--model", required=True, help="Output Joblib model file")
    classify = commands.add_parser("predict", help="Classify text or a text file")
    classify.add_argument("--model", required=True)
    source = classify.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--text")
    test = commands.add_parser("evaluate", help="Evaluate against a separate labeled CSV")
    test.add_argument("--model", required=True)
    test.add_argument("--data", required=True, help="Untouched holdout CSV")
    plagiarism = commands.add_parser("plagiarism", help="Search for matching text in a supplied JSON corpus")
    query = plagiarism.add_mutually_exclusive_group(required=True)
    query.add_argument("--file")
    query.add_argument("--text")
    plagiarism.add_argument("--corpus", required=True, help="JSON list of {id, text} documents")
    plagiarism.add_argument("--top-k", type=int, default=5)
    plagiarism.add_argument("--threshold", type=float, default=0.15)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "train":
            result = train_model(args.data, args.model)
        elif args.command == "predict":
            result = predict(load_model(args.model), _read_text(args.text, args.file))
        elif args.command == "evaluate":
            result = evaluate(load_model(args.model), args.data)
        else:
            if not 0 <= args.threshold <= 1:
                raise ValueError("Threshold must be between 0 and 1")
            documents = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
            if not isinstance(documents, list):
                raise ValueError("Corpus JSON must contain a list of {id, text} objects")
            result = compare_corpus(_read_text(args.text, args.file), documents, args.top_k, args.threshold)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
