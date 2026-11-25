"""
AI-generated vs human-written source code: likelihood analysis.

Two modes:
  1. Heuristic (no training needed): stylometric signals -> likelihood + explanation.
     It is UNCALIBRATED, so treat the number as a rough indicator, not a probability.
  2. Trained model (recommended for real use): logistic regression on style features
     + token TF-IDF, trained on your own labeled data (CSV: code,label  0=human 1=AI).

Install:
    pip install numpy pandas scikit-learn scipy joblib

Usage:
    python code_ai_detector.py analyze --file solution.py
    python code_ai_detector.py train --data code_samples.csv --out code_model.joblib
    python code_ai_detector.py analyze --file solution.py --model code_model.joblib
"""
import argparse
import ast
import keyword
import math
import re
import statistics
import sys
from pathlib import Path

SEED = 42

# ------------------------------------------------------------------
# helpers / constants
# ------------------------------------------------------------------
NON_COMMENT_HASH = ("#include", "#define", "#pragma", "#!", "#if", "#endif",
                    "#else", "#ifdef", "#ifndef", "#import")
INLINE_RE = re.compile(r"\S\s+(#|//)\s")
CODE_LIKE_RE = re.compile(
    r"^\s*(print\(|return\b|if\b.*:|for\b.*:|while\b.*:|import\b|"
    r"\w[\w\.]*\s*=\s*\S|[\w\.]+\(.*\);?\s*$)"
)
STRUCT_DOC_RE = re.compile(r"(Args|Arguments|Parameters|Returns|Raises|Yields)\s*:|:param |:return")
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
STRING_RE = re.compile(r"\"[^\"\n]*\"|'[^'\n]*'")

AI_PHRASES = [
    "helper function", "initialize", "example usage", "this function", "this method",
    "edge case", "main function", "ensure that", "iterate over", "loop through",
    "return the result", "utility function", "for demonstration", "step 1", "step 2",
    "handle the case", "create a new", "define the", "main entry point",
]

KEYWORDS = set(keyword.kwlist) | {
    "function", "var", "let", "const", "int", "char", "float", "double", "void", "public",
    "private", "static", "class", "new", "this", "null", "true", "false", "string", "boolean",
    "long", "short", "final", "package", "include", "struct", "enum", "switch", "case",
    "break", "continue", "default", "throw", "throws", "catch", "finally", "extends",
    "implements", "interface", "namespace", "using", "typedef", "sizeof", "print", "self",
    "cls", "str", "len", "range", "list", "dict", "set", "return", "console", "log",
}


def clip(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def sigmoid(z):
    return 1.0 / (1.0 + math.exp(-z))


def is_line_comment(s: str) -> bool:
    if s.startswith("#"):
        return not s.startswith(NON_COMMENT_HASH)
    return s.startswith(("//", "--"))


# ------------------------------------------------------------------
# feature extraction
# ------------------------------------------------------------------
def python_features(src: str) -> dict:
    out = {"is_python": 0.0, "n_funcs": 0.0, "doc_ratio": 0.0, "struct_doc_ratio": 0.0,
           "hint_ratio": 0.0, "has_main_guard": 0.0, "func_len_cv": 0.0,
           "bare_except": 0.0, "module_doc": 0.0}
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return out
    out["is_python"] = 1.0
    out["module_doc"] = 1.0 if ast.get_docstring(tree) else 0.0
    out["has_main_guard"] = 1.0 if re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", src) else 0.0

    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    out["n_funcs"] = float(len(funcs))
    if funcs:
        docs = [ast.get_docstring(f) for f in funcs]
        out["doc_ratio"] = sum(1 for d in docs if d) / len(funcs)
        out["struct_doc_ratio"] = sum(1 for d in docs if d and STRUCT_DOC_RE.search(d)) / len(funcs)
        out["hint_ratio"] = sum(1 for f in funcs if f.returns is not None) / len(funcs)
        lengths = [(f.end_lineno - f.lineno + 1) for f in funcs if getattr(f, "end_lineno", None)]
        if len(lengths) >= 3 and statistics.mean(lengths) > 0:
            out["func_len_cv"] = statistics.pstdev(lengths) / statistics.mean(lengths)
    out["bare_except"] = float(sum(
        1 for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler) and n.type is None))
    return out


