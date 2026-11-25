"""Command-line interface for video deepfake baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .model import evaluate, load_model, predict, train_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="video-deepfake", description="Train/evaluate a research video manipulation classifier")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Train using a labeled video manifest CSV")
    train.add_argument("--manifest", required=True)
    train.add_argument("--model", required=True)
    train.add_argument("--frames", type=int, default=16)
    infer = commands.add_parser("predict", help="Predict a single video")
    infer.add_argument("--model", required=True)
    infer.add_argument("--video", required=True)
    infer.add_argument("--frames", type=int)
    test = commands.add_parser("evaluate", help="Evaluate a held-out manifest")
    test.add_argument("--model", required=True)
    test.add_argument("--manifest", required=True)
    test.add_argument("--frames", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            if args.frames < 2:
                raise ValueError("--frames must be at least 2")
            result = train_model(args.manifest, args.model, args.frames)
        elif args.command == "predict":
            result = predict(load_model(args.model), args.video, args.frames)
        else:
            result = evaluate(load_model(args.model), args.manifest, args.frames)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
