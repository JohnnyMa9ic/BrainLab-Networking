# StreamerBox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CRT-styled ambient anime/YouTube player that autostarts on GNOME login, runs mpv fullscreen, and overlays a cyberpunk-themed GTK3 channel strip + search UI on top.

**Architecture:** mpv runs as a subprocess filling the screen via `--geometry/--no-border` (not `--fullscreen`, to preserve keyboard focus for the overlay). A GTK3 always-on-top transparent window captures all key events and communicates with mpv via its Unix IPC socket. yt-dlp is invoked on demand for search and URL resolution.

**Tech Stack:** Python 3.12, GTK3 (python3-gi), mpv, yt-dlp, PyYAML, pytest, xdotool, Pillow (nosignal.png generation)

---

## File Map

| File | Role |
|---|---|
| `~/streamerbox/channels.py` | Channel model, YAML load/merge/save |
| `~/streamerbox/player.py` | mpv subprocess, IPC socket, background state thread, crash recovery |
| `~/streamerbox/search.py` | yt-dlp search subprocess, output parsing, result model |
| `~/streamerbox/overlay.py` | GTK3 window, channel strip rendering, keyboard dispatch, fade behaviour |
| `~/streamerbox/main.py` | Entry point — wires player + overlay, launches everything |
| `~/streamerbox/themes/cyberpunk.css` | GTK CSS — colours, scanlines, glow, monospace font |
| `~/streamerbox/assets/nosignal.png` | 1920x1080 CRT no-signal graphic (generated once) |
| `~/streamerbox/tests/test_channels.py` | Unit tests for channel loading, merging, saving |
| `~/streamerbox/tests/test_player.py` | Unit tests for IPC command building, mpv arg construction |
| `~/streamerbox/tests/test_search.py` | Unit tests for yt-dlp output parsing |
| `~/.config/streamerbox/channels.yaml` | Base channel config (hand-edited) |
| `~/.config/autostart/streamerbox.desktop` | GNOME autostart entry |

---

## Task 1: Project Scaffold

**Files:**
- Create: `~/streamerbox/` (directory structure)
- Create: `~/streamerbox/tests/__init__.py`
- Create: `~/streamerbox/themes/` and `~/streamerbox/assets/`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p ~/streamerbox/tests ~/streamerbox/themes ~/streamerbox/assets
touch ~/streamerbox/tests/__init__.py
cd ~/streamerbox
git init
```

- [ ] **Step 2: Create initial channels.yaml**

```bash
mkdir -p ~/.config/streamerbox
```

Write `~/.config/streamerbox/channels.yaml`:
```yaml
channels:
  - id: 1
    name: Cowboy Bebop
    url: https://www.youtube.com/playlist?list=PLJAOZgYiCEnAk0xUMvCYiY5SVzVHBbT55
  - id: 2
    name: Ghost in the Shell SAC
    url: https://www.crunchyroll.com/series/GY5VW29G6/ghost-in-the-shell-stand-alone-complex
```

- [ ] **Step 3: Create empty saved.yaml**

```bash
echo "channels: []" > ~/.config/streamerbox/saved.yaml
```

- [ ] **Step 4: Verify cookies exist**

```bash
wc -l ~/.config/streamerbox/cookies.txt
grep -c "crunchyroll" ~/.config/streamerbox/cookies.txt
```

Expected: 150+ lines, at least 1 crunchyroll match.

- [ ] **Step 5: Commit scaffold**

```bash
cd ~/streamerbox
git add .
git commit -m "chore: project scaffold"
```

---

## Task 2: channels.py — Channel Model + YAML I/O

**Files:**
- Create: `~/streamerbox/channels.py`
- Create: `~/streamerbox/tests/test_channels.py`

- [ ] **Step 1: Write failing tests**

Write `~/streamerbox/tests/test_channels.py`:
```python
import os
import tempfile
import yaml
import pytest
from channels import Channel, ChannelManager


def make_yaml(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def test_channel_model():
    ch = Channel(id=1, name="Bebop", url="https://example.com")
    assert ch.id == 1
    assert ch.name == "Bebop"
    assert ch.url == "https://example.com"


def test_load_channels_yaml(tmp_path):
    path = make_yaml(tmp_path, "channels.yaml", {
        "channels": [
            {"id": 1, "name": "Bebop", "url": "https://yt.com/1"},
            {"id": 2, "name": "GitS", "url": "https://cr.com/2"},
        ]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {"channels": []})
    mgr = ChannelManager(channels_path=path, saved_path=saved)
    assert len(mgr.channels) == 2
    assert mgr.channels[0].name == "Bebop"


def test_saved_channels_appended_after_base(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": 1, "name": "Bebop", "url": "https://yt.com/1"}]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {
        "channels": [{"id": 2, "name": "Akira", "url": "https://yt.com/2"}]
    })
    mgr = ChannelManager(channels_path=base, saved_path=saved)
    assert len(mgr.channels) == 2
    assert mgr.channels[1].name == "Akira"


def test_save_new_channel_assigns_next_id(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": 1, "name": "Bebop", "url": "https://yt.com/1"}]
    })
    saved_path = str(tmp_path / "saved.yaml")
    with open(saved_path, "w") as f:
        yaml.dump({"channels": []}, f)
    mgr = ChannelManager(channels_path=base, saved_path=saved_path)
    mgr.save_channel(name="Akira", url="https://yt.com/2")
    assert len(mgr.channels) == 2
    assert mgr.channels[1].id == 2


