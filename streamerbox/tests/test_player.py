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
