import os
from llm import ask_llm
from chunker import walk_repo, SKIP_DIRS


def _read_readme(repo_path: str) -> str:
    for name in ("README.md", "README.rst", "README.txt", "readme.md"):
        candidate = os.path.join(repo_path, name)
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:4000]  
    return ""


def _top_level_structure(repo_path: str) -> str:
    """A shallow directory listing — gives the LLM the shape of the project
    without needing every file's contents."""
    lines = []
    for entry in sorted(os.listdir(repo_path)):
        if entry in SKIP_DIRS or entry.startswith("."):
            continue
        full = os.path.join(repo_path, entry)
        marker = "/" if os.path.isdir(full) else ""
        lines.append(f"- {entry}{marker}")
    return "\n".join(lines)


def generate_overview(repo_path: str) -> str:
    """Plain-language summary of what the repo does, using README + top-level structure."""
    readme = _read_readme(repo_path)
    structure = _top_level_structure(repo_path)

    prompt = f"""You are helping a developer understand an unfamiliar codebase.

Top-level project structure:
{structure}

README contents (may be partial):
{readme if readme else "(no README found)"}

In 4-6 plain-language sentences, explain:
1. What this project does
2. What tech stack / main components it uses
3. Where a new contributor should start looking

Be concrete. If the README is missing or unhelpful, infer from the folder structure and say so."""

    return ask_llm(prompt)


def generate_file_map(chunks: list, max_files: int = 25) -> dict:
    """
    One-line plain-English description per file — beginner-friendly sidebar.
    Capped at max_files to keep this fast and cheap; prioritizes files
    at shallower paths (more likely to be structurally important).
    """
    
    seen = {}
    for c in chunks:
        if c["filepath"] not in seen:
            seen[c["filepath"]] = c["text"]

    sorted_files = sorted(seen.items(), key=lambda kv: kv[0].count(os.sep))[:max_files]

    file_map = {}
    for filepath, text in sorted_files:
        snippet = text[:800]  # short snippet is enough for a one-liner
        prompt = (
            f"File: {filepath}\n\nContents (truncated):\n{snippet}\n\n"
            "In ONE short sentence (plain English, no jargon), describe what this file does."
        )
        try:
            file_map[filepath] = ask_llm(prompt).strip()
        except Exception:
            file_map[filepath] = "(description unavailable)"

    return file_map
