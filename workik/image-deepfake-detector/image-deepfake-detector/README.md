# Image Deepfake Detector

A trainable, CPU-friendly research baseline that classifies images as likely authentic or likely manipulated/generated. It extracts simple color, spatial, edge, DCT/Fourier frequency, noise, and JPEG-grid proxy features, then trains an RBF SVM and tree ensembles. It accepts still images readable by Pillow.

## Important limitations

This is **not a state-of-the-art detector**, ships with no pretrained model or made-up dataset, and cannot prove that an image is authentic, manipulated, or AI-generated. Handcrafted features can miss modern generators; ordinary resizing, recompression, screenshots, edits, or camera processing can erase or imitate the weak cues. Scores are not calibrated probabilities that an image is fake. Do not use this tool alone for accusations or high-stakes decisions.

Collect diverse, permissioned real and manipulated images relevant to the expected use. Include different cameras, subjects, scenes, generators, edits, resolutions, and compression levels. Split by original photograph, subject identity, and generation source/method before training. Near-duplicates and derivative crops in both train and test create leakage and misleading metrics. The evaluator calculates metrics but cannot verify split independence. This model is not a provenance or watermark verifier.

## Install

Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Dataset manifest

Create a UTF-8 CSV with `image,label` columns; paths can be absolute or relative to the CSV. Add an optional `group` column for the original source/subject to help prevent leakage. Labels: `real`/`authentic`/`0` or `fake`/`deepfake`/`synthetic`/`generated`/`1`. To run training, include at least 20 files (10 per class) and two distinct groups in each class; this is only a minimum plumbing check, not enough for reliability.

```csv
image,label,group
images/real/photo-a.jpg,real,subject-a-camera-session-1
images/fake/photo-a-synthetic.png,fake,subject-a-camera-session-1
images/real/photo-b.png,real,subject-b-camera-session-1
images/fake/generated-b.jpg,fake,generated-source-b
```

Prefer group-aware, separate train, validation, and holdout manifests. Keep related original and derived manipulated images in the same split.

## Train, predict, evaluate

```bash
image-deepfake train --manifest train.csv --model artifacts/image-model.joblib
image-deepfake predict --model artifacts/image-model.joblib --image sample.jpg
image-deepfake evaluate --model artifacts/image-model.joblib --manifest heldout.csv
```

The JSON prediction has class scores and a warning. Evaluation reports accuracy, macro F1, fake precision/recall, and a confusion matrix. Only evaluate on a truly untouched and representative holdout. Joblib artifacts are pickle-based; load only models from trusted sources.

## Tests

```bash
python -m pytest
```
