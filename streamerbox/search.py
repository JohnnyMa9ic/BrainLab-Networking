import os
import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

YTDLP = shutil.which("yt-dlp") or "/usr/local/bin/yt-dlp"

AUTH_PATTERNS = ["sign in", "premium", "members only", "403"]


@dataclass
class SearchResult:
    name: str
    url: str


def is_auth_error(stderr: str) -> bool:
    lower = stderr.lower()
    return any(p in lower for p in AUTH_PATTERNS)


def parse_ytdlp_result(line: str) -> Optional[SearchResult]:
    try:
        data = json.loads(line)
        url = data.get("webpage_url") or data.get("url")
        title = data.get("title")
        if not url or not title:
            return None
        return SearchResult(name=title, url=url)
    except (json.JSONDecodeError, AttributeError):
        return None


def _run_ytdlp(cmd: list[str]) -> tuple[list[SearchResult], str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return [], "TIMEOUT — search took too long"
    except OSError as e:
        return [], f"yt-dlp error: {e}"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if is_auth_error(stderr):
            return [], "AUTH REQUIRED — run: yt-dlp --cookies-from-browser firefox --cookies ~/.config/streamerbox/cookies.txt --skip-download https://www.youtube.com"
        return [], f"ERROR — {stderr[:200]}"

    results = []
    for line in result.stdout.strip().splitlines():
        parsed = parse_ytdlp_result(line)
        if parsed:
            results.append(parsed)

    if not results:
        return [], "NO SIGNAL — no results"

    return results, ""


def search(query: str, max_results: int = 25) -> tuple[list[SearchResult], str]:
    """Search YouTube for videos."""
    home = os.path.expanduser("~")
    cookies = os.path.join(home, ".config/streamerbox/cookies.txt")
    cmd = [
        YTDLP,
        "--cookies", cookies,
        "--dump-json",
        "--flat-playlist",
        "--no-playlist",
        f"ytsearch{max_results}:{query}",
    ]
    return _run_ytdlp(cmd)


def search_playlists(query: str, max_results: int = 25) -> tuple[list[SearchResult], str]:
    """Search YouTube for playlists."""
    import urllib.parse
    home = os.path.expanduser("~")
    cookies = os.path.join(home, ".config/streamerbox/cookies.txt")
    # WARNING: yt-dlp does not expose a native playlist search extractor in this
    # environment (ytsearchplaylist: is unsupported), so this relies on YouTube's
    # web search filter URL. sp=EgIQAw%3D%3D is the current "playlist" filter and
    # may break if YouTube changes its web UI or query params.
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp=EgIQAw%3D%3D"
    cmd = [
        YTDLP,
        "--cookies", cookies,
        "--dump-json",
        "--flat-playlist",
        f"--playlist-end={max_results}",
        search_url,
    ]
    return _run_ytdlp(cmd)
