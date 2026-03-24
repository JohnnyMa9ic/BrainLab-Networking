import os
import time
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import threading
from search import search as do_search, search_playlists as do_search_playlists

THEME_PATH = os.path.join(os.path.dirname(__file__), "themes/cyberpunk.css")
NOSIGNAL_PATH = os.path.join(os.path.dirname(__file__), "assets/nosignal.png")


class StreamerOverlay(Gtk.Window):
    def __init__(self, channels, player, on_quit):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self._channels = channels
        self._player = player
        self._on_quit = on_quit
        self._current_idx = 0
        self._search_mode = "videos"  # "videos" or "playlists"
        self._search_results = []
        self._search_selected = 0
        self._state = {"time_pos": 0, "duration": 0, "title": "", "idle": True}
        self._paused = False
        self._fullscreen = False
        self._playlist_pos_times = []
        self._searching = False
        self._playlist_pos = 0
        self._playlist_count = 0
        self._user_nav_time = 0.0

        self._apply_css()
        self._build_window()
        self._connect_keys()
        self.connect("window-state-event", self._on_window_state)

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
        self.set_default_size(1280, 720)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        # Stack: nosignal / video / search — takes all available space
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(150)
        vbox.pack_start(self._stack, True, True, 0)

        # Page: no signal
        self._stack.add_named(self._build_nosignal(), "nosignal")

        # Page: mpv video area
        self._mpv_area = Gtk.DrawingArea()
        self._mpv_area.set_name("mpv-area")
        self._stack.add_named(self._mpv_area, "video")

        # Page: search
        self._stack.add_named(self._build_search_page(), "search")

        # Control bar — always visible
        vbox.pack_start(self._build_bar(), False, False, 0)

        self.show_all()
        self._stack.set_visible_child_name("nosignal")

    def _build_nosignal(self):
        box = Gtk.Box()
        box.set_name("nosignal-box")
        box.set_hexpand(True)
        box.set_vexpand(True)
        return box

    def _build_bar(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_name("overlay-bar")

        # Row 1: now-playing + time
        info_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._now_playing = Gtk.Label(label="✦ NO SIGNAL")
        self._now_playing.set_name("now-playing")
        self._now_playing.set_halign(Gtk.Align.START)
        self._time_label = Gtk.Label(label="")
        self._time_label.set_name("time-label")
        self._time_label.set_halign(Gtk.Align.END)
        self._time_label.set_hexpand(True)
        info_row.pack_start(self._now_playing, False, False, 0)
        info_row.pack_end(self._time_label, False, False, 0)
        vbox.pack_start(info_row, False, False, 0)

        # Row 2: channel strip (collapsible, left) + playback controls (right)
        mid_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Channel strip wrapped in a Revealer for collapse/expand
        # Toggle button sits on the far left
        self._ch_toggle = Gtk.Button(label="≡")
        self._ch_toggle.set_name("control-btn")
        self._ch_toggle.connect("clicked", lambda _: self._toggle_channel_strip())
        mid_row.pack_start(self._ch_toggle, False, False, 0)

        self._ch_revealer = Gtk.Revealer()
        self._ch_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        self._ch_revealer.set_transition_duration(200)
        self._ch_revealer.set_reveal_child(True)
        self._channel_strip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self._ch_revealer.add(self._channel_strip)
        mid_row.pack_start(self._ch_revealer, False, False, 0)

        # Playback buttons — order: ◀◀ ◀ −10 ▌▌ +10 ▶ ▶▶ M
        btn_defs = [
            ("◀◀",  "prev-ch",      lambda _: self._change_channel(-1)),
            ("◀",   "playlist-prev", lambda _: self._playlist_prev()),
            ("−10", "seek-back",    lambda _: self._player.seek(-10)),
            ("▌▌",  "play-pause",   lambda _: self._toggle_pause()),
            ("+10", "seek-fwd",     lambda _: self._player.seek(10)),
            ("▶",   "playlist-next", lambda _: self._playlist_next()),
            ("▶▶",  "next-ch",      lambda _: self._change_channel(1)),
            ("M",   "mute",         lambda _: self._player.cycle_mute()),
        ]
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._btn_play = None
        for label, name, cb in btn_defs:
            btn = Gtk.Button(label=label)
            btn.set_name("control-btn")
            btn.connect("clicked", cb)
            btn_box.pack_start(btn, False, False, 0)
            if name == "play-pause":
                self._btn_play = btn
        mid_row.pack_end(btn_box, False, False, 0)

        vbox.pack_start(mid_row, False, False, 0)

        # Row 3: action strip (left) + danger zone (right)
        hint_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        action_defs = [
            ("SEARCH",     lambda _: self._open_search()),
            ("PAUSE",      lambda _: self._toggle_pause()),
            ("STOP",       lambda _: self._stop_playback()),
            ("MUTE",       lambda _: self._player.cycle_mute()),
            ("FULLSCREEN", lambda _: self._toggle_fullscreen()),
        ]
        for i, (label, cb) in enumerate(action_defs):
            if i > 0:
                sep = Gtk.Label(label=" · ")
                sep.set_name("hint-sep")
                hint_row.pack_start(sep, False, False, 0)
            btn = Gtk.Button(label=label)
            btn.set_name("hint-btn")
            btn.connect("clicked", cb)
            hint_row.pack_start(btn, False, False, 0)

        # Spacer pushes danger buttons to far right
        hint_row.pack_start(Gtk.Label(label=""), True, True, 0)

        danger_defs = [
            ("REMOVE CH", lambda _: self._delete_current_channel()),
            ("QUIT",      lambda _: self._on_quit()),
        ]
        for i, (label, cb) in enumerate(danger_defs):
            if i > 0:
                sep = Gtk.Label(label=" · ")
                sep.set_name("hint-sep")
                hint_row.pack_start(sep, False, False, 0)
            btn = Gtk.Button(label=label)
            btn.set_name("hint-btn-danger")
            btn.connect("clicked", cb)
            hint_row.pack_start(btn, False, False, 0)

        vbox.pack_start(hint_row, False, False, 0)

        return vbox

    def _build_search_page(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_name("search-page")

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        inner.set_name("search-modal")
        inner.set_halign(Gtk.Align.CENTER)
        inner.set_valign(Gtk.Align.CENTER)
        inner.set_size_request(500, -1)
        outer.pack_start(inner, True, True, 0)

        title = Gtk.Label(label="SEARCH")
        title.set_name("now-playing")
        inner.pack_start(title, False, False, 8)

        # Video / Playlist tabs
        tab_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tab_row.set_halign(Gtk.Align.CENTER)
        self._tab_videos = Gtk.ToggleButton(label="VIDEOS")
        self._tab_playlists = Gtk.ToggleButton(label="PLAYLISTS")
        self._tab_videos.set_name("tab-btn")
        self._tab_playlists.set_name("tab-btn")
        self._tab_videos.set_active(True)
        self._tab_videos.connect("toggled", self._on_tab_toggle)
        self._tab_playlists.connect("toggled", self._on_tab_toggle)
        tab_row.pack_start(self._tab_videos, False, False, 0)
        tab_row.pack_start(self._tab_playlists, False, False, 0)
        inner.pack_start(tab_row, False, False, 0)

        self._search_entry = Gtk.Entry()
        self._search_entry.set_name("search-entry")
        self._search_entry.set_placeholder_text("Search YouTube...")
        self._search_entry.connect("activate", self._on_search_submit)
        inner.pack_start(self._search_entry, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(400)
        scroll.set_max_content_height(600)
        self._results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        scroll.add(self._results_box)
        inner.pack_start(scroll, True, True, 0)

        self._search_status = Gtk.Label(label="")
        self._search_status.set_name("status-label")
        self._search_status.set_halign(Gtk.Align.CENTER)
        inner.pack_start(self._search_status, False, False, 0)

        hint = Gtk.Label(label="ENTER search  ·  ↑↓ select  ·  ENTER play  ·  S save  ·  ESC back")
        hint.set_name("hint-bar")
        inner.pack_start(hint, False, False, 8)

        return outer

    def _on_tab_toggle(self, btn):
        if not btn.get_active():
            return
        if btn is self._tab_videos:
            self._tab_playlists.set_active(False)
            self._search_mode = "videos"
        else:
            self._tab_videos.set_active(False)
            self._search_mode = "playlists"

    def _connect_keys(self):
        self.connect("key-press-event", self._on_key)
        self.set_can_focus(True)
        self.grab_focus()

    def _on_key(self, widget, event):
        key = Gdk.keyval_name(event.keyval)

        if self._stack.get_visible_child_name() == "search":
            return self._handle_search_key(key, event)

        if key == "Up":
            self._change_channel(-1)
            return True
        if key == "Down":
            self._change_channel(1)
            return True
        if key == "slash":
            self._open_search()
            return True
        if key == "q":
            self._on_quit()
            return True
        if key in ("1","2","3","4","5","6","7","8","9"):
            self._jump_to_channel(int(key) - 1)
            return True
        if key == "space":
            self._toggle_pause()
            return True
        if key == "Left":
            self._player.seek(-10)
            return True
        if key == "Right":
            self._player.seek(10)
            return True
        if key == "m":
            self._player.cycle_mute()
            return True
        if key == "j":
            self._player.cycle_sub()
            return True
        if key in ("f", "i"):
            self._player.forward_key(key)
            return True
        if key == "Delete":
            self._delete_current_channel()
            return True
        if key == "F11":
            self._toggle_fullscreen()
            return True
        if key == "x":
            self._stop_playback()
            return True

        return False

    def _handle_search_key(self, key, event):
        entry_focused = self._search_entry.has_focus()

        if key == "Escape":
            self._close_search()
            return True
        # Let the entry handle all typing; only intercept nav/action keys when entry is not focused
        if entry_focused:
            return False
        if key == "Up":
            if not self._search_results:
                return False
            self._search_selected = max(0, self._search_selected - 1)
            self._update_result_selection()
            return True
        if key == "Down":
            if not self._search_results:
                return False
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
            self._update_now_playing(r.name)
            self._close_search()
            return True
        return False

    def _stop_playback(self):
        self._player.stop_playback()
        self._paused = False
        if self._btn_play:
            self._btn_play.set_label("▌▌")

    def _toggle_channel_strip(self):
        visible = self._ch_revealer.get_reveal_child()
        self._ch_revealer.set_reveal_child(not visible)
        self._ch_toggle.set_label("≡" if not visible else "×")

    def _toggle_fullscreen(self):
        if self._fullscreen:
            self.unfullscreen()
        else:
            self.fullscreen()

    def _on_window_state(self, window, event):
        self._fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)

    def _delete_current_channel(self):
        ch = self._channels.get(self._current_idx)
        if not ch:
            return
        removed = self._channels.remove_channel(ch.url)
        if removed:
            self._current_idx = max(0, self._current_idx - 1)
            self._refresh_channel_strip()
            next_ch = self._channels.get(self._current_idx)
            if next_ch:
                self._player.load(next_ch.url)
                self._update_now_playing(next_ch.name)
        else:
            self._now_playing.set_text("✦ BASE CHANNELS CANNOT BE REMOVED")

    def _toggle_pause(self):
        self._player.cycle_pause()
        self._paused = not self._paused
        if self._btn_play:
            self._btn_play.set_label("▶" if self._paused else "▌▌")

    def _playlist_next(self):
        self._user_nav_time = time.time()
        if self._playlist_count > 1:
            self._player.goto_playlist_index((self._playlist_pos + 1) % self._playlist_count)
        else:
            self._player.playlist_next()

    def _playlist_prev(self):
        self._user_nav_time = time.time()
        if self._playlist_count > 1:
            self._player.goto_playlist_index((self._playlist_pos - 1) % self._playlist_count)
        else:
            self._player.playlist_prev()

    def _change_channel(self, delta: int):
        self._playlist_pos = 0
        self._playlist_count = 0
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
        if self._stack.get_visible_child_name() == "search":
            return
        self._search_results = []
        self._search_selected = 0
        self._search_entry.set_text("")
        self._search_status.set_text("")
        self._clear_results()
        self._stack.set_visible_child_name("search")
        self._search_entry.grab_focus()

    def _close_search(self):
        playing = self._stack.get_visible_child_name() == "search"
        if playing:
            name = "video" if not self._state["idle"] else "nosignal"
            self._stack.set_visible_child_name(name)
        self.grab_focus()

    def _on_search_submit(self, entry):
        if self._searching:
            return
        query = entry.get_text().strip()
        if not query:
            return
        self._searching = True
        self._search_status.set_text("SEARCHING...")
        self._clear_results()
        mode = self._search_mode
        def _run():
            if mode == "playlists":
                results, err = do_search_playlists(query)
            else:
                results, err = do_search(query)
            GLib.idle_add(self._on_search_done, results, err)
        threading.Thread(target=_run, daemon=True).start()

    def _on_search_done(self, results, error):
        self._searching = False
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
        return False

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
                btn = Gtk.Button(label=f"{ch.id:02d} {ch.name[:10]}")
                btn.set_name("channel-btn")
                if i == self._current_idx:
                    btn.get_style_context().add_class("active")
                idx = i
                btn.connect("clicked", lambda _, n=idx: self._jump_to_channel(n))
                self._channel_strip.pack_start(btn, False, False, 0)
        self._channel_strip.show_all()

    def _update_now_playing(self, title: str):
        ch = self._channels.get(self._current_idx)
        ch_num = ch.id if ch else 0
        self._now_playing.set_text(f"✦ CH {ch_num:02d} — {title.upper()[:40]}")

    def on_mpv_event(self, event: dict):
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
            elif name == "playlist-pos" and data is not None:
                if data >= 0:
                    self._playlist_pos = int(data)
                now = time.time()
                if now - self._user_nav_time >= 3:
                    self._playlist_pos_times.append(now)
                    self._playlist_pos_times = [t for t in self._playlist_pos_times if now - t < 5]
                    if len(self._playlist_pos_times) >= 5:
                        self._playlist_pos_times = []
                        GLib.idle_add(self._on_playlist_stall)
            elif name == "playlist-count" and data is not None:
                self._playlist_count = int(data)
            elif name == "idle-active":
                self._state["idle"] = bool(data)
                if data:
                    GLib.idle_add(self._on_idle)
                else:
                    GLib.idle_add(self._on_playing)

    def _on_playlist_stall(self):
        self._player.stop_playback()
        self._stack.set_visible_child_name("nosignal")
        self._now_playing.set_text("✦ UPDATING yt-dlp…")
        threading.Thread(target=self._auto_update_ytdlp, daemon=True).start()
        return False

    def _auto_update_ytdlp(self):
        import subprocess
        try:
            result = subprocess.run(
                ["/usr/local/bin/yt-dlp", "-U"],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0
        except subprocess.TimeoutExpired:
            success = False
        if success:
            GLib.idle_add(self._after_ytdlp_update)
        else:
            GLib.idle_add(
                self._now_playing.set_text,
                "✦ UPDATE FAILED — check connection and retry manually"
            )

    def _after_ytdlp_update(self):
        self._now_playing.set_text("✦ yt-dlp updated — restarting stream…")
        ch = self._channels.get(self._current_idx)
        if not ch:
            return False
        self._player.restart(ch.url)
        return False

    def _on_idle(self):
        if self._stack.get_visible_child_name() != "search":
            self._stack.set_visible_child_name("nosignal")
        self._paused = False
        if self._btn_play:
            self._btn_play.set_label("▌▌")
        return False

    def _on_playing(self):
        if self._stack.get_visible_child_name() != "search":
            self._stack.set_visible_child_name("video")
        return False

    def _update_progress(self):
        pos = self._state["time_pos"] or 0
        dur = self._state["duration"] or 0
        def fmt(s):
            s = int(s)
            return f"{s//60}:{s%60:02d}"
        if dur:
            self._time_label.set_text(f"{fmt(pos)} / {fmt(dur)}")
        return False

    def get_mpv_wid(self) -> int:
        return self._mpv_area.get_window().get_xid()

    def start_ui(self):
        ch = self._channels.get(0)
        if ch:
            self._current_idx = 0
            self._update_now_playing(ch.name)
            self._refresh_channel_strip()

    def start_load(self):
        ch = self._channels.get(0)
        if ch:
            self._player.load(ch.url)
