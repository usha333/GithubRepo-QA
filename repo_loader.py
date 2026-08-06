import os
import shutil
import tempfile
from git import Repo, GitCommandError


def clone_repo(github_url: str) -> str:
    """
    Clones a public GitHub repo into a temp directory.
    Returns the local path to the cloned repo.

    Raises ValueError with a clear message on bad URL / private repo / not found.
    """
    
    if not github_url.startswith(("https://github.com/", "http://github.com/")):
        raise ValueError("Please provide a valid GitHub URL, e.g. https://github.com/user/repo")

    local_dir = tempfile.mkdtemp(prefix="repo_qa_")

    try:
        
        Repo.clone_from(github_url, local_dir, depth=1)
    except GitCommandError as e:
        shutil.rmtree(local_dir, ignore_errors=True)
        if "Authentication" in str(e) or "not found" in str(e).lower():
            raise ValueError(
                "Couldn't clone this repo. It may be private, deleted, or the URL is wrong. "
                "This tool only supports public repos."
            )
        raise ValueError(f"Clone failed: {e}")

    return local_dir


def cleanup_repo(local_dir: str):
    """Remove the cloned repo from disk once we're done indexing it."""
    shutil.rmtree(local_dir, ignore_errors=True)
