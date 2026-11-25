"""
Project mapper: prints your project's folder tree, detects your tech stack,
and highlights the files most likely needed to add new features.

It only reads file NAMES and SIZES (plus dependency names from package.json and
requirements.txt). It never prints the contents of your code or secret files.

Usage (run from anywhere, point it at your project folder):
    python project_map.py /path/to/your/project
    python project_map.py . --max-depth 5 --out project_map.txt

Then paste the contents of project_map.txt into the chat (or upload the file).
"""
import argparse
import json
import os
import re
from pathlib import Path

IGNORE_DIRS = {
    "node_modules", ".git", "venv", ".venv", "env", "__pycache__", "dist", "build",
    ".next", ".nuxt", ".idea", ".vscode", "target", "vendor", "coverage", ".cache",
    ".gradle", "Pods", ".dart_tool", ".pytest_cache", ".mypy_cache", "site-packages",
    ".expo", ".svelte-kit", "out", "bin", "obj",
}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".mp4", ".mp3", ".wav",
    ".pdf", ".zip", ".tar", ".gz", ".woff", ".woff2", ".ttf", ".eot", ".pt", ".pth",
    ".onnx", ".bin", ".h5", ".safetensors", ".joblib", ".pkl", ".csv", ".parquet",
}
SECRET_NAMES = re.compile(r"^\.env(\..*)?$|secrets?\.|credentials|\.pem$|\.key$|id_rsa", re.I)
COLLAPSE_OVER = 40  # folders with more files than this are summarised

KEY_NAMES = {
    "app.py", "main.py", "server.py", "manage.py", "wsgi.py", "asgi.py", "urls.py",
    "views.py", "routes.py", "server.js", "app.js", "index.js", "index.ts", "main.ts",
    "app.ts", "main.dart", "App.jsx", "App.tsx", "App.js", "App.vue", "index.html",
    "package.json", "requirements.txt", "pyproject.toml", "pubspec.yaml", "pom.xml",
    "build.gradle", "go.mod", "composer.json", "Gemfile", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "AndroidManifest.xml", "Info.plist",
}
KEY_HINTS = re.compile(r"route|router|api|controller|upload|detect|analy|classif|service|handler|endpoint", re.I)

STACK_MARKERS = {
    "package.json": "Node.js / JavaScript", "requirements.txt": "Python",
    "pyproject.toml": "Python", "manage.py": "Django", "pubspec.yaml": "Flutter / Dart",
    "pom.xml": "Java (Maven)", "build.gradle": "Java/Kotlin/Android (Gradle)",
    "go.mod": "Go", "composer.json": "PHP", "Gemfile": "Ruby",
    "Dockerfile": "Docker", "docker-compose.yml": "Docker Compose",
    "AndroidManifest.xml": "Android", "Cargo.toml": "Rust",
}
JS_LIBS = ["react", "next", "vue", "nuxt", "@angular/core", "svelte", "express", "fastify",
           "koa", "nestjs", "@nestjs/core", "react-native", "expo", "electron", "axios", "typescript"]
PY_LIBS = ["flask", "fastapi", "django", "streamlit", "gradio", "torch", "tensorflow",
           "transformers", "opencv-python", "numpy", "pandas", "scikit-learn", "uvicorn", "celery"]


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024


def walk(root: Path, max_depth: int):
    lines, key_files, all_names = [], [], []

    def rec(folder: Path, prefix: str, depth: int):
        try:
            entries = sorted(os.scandir(folder), key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))
        except PermissionError:
            lines.append(f"{prefix}[permission denied]")
            return
        dirs = [e for e in entries if e.is_dir(follow_symlinks=False)]
        files = [e for e in entries if not e.is_dir(follow_symlinks=False)]

        for d in dirs:
            if d.name in IGNORE_DIRS:
                lines.append(f"{prefix}|-- {d.name}/  (skipped)")
                continue
            lines.append(f"{prefix}|-- {d.name}/")
            if depth < max_depth:
                rec(Path(d.path), prefix + "|   ", depth + 1)
            else:
                lines.append(f"{prefix}|   ... (max depth reached)")

        if len(files) > COLLAPSE_OVER:
            exts = {}
            for f in files:
                exts[Path(f.name).suffix.lower() or "(none)"] = exts.get(Path(f.name).suffix.lower() or "(none)", 0) + 1
            summary = ", ".join(f"{c}x{e}" for e, c in sorted(exts.items(), key=lambda x: -x[1])[:6])
            lines.append(f"{prefix}|-- [{len(files)} files: {summary}]")
            files = [f for f in files if f.name in KEY_NAMES]  # still show key ones

        for f in files:
            rel = Path(f.path).relative_to(root)
            all_names.append(f.name)
            ext = Path(f.name).suffix.lower()
            try:
                size = human(f.stat().st_size)
            except OSError:
                size = "?"
            if SECRET_NAMES.search(f.name):
                lines.append(f"{prefix}|-- {f.name}  ({size})  [SECRET FILE - do not share contents]")
                continue
            tag = ""
            if ext not in BINARY_EXT and (f.name in KEY_NAMES or KEY_HINTS.search(f.name)):
                tag = "  <== likely needed"
                key_files.append(str(rel))
            lines.append(f"{prefix}|-- {f.name}  ({size}){tag}")

    rec(root, "", 1)
    return lines, key_files, all_names


def detect_stack(root: Path, all_names):
    stack = sorted({STACK_MARKERS[n] for n in all_names if n in STACK_MARKERS})
    libs = []
    for pkg in root.rglob("package.json"):
        if any(part in IGNORE_DIRS for part in pkg.parts):
            continue
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            libs += [f"{k}@{deps[k]}" for k in JS_LIBS if k in deps]
        except Exception:
            pass
    for req in root.rglob("requirements*.txt"):
        if any(part in IGNORE_DIRS for part in req.parts):
            continue
        try:
            text = req.read_text(encoding="utf-8", errors="ignore").lower()
            libs += [k for k in PY_LIBS if re.search(rf"^{re.escape(k)}\b", text, re.M)]
        except Exception:
            pass
    return stack, sorted(set(libs))


def main():
    ap = argparse.ArgumentParser(description="Map a project folder without exposing code.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--max-depth", type=int, default=6)
    ap.add_argument("--out", default="project_map.txt")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")

    lines, key_files, all_names = walk(root, args.max_depth)
    stack, libs = detect_stack(root, all_names)

    out = [f"PROJECT: {root.name}", f"Detected stack: {', '.join(stack) or 'unknown'}",
           f"Key libraries: {', '.join(libs) or 'none detected'}", "", "FOLDER TREE:", f"{root.name}/"]
    out += lines
    out += ["", "FILES MOST LIKELY NEEDED (entry points, routes, APIs, config):"]
    out += [f"  - {k}" for k in key_files] or ["  (none detected)"]
    text = "\n".join(out)

    print(text)
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"\nSaved to {args.out}. Paste its contents or upload it in the chat.")


if __name__ == "__main__":
    main()
    