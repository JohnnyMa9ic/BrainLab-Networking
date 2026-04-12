# streamerbox/dossier.py
"""
WY Dossier startup window — amber phosphor terminal sequence.
Runs before the main StreamerOverlay becomes visible.
Calls on_complete() when the sequence finishes.
"""
import shutil
import time
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import theme


class DossierWindow(Gtk.Window):
    CHAR_DELAY_MS = 18
    LINE_DELAY_MS = 120
    FINAL_HOLD_MS = 900
    IPC_POLL_MS   = 100

    def __init__(self, channels, player, on_complete):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self._channels   = channels
        self._player     = player
        self._on_complete = on_complete

        self._lines = list(theme.DOSSIER_LINES)
        self._line_idx = 0
        self._char_idx = 0
        self._waiting_for_ipc = False
        self._ipc_start = None

        self._apply_style()
        self._build_ui()
        self.show_all()
        self.fullscreen()

        GLib.timeout_add(400, self._start_tick)

    def _apply_style(self):
        css = (
            f"window {{ background-color: {theme.COLORS['amber_void']}; }}\n"
            f"#dossier-text {{\n"
            f"    color: {theme.COLORS['amber']};\n"
            f"    font-family: \"JetBrains Mono\", \"Monospace\", monospace;\n"
            f"    font-size: 13px;\n"
            f"}}\n"
            f"#dossier-fault {{\n"
            f"    color: {theme.COLORS['crimson']};\n"
            f"    font-family: \"JetBrains Mono\", \"Monospace\", monospace;\n"
            f"    font-size: 13px;\n"
            f"}}\n"
        ).encode()
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_valign(Gtk.Align.CENTER)
        outer.set_halign(Gtk.Align.CENTER)
        self.add(outer)

        self._label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._label_box.set_halign(Gtk.Align.START)
        outer.pack_start(self._label_box, False, False, 0)

        self._line_labels = []
        self._current_label = self._new_label()

    def _new_label(self, fault=False):
        lbl = Gtk.Label(label="")
        lbl.set_name("dossier-fault" if fault else "dossier-text")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_selectable(False)
        self._label_box.pack_start(lbl, False, False, 0)
        lbl.show()
        self._line_labels.append(lbl)
        return lbl

    def _check_channels(self) -> bool:
        return self._channels.count() > 0

    def _check_yt_dlp(self) -> bool:
        return shutil.which("yt-dlp") is not None

    def _check_ipc(self) -> bool:
        return self._player.ipc_socket_ready()

    def _resolve_check(self, check: str):
        """Returns suffix string for synchronous checks; None for 'ipc' (async)."""
        if check == "channels":
            return "  OK" if self._check_channels() else "  FAULT"
        if check == "yt_dlp":
            return "  OK" if self._check_yt_dlp() else "  FAULT"
        if check == "ipc":
            return None  # handled async in _poll_ipc
        return ""

    def _start_tick(self) -> bool:
        GLib.timeout_add(self.CHAR_DELAY_MS, self._tick)
        return False

    def _tick(self) -> bool:
        if self._line_idx >= len(self._lines):
            GLib.timeout_add(self.FINAL_HOLD_MS, self._finish)
            return False

        line   = self._lines[self._line_idx]
        text   = line["text"]
        check  = line.get("check")
        suffix = line.get("_resolved_suffix", "")

        # Async IPC path
        if check == "ipc" and not self._waiting_for_ipc:
            if self._char_idx < len(text):
                self._char_idx += 1
                self._current_label.set_text(text[:self._char_idx])
                return True
            # Full text typed — now poll for IPC readiness
            self._waiting_for_ipc = True
            self._ipc_start = time.time()
            GLib.timeout_add(self.IPC_POLL_MS, self._poll_ipc)
            return False

        if self._waiting_for_ipc:
            return False

        # Synchronous line — resolve suffix once
        if self._char_idx == 0 and check and check != "ipc":
            resolved = self._resolve_check(check)
            line["_resolved_suffix"] = resolved
            suffix = resolved

        display = text + (suffix or "")
        if self._char_idx < len(display):
            self._char_idx += 1
            self._current_label.set_text(display[:self._char_idx])
            return True

        self._advance_line()
        return True

    def _poll_ipc(self) -> bool:
        if self._player.ipc_socket_ready():
            full = self._lines[self._line_idx]["text"] + "  OK"
            self._current_label.set_text(full)
            self._waiting_for_ipc = False
            self._advance_line()
            GLib.timeout_add(self.LINE_DELAY_MS, self._resume_tick)
            return False

        if time.time() - self._ipc_start > 10.0:
            full = self._lines[self._line_idx]["text"] + "  FAULT"
            self._current_label.set_name("dossier-fault")
            self._current_label.set_text(full)
            self._waiting_for_ipc = False
            self._advance_line()
            GLib.timeout_add(self.LINE_DELAY_MS, self._resume_tick)
            return False

        return True

    def _resume_tick(self) -> bool:
        GLib.timeout_add(self.CHAR_DELAY_MS, self._tick)
        return False

    def _advance_line(self):
        self._line_idx += 1
        self._char_idx = 0
        if self._line_idx < len(self._lines):
            self._current_label = self._new_label()

    def _finish(self) -> bool:
        self.destroy()
        self._on_complete()
        return False