def test_save_duplicate_url_silently_skipped(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": 1, "name": "Bebop", "url": "https://yt.com/1"}]
    })
    saved_path = str(tmp_path / "saved.yaml")
    with open(saved_path, "w") as f:
        yaml.dump({"channels": []}, f)
    mgr = ChannelManager(channels_path=base, saved_path=saved_path)
    mgr.save_channel(name="Bebop Again", url="https://yt.com/1")
    assert len(mgr.channels) == 1


def test_get_channel_by_index(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [
            {"id": 1, "name": "A", "url": "https://a.com"},
            {"id": 2, "name": "B", "url": "https://b.com"},
        ]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {"channels": []})
    mgr = ChannelManager(channels_path=base, saved_path=saved)
    assert mgr.get(0).name == "A"
    assert mgr.get(1).name == "B"
    assert mgr.get(2) is None  # out of bounds returns None


def test_channel_count(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": i, "name": f"CH{i}", "url": f"https://{i}.com"} for i in range(1, 6)]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {"channels": []})
    mgr = ChannelManager(channels_path=base, saved_path=saved)
    assert mgr.count() == 5
```

- [ ] **Step 2: Run tests — verify they all fail**

```bash
cd ~/streamerbox && python3 -m pytest tests/test_channels.py -v
```

Expected: ImportError on `channels`

- [ ] **Step 3: Implement channels.py**

Write `~/streamerbox/channels.py`:
```python
import os
import yaml
from dataclasses import dataclass
from typing import Optional


@dataclass
class Channel:
    id: int
    name: str
    url: str


class ChannelManager:
    def __init__(self, channels_path: str = None, saved_path: str = None):
        home = os.path.expanduser("~")
        self._channels_path = channels_path or os.path.join(home, ".config/streamerbox/channels.yaml")
        self._saved_path = saved_path or os.path.join(home, ".config/streamerbox/saved.yaml")
        self.channels: list[Channel] = []
        self._reload()

    def _load_yaml(self, path: str) -> list[dict]:
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return data.get("channels") or []
        except FileNotFoundError:
            return []

    def _reload(self):
        base = [Channel(**c) for c in self._load_yaml(self._channels_path)]
        saved = [Channel(**c) for c in self._load_yaml(self._saved_path)]
        self.channels = base + saved

    def get(self, index: int) -> Optional[Channel]:
        if 0 <= index < len(self.channels):
            return self.channels[index]
        return None

    def count(self) -> int:
        return len(self.channels)

    def save_channel(self, name: str, url: str):
        existing_urls = {ch.url for ch in self.channels}
        if url in existing_urls:
            return
        next_id = max((ch.id for ch in self.channels), default=0) + 1
        saved = self._load_yaml(self._saved_path)
        saved.append({"id": next_id, "name": name, "url": url})
        with open(self._saved_path, "w") as f:
            yaml.dump({"channels": saved}, f)
        self._reload()
```

- [ ] **Step 4: Run tests — verify they all pass**

```bash
cd ~/streamerbox && python3 -m pytest tests/test_channels.py -v
```

Expected: 7 tests PASSED

- [ ] **Step 5: Commit**

```bash
cd ~/streamerbox
git add channels.py tests/test_channels.py
git commit -m "feat: channel model, YAML load/merge/save"
```

---

## Task 3: player.py — mpv Subprocess + IPC

**Files:**
- Create: `~/streamerbox/player.py`
- Create: `~/streamerbox/tests/test_player.py`

- [ ] **Step 1: Write failing tests**

Write `~/streamerbox/tests/test_player.py`:
```python
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from player import MpvPlayer, build_mpv_args, build_ipc_command


def test_build_mpv_args_no_fullscreen():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert "--fullscreen" not in args
    assert "--geometry=1920x1080+0+0" in args
    assert "--no-border" in args


def test_build_mpv_args_ipc_socket():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert "--input-ipc-server=/tmp/test.sock" in args


def test_build_mpv_args_cookies_expanded():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/home/user/cookies.txt")
    cookie_arg = next(a for a in args if "cookies" in a and "ytdl-raw" in a)
    assert "/home/user/cookies.txt" in cookie_arg


def test_build_mpv_args_ytdlp_path():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert "--ytdl-path=/usr/local/bin/yt-dlp" in args


def test_build_ipc_loadfile():
    cmd = build_ipc_command("loadfile", "https://example.com", "replace")
    data = json.loads(cmd)
    assert data["command"] == ["loadfile", "https://example.com", "replace"]


def test_build_ipc_cycle_pause():
    cmd = build_ipc_command("cycle", "pause")
    data = json.loads(cmd)
    assert data["command"] == ["cycle", "pause"]


def test_build_ipc_seek():
    cmd = build_ipc_command("seek", "5")
    data = json.loads(cmd)
    assert data["command"] == ["seek", "5"]


def test_build_ipc_observe_property():
    cmd = build_ipc_command("observe_property", 1, "time-pos")
    data = json.loads(cmd)
    assert data["command"] == ["observe_property", 1, "time-pos"]
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd ~/streamerbox && python3 -m pytest tests/test_player.py -v
```

Expected: ImportError on `player`

- [ ] **Step 3: Implement player.py**

Write `~/streamerbox/player.py`:
```python
import os
import json
import socket
import subprocess
import threading
import queue
import time
from typing import Optional, Callable


def build_mpv_args(ipc_sock: str, cookies: str) -> list[str]:
    return [
        "mpv",
        "--geometry=1920x1080+0+0",
        "--no-border",
        "--really-quiet",
        "--no-terminal",
        "--sub-auto=fuzzy",
        f"--input-ipc-server={ipc_sock}",
        "--ytdl-path=/usr/local/bin/yt-dlp",
        "--ytdl-format=bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        f"--ytdl-raw-options=cookies={cookies}",
        "--cache=yes",
        "--demuxer-max-bytes=150MiB",
        "--loop-playlist=inf",
        "--idle=yes",
    ]


def build_ipc_command(*args) -> str:
    return json.dumps({"command": list(args)}) + "\n"


class MpvPlayer:
    OBSERVED = ["time-pos", "duration", "media-title", "playlist-pos", "idle-active"]

    def __init__(self, on_event: Optional[Callable] = None):
        home = os.path.expanduser("~")
        self._sock_path = os.path.join(home, ".config/streamerbox/mpv.sock")
        self._cookies = os.path.join(home, ".config/streamerbox/cookies.txt")
        self._proc: Optional[subprocess.Popen] = None
        self._sock: Optional[socket.socket] = None
        self._on_event = on_event or (lambda e: None)
        self._event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._window_id: Optional[int] = None

    def start(self, url: str):
        args = build_mpv_args(self._sock_path, self._cookies)
        args.append(url)
        if os.path.exists(self._sock_path):
            os.unlink(self._sock_path)
        self._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._running = True
        self._thread = threading.Thread(target=self._ipc_loop, daemon=True)
        self._thread.start()

    def _wait_for_socket(self, timeout=10.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(self._sock_path):
                return True
            time.sleep(0.1)
        return False

    def _ipc_loop(self):
        if not self._wait_for_socket():
            return
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.connect(self._sock_path)
            for i, prop in enumerate(self.OBSERVED):
                self._send(build_ipc_command("observe_property", i + 1, prop))
            buf = ""
            while self._running:
                try:
                    chunk = self._sock.recv(4096).decode("utf-8", errors="replace")
                    if not chunk:
                        break
                    buf += chunk
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        if line.strip():
                            try:
                                event = json.loads(line)
                                self._on_event(event)
                            except json.JSONDecodeError:
                                pass
                except OSError:
                    break
        except OSError:
            pass

    def _send(self, cmd: str):
        if self._sock:
            try:
                self._sock.sendall(cmd.encode())
            except OSError:
                pass

    def load(self, url: str):
        self._send(build_ipc_command("loadfile", url, "replace"))

    def cycle_pause(self):
        self._send(build_ipc_command("cycle", "pause"))

    def seek(self, seconds: int):
        self._send(build_ipc_command("seek", str(seconds)))

    def cycle_mute(self):
        self._send(build_ipc_command("cycle", "mute"))

    def cycle_sub(self):
        self._send(build_ipc_command("cycle", "sub"))

    def forward_key(self, key: str):
        """Forward keys with no IPC equivalent (f, i) via xdotool."""
        if self._proc and self._window_id is None:
            try:
                result = subprocess.run(
                    ["xdotool", "search", "--pid", str(self._proc.pid)],
                    capture_output=True, text=True
                )
                ids = result.stdout.strip().split()
                if ids:
                    self._window_id = int(ids[-1])
            except (OSError, ValueError):
                pass
        if self._window_id:
            try:
                subprocess.run(
                    ["xdotool", "key", "--window", str(self._window_id), key],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except OSError:
                pass

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def restart(self, url: str):
        self.stop()
        self._window_id = None  # force xdotool re-lookup on new process
        time.sleep(0.5)
        self.start(url)

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd ~/streamerbox && python3 -m pytest tests/test_player.py -v
```

Expected: 8 tests PASSED

- [ ] **Step 5: Commit**

```bash
cd ~/streamerbox
git add player.py tests/test_player.py
git commit -m "feat: mpv subprocess manager, IPC commands, background state thread"
```

---

## Task 4: search.py — yt-dlp Search + Output Parsing

**Files:**
- Create: `~/streamerbox/search.py`
- Create: `~/streamerbox/tests/test_search.py`

- [ ] **Step 1: Write failing tests**

Write `~/streamerbox/tests/test_search.py`:
```python
import json
import pytest
from unittest.mock import patch, MagicMock
from search import parse_ytdlp_result, SearchResult, is_auth_error


def make_ytdlp_json(title="Test Video", url="https://yt.com/watch?v=abc", duration=1200):
    return json.dumps({
        "title": title,
        "webpage_url": url,
        "duration": duration,
        "extractor": "youtube",
    })


def test_parse_result_extracts_title():
    result = parse_ytdlp_result(make_ytdlp_json())
    assert result.name == "Test Video"


def test_parse_result_extracts_url():
    result = parse_ytdlp_result(make_ytdlp_json())
    assert result.url == "https://yt.com/watch?v=abc"


def test_parse_result_returns_none_on_bad_json():
    result = parse_ytdlp_result("not json at all")
    assert result is None


def test_parse_result_returns_none_on_missing_url():
    data = json.dumps({"title": "Test"})
    result = parse_ytdlp_result(data)
    assert result is None


def test_is_auth_error_sign_in():
    assert is_auth_error("ERROR: Sign in to confirm your age") is True


def test_is_auth_error_premium():
    assert is_auth_error("This video is only available for Premium members") is True


def test_is_auth_error_members_only():
    assert is_auth_error("members only content") is True


def test_is_auth_error_403():
    assert is_auth_error("HTTP Error 403: Forbidden") is True


def test_is_auth_error_normal_error():
    assert is_auth_error("ERROR: Unable to extract video URL") is False
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd ~/streamerbox && python3 -m pytest tests/test_search.py -v
```

Expected: ImportError on `search`

- [ ] **Step 3: Implement search.py**

Write `~/streamerbox/search.py`:
```python
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


def search(query: str, max_results: int = 5) -> tuple[list[SearchResult], str]:
    """
    Run yt-dlp search. Returns (results, error_message).
    error_message is empty string on success.
    """
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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd ~/streamerbox && python3 -m pytest tests/test_search.py -v
```

Expected: 9 tests PASSED

- [ ] **Step 5: Commit**

```bash
cd ~/streamerbox
git add search.py tests/test_search.py
git commit -m "feat: yt-dlp search, result parsing, auth error detection"
```

---

## Task 5: nosignal.png + cyberpunk.css

**Files:**
- Create: `~/streamerbox/assets/nosignal.png`
- Create: `~/streamerbox/themes/cyberpunk.css`

- [ ] **Step 1: Generate nosignal.png**

Run this Python script once to generate the asset:
```bash
python3 - << 'EOF'
from PIL import Image, ImageDraw, ImageFont
import random

W, H = 1920, 1080
img = Image.new("RGB", (W, H), (5, 0, 8))
draw = ImageDraw.Draw(img)

# Scanlines
for y in range(0, H, 4):
    draw.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)

# Static noise
for _ in range(40000):
    x, y = random.randint(0, W-1), random.randint(0, H-1)
    v = random.randint(20, 60)
    draw.point((x, y), fill=(v, 0, v))

# Centre text
cx, cy = W // 2, H // 2
draw.rectangle([cx-320, cy-80, cx+320, cy+80], fill=(5, 0, 8))
draw.rectangle([cx-318, cy-78, cx+318, cy+78], outline=(255, 0, 255), width=2)

text = "NO SIGNAL"
draw.text((cx, cy - 20), text, fill=(255, 0, 255), anchor="mm")
draw.text((cx, cy + 20), "THOUGHT-RELIQUARY BROADCAST", fill=(100, 0, 100), anchor="mm")

import os
img.save(os.path.expanduser("~/streamerbox/assets/nosignal.png"))
print("nosignal.png written")
EOF
```

- [ ] **Step 2: Verify the image**

```bash
python3 -c "from PIL import Image; img=Image.open('/home/johnny/streamerbox/assets/nosignal.png'); print(img.size)"
```

Expected: `(1920, 1080)`

- [ ] **Step 3: Write cyberpunk.css**

Write `~/streamerbox/themes/cyberpunk.css`:
```css
/* StreamerBox — Synthwave/Cyberpunk theme */

* {
    font-family: "Monospace", monospace;
    color: #ff66ff;
}

window {
    background-color: transparent;
}

/* Overlay container — bottom strip */
#overlay-bar {
    background-color: rgba(5, 0, 8, 0.88);
    border-top: 1px solid #ff00ff;
    padding: 8px 12px;
}

/* Now-playing label */
#now-playing {
    color: #ff00ff;
    font-size: 11px;
    letter-spacing: 2px;
}

