import os
import json
import shutil
import socket
import subprocess
import threading
import queue
import time
from typing import Optional, Callable

YTDLP = shutil.which("yt-dlp") or "/usr/local/bin/yt-dlp"


def build_mpv_args(ipc_sock: str, cookies: str, wid: Optional[int] = None) -> list[str]:
    args = [
        "mpv",
        "--really-quiet",
        "--no-terminal",
        "--sub-auto=fuzzy",
        f"--input-ipc-server={ipc_sock}",
        f"--script-opts=ytdl_hook-ytdl_path={YTDLP}",
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
    OBSERVED = ["time-pos", "duration", "media-title", "playlist-pos", "playlist-count", "idle-active"]

    def __init__(self, on_event: Optional[Callable] = None):
        home = os.path.expanduser("~")
        self._sock_path = os.path.join(home, ".config/streamerbox/mpv.sock")
        self._cookies = os.path.join(home, ".config/streamerbox/cookies.txt")
        self._proc: Optional[subprocess.Popen] = None
        self._sock: Optional[socket.socket] = None
        self._on_event = on_event or (lambda e: None)
        self._event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._ipc_alive = False
        self._ipc_failed = False
        self._thread: Optional[threading.Thread] = None
        self._window_id: Optional[int] = None
        self._wid: Optional[int] = None
        self._response_lock = threading.Lock()
        self._response_queues: dict[int, queue.Queue] = {}
        self._next_request_id = 1000

    def start(self, url: Optional[str] = None, wid: Optional[int] = None):
        self._wid = wid
        args = build_mpv_args(self._sock_path, self._cookies, wid)
        if url:
            args.append(url)
        if os.path.exists(self._sock_path):
            os.unlink(self._sock_path)
        self._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._running = True
        self._ipc_alive = False
        self._ipc_failed = False
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
            self._ipc_alive = False
            self._ipc_failed = True
            return
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.connect(self._sock_path)
            self._sock.settimeout(2.0)
            self._ipc_alive = True
            self._ipc_failed = False
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
                                if "request_id" in event:
                                    with self._response_lock:
                                        response_queue = self._response_queues.get(event["request_id"])
                                    if response_queue:
                                        response_queue.put(event)
                                        continue
                                self._on_event(event)
                            except json.JSONDecodeError:
                                pass
                except socket.timeout:
                    continue
                except OSError:
                    break
        except OSError:
            self._ipc_alive = False
            self._ipc_failed = True
        finally:
            self._ipc_alive = False
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None

    def _send(self, cmd: str):
        if self._sock:
            try:
                self._sock.sendall(cmd.encode())
            except OSError:
                self._ipc_alive = False
                pass

    def _request(self, *args, timeout: float = 1.0) -> Optional[dict]:
        if not self._ipc_alive or not self._sock:
            return None
        request_id = self._next_request_id
        self._next_request_id += 1
        response_queue: queue.Queue = queue.Queue(maxsize=1)
        with self._response_lock:
            self._response_queues[request_id] = response_queue
        try:
            payload = json.dumps({"command": list(args), "request_id": request_id}) + "\n"
            self._send(payload)
            try:
                return response_queue.get(timeout=timeout)
            except queue.Empty:
                self._ipc_alive = False
                self._ipc_failed = True
                return None
        finally:
            with self._response_lock:
                self._response_queues.pop(request_id, None)

    def load(self, url: str):
        self._send(build_ipc_command("loadfile", url, "replace"))

    def cycle_pause(self):
        self._send(build_ipc_command("cycle", "pause"))

    def get_pause_state(self, retries: int = 5, delay: float = 0.05) -> Optional[bool]:
        for _ in range(retries):
            response = self._request("get_property", "pause")
            if response and response.get("error") == "success":
                data = response.get("data")
                if isinstance(data, bool):
                    return data
            time.sleep(delay)
        return None

    def playlist_next(self):
        self._send(build_ipc_command("playlist-next"))

    def playlist_prev(self):
        self._send(build_ipc_command("playlist-prev"))

    def goto_playlist_index(self, idx: int):
        self._send(build_ipc_command("set_property", "playlist-pos", idx))

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
        """Handle legacy direct-player keybindings that don't map cleanly in embedded mode."""
        if key == "i":
            # Embedded mpv has no discoverable top-level X11 window, so show a small
            # OSD overlay through IPC instead of trying to synthesize the keypress.
            self._send(build_ipc_command("show-text", "${media-title}", 3000))
            return
        if key == "f":
            # mpv fullscreen targets the embedded child surface and conflicts with the
            # GTK window fullscreen toggle, so this key is intentionally ignored here.
            return
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

    def is_ipc_alive(self) -> bool:
        return self._ipc_alive

    def has_ipc_failed(self) -> bool:
        return self._ipc_failed

    def ipc_socket_ready(self) -> bool:
        if not os.path.exists(self._sock_path):
            return False
        try:
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            probe.settimeout(0.2)
            probe.connect(self._sock_path)
            probe.close()
            return True
        except OSError:
            return False

    def restart(self, url: str):
        self.stop()
        self._window_id = None
        deadline = time.time() + 3.0
        while os.path.exists(self._sock_path) and time.time() < deadline:
            time.sleep(0.1)
        self.start(url, wid=self._wid)

    def stop(self):
        self._running = False
        self._ipc_alive = False
        self._ipc_failed = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
