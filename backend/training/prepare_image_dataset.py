
import argparse
import random
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError


AI_MARKERS = {
    "ai",
    "ai_generated",
    "ai_images",
    "generated",
    "generated_images",
    "synthetic",
    "synthetic_images",
    "fake",
    "fake_images",
}

REAL_MARKERS = {
    "real",
    "real_images",
    "authentic",
    "authentic_images",
    "genuine",
    "genuine_images",
}

EXCLUDED_MARKERS = {
    "val",
    "valid",
    "validation",
    "test",
    "testing",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}


def classify_path(path: Path):
    parts = {part.lower() for part in path.parts}

    if parts & EXCLUDED_MARKERS:
        return None

    if parts & AI_MARKERS:
        return "ai_generated"

    if parts & REAL_MARKERS:
        return "real"

    return None


def is_valid_image(path: Path):
    try:
        with Image.open(path) as image:
            image.verify()
        return True

    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ):
        return False


def collect_images(source: Path):
    collected = {
        "ai_generated": [],
        "real": [],
    }

    for path in source.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label = classify_path(path)

        if label is not None and is_valid_image(path):
            collected[label].append(path)

    return collected


def copy_split(images, output, label, seed):
    images = list(images)
    rng = random.Random(seed)
    rng.shuffle(images)

    total = len(images)

    train_end = int(total * 0.70)
    val_end = train_end + int(total * 0.15)

    splits = {
        "train": images[:train_end],
        "val": images[train_end:val_end],
        "test": images[val_end:],
    }

    for split_name, split_images in splits.items():
        destination = output / split_name / label
        destination.mkdir(parents=True, exist_ok=True)

        for index, source_path in enumerate(split_images):
            target = destination / (
                f"{index:06d}{source_path.suffix.lower()}"
            )

            shutil.copy2(source_path, target)

    return {
        name: len(paths)
        for name, paths in splits.items()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prepare a balanced real/AI image dataset."
    )

    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/image_source"),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/image_dataset"),
    )

    parser.add_argument(
        "--max-per-class",
        type=int,
        default=2000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
    )

    args = parser.parse_args()

    if args.max_per_class < 2:
        parser.error("--max-per-class must be at least 2.")

    if not args.source.is_dir():
        raise FileNotFoundError(
            f"Dataset source directory not found: {args.source}"
        )

    if args.output.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"{args.output} already exists. "
                "Use --overwrite to replace it."
            )

        shutil.rmtree(args.output)

    collected = collect_images(args.source)

    for label, images in collected.items():
        print(f"{label}: {len(images)} valid images found")

    for label in ("ai_generated", "real"):
        if not collected[label]:
            raise ValueError(
                f"No images found for '{label}'. "
                "Check the dataset folder names."
            )

    rng = random.Random(args.seed)

    selected = {}

    for label, images in collected.items():
        images = list(images)
        rng.shuffle(images)
        selected[label] = images[:args.max_per_class]

    # Keep both classes equally represented.
    balanced_count = min(
        len(selected["ai_generated"]),
        len(selected["real"]),
    )

    if balanced_count < 2:
        raise ValueError(
            "Not enough images to prepare a dataset."
        )

    for label in selected:
        selected[label] = selected[label][:balanced_count]

    print(f"\nUsing {balanced_count} images per class.")

    for label, images in selected.items():
        counts = copy_split(
            images=images,
            output=args.output,
            label=label,
            seed=args.seed,
        )

        print(f"\n{label}:")

        for split, count in counts.items():
            print(f"  {split}: {count}")

    print("\nDataset preparation completed.")
    print(f"Dataset location: {args.output.resolve()}")

    print("\nExpected structure:")
    print("image_dataset/")
    print("  train/")
    print("    ai_generated/")
    print("    real/")
    print("  val/")
    print("    ai_generated/")
    print("    real/")
    print("  test/")
    print("    ai_generated/")
    print("    real/")


if __name__ == "__main__":
    main()