/* Progress/time label */
#time-label {
    color: #ff66ff;
    font-size: 10px;
    opacity: 0.7;
}

/* Channel button — inactive */
#channel-btn {
    background-color: transparent;
    border: 1px solid rgba(42, 0, 64, 0.8);
    color: rgba(255, 102, 255, 0.4);
    font-size: 9px;
    padding: 4px 8px;
    border-radius: 2px;
}

/* Channel button — active/current */
#channel-btn.active {
    background-color: rgba(255, 0, 255, 0.08);
    border: 1px solid #ff00ff;
    color: #ff66ff;
}

/* Hint bar */
#hint-bar {
    color: rgba(255, 0, 255, 0.25);
    font-size: 8px;
    letter-spacing: 1px;
}

/* Search modal */
#search-modal {
    background-color: rgba(5, 0, 10, 0.96);
    border: 1px solid #ff00ff;
    padding: 16px 20px;
    border-radius: 4px;
}

/* Search input */
#search-entry {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid #ff00ff;
    color: #ff66ff;
    font-size: 14px;
    caret-color: #ff00ff;
    padding: 4px 0;
}

/* Search result row — normal */
#result-row {
    padding: 4px 6px;
    color: rgba(255, 102, 255, 0.6);
    font-size: 10px;
    border-radius: 2px;
}

