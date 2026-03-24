import os
import json
import subprocess
from dataclasses import dataclass
from typing import Optional


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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return [], "TIMEOUT — search took too long"
    except OSError as e:
        return [], f"yt-dlp error: {e}"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if is_auth_error(stderr):
            return [], "AUTH REQUIRED — run: yt-dlp --cookies-from-browser firefox --cookies ~/.config/streamerbox/cookies.txt --skip-download https://www.youtube.com"
        return [], f"PLAYBACK ERROR — {stderr[:80]}"

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
        "/usr/local/bin/yt-dlp",
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
    # sp=EgIQAw%3D%3D is YouTube's playlist filter
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp=EgIQAw%3D%3D"
    cmd = [
        "/usr/local/bin/yt-dlp",
        "--cookies", cookies,
        "--dump-json",
        "--flat-playlist",
        f"--playlist-end={max_results}",
        search_url,
    ]
    return _run_ytdlp(cmd)
