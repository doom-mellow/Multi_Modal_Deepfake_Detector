# Audio Deepfake Detector

A trainable, CPU-friendly research baseline for detecting **audio spoofing or synthetic-speech signals**. It decodes common audio formats (FFmpeg recommended), resamples to mono 16 kHz, extracts MFCC/log-mel, spectral, harmonic, clipping, silence, and temporal features, and trains an ensemble of an RBF SVM and tree classifiers. It can be used for labeled audio such as bonafide speech versus generated, cloned, or replay-spoofed audio, if those categories are represented in the training set.

## Important limitations

This is a **feature-based baseline, not a state-of-the-art detector** and ships without pretrained weights or invented training data. It cannot reliably prove who spoke, whether audio is authentic, or how a clip was made. Unknown generators, codecs, speakers, languages, recording environments, editing, and channel effects can change results. A synthetic voice may evade it; genuine speech may be flagged. Scores are not calibrated probabilities of fakery. Do not rely on this by itself for identity, legal, financial, or other high-stakes decisions.

Use a diverse, permissioned labeled dataset that matches your intended setting. Split training and evaluation by speaker identity, original recording session/source, and generation method; duplicate or related clips across splits cause leakage and inflated scores. Audit errors across speakers, languages, and recording conditions. The evaluation command calculates metrics but cannot confirm your split is genuinely independent.

## Install

Python 3.10+ and FFmpeg recommended for MP3/M4A/FLAC and other compressed audio. WAV PCM works via SciPy when FFmpeg is absent.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Manifest and training

Prepare a UTF-8 CSV with `audio,label` columns. Relative audio paths are resolved from the manifest's directory. Optional `group` should identify the speaker/source recording or a leakage-safe group. Labels accept `real`/`authentic`/`bonafide`/`0` and `fake`/`deepfake`/`spoof`/`synthetic`/`1`. At least 20 audio clips (10 per class) and two distinct groups per class are required to train. These are just minimum checks, not enough evidence of model quality.

```csv
audio,label,group
clips/person-a-original-1.wav,real,person-a-session-1
clips/person-a-voice-clone-1.wav,fake,person-a-session-1
clips/person-b-original-1.wav,real,person-b-session-1
clips/person-b-generated-1.wav,fake,person-b-session-1
```

Avoid putting a speaker's real recordings in one split and that same speaker's generated copies in another if you want to test generalization to new people. Create train/validation/test manifests before training. Train only on your training manifest:

```bash
audio-deepfake train --manifest train.csv --model artifacts/audio-model.joblib --max-duration 10
```

## Predict and evaluate

```bash
audio-deepfake predict --model artifacts/audio-model.joblib --audio sample.wav
audio-deepfake evaluate --model artifacts/audio-model.joblib --manifest heldout.csv
```

Prediction results include the likely class, scores, analyzed duration, and a warning. Evaluation reports accuracy, macro F1, fake precision/recall, and a confusion matrix. Evaluation is meaningful only for a separate, representative holdout.

The `.joblib` artifact is a pickle-based file. Load models only from sources you trust.

## Tests

```bash
python -m pytest
```
