"""
pipeline/downloader.py – Generic file downloader used by all scrapers.
"""
import os
import time
import requests
from pathlib import Path

# Files larger than this will NOT be downloaded (record FAILED_TOO_LARGE instead)
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

DATA_ROOT = Path(__file__).parent.parent / "data"

HEADERS = {
    "User-Agent": (
        "QDArchive-Seeder/1.0 "
        "(FAU Erlangen; student project; contact: 23129103@stud.uni-erlangen.de)"
    )
}

import requests

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
})
SESSION.headers.update(HEADERS)


def make_project_dir(repo_folder: str, project_folder: str, version_folder: str = None) -> Path:
    """Create and return the local directory for this project's files."""
    parts = [DATA_ROOT, repo_folder, project_folder]
    if version_folder:
        parts.append(version_folder)
    path = Path(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_file(url: str, dest_dir: Path, file_name: str) -> str:
    """
    Download a single file.

    Returns one of:
        SUCCEEDED
        FAILED_LOGIN_REQUIRED
        FAILED_SERVER_UNRESPONSIVE
        FAILED_TOO_LARGE
    """
    dest_path = dest_dir / file_name
    if dest_path.exists():
        return "SUCCEEDED"          # already downloaded

    try:
        # HEAD request first to check size and auth
        head = SESSION.head(url, timeout=30, allow_redirects=True)
        if head.status_code in (401, 403):
            return "FAILED_LOGIN_REQUIRED"

        content_length = head.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_FILE_SIZE_BYTES:
            return "FAILED_TOO_LARGE"

        # Actual download (stream to disk)
        resp = SESSION.get(url, timeout=120, stream=True)
        if resp.status_code in (401, 403):
            return "FAILED_LOGIN_REQUIRED"
        if resp.status_code != 200:
            return "FAILED_SERVER_UNRESPONSIVE"

        total = 0
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                fh.write(chunk)
                total += len(chunk)
                if total > MAX_FILE_SIZE_BYTES:
                    fh.close()
                    dest_path.unlink(missing_ok=True)
                    return "FAILED_TOO_LARGE"

        return "SUCCEEDED"

    except requests.exceptions.Timeout:
        return "FAILED_SERVER_UNRESPONSIVE"
    except requests.exceptions.ConnectionError:
        return "FAILED_SERVER_UNRESPONSIVE"
    except Exception as exc:
        print(f"  [downloader] Unexpected error for {url}: {exc}")
        return "FAILED_SERVER_UNRESPONSIVE"


def safe_filename(name: str) -> str:
    """Sanitise a filename so it is safe on all platforms."""
    keepchars = " .-_()"
    return "".join(c for c in name if c.isalnum() or c in keepchars).strip()

