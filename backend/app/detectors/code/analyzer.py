
import re
from collections import Counter


def analyze_code_features(
    content: str,
    language_hint: str = "auto",
) -> dict:

    source = content.strip()

    if not source:
        raise ValueError("Source code cannot be empty.")

    lines = source.splitlines()

    tokens = re.findall(
        r"[A-Za-z_]\w*|\d+(?:\.\d+)?|[^\s]",
        source
    )

    token_counts = Counter(tokens)

    nonempty_lines = [
        line for line in lines if line.strip()
    ]

    repeated_lines = {
        line.strip(): count
        for line, count in Counter(
            line.strip()
            for line in nonempty_lines
        ).items()
        if count > 1
    }

    comment_patterns = [
        r"^\s*#",
        r"^\s*//",
        r"^\s*/\*",
        r"^\s*\*",
    ]

    comment_lines = sum(
        1
        for line in lines
        if any(
            re.match(pattern, line)
            for pattern in comment_patterns
        )
    )

    average_line_length = (
        sum(len(line) for line in nonempty_lines)
        / len(nonempty_lines)
        if nonempty_lines else 0
    )

    return {
        "language_hint": language_hint,
        "character_count": len(source),
        "line_count": len(lines),
        "nonempty_line_count": len(nonempty_lines),
        "token_count": len(tokens),
        "unique_token_count": len(token_counts),
        "token_diversity": round(
            len(token_counts) / len(tokens), 4
        ) if tokens else 0,
        "comment_line_count": comment_lines,
        "comment_line_ratio": round(
            comment_lines / len(nonempty_lines), 4
        ) if nonempty_lines else 0,
        "average_line_length": round(
            average_line_length, 2
        ),
        "repeated_lines": repeated_lines,
    }
