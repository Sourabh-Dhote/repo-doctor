import re
import os
import shutil
import stat
import asyncio
from git import Repo

def validate_github_url(url: str) -> tuple[str, str]:
    """Validate and extract (owner, repo_name) from various GitHub URL formats."""
    cleaned = str(url).strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    
    # Matches:
    # https://github.com/owner/repo
    # http://github.com/owner/repo
    # github.com/owner/repo
    # www.github.com/owner/repo
    pattern = r"^(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:/.*)?$"
    match = re.match(pattern, cleaned, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid GitHub URL. Must be in the format: https://github.com/owner/repository")
    
    owner = match.group(1).strip()
    repo_name = match.group(2).strip()
    if not owner or not repo_name:
        raise ValueError("Could not determine owner and repository name from URL.")
    return owner, repo_name

def _remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree on Windows read-only git files."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

async def clone_repo(url: str, target_dir: str) -> str:
    """Clone a public GitHub repository with depth=1 without hanging on credentials."""
    # Ensure URL starts with https:// for git cloning
    normalized_url = str(url).strip()
    if not normalized_url.startswith(("http://", "https://")):
        normalized_url = f"https://{normalized_url}"

    def _clone():
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, onerror=_remove_readonly)
        os.makedirs(target_dir, exist_ok=True)
        
        # Disable interactive credential prompts so private/non-existent repos fail quickly
        clone_env = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "",
            "GCM_INTERACTIVE": "never",
        }
        Repo.clone_from(normalized_url, target_dir, depth=1, env=clone_env)
        return target_dir

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _clone)

def cleanup_repo(repo_path: str) -> None:
    """Safely remove cloned repository directory handling Windows permissions."""
    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, onerror=_remove_readonly)
    except Exception as e:
        print(f"[RepoDoctor] Failed to cleanup {repo_path}: {e}")
