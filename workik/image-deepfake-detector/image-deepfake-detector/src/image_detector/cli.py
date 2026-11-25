"""Command-line tools for the image manipulation detection baseline."""
from __future__ import annotations

import argparse
import json
import sys

from .model import evaluate, load_model, predict, train_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="image-deepfake", description="Train/evaluate a research image authenticity classifier")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Train from labeled image manifest CSV")
    train.add_argument("--manifest", required=True)
    train.add_argument("--model", required=True)
    infer = commands.add_parser("predict", help="Classify one image")
    infer.add_argument("--model", required=True)
    infer.add_argument("--image", required=True)
    test = commands.add_parser("evaluate", help="Evaluate using a separate held-out manifest")
    test.add_argument("--model", required=True)
    test.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            result = train_model(args.manifest, args.model)
        elif args.command == "predict":
            result = predict(load_model(args.model), args.image)
        else:
            result = evaluate(load_model(args.model), args.manifest)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