/* Search result row — selected */
#result-row.selected {
    background-color: rgba(255, 0, 255, 0.12);
    color: #ff66ff;
}

/* Error / status message */
#status-label {
    color: #ff00ff;
    font-size: 10px;
    letter-spacing: 1px;
}

/* No-signal image container */
#nosignal-box {
    background-color: rgba(5, 0, 8, 0.9);
}
```

- [ ] **Step 4: Commit**

```bash
cd ~/streamerbox
git add assets/nosignal.png themes/cyberpunk.css
git commit -m "feat: nosignal.png asset and cyberpunk GTK CSS theme"
```

---

## Task 6: overlay.py — GTK3 Window + Channel Strip

**Files:**
- Create: `~/streamerbox/overlay.py`

Note: GTK windows cannot be unit-tested without a display. This task has no automated tests — verify manually at the end of Task 8.

- [ ] **Step 1: Write overlay.py**

Write `~/streamerbox/overlay.py`:
```python
import os
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

THEME_PATH = os.path.join(os.path.dirname(__file__), "themes/cyberpunk.css")
NOSIGNAL_PATH = os.path.join(os.path.dirname(__file__), "assets/nosignal.png")
FADE_TIMEOUT_MS = 3000  # hide overlay after 3s inactivity


class StreamerOverlay(Gtk.Window):
    def __init__(self, channels, player, on_quit):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self._channels = channels
        self._player = player
        self._on_quit = on_quit
        self._current_idx = 0
        self._search_open = False
        self._search_results = []
        self._search_selected = 0
        self._fade_timer = None
        self._state = {"time_pos": 0, "duration": 0, "title": "", "idle": True}

        self._apply_css()
        self._build_window()
        self._connect_keys()

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_path(THEME_PATH)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_window(self):
        self.set_title("StreamerBox")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_default_size(1920, 1080)
        self.move(0, 0)

        self._stack = Gtk.Stack()
        self.add(self._stack)

        # Main overlay layout
        self._overlay_box = Gtk.Overlay()
        self._stack.add_named(self._overlay_box, "overlay")

        # Transparent fill
        self._bg = Gtk.EventBox()
        self._bg.set_name("transparent-bg")
        self._overlay_box.add(self._bg)

        # Bottom bar
        self._bar = self._build_bar()
        self._bar.set_valign(Gtk.Align.END)
        self._overlay_box.add_overlay(self._bar)
        self._bar.set_no_show_all(True)

        # Search modal (centred)
        self._search_box = self._build_search()
        self._search_box.set_halign(Gtk.Align.CENTER)
        self._search_box.set_valign(Gtk.Align.CENTER)
        self._overlay_box.add_overlay(self._search_box)
        self._search_box.set_no_show_all(True)

        # No-signal view
        self._nosignal = self._build_nosignal()
        self._stack.add_named(self._nosignal, "nosignal")

        self.show_all()
        self._show_nosignal()

    def _build_bar(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_name("overlay-bar")

        # Now-playing row
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._now_playing = Gtk.Label(label="✦ LOADING...")
        self._now_playing.set_name("now-playing")
        self._now_playing.set_halign(Gtk.Align.START)
        self._time_label = Gtk.Label(label="")
        self._time_label.set_name("time-label")
        self._time_label.set_halign(Gtk.Align.END)
        self._time_label.set_hexpand(True)
        top_row.pack_start(self._now_playing, False, False, 0)
        top_row.pack_end(self._time_label, False, False, 0)
        vbox.pack_start(top_row, False, False, 0)

        # Channel strip
        self._channel_strip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vbox.pack_start(self._channel_strip, False, False, 0)

        # Hint
        hint = Gtk.Label(label="↑↓ CH  ·  / SEARCH  ·  J SUBS  ·  Q QUIT")
        hint.set_name("hint-bar")
        hint.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(hint, False, False, 0)

        return vbox

    def _build_search(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_name("search-modal")
        vbox.set_size_request(400, -1)

        title = Gtk.Label(label="SEARCH CHANNELS")
        title.set_name("now-playing")
        vbox.pack_start(title, False, False, 0)

        self._search_entry = Gtk.Entry()
        self._search_entry.set_name("search-entry")
        self._search_entry.connect("activate", self._on_search_submit)
        vbox.pack_start(self._search_entry, False, False, 0)

        self._results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.pack_start(self._results_box, False, False, 0)

        self._search_status = Gtk.Label(label="")
        self._search_status.set_name("status-label")
        self._search_status.set_halign(Gtk.Align.START)
        vbox.pack_start(self._search_status, False, False, 0)

        hint = Gtk.Label(label="ENTER search  ·  ↑↓ select  ·  ENTER play  ·  S save  ·  ESC cancel")
        hint.set_name("hint-bar")
        vbox.pack_start(hint, False, False, 0)

        return vbox

    def _build_nosignal(self):
        box = Gtk.Box()
        box.set_name("nosignal-box")
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(NOSIGNAL_PATH, 1920, 1080, False)
            img = Gtk.Image.new_from_pixbuf(pb)
            box.pack_start(img, True, True, 0)
        except Exception:
            lbl = Gtk.Label(label="NO SIGNAL")
            lbl.set_name("status-label")
            box.pack_start(lbl, True, True, 0)
        return box

    def _connect_keys(self):
        self.connect("key-press-event", self._on_key)
        self.set_can_focus(True)
        self.grab_focus()

    def _on_key(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        self._show_bar()

        if self._search_open:
            return self._handle_search_key(key, event)

        # Overlay-consumed keys
        if key in ("Up",):
            self._change_channel(-1)
            return True
        if key in ("Down",):
            self._change_channel(1)
            return True
        if key in ("slash", "F") and (event.state & Gdk.ModifierType.SHIFT_MASK or key == "slash"):
            self._open_search()
            return True
        if key == "q":
            self._on_quit()
            return True
        if key in ("1","2","3","4","5","6","7","8","9"):
            self._jump_to_channel(int(key) - 1)
            return True

        # Keys forwarded via IPC
        if key == "space":
            self._player.cycle_pause()
            return True
        if key == "Left":
            self._player.seek(-5)
            return True
        if key == "Right":
            self._player.seek(5)
            return True
        if key == "m":
            self._player.cycle_mute()
            return True
        if key == "j":
            self._player.cycle_sub()
            return True

        # Keys forwarded via xdotool
        if key in ("f", "i"):
            self._player.forward_key(key)
            return True

        return False

    def _handle_search_key(self, key, event):
        if key == "Escape":
            self._close_search()
            return True
        if key == "Up":
            self._search_selected = max(0, self._search_selected - 1)
            self._update_result_selection()
            return True
        if key == "Down":
            self._search_selected = min(len(self._search_results) - 1, self._search_selected + 1)
            self._update_result_selection()
            return True
        if key == "s" and self._search_results:
            r = self._search_results[self._search_selected]
            self._channels.save_channel(r.name, r.url)
            self._search_status.set_text(f"SAVED: {r.name}")
            self._refresh_channel_strip()
            return True
        if key == "Return" and self._search_results:
            r = self._search_results[self._search_selected]
            self._player.load(r.url)
            self._close_search()
            return True
        return False

    def _change_channel(self, delta: int):
        new_idx = (self._current_idx + delta) % self._channels.count()
        self._current_idx = new_idx
        ch = self._channels.get(self._current_idx)
        if ch:
            self._player.load(ch.url)
            self._update_now_playing(ch.name)
        self._refresh_channel_strip()

    def _jump_to_channel(self, idx: int):
        if self._channels.get(idx):
            self._current_idx = idx
            ch = self._channels.get(idx)
            self._player.load(ch.url)
            self._update_now_playing(ch.name)
            self._refresh_channel_strip()

    def _open_search(self):
        self._search_open = True
        self._search_results = []
        self._search_selected = 0
        self._search_entry.set_text("")
        self._search_status.set_text("")
        self._clear_results()
        self._search_box.show()
        self._search_entry.grab_focus()

    def _close_search(self):
        self._search_open = False
        self._search_box.hide()
        self.grab_focus()

    def _on_search_submit(self, entry):
        query = entry.get_text().strip()
        if not query:
            return
        self._search_status.set_text("SEARCHING...")
        self._clear_results()
        # Run search in background to avoid blocking GTK
        import threading
        from search import search as do_search
        def _run():
            results, err = do_search(query)
            GLib.idle_add(self._on_search_done, results, err)
        threading.Thread(target=_run, daemon=True).start()

    def _on_search_done(self, results, error):
        self._search_results = results
        self._search_selected = 0
        self._clear_results()
        if error:
            self._search_status.set_text(error)
        else:
            self._search_status.set_text(f"{len(results)} results")
            for r in results:
                lbl = Gtk.Label(label=f"▶ {r.name}")
                lbl.set_name("result-row")
                lbl.set_halign(Gtk.Align.START)
                self._results_box.pack_start(lbl, False, False, 0)
            self._update_result_selection()
            self._results_box.show_all()
        return False  # GLib.idle_add one-shot

    def _clear_results(self):
        for child in self._results_box.get_children():
            self._results_box.remove(child)

    def _update_result_selection(self):
        for i, child in enumerate(self._results_box.get_children()):
            ctx = child.get_style_context()
            if i == self._search_selected:
                ctx.add_class("selected")
            else:
                ctx.remove_class("selected")

    def _refresh_channel_strip(self):
        for child in self._channel_strip.get_children():
            self._channel_strip.remove(child)
        total = self._channels.count()
        start = max(0, self._current_idx - 3)
        end = min(total, start + 7)
        for i in range(start, end):
            ch = self._channels.get(i)
            if ch:
                btn = Gtk.Label(label=f"{ch.id:02d}\n{ch.name[:8]}")
                btn.set_name("channel-btn")
                if i == self._current_idx:
                    btn.get_style_context().add_class("active")
                self._channel_strip.pack_start(btn, False, False, 0)
        self._channel_strip.show_all()

    def _update_now_playing(self, title: str):
        ch = self._channels.get(self._current_idx)
        ch_num = ch.id if ch else 0
        self._now_playing.set_text(f"✦ CH {ch_num:02d} — {title.upper()[:30]}")

    def _show_bar(self):
        self._bar.show()
        self._stack.set_visible_child_name("overlay")
        if self._fade_timer:
            GLib.source_remove(self._fade_timer)
        self._fade_timer = GLib.timeout_add(FADE_TIMEOUT_MS, self._hide_bar)

    def _hide_bar(self):
        if not self._search_open:
            self._bar.hide()
        self._fade_timer = None
        return False

    def _show_nosignal(self):
        self._stack.set_visible_child_name("nosignal")

    def on_mpv_event(self, event: dict):
        """Called from player.py background thread via GLib.idle_add."""
        if event.get("event") == "property-change":
            name = event.get("name")
            data = event.get("data")
            if name == "time-pos" and data is not None:
                self._state["time_pos"] = data
                GLib.idle_add(self._update_progress)
            elif name == "duration" and data is not None:
                self._state["duration"] = data
            elif name == "media-title" and data:
                self._state["title"] = data
                GLib.idle_add(self._update_now_playing, data)
            elif name == "idle-active" and data:
                GLib.idle_add(self._show_nosignal)
            elif name == "idle-active" and data is False:
                GLib.idle_add(lambda: self._stack.set_visible_child_name("overlay"))

    def _update_progress(self):
        pos = self._state["time_pos"] or 0
        dur = self._state["duration"] or 0
        def fmt(s):
            s = int(s)
            return f"{s//60}:{s%60:02d}"
        self._time_label.set_text(f"{fmt(pos)} / {fmt(dur)}")
        return False

    def start(self):
        """Load first channel and begin."""
        ch = self._channels.get(0)
        if ch:
            self._current_idx = 0
            self._player.load(ch.url)
            self._update_now_playing(ch.name)
            self._refresh_channel_strip()
            self._stack.set_visible_child_name("overlay")
```

- [ ] **Step 2: Commit**

```bash
cd ~/streamerbox
git add overlay.py
git commit -m "feat: GTK3 overlay — channel strip, search modal, keyboard dispatch"
```

---

## Task 7: main.py — Wire Everything Together

**Files:**
- Create: `~/streamerbox/main.py`

- [ ] **Step 1: Write main.py**

Write `~/streamerbox/main.py`:
```python
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import os
import time
from channels import ChannelManager
from player import MpvPlayer
from overlay import StreamerOverlay


def main():
    channels = ChannelManager()

    if channels.count() == 0:
        print("ERROR: No channels found in ~/.config/streamerbox/channels.yaml")
        print("Add at least one channel and restart.")
        return

    overlay_ref = [None]

    def on_mpv_event(event):
        if overlay_ref[0]:
            overlay_ref[0].on_mpv_event(event)

    player = MpvPlayer(on_event=on_mpv_event)

    def on_quit():
        player.stop()
        Gtk.main_quit()

    overlay = StreamerOverlay(channels=channels, player=player, on_quit=on_quit)
    overlay_ref[0] = overlay
    overlay.connect("destroy", lambda w: on_quit())

    # Start mpv with first channel URL, then hand control to overlay
    first_ch = channels.get(0)
    player.start(first_ch.url)

    # Watchdog: restart mpv if it crashes
    def watchdog():
        if not player.is_alive():
            ch = channels.get(overlay._current_idx)
            if ch:
                player.restart(ch.url)
        return True  # keep repeating

    GLib.timeout_add(2000, watchdog)

    overlay.start()
    Gtk.main()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
cd ~/streamerbox
git add main.py
git commit -m "feat: main entry point, wires player + overlay + watchdog"
```

---

## Task 8: Manual Integration Test

- [ ] **Step 1: Run all unit tests**

```bash
cd ~/streamerbox && python3 -m pytest tests/ -v
```

Expected: All tests PASSED (channels + player + search)

- [ ] **Step 2: Launch StreamerBox manually**

```bash
cd ~/streamerbox && GDK_BACKEND=x11 python3 main.py
```

Expected: mpv window appears filling screen, no-signal graphic shows briefly, first channel begins playing.

- [ ] **Step 3: Test keyboard controls**

Verify each of the following works:
- Press any key → overlay bar appears at bottom with channel strip
- `↑` / `↓` → channel changes, mpv loads new stream
- `1`-`9` → jumps to channel by number
- `Space` → pauses/resumes
- `←` / `→` → seeks
- `m` → mutes
- `j` → cycles subtitles (try on a Crunchyroll channel)
- `/` → search modal opens
- Type a query + Enter → results appear
- `↑`/`↓` in search → selects result
- `Enter` on result → plays immediately
- `S` on result → saves as new channel, visible in strip
- `Esc` → closes search
- `Q` → quits cleanly

- [ ] **Step 4: Test YouTube Premium**

Load a YouTube channel. Verify no ads appear.

- [ ] **Step 5: Test Crunchyroll**

Load a Crunchyroll series URL. Verify it plays and has no ads.

- [ ] **Step 6: Test crash recovery**

While playing, run `pkill mpv` in another terminal. Within 2 seconds, mpv should restart on the same channel.

- [ ] **Step 7: Commit test results**

```bash
cd ~/streamerbox
git commit --allow-empty -m "test: manual integration verified"
```

---

## Task 9: Autostart + Final Setup

**Files:**
- Create: `~/.config/autostart/streamerbox.desktop`

- [ ] **Step 1: Write the .desktop file**

```bash
cat > ~/.config/autostart/streamerbox.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=StreamerBox
Exec=bash -c 'GDK_BACKEND=x11 exec python3 "$HOME/streamerbox/main.py"'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

- [ ] **Step 2: Verify it's valid**

```bash
cat ~/.config/autostart/streamerbox.desktop
```

- [ ] **Step 3: Test autostart by logging out and back in**

Log out of GNOME and log back in. StreamerBox should start automatically and begin playing the first channel within 30 seconds of desktop load.

- [ ] **Step 4: Final commit**

```bash
cd ~/streamerbox
git add .
git commit -m "chore: autostart .desktop — StreamerBox launch on GNOME login"
```

---

## Done

StreamerBox is running. To re-export cookies when they expire (every few months):

```bash
yt-dlp --cookies-from-browser firefox \
       --cookies ~/.config/streamerbox/cookies.txt \
       --skip-download "https://www.youtube.com"
```
