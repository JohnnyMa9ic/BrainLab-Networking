import threading
from unittest.mock import MagicMock, patch

from overlay import StreamerOverlay


@patch("overlay.threading.Thread")
def test_stall_recovery_reentrancy_guard_prevents_second_thread(mock_thread_cls):
    thread = MagicMock()
    mock_thread_cls.return_value = thread

    overlay = StreamerOverlay.__new__(StreamerOverlay)
    overlay._stall_recovery_lock = threading.Lock()
    overlay._stall_recovery_active = False
    overlay._player = MagicMock()
    overlay._stack = MagicMock()
    overlay._now_playing = MagicMock()

    overlay._on_playlist_stall()
    overlay._on_playlist_stall()

    overlay._player.stop_playback.assert_called_once()
    overlay._stack.set_visible_child_name.assert_called_once_with("nosignal")
    overlay._now_playing.set_text.assert_called_once_with("✦ UPDATING yt-dlp…")
    mock_thread_cls.assert_called_once()
    thread.start.assert_called_once()