def extract_features(src: str) -> dict:
    lines = src.splitlines()
    nonblank = [l for l in lines if l.strip()]
    comment_lines, code_lines = [], []
    in_block = False
    for raw in nonblank:
        s = raw.strip()
        if in_block:
            comment_lines.append(s)
            if "*/" in s:
                in_block = False
        elif s.startswith("/*"):
            comment_lines.append(s)
            in_block = "*/" not in s
        elif is_line_comment(s):
            comment_lines.append(s)
        else:
            code_lines.append(raw)

    n_code, n_comment = len(code_lines), len(comment_lines)
    lens = [len(l) for l in nonblank] or [0]
    avg_len = statistics.mean(lens)

    # identifiers (strip string literals first)
    text = STRING_RE.sub('""', "\n".join(code_lines))
    idents = [i for i in IDENT_RE.findall(text) if i not in KEYWORDS]
    uniq = set(idents)
    snake = sum(1 for i in uniq if "_" in i.strip("_") and i.lower() == i)
    camel = sum(1 for i in uniq if i[0].islower() and "_" not in i and any(c.isupper() for c in i))
    mixed = (min(snake, camel) / (snake + camel)) if (snake and camel) else 0.0

    comment_text = " ".join(comment_lines).lower()
    cc = 0
    for s in comment_lines:
        body = re.sub(r"^(#|//|--)\s?", "", s)
        if s.startswith(("#", "//", "--")) and CODE_LIKE_RE.match(body):
            cc += 1

    tabs = sum(1 for l in lines if l.startswith("\t"))
    spaces = sum(1 for l in lines if l.startswith("  "))

    f = {
        "n_code_lines": float(n_code),
        "comment_ratio": n_comment / max(1, n_comment + n_code),
        "inline_comment_ratio": sum(1 for l in code_lines if INLINE_RE.search(l)) / max(1, n_code),
        "blank_ratio": (len(lines) - len(nonblank)) / max(1, len(lines)),
        "avg_line_len": avg_len,
        "line_len_cv": statistics.pstdev(lens) / avg_len if avg_len else 0.0,
        "max_line_len": float(max(lens)),
        "trailing_ws_ratio": sum(1 for l in nonblank if l != l.rstrip()) / max(1, len(nonblank)),
        "mixed_indent": 1.0 if (tabs and spaces) else 0.0,
        "avg_ident_len": statistics.mean(len(i) for i in idents) if idents else 0.0,
        "short_ident_ratio": (sum(1 for i in idents if len(i) <= 2) / len(idents)) if idents else 0.0,
        "mixed_naming": mixed,
        "ai_phrase_hits": float(sum(comment_text.count(p) for p in AI_PHRASES)),
        "commented_code_ratio": cc / max(1, n_code),
        "todo_count": float(len(TODO_RE.findall(src))),
    }
    f.update(python_features(src))
    return f


FEATURE_NAMES = list(extract_features("x = 1\n").keys())


def feature_vector(src: str):
    f = extract_features(src)
    return [f[k] for k in FEATURE_NAMES]


# ------------------------------------------------------------------
# heuristic scoring
# ------------------------------------------------------------------
def heuristic_score(f: dict):
    sig = []

    def add(name, value, note):
        sig.append((name, value, note))

    add("Comment density", 1.5 * clip((f["comment_ratio"] - 0.12) / 0.15),
        f"{f['comment_ratio']:.0%} of non-blank lines are comments")
    if f["is_python"] and f["n_funcs"] > 0:
        add("Docstring coverage", 1.2 * clip((f["doc_ratio"] - 0.3) / 0.5),
            f"{f['doc_ratio']:.0%} of functions have docstrings")
        add("Structured docstrings (Args/Returns)", 2.0 * f["struct_doc_ratio"],
            f"{f['struct_doc_ratio']:.0%} of functions")
        add("Return type hints", 1.0 * clip((f["hint_ratio"] - 0.3) / 0.5),
            f"{f['hint_ratio']:.0%} of functions annotated")
        if f["has_main_guard"] and f["n_funcs"] >= 2:
            add("Main guard with demo block", 0.8, "typical of generated examples")
        if f["bare_except"]:
            add("Bare 'except:'", -0.5 * min(f["bare_except"], 2), "more common in hand-written code")
    add("Typical AI comment phrasing", 0.5 * min(f["ai_phrase_hits"], 4),
        f"{int(f['ai_phrase_hits'])} stock phrases in comments")
    add("Identifier length", 0.8 * clip((f["avg_ident_len"] - 8) / 4),
        f"average identifier length {f['avg_ident_len']:.1f}")
    add("Short throwaway names", -0.8 * clip((f["short_ident_ratio"] - 0.15) / 0.15, 0, 1),
        f"{f['short_ident_ratio']:.0%} identifiers are 1-2 chars")
    add("Inconsistent naming style", -3.0 * f["mixed_naming"],
        f"snake_case/camelCase mix {f['mixed_naming']:.0%}")
    add("Trailing whitespace", -4.0 * min(f["trailing_ws_ratio"], 0.25),
        f"{f['trailing_ws_ratio']:.0%} of lines")
    add("Mixed tabs/spaces", -1.0 * f["mixed_indent"], "inconsistent indentation")
    add("Commented-out code", -6.0 * min(f["commented_code_ratio"], 0.2),
        f"{f['commented_code_ratio']:.0%} of code lines")
    add("TODO/FIXME/HACK markers", -0.8 * min(f["todo_count"], 2), f"{int(f['todo_count'])} found")
    if f["max_line_len"] > 120:
        add("Very long lines", -0.5, f"longest line {int(f['max_line_len'])} chars")

    logit = -0.3 + sum(v for _, v, _ in sig)
    logit *= min(1.0, f["n_code_lines"] / 40.0)  # shrink toward 0.5 for tiny snippets
    return sigmoid(logit), sig


