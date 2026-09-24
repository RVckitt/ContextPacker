import os
import sys
import argparse
from pathlib import Path
from fnmatch import fnmatch

DEFAULT_IGNORE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", ".venv", "venv", "env",
    "node_modules", ".idea", ".vscode", "dist", "build", ".pytest_cache"
}

DEFAULT_IGNORE_EXTS = {
    ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".png", ".jpg",
    ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".zip", ".tar", ".gz",
    ".7z", ".mp3", ".mp4", ".lock", ".bin", ".woff", ".woff2", ".ttf"
}

def load_gitignore_patterns(root_path: Path) -> list:
    gitignore_file = root_path / ".gitignore"
    patterns = []
    if gitignore_file.is_file():
        try:
            with open(gitignore_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:
            pass
    return patterns

def is_ignored(path: Path, root_path: Path, ignore_patterns: list) -> bool:
    if any(part in DEFAULT_IGNORE_DIRS for part in path.parts):
        return True
        
    if path.suffix.lower() in DEFAULT_IGNORE_EXTS:
        return True

    try:
        rel_path_str = str(path.relative_to(root_path))
    except ValueError:
        rel_path_str = path.name

    for pattern in ignore_patterns:
        clean_pat = pattern.rstrip("/")
        if fnmatch(rel_path_str, clean_pat) or fnmatch(path.name, clean_pat):
            return True
        if pattern.endswith("/") and path.is_dir() and fnmatch(path.name, clean_pat):
            return True

    return False

def generate_tree(root_path: Path, ignore_patterns: list, prefix: str = "") -> str:
    lines = []
    try:
        entries = sorted([
            p for p in root_path.iterdir() 
            if not is_ignored(p, root_path, ignore_patterns)
        ], key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return ""

    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            sub_tree = generate_tree(entry, ignore_patterns, prefix + extension)
            if sub_tree:
                lines.append(sub_tree)
    return "\n".join(lines)

def run():
    parser = argparse.ArgumentParser(
        description="Pakuje strukturę i pliki projektu do jednego pliku Markdown dla AI."
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Ścieżka do katalogu projektu (domyślnie obecny katalog)"
    )
    parser.add_argument(
        "-o", "--output", default="project_context.md", help="Plik wyjściowy (domyślnie project_context.md)"
    )
    args = parser.parse_args()

    root_path = Path(args.path).resolve()
    if not root_path.is_dir():
        print(f"Błąd: Ścieżka '{root_path}' nie jest katalogiem.", file=sys.stderr)
        sys.exit(1)

    ignore_patterns = load_gitignore_patterns(root_path)
    output_file = Path(args.output).resolve()

    print(f"Skanowanie projektu: {root_path}")
    
    tree_str = generate_tree(root_path, ignore_patterns)
    
    markdown_content = []
    markdown_content.append(f"# Struktura Projektu: {root_path.name}\n")
    markdown_content.append("```text")
    markdown_content.append(f"{root_path.name}/")
    markdown_content.append(tree_str)
    markdown_content.append("```\n")
    markdown_content.append("---\n")
    markdown_content.append("# Zawartość Plików\n")

    files_processed = 0
    total_chars = 0

    for path in sorted(root_path.rglob("*")):
        if path.is_file() and not is_ignored(path, root_path, ignore_patterns):
            if path.resolve() == output_file:
                continue

            rel_path = path.relative_to(root_path)
            ext = path.suffix.lstrip(".") or "text"

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                markdown_content.append(f"## Plik: `{rel_path}`\n")
                markdown_content.append(f"```{ext}")
                markdown_content.append(content)
                markdown_content.append("```\n")

                files_processed += 1
                total_chars += len(content)
            except Exception:
                continue

    output_file.write_text("\n".join(markdown_content), encoding="utf-8")

    print(f"Gotowe!")
    print(f"- Przetworzono plików: {files_processed}")
    print(f"- Szacowana liczba znaków: {total_chars:,}")
    print(f"- Wynik zapisano w: {output_file.name}")

if __name__ == "__main__":
    run()
