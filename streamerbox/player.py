import os
import json
import socket
import subprocess
import threading
import queue
import time
from typing import Optional, Callable


def build_mpv_args(ipc_sock: str, cookies: str, wid: Optional[int] = None) -> list[str]:
    args = [
        "mpv",
        "--really-quiet",
        "--no-terminal",
        "--sub-auto=fuzzy",
        f"--input-ipc-server={ipc_sock}",
        "--script-opts=ytdl_hook-ytdl_path=/usr/local/bin/yt-dlp",
        "--ytdl-format=bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        f"--ytdl-raw-options=cookies={cookies},retries=3",
        "--cache=yes",
        "--demuxer-max-bytes=150MiB",
        "--loop-playlist=inf",
        "--idle=yes",
    ]
    if wid is not None:
        args.append(f"--wid={wid}")
    return args


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
        self._wid: Optional[int] = None

    def start(self, url: str, wid: Optional[int] = None):
        self._wid = wid
        args = build_mpv_args(self._sock_path, self._cookies, wid)
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

    def stop_playback(self):
        """Stop current stream and return mpv to idle (shows nosignal)."""
        self._send(build_ipc_command("stop"))

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
        self._window_id = None
        time.sleep(0.5)
        self.start(url, wid=self._wid)

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
