"""Command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .features import language_from_path, normalize_language
from .model import load_model, predict, train_model


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code-origin", description="Train and use a code-origin classifier")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Train a model from labeled CSV examples")
    train.add_argument("--data", required=True, help="CSV with code,label and optional language columns")
    train.add_argument("--model", required=True, help="Output .joblib model file")
    infer = commands.add_parser("predict", help="Score a source file or inline code")
    infer.add_argument("--model", required=True, help="Trained .joblib model file")
    source = infer.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Source file to inspect")
    source.add_argument("--code", help="Inline source code")
    infer.add_argument("--language", choices=("python", "java", "c", "cpp", "javascript"),
                       help="Override language detection")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            summary = train_model(args.data, args.model)
            print(json.dumps(summary, indent=2))
            return 0
        if args.file:
            code = Path(args.file).read_text(encoding="utf-8")
            language = normalize_language(args.language) if args.language else language_from_path(args.file)
        else:
            code = args.code
            language = args.language
        result = predict(load_model(args.model), code, language)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
