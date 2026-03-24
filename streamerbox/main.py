import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
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

    # Briefly show the video page so the DrawingArea is realized and has an XID,
    # then switch back to nosignal while mpv buffers.
    overlay._stack.set_visible_child_name("video")
    while Gtk.events_pending():
        Gtk.main_iteration()
    wid = overlay.get_mpv_wid()
    overlay._stack.set_visible_child_name("nosignal")

    # Start mpv embedded inside the GTK DrawingArea
    first_ch = channels.get(0)
    player.start(first_ch.url, wid=wid)

    # Watchdog: restart mpv if it crashes
    def watchdog():
        if not player.is_alive():
            ch = channels.get(overlay._current_idx)
            if ch:
                player.restart(ch.url)
        return True  # keep repeating

    GLib.timeout_add(2000, watchdog)

    # Update UI immediately; mpv already has the URL from argv.
    # Defer the IPC load until the socket is ready (avoids race on startup).
    overlay.start_ui()
    GLib.timeout_add(2000, lambda: [overlay.start_load(), False][1])
    Gtk.main()


if __name__ == "__main__":
    main()
