# Text Integrity Detector

A trainable Python project with two distinct tools:

1. **AI-vs-human text classifier** — combines word and character TF-IDF n-grams with basic writing-style features in a supervised logistic-regression model.
2. **Plagiarism similarity search** — compares text against a reference corpus that you provide, using TF-IDF similarity plus exact token-shingle overlap.

## Important limits

No text-only detector can reliably prove whether writing came from a person or a language model. Classifier scores are learned from your training data and may be wrong, particularly on short passages, edited text, new models, other languages, and out-of-domain writing. Do not use them alone to accuse, penalize, or make high-stakes decisions.

Plagiarism search only checks documents you explicitly provide. It does not search the web, subscription databases, private documents, or sources omitted from your corpus. Similarity is a lead for human review, not a finding of plagiarism: quotations, citations, common phrases, and coincidental overlap can match. This starter project does not ship fabricated training data, a pretrained detector, or a reference corpus.

## Install

Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Train the AI-text classifier

Create UTF-8 CSV with `text,label` columns. Labels can be `human`/`human-written`/`0` or `ai`/`ai-generated`/`generated`/`1`. Quote multiline fields following CSV rules. At least 20 examples and at least 10 per class are required; that is only a minimum to run, not enough to establish meaningful quality.

```csv
text,label
"I took the long path home and watched the clouds gather over the station.",human
"This comprehensive overview highlights several important considerations. Furthermore, it demonstrates the significance of the topic.",ai
```

Collect texts from the languages, domains, lengths, and writing workflows where you expect to use the model. Avoid training/test leakage by splitting by original author, document, prompt, and source—not random sentence rows. Evaluate on an untouched holdout representative of the intended use; report per-domain precision, recall, F1, and calibration.

```bash
text-integrity train --data examples.csv --model artifacts/text-detector.joblib
text-integrity predict --model artifacts/text-detector.joblib --file essay.txt
text-integrity predict --model artifacts/text-detector.joblib --text 'A paragraph to inspect.'
text-integrity evaluate --model artifacts/text-detector.joblib --data holdout.csv
```

Evaluation reports metrics on the entire supplied CSV; use only a genuinely separate holdout. Scores are model probabilities, not calibrated probabilities of actual authorship.

## Check for text in your own reference corpus

Prepare a JSON list of documents. Keep sources you are authorized to process:

```json
[
  {"id": "source-001", "text": "Full text of a reference document goes here."},
  {"id": "source-002", "text": "Another authorized reference text goes here."}
]
```

Then compare:

```bash
text-integrity plagiarism --file essay.txt --corpus references.json --top-k 5 --threshold 0.15
```

Or pass `--text` instead of `--file`. Results include a combined retrieval score, TF-IDF cosine score, and query shingle coverage. The threshold is a tunable retrieval cutoff, **not** a legal or academic plagiarism threshold. The search compares the submitted passage against each supplied record; it does not identify where individual matches occur or determine whether a match is appropriately cited.

## Tests

```bash
python -m pytest
```
