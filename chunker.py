import os
import re


SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
    "build", ".next", "target", ".idea", ".vscode", "vendor",
    "coverage", ".pytest_cache", "egg-info",
}

INCLUDE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt",
    ".md", ".txt", ".yaml", ".yml", ".toml", ".json",
}

MAX_FILE_SIZE_BYTES = 200_000  
MAX_LINES_PER_CHUNK = 300      
MAX_FILES = 500                 


def walk_repo(repo_path: str):
    """Yields (relative_path, absolute_path) for every file worth indexing."""
    file_count = 0
    for root, dirs, files in os.walk(repo_path):
        
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            if file_count >= MAX_FILES:
                return
            ext = os.path.splitext(fname)[1]
            if ext not in INCLUDE_EXTENSIONS:
                continue

            abs_path = os.path.join(root, fname)
            try:
                if os.path.getsize(abs_path) > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            rel_path = os.path.relpath(abs_path, repo_path)
            file_count += 1
            yield rel_path, abs_path


def _split_large_file(text: str, max_lines: int):
    """
    Fallback splitter for big files: cut on blank-line boundaries near
    the max_lines mark, rather than mid-line, so we don't sever a
    statement in half.
    """
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return [text]

    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + max_lines, len(lines))
        # try to end on a blank line for a cleaner cut
        while end < len(lines) and lines[end].strip() != "":
            end += 1
        chunks.append("\n".join(lines[start:end]))
        start = end
    return chunks


def chunk_repo(repo_path: str):
    """
    Returns a list of dicts: {"text": ..., "filepath": ..., "chunk_id": ...}
    ready to be embedded.
    """
    chunks = []
    for rel_path, abs_path in walk_repo(repo_path):
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            continue

        if not text.strip():
            continue

        pieces = _split_large_file(text, MAX_LINES_PER_CHUNK)
        for i, piece in enumerate(pieces):
            chunks.append({
                "text": piece,
                "filepath": rel_path,
                "chunk_id": f"{rel_path}::{i}",
            })

    return chunks
