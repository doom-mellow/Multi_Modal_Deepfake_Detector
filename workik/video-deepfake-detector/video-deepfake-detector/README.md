# Video Deepfake Detector

A CPU-friendly, **trainable research baseline** for classifying video as likely authentic or likely manipulated. It samples frames, attempts to locate a face with OpenCV's Haar cascade, and extracts coarse spatial/color/edge/compression-like cues plus frame-to-frame change. Two tree ensembles classify these features. It accepts ordinary video files decoded by OpenCV/FFmpeg.

## Critical limitations

This is **not a state-of-the-art deepfake detector** and includes no pretrained weights, fabricated training set, or performance claim. Handcrafted visual features can miss modern face swaps and generated video. Detection is sensitive to codecs, resizing, lighting, face size, camera/source identity, frame rate, edits, and manipulation methods. A likely-authentic score does not certify a video is genuine; a likely-manipulated score is not proof. Do not use it by itself for high-stakes, legal, employment, or identity decisions.

For meaningful results, assemble diverse labeled videos representative of the intended use, get permission to use them, and split training/evaluation by **original source video and subject identity** (and preferably manipulation method). Near-duplicate clips or the same person's videos across splits can yield misleadingly high scores. This starter reports evaluation metrics but cannot verify that your holdout split is independent. Audit false positives across demographic and recording conditions before use.

## Install

Python 3.10+; video codecs need to be supported by OpenCV/FFmpeg.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Labeled manifest

Create a UTF-8 CSV with `video,label` columns. Paths are relative to the manifest file or absolute. Optional `group` should identify the original source video/subject for split tracking. Labels: `real`/`authentic`/`0`, and `fake`/`deepfake`/`1`. Training currently requires 10 or more video files, at least 5 per class, and at least 2 distinct `group` values in each class. These are run-time minimums—not enough for robust generalization.

```csv
video,label,group
clips/real-01.mp4,real,source-real-01-personA
clips/fake-01.mp4,fake,source-real-01-personA
clips/real-02.mp4,real,source-real-02-personB
clips/fake-02.mp4,fake,source-real-02-personB
```

For each manipulated sample, use the original source as its group when applicable. Avoid source leakage across train and holdout datasets.

## Train / predict / evaluate

```bash
video-deepfake train --manifest train.csv --model artifacts/video-model.joblib --frames 16
video-deepfake predict --model artifacts/video-model.joblib --video sample.mp4
video-deepfake evaluate --model artifacts/video-model.joblib --manifest heldout.csv
```

Use more sampled frames for longer/more variable footage at increased CPU cost. Prediction JSON has class scores and a caution. These model scores are not calibrated odds that footage is fake. Evaluation outputs accuracy, macro F1, fake precision/recall, and a confusion matrix; pass only a genuinely held-out manifest.

The `.joblib` model file is a pickle-based artifact: only load models you trust.

## Tests

```bash
python -m pytest
```
