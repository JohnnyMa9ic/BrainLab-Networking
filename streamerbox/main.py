import os
import time
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from channels import ChannelManager
from player import MpvPlayer
from overlay import StreamerOverlay


def is_wayland_session() -> bool:
    return bool(
        os.environ.get("WAYLAND_DISPLAY") or
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    )


def show_startup_error(message: str):
    dialog = Gtk.MessageDialog(
        parent=None,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.CLOSE,
        text="StreamerBox startup error",
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def main():
    if is_wayland_session():
        message = (
            "StreamerBox currently supports embedded mpv only on X11/XWayland sessions.\n"
            "This session appears to be native Wayland, so startup was stopped before the app crashed.\n"
            "Please launch StreamerBox from an X11 session instead."
        )
        print(message)
        show_startup_error(message)
        return

    channels = ChannelManager()

    if channels.count() == 0:
        print("ERROR: No channels found in ~/.config/streamerbox/channels.yaml")
        print("Add at least one channel and restart.")
        return

    overlay_ref = [None]
    _quitting = [False]

    def on_mpv_event(event):
        if overlay_ref[0]:
            overlay_ref[0].on_mpv_event(event)

    player = MpvPlayer(on_event=on_mpv_event)

    def on_quit():
        if _quitting[0]:
            return
        _quitting[0] = True
        player.stop()
        Gtk.main_quit()

    overlay = StreamerOverlay(channels=channels, player=player, on_quit=on_quit)
    overlay_ref[0] = overlay
    overlay.connect("destroy", lambda w: on_quit())

    # Briefly show the video page so the DrawingArea is realized and has an XID,
    # then switch back to nosignal while mpv buffers.
    overlay._stack.set_visible_child_name("video")
    while Gtk.events_pending():
        Gtk.main_iteration()
    try:
        wid = overlay.get_mpv_wid()
    except RuntimeError as e:
        print(str(e))
        show_startup_error(str(e))
        return
    overlay._stack.set_visible_child_name("nosignal")

    # Start mpv embedded inside the GTK DrawingArea (idle; first URL loaded via IPC below)
    player.start(wid=wid)

    # Watchdog: restart mpv if it crashes
    def watchdog():
        if _quitting[0]:
            return False  # deregister callback
        if not player.is_alive() or player.has_ipc_failed():
            ch = channels.get(overlay._current_idx)
            if ch:
                player.restart(ch.url)
        return True  # keep repeating

    GLib.timeout_add(2000, watchdog)

    # Update UI immediately; defer the first IPC load until the socket is accepting connections.
    overlay.start_ui()
    load_deadline = [time.time() + 10.0]

    def load_initial_channel():
        if _quitting[0]:
            return False
        if player.ipc_socket_ready():
            overlay.start_load()
            return False
        if time.time() >= load_deadline[0]:
            message = "StreamerBox could not connect to mpv IPC within 10 seconds. Startup was aborted."
            print(message)
            show_startup_error(message)
            on_quit()
            return False
        return True

    GLib.timeout_add(100, load_initial_channel)
    Gtk.main()


if __name__ == "__main__":
    main()
