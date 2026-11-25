# Code Origin Detector

A small, trainable baseline for distinguishing **AI-like** from **human-like** source code. It supports Python, Java, C, C++, and JavaScript. It combines character n-grams, token n-grams, and language-aware style/structure features in a scikit-learn logistic-regression pipeline.

> **Important limitation:** code authorship is not reliably inferable from source alone. This is a dataset-dependent classifier, not a forensic detector or proof that code was AI-generated. Human and model-written code overlap heavily; formatting, edits, templates, language, and project conventions all affect results. Use representative, independently held-out examples and treat scores as weak signals only. This repository intentionally does not ship a fabricated pretrained model: you must train it on labeled examples relevant to your use case.

## Setup

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Prepare data

Create a UTF-8 CSV with a `code` column containing the complete source sample, a `label` column, and optionally a `language` column. Each CSV record may contain multiline source code (quote/escape it as standard CSV). Accepted labels are `human`/`human-written`/`0` and `ai`/`ai-generated`/`generated`/`1`. Language values: `python`, `java`, `c`, `cpp`, `javascript` (aliases like `py`, `c++`, and `js` also work). If omitted, a best-effort language guess is used.

```csv
code,label,language
"def add(a, b):\n    return a + b",human,python
"def sum_values(first, second):\n    result = first + second\n    return result",ai,python
```

That two-row illustration is **not enough to train**. Training requires at least 10 samples total and 4 from each class; useful performance generally requires substantially more balanced, diverse examples. Keep examples from the same project, author, or generation prompt in only one split when evaluating, to avoid leakage. Include all five languages and varied code lengths/styles if the model will see all five.

## Train

```bash
code-origin train --data examples.csv --model artifacts/code-origin.joblib
```

The model artifact is a pickle-based Joblib file; only load artifacts you trust. Training fits one model on all supplied examples and prints sample counts. It does **not** claim accuracy on unseen data. For a credible evaluation, make a separate project-/author-/prompt-level test set and report per-language precision, recall, F1, and calibration.

## Predict

Pass a source file (language inferred from extension) or inline code. `--language` can explicitly override/determine the language:

```bash
code-origin predict --model artifacts/code-origin.joblib --file example.cpp
code-origin predict --model artifacts/code-origin.joblib --file snippet.txt --language javascript
code-origin predict --model artifacts/code-origin.joblib --code 'const add = (a, b) => a + b;' --language javascript
```

JSON output includes an `ai-like`/`human-like` prediction, the two model scores, detected language, and a caution. These scores are classifier probabilities, not calibrated probabilities of actual authorship.

## Development

```bash
pip install -e '.[dev]'  # or install pytest separately
pytest
```

The feature extractor uses lightweight lexical and formatting proxies, not full compiler ASTs. It accepts source as text and does not execute the submitted code.
