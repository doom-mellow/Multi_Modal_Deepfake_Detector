"""Language-aware feature extraction for code-origin classification."""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

LANGUAGES = ("python", "java", "c", "cpp", "javascript")
ALIASES = {
    "py": "python", "python3": "python", "js": "javascript", "node": "javascript",
    "c++": "cpp", "cc": "cpp", "cxx": "cpp", "h": "c", "hpp": "cpp",
    "mjs": "javascript", "jsx": "javascript", "ts": "javascript",
}
EXTENSIONS = {
    ".py": "python", ".java": "java", ".c": "c", ".h": "c", ".cc": "cpp",
    ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".js": "javascript",
    ".mjs": "javascript", ".jsx": "javascript", ".ts": "javascript",
}

KEYWORDS = {
    "python": "and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield self",
    "java": "abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null record var",
    "c": "auto break case char const continue default do double else enum extern float for goto if inline int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while _Bool _Complex _Atomic",
    "cpp": "alignas auto bool break case catch char class const constexpr continue decltype default delete do double else enum explicit export extern false float for friend goto if inline int long namespace new noexcept nullptr operator private protected public register return short signed sizeof static struct switch template this throw try typedef typename union unsigned using virtual void volatile while",
    "javascript": "async await break case catch class const continue debugger default delete do else export extends false finally for function if import in instanceof let new null return super switch this throw true try typeof undefined var void while with yield",
}

# Keep tokens language-neutral enough to work across repositories while preserving
# identifiers, operators, and punctuation that can carry stylistic signal.
TOKEN_RE = re.compile(r"(?:[A-Za-z_$][\w$]*|\d+(?:\.\d+)?|==|!=|<=|>=|->|=>|\+\+|--|&&|\|\||\S)")
IDENT_RE = re.compile(r"^[A-Za-z_$][\w$]*$")


def normalize_language(language: str | None) -> str:
    value = (language or "").strip().lower().lstrip(".")
    value = ALIASES.get(value, value)
    if value not in LANGUAGES:
        raise ValueError(f"Unsupported language {language!r}; choose one of: {', '.join(LANGUAGES)}")
    return value


def language_from_path(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix not in EXTENSIONS:
        raise ValueError(f"Cannot infer language from extension {suffix or '(none)'!r}; pass --language")
    return EXTENSIONS[suffix]


def detect_language(code: str) -> str:
    """Best-effort guess for snippets; explicit language labels are preferable."""
    scores = {language: 0 for language in LANGUAGES}
    for language, words in KEYWORDS.items():
        scores[language] += sum(1 for word in words.split() if re.search(rf"\b{re.escape(word)}\b", code))
    scores["python"] += 5 * len(re.findall(r"^\s*(?:def|class)\s+\w+.*:|^\s*import\s+\w+", code, re.M))
    scores["java"] += 4 * len(re.findall(r"\bpublic\s+(?:static\s+)?(?:class|interface|enum|void|int|String)", code))
    scores["javascript"] += 3 * len(re.findall(r"\b(?:console\.log|require\s*\(|module\.exports|document\.)", code))
    scores["cpp"] += 2 * len(re.findall(r"\b(?:std::|cout\s*<<|cin\s*>>|template\s*<)", code))
    scores["c"] += 2 * len(re.findall(r"#include\s*<[^>]+>|\bprintf\s*\(", code))
    return max(LANGUAGES, key=lambda language: scores[language])


def _comment_mask_and_count(code: str, language: str) -> tuple[list[bool], int]:
    """Approximate comment line detection without requiring a compiler/parser."""
    lines = code.splitlines() or [""]
    mask: list[bool] = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if language == "python":
            # Treat full-line # comments as comments (not '#' inside strings).
            mask.append(bool(re.match(r"^\s*#", line)))
            continue
        was_block = in_block
        starts = "/*" in line
        ends = "*/" in line
        is_comment = was_block or stripped.startswith("//") or stripped.startswith("/*") or (starts and (ends or was_block))
        mask.append(is_comment)
        if starts and not ends:
            in_block = True
        if ends:
            in_block = False
    return mask, sum(mask)


def style_features(sample: dict[str, str]) -> dict[str, float]:
    code = sample["code"]
    language = normalize_language(sample["language"])
    lines = code.splitlines() or [""]
    nonblank = [line for line in lines if line.strip()]
    tokens = TOKEN_RE.findall(code)
    identifiers = [token for token in tokens if IDENT_RE.match(token)]
    counts = Counter(tokens)
    comment_mask, comment_lines = _comment_mask_and_count(code, language)
    lengths = [len(line) for line in nonblank]
    indent_widths = []
    for line in nonblank:
        indent = len(line) - len(line.lstrip(" \t"))
        if indent:
            indent_widths.append(indent)
    keyword_set = set(KEYWORDS[language].split())
    keyword_count = sum(counts[word] for word in keyword_set)
    identifier_counts = Counter(identifiers)
    line_counts = Counter(line.strip() for line in nonblank)
    unique_lines = len(line_counts)
    token_total = len(tokens)
    entropy = 0.0
    if token_total:
        entropy = -sum((n / token_total) * math.log2(n / token_total) for n in counts.values())
    features: dict[str, float] = {
        "language": 1.0,
        "log_chars": math.log1p(len(code)),
        "log_lines": math.log1p(len(lines)),
        "log_tokens": math.log1p(token_total),
        "avg_line_length": sum(lengths) / max(1, len(lengths)),
        "line_length_std": _std(lengths),
        "blank_line_ratio": (len(lines) - len(nonblank)) / len(lines),
        "comment_line_ratio": comment_lines / len(lines),
        "comment_to_code_ratio": comment_lines / max(1, len(nonblank) - comment_lines),
        "indent_mean": sum(indent_widths) / max(1, len(indent_widths)),
        "indent_std": _std(indent_widths),
        "trailing_whitespace_ratio": sum(line.rstrip() != line for line in lines) / len(lines),
        "unique_token_ratio": len(counts) / max(1, token_total),
        "token_entropy": entropy,
        "identifier_mean_length": sum(map(len, identifiers)) / max(1, len(identifiers)),
        "identifier_unique_ratio": len(identifier_counts) / max(1, len(identifiers)),
        "repeated_line_ratio": (len(nonblank) - unique_lines) / max(1, len(nonblank)),
        "keyword_ratio": keyword_count / max(1, token_total),
        "punctuation_ratio": sum(not t.isalnum() and not t.startswith("_") for t in tokens) / max(1, token_total),
        "semicolon_ratio": code.count(";") / max(1, len(nonblank)),
        "brace_ratio": (code.count("{") + code.count("}")) / max(1, token_total),
        "paren_ratio": (code.count("(") + code.count(")")) / max(1, token_total),
        "comment_marker_count": float(code.count("//") + code.count("/*") + code.count("#")),
        "max_line_length": float(max(lengths, default=0)),
        "max_identifier_frequency": float(max(identifier_counts.values(), default=0)),
    }
    for name in LANGUAGES:
        features[f"lang_{name}"] = float(language == name)
    # Broad, language-neutral structural proxies (not claimed to be AST metrics).
    for name, pattern in {
        "control_if": r"\bif\b", "control_loop": r"\b(?:for|while|do)\b",
        "control_try": r"\b(?:try|catch|except)\b", "function_like": r"\b(?:def|function|fn)\b|=>",
        "class_like": r"\bclass\b", "return_like": r"\breturn\b",
    }.items():
        features[name + "_count"] = float(len(re.findall(pattern, code)))
    return features


def _std(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
