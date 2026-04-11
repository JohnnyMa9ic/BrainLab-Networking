import os
import json
import pytest
from unittest.mock import patch, MagicMock
from player import MpvPlayer, build_mpv_args, build_ipc_command


def test_build_mpv_args_no_fullscreen():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert "--fullscreen" not in args
    assert "--geometry=1920x1080+0+0" not in args
    assert "--no-border" not in args

def test_build_mpv_args_wid_embedded():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt", wid=12345)
    assert "--wid=12345" in args

def test_build_mpv_args_no_wid_by_default():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert not any(a.startswith("--wid=") for a in args)


def test_build_mpv_args_ipc_socket():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert "--input-ipc-server=/tmp/test.sock" in args


def test_build_mpv_args_cookies_expanded():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/home/user/cookies.txt")
    cookie_arg = next(a for a in args if "cookies" in a and "ytdl-raw" in a)
    assert "/home/user/cookies.txt" in cookie_arg


def test_build_mpv_args_ytdlp_path():
    args = build_mpv_args(ipc_sock="/tmp/test.sock", cookies="/tmp/cookies.txt")
    assert any("/usr/local/bin/yt-dlp" in a for a in args)


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


@patch("player.threading.Thread")
@patch("player.subprocess.Popen")
@patch("player.os.path.exists", return_value=False)
def test_player_start_spawns_process_and_ipc_thread(mock_exists, mock_popen, mock_thread_cls):
    proc = MagicMock()
    proc.pid = 4321
    mock_popen.return_value = proc
    thread = MagicMock()
    mock_thread_cls.return_value = thread
    player = MpvPlayer()

    player.start(url="https://example.com/live", wid=12345)

    mock_popen.assert_called_once()
    args = mock_popen.call_args.args[0]
    assert "--wid=12345" in args
    assert args[-1] == "https://example.com/live"
    thread.start.assert_called_once()
    assert player._proc is proc
    assert player._thread is thread
    assert player._running is True


def test_player_stop_terminates_process_and_joins_thread():
    player = MpvPlayer()
    player._running = True
    sock = MagicMock()
    player._sock = sock
    player._proc = MagicMock()
    thread = MagicMock()
    thread.is_alive.return_value = True
    player._thread = thread

    player.stop()

    assert player._running is False
    sock.close.assert_called_once()
    player._proc.terminate.assert_called_once()
    player._proc.wait.assert_called_once_with(timeout=3)
    thread.join.assert_called_once_with(timeout=3)


def test_player_restart_calls_stop_then_start():
    player = MpvPlayer()
    player._wid = 2468
    player._window_id = 999

    with patch.object(player, "stop") as mock_stop, \
         patch.object(player, "start") as mock_start, \
         patch("player.os.path.exists", return_value=False):
        player.restart("https://example.com/restart")

    mock_stop.assert_called_once_with()
    mock_start.assert_called_once_with("https://example.com/restart", wid=2468)
    assert player._window_id is None


def test_player_is_alive_reflects_process_state():
    player = MpvPlayer()
    assert player.is_alive() is False

    player._proc = MagicMock()
    player._proc.poll.return_value = None
    assert player.is_alive() is True

    player._proc.poll.return_value = 0
    assert player.is_alive() is False


def test_player_can_have_live_process_with_dead_ipc():
    player = MpvPlayer()
    player._proc = MagicMock()
    player._proc.poll.return_value = None
    player._ipc_alive = False
    player._ipc_failed = True

    assert player.is_alive() is True
    assert player.is_ipc_alive() is False
    assert player.has_ipc_failed() is True