# ------------------------------------------------------------------
# training
# ------------------------------------------------------------------
def train(csv_path: str, out_path: str):
    import joblib
    import numpy as np
    import pandas as pd
    from scipy.sparse import csr_matrix, hstack
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    df = pd.read_csv(csv_path)
    if not {"code", "label"}.issubset(df.columns):
        sys.exit("CSV needs 'code' and 'label' columns (0=human, 1=AI).")
    df = df.dropna(subset=["code", "label"]).drop_duplicates(subset="code")
    df["label"] = df["label"].astype(int)
    if len(df) < 100 or df["label"].nunique() < 2:
        sys.exit("Need at least ~100 samples covering both classes.")

    tr, te = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=SEED)
    tfidf = TfidfVectorizer(token_pattern=r"[A-Za-z_]+|\S", ngram_range=(1, 2),
                            max_features=50000, sublinear_tf=True, lowercase=False)
    scaler = StandardScaler()

    def build(frame, fit=False):
        feats = np.array([feature_vector(c) for c in frame["code"]], dtype=float)
        if fit:
            T = tfidf.fit_transform(frame["code"])
            F = scaler.fit_transform(feats)
        else:
            T = tfidf.transform(frame["code"])
            F = scaler.transform(feats)
        return hstack([T, csr_matrix(F)]).tocsr()

    Xtr, Xte = build(tr, fit=True), build(te)
    clf = LogisticRegression(max_iter=3000, class_weight="balanced", C=1.0)
    clf.fit(Xtr, tr["label"])

    prob = clf.predict_proba(Xte)[:, 1]
    pred = (prob >= 0.5).astype(int)
    print(f"Held-out test: accuracy={accuracy_score(te['label'], pred):.3f} "
          f"f1={f1_score(te['label'], pred):.3f} "
          f"roc_auc={roc_auc_score(te['label'], prob):.3f}")
    joblib.dump({"tfidf": tfidf, "scaler": scaler, "clf": clf,
                 "feature_names": FEATURE_NAMES}, out_path)
    print("Saved model to", out_path)


def model_probability(src: str, model_path: str) -> float:
    import joblib
    import numpy as np
    from scipy.sparse import csr_matrix, hstack

    m = joblib.load(model_path)
    if m["feature_names"] != FEATURE_NAMES:
        sys.exit("Model was trained with a different feature set; retrain it.")
    T = m["tfidf"].transform([src])
    F = m["scaler"].transform(np.array([feature_vector(src)], dtype=float))
    return float(m["clf"].predict_proba(hstack([T, csr_matrix(F)]).tocsr())[0, 1])


# ------------------------------------------------------------------
# public API
# ------------------------------------------------------------------
def analyze(src: str, model_path: str = None) -> dict:
    if not src or not src.strip():
        raise ValueError("Empty code.")
    f = extract_features(src)
    h_prob, signals = heuristic_score(f)
    if model_path:
        prob, mode = model_probability(src, model_path), "trained model"
    else:
        # uncalibrated heuristic: keep it away from 0%/100% so it never claims certainty
        prob, mode = 0.1 + 0.8 * h_prob, "heuristic (uncalibrated)"

    if prob >= 0.70:
        label = "Likely AI-generated"
    elif prob <= 0.30:
        label = "Likely human-written"
    else:
        label = "Uncertain"
    n = f["n_code_lines"]
    confidence = "low" if n < 20 else "medium"
    return {
        "ai_likelihood": round(prob, 3),
        "label": label,
        "mode": mode,
        "confidence": confidence,
        "code_lines": int(n),
        "signals": sorted(signals, key=lambda s: -abs(s[1])),
    }


def print_report(r: dict):
    print(f"\nAI likelihood : {r['ai_likelihood']:.0%}  ->  {r['label']}")
    print(f"Mode          : {r['mode']} | confidence: {r['confidence']} | {r['code_lines']} code lines")
    if r["confidence"] == "low":
        print("Note          : very short snippet, treat this as nearly meaningless.")
    print("\nSignals (+ leans AI, - leans human):")
    for name, val, note in r["signals"]:
        if abs(val) >= 0.05:
            print(f"  {val:+.2f}  {name}: {note}")
    print("\nThis is a statistical estimate and not proof of authorship.")


def main():
    p = argparse.ArgumentParser(description="AI vs human code likelihood analyzer")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--file", required=True)
    a.add_argument("--model")
    t = sub.add_parser("train")
    t.add_argument("--data", required=True)
    t.add_argument("--out", default="code_model.joblib")
    args = p.parse_args()

    if args.cmd == "train":
        train(args.data, args.out)
    else:
        src = Path(args.file).read_text(encoding="utf-8", errors="replace")
        print_report(analyze(src, args.model))


if __name__ == "__main__":
    main()
