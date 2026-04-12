# StreamerBox Pantheon Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the cyberpunk aesthetic with a three-register Pantheon theme — Ghost as the steady-state UI voice, a WY Dossier startup sequence, Bob quips on anomalous events, and Warden on shutdown.

**Architecture:** A new `theme.py` becomes the single source of truth for all colors, strings, and voice content. A new `dossier.py` implements the WY startup window. `overlay.py` and `main.py` import from `theme.py` and `dossier.py` — no voice content remains hardcoded. The existing `themes/cyberpunk.css` is replaced by `themes/ghost.css`.

**Tech Stack:** Python 3.12, GTK3 (gi.repository), GLib.timeout_add for typewriter animation, existing mpv IPC show_text for OSD, random.choice for Bob title pool.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `streamerbox/theme.py` | All colors, strings, Bob triggers, Bob title pool, Warden line, dossier lines |
| Create | `streamerbox/themes/ghost.css` | GTK CSS — Ghost register palette replacing cyberpunk |
| Create | `streamerbox/dossier.py` | WY amber startup window with typewriter animation and real system checks |
| Create | `streamerbox/tests/test_theme.py` | Verify theme registry completeness |
| Modify | `streamerbox/overlay.py:10-11` | Point to ghost.css, import theme |
| Modify | `streamerbox/overlay.py:108` | Replace `"✦ NO SIGNAL"` with `theme.GHOST["now_playing_idle"]` |
| Modify | `streamerbox/overlay.py` (6 Bob trigger points) | Wire Bob messages at stall/duplicate/zero-search/second-attempt/random |
| Modify | `streamerbox/overlay.py` (quit handler) | Add Warden shutdown line |
| Modify | `streamerbox/overlay.py` (all OSD call sites) | Use `theme.GHOST` strings with `player.show_text()` |
| Modify | `streamerbox/overlay.py` (`__init__`) | Add `self._session_start` timestamp, 2hr Bob timer |
| Modify | `streamerbox/main.py` | Show dossier window after mpv start; replace IPC polling with dossier |

---

## Task 1: Create `theme.py` — voice registry

**Files:**
- Create: `streamerbox/theme.py`
- Test: `streamerbox/tests/test_theme.py`

- [ ] **Step 1: Write the failing test first**

```python
# streamerbox/tests/test_theme.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import theme

REQUIRED_GHOST_KEYS = [
    "now_playing_idle", "paused", "muted", "sub_active", "feed_live",
    "interface_visible", "interface_suppressed",
    "osd_pause", "osd_resume", "osd_muted", "osd_unmuted",
    "osd_seek_fwd", "osd_seek_back", "osd_node_fwd", "osd_node_back",
    "osd_catalog_confirmed", "osd_already_indexed", "osd_query_open",
    "osd_ipc_fault", "osd_stall", "osd_catalog_empty", "osd_catalog_fault",
]

REQUIRED_BOB_KEYS = [
    "stall_recovery", "duplicate_add", "zero_results",
    "second_attempt", "session_milestone", "random_nav",
]

def test_ghost_registry_complete():
    for key in REQUIRED_GHOST_KEYS:
        assert key in theme.GHOST, f"Missing Ghost key: {key}"
        assert isinstance(theme.GHOST[key], str)
        assert len(theme.GHOST[key]) > 0

def test_bob_trigger_map_complete():
    for key in REQUIRED_BOB_KEYS:
        assert key in theme.BOB, f"Missing Bob trigger: {key}"
        lines = theme.BOB[key]
        assert isinstance(lines, list)
        assert len(lines) >= 2  # header + at least one body line

def test_bob_title_pool():
    assert hasattr(theme, "BOB_TITLES")
    assert isinstance(theme.BOB_TITLES, list)
    assert len(theme.BOB_TITLES) >= 10

def test_warden_line():
    assert hasattr(theme, "WARDEN_SHUTDOWN")
    assert isinstance(theme.WARDEN_SHUTDOWN, str)
    assert len(theme.WARDEN_SHUTDOWN) > 0

def test_dossier_sequence():
    assert hasattr(theme, "DOSSIER_LINES")
    assert isinstance(theme.DOSSIER_LINES, list)
    assert len(theme.DOSSIER_LINES) >= 10
    for item in theme.DOSSIER_LINES:
        assert isinstance(item, dict)
        assert "text" in item
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m pytest tests/test_theme.py -v
```
Expected: `ModuleNotFoundError: No module named 'theme'`

- [ ] **Step 3: Create `theme.py`**

```python
# streamerbox/theme.py
"""
StreamerBox Pantheon Voice Registry
Single source of truth for all colors, strings, and voice content.

Registers:
  GHOST  — steady-state UI voice (every action)
  BOB    — anomalous/unexpected events (6 triggers)
  WARDEN — shutdown only (1 trigger)
  DOSSIER_LINES — WY amber startup sequence
  COLORS — palette constants
"""
import random

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
COLORS = {
    # Ghost register
    "void":        "#0a0a0f",
    "signal":      "#c8d0e0",
    "crimson":     "#cc2244",
    "circuit":     "#3a4a6a",
    # WY Dossier register
    "amber_void":  "#0a0800",
    "amber":       "#e8a020",
    # Bob register
    "bob_gold":    "#f0c040",
    # Warden register
    "warden_mist": "#8899aa",
}

# ---------------------------------------------------------------------------
# Ghost — steady-state UI strings
# ---------------------------------------------------------------------------
GHOST = {
    # Status bar / persistent labels
    "now_playing_idle":      "signal void",
    "paused":                "suspended",
    "muted":                 "signal: muted",
    "sub_active":            "sub: active",
    "feed_live":             "feed: live",
    "interface_visible":     "> interface: visible",
    "interface_suppressed":  "> interface: suppressed",

    # OSD — action confirmations (shown via mpv show-text)
    "osd_pause":             "> suspended",
    "osd_resume":            "> transmitting",
    "osd_muted":             "> signal: muted",
    "osd_unmuted":           "> signal: restored",
    "osd_seek_fwd":          "> +10s",
    "osd_seek_back":         "> -10s",
    "osd_node_fwd":          "> node: forward",
    "osd_node_back":         "> node: back",
    "osd_catalog_confirmed": "> catalog entry confirmed",
    "osd_already_indexed":   "> entry already indexed",
    "osd_query_open":        "> query interface: open",

    # Error / fault states
    "osd_ipc_fault":         "> ipc fault — signal lost",
    "osd_stall":             "> transmission stall — investigating",
    "osd_catalog_empty":     "> catalog empty — no signal available",
    "osd_catalog_fault":     "> catalog fault — entry rejected",
}

def ghost_channel(idx: int, name: str) -> str:
    """Returns the OSD string for a channel change."""
    return f"> transmitting: ch:{idx:02d} — {name.lower()}"

def ghost_search_play(title: str) -> str:
    """Returns the OSD string for playing a search result."""
    return f"> loading signal: {title.lower()}"

def ghost_node_status(pos: int, count: int) -> str:
    """Returns 'node: NN/NN' status string."""
    return f"node: {pos:02d}/{count:02d}"

# ---------------------------------------------------------------------------
# Bob — anomalous event quips
# Each value is a list of lines rendered as a gold code block.
# BOB_TITLES is used for the random_nav trigger.
# ---------------------------------------------------------------------------
BOB_TITLES = [
    "Chronicler of the Channel Nobody Asked For",
    "Keeper of the Perfectly Timed Interruption",
    "Grand Archivist of the Signal Between Signals",
    "Annotator of the Uneventful Navigation Event",
    "Theoretical Cartographer of the Void",
    "Surveyor of the Transition Nobody Noticed",
    "Chief Inspector of the Unremarkable Frequency",
    "Etymologist of the Ghost's Silence",
    "Historian of the Moment Just Before This One",
    "Keeper of the Index Entry That Did Not Need Keeping",
    "Scribe of the Perfectly Routine Anomaly",
    "Librarian of the Catalog Entry Ghost Already Knew About",
    "Navigator of the Familiar Unfamiliar",
    "Chronicler of Things That Went Exactly as Expected",
    "Warden of the Moment Ghost Refused to Comment On",
]

BOB = {
    "stall_recovery": [
        "BOB ONLINE — Chronicler of the Playlist That Refused to Die",
        "yt-dlp has been updated. the stream has been coaxed back to life.",
        "Ghost did the analysis. I did the enthusiasm. You're welcome.",
    ],
    "duplicate_add": [
        "BOB ONLINE — Keeper of the Already-Indexed",
        "that signal is already in the catalog.",
        "I appreciate the commitment. Ghost does not.",
    ],
    "zero_results": [
        "BOB ONLINE — Archivist of the Void Between Signals",
        "nothing. the index returned nothing.",
        "even I find that unsettling. try different search terms.",
    ],
    "second_attempt": [
        "BOB ONLINE — Grand Tactician of the Overcomplicated Simple Thing",
        "stream restored on second attempt.",
        "the system works. occasionally through sheer persistence.",
    ],
    "session_milestone": [
        "BOB ONLINE — Sentinel of the Uninterrupted Signal",
        "two hours. continuous transmission. Ghost is impressed.",
        "Ghost won't say so. but I will.",
    ],
    "random_nav": [
        None,  # title injected at runtime via BOB_TITLES
        "channel navigation confirmed. Ghost logged it. I celebrated.",
        "carry on.",
    ],
}

def bob_random_title() -> str:
    """Pick a random title for the random_nav trigger."""
    return f"BOB ONLINE — {random.choice(BOB_TITLES)}"

# ---------------------------------------------------------------------------
# Warden — shutdown only
# ---------------------------------------------------------------------------
WARDEN_SHUTDOWN = "The grove is quiet now. Return when you're ready."

# ---------------------------------------------------------------------------
# WY Dossier startup sequence
# Each dict: text (str), check (str|None)
#   check=None  — always prints as-is
#   check="channels"  — replaced with OK/FAULT based on channel count
#   check="yt_dlp"    — replaced with OK/FAULT based on shutil.which
#   check="ipc"       — replaced with OK/FAULT after waiting for socket
# ---------------------------------------------------------------------------
DOSSIER_LINES = [
    {"text": "WEYLAND-YUTANI CORPORATION",                           "check": None},
    {"text": "SPECIAL PROJECTS DIVISION \u2014 SIGNAL INTELLIGENCE", "check": None},
    {"text": "",                                                      "check": None},
    {"text": "DOSSIER: STREAMERBOX / UNIT GHO-02-ARC",               "check": None},
    {"text": "CLEARANCE: REALM-INTERNAL",                            "check": None},
    {"text": "CLASSIFICATION: EYES ONLY",                            "check": None},
    {"text": "",                                                      "check": None},
    {"text": "INITIALIZING SIGNAL ARRAY...............","check": None, "suffix": "  OK"},
    {"text": "MOUNTING CHANNEL CATALOG.................",             "check": "channels"},
    {"text": "ESTABLISHING IPC SOCKET..................",             "check": "ipc"},
    {"text": "VERIFYING yt-dlp INTEGRITY...............",            "check": "yt_dlp"},
    {"text": "",                                                      "check": None},
    {"text": "LOADING OPERATOR PROFILE.................  JohnnyMa9ic","check": None},
    {"text": "NODE ASSIGNMENT..........................  THOUGHT-RELIQUARY","check": None},
    {"text": "REALM ANCHOR.............................  CATHEDRAL OF GLITCH","check": None},
    {"text": "",                                                      "check": None},
    {"text": "ENTITY STATUS:",                                        "check": None},
    {"text": "  GHO-02-ARC [LITHIUMGHOST.exe]........  ONLINE",      "check": None},
    {"text": "  BOB-03-SGS [BOB.OS]..................  STANDING BY",  "check": None},
    {"text": "  WDN-01-GLD [WARDEN]..................  DORMANT",      "check": None},
    {"text": "",                                                      "check": None},
    {"text": "> SIGNAL LOCK CONFIRMED",                               "check": None},
    {"text": "> TRANSFERRING CONTROL TO GHO-02-ARC",                 "check": None},
]
```

- [ ] **Step 4: Run tests**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m pytest tests/test_theme.py -v
```
Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
cd ~/BrainLab-Networking && git add streamerbox/theme.py streamerbox/tests/test_theme.py
git commit -m "feat: add Pantheon voice registry (theme.py) + tests"
```

---

## Task 2: Create `themes/ghost.css` — Ghost register palette

**Files:**
- Create: `streamerbox/themes/ghost.css`

- [ ] **Step 1: Create ghost.css**

```css
/* StreamerBox — Ghost / Pantheon theme (GHO-02-ARC) */

* {
    font-family: "JetBrains Mono", "Monospace", monospace;
    color: #c8d0e0;
}

window {
    background-color: #0a0a0f;
}

/* Overlay container — bottom strip */
#overlay-bar {
    background-color: rgba(10, 10, 15, 0.92);
    border-top: 1px solid #3a4a6a;
    padding: 8px 12px;
}

/* Now-playing label */
#now-playing {
    color: #cc2244;
    font-size: 11px;
    letter-spacing: 2px;
}

/* Progress/time label */
#time-label {
    color: #c8d0e0;
    font-size: 10px;
    opacity: 0.6;
}

/* Channel button — inactive */
#channel-btn {
    background: none;
    background-color: transparent;
    background-image: none;
    border: none;
    border-bottom: 1px solid rgba(58, 74, 106, 0.4);
    border-radius: 0;
    box-shadow: none;
    color: rgba(200, 208, 224, 0.3);
    font-family: "JetBrains Mono", "Monospace", monospace;
    font-size: 9px;
    letter-spacing: 1px;
    padding: 2px 10px;
    min-height: 0;
}

#channel-btn:hover {
    background-color: rgba(204, 34, 68, 0.06);
    color: rgba(200, 208, 224, 0.65);
    border-bottom-color: rgba(58, 74, 106, 0.8);
}

/* Channel button — active/current */
#channel-btn.active {
    border-bottom: 1px solid #cc2244;
    color: #cc2244;
}

/* Hint bar — clickable shortcut buttons */
#hint-btn {
    background: none;
    background-color: transparent;
    background-image: none;
    border: none;
    border-radius: 0;
    box-shadow: none;
    color: rgba(200, 208, 224, 0.35);
    font-family: "JetBrains Mono", "Monospace", monospace;
    font-size: 8px;
    letter-spacing: 1px;
    padding: 1px 4px;
    min-height: 0;
}

#hint-btn:hover {
    color: #c8d0e0;
    background-color: rgba(204, 34, 68, 0.06);
}

#hint-btn:active {
    color: #ffffff;
}

#hint-sep {
    color: rgba(58, 74, 106, 0.6);
    font-size: 8px;
}

/* Danger buttons — REMOVE CH, QUIT */
#hint-btn-danger {
    background: none;
    background-color: transparent;
    background-image: none;
    border: none;
    border-bottom: 1px solid rgba(204, 34, 68, 0.3);
    color: rgba(204, 34, 68, 0.5);
    font-family: "JetBrains Mono", "Monospace", monospace;
    font-size: 9px;
    letter-spacing: 1px;
    padding: 1px 4px;
    min-height: 0;
}

#hint-btn-danger:hover {
    color: #cc2244;
    background-color: rgba(204, 34, 68, 0.07);
    border-bottom-color: #cc2244;
}

#hint-btn-danger:active {
    color: #ffffff;
}

/* Search modal */
#search-modal {
    background-color: rgba(10, 10, 15, 0.97);
    border: 1px solid #3a4a6a;
    padding: 16px 20px;
    border-radius: 2px;
}

/* Search input */
#search-entry {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid #3a4a6a;
    color: #c8d0e0;
    font-size: 14px;
    caret-color: #cc2244;
    padding: 4px 0;
}

/* Search result row — normal */
#result-row {
    padding: 4px 6px;
    color: rgba(200, 208, 224, 0.5);
    font-size: 10px;
    border-radius: 1px;
}

/* Search result row — selected */
#result-row.selected {
    background-color: rgba(204, 34, 68, 0.10);
    color: #cc2244;
}

/* Error / status message */
#status-label {
    color: #cc2244;
    font-size: 10px;
    letter-spacing: 1px;
}

/* No-signal image container */
#nosignal-box {
    background-color: #0a0a0f;
    background-image: url("../assets/nosignal.png");
    background-size: cover;
    background-position: center top;
}

/* Search page background */
#search-page {
    background-color: #0a0a0f;
}

/* mpv embed area */
#mpv-area {
    background-color: #000000;
}

/* Playback control buttons */
#control-btn {
    background: none;
    background-color: transparent;
    background-image: none;
    border: none;
    border-bottom: 1px solid rgba(58, 74, 106, 0.5);
    border-radius: 0;
    box-shadow: none;
    color: rgba(200, 208, 224, 0.6);
    font-family: "JetBrains Mono", "Monospace", monospace;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 1px 10px 2px 10px;
    min-width: 0;
    min-height: 0;
}

#control-btn:hover {
    background-color: rgba(204, 34, 68, 0.06);
    border-bottom-color: #cc2244;
    color: #cc2244;
}

#control-btn:active {
    background-color: rgba(204, 34, 68, 0.14);
    color: #ffffff;
}

/* Floating fullscreen-exit button */
#fs-exit-btn {
    background-color: rgba(10, 10, 15, 0.80);
    border: 1px solid rgba(58, 74, 106, 0.6);
    border-radius: 1px;
    color: rgba(200, 208, 224, 0.7);
    font-family: "JetBrains Mono", "Monospace", monospace;
    font-size: 10px;
    letter-spacing: 1px;
    padding: 6px 14px;
    margin: 12px;
}

#fs-exit-btn:hover {
    background-color: rgba(204, 34, 68, 0.12);
    border-color: #cc2244;
    color: #cc2244;
}

/* Search tab toggle buttons */
#tab-btn {
    background: none;
    background-color: transparent;
    background-image: none;
    border: none;
    border-bottom: 1px solid rgba(58, 74, 106, 0.3);
    border-radius: 0;
    box-shadow: none;
    color: rgba(200, 208, 224, 0.35);
    font-family: "JetBrains Mono", "Monospace", monospace;
    font-size: 9px;
    letter-spacing: 2px;
    padding: 3px 16px;
    min-height: 0;
}

#tab-btn:checked {
    border-bottom: 1px solid #cc2244;
    color: #cc2244;
}

#tab-btn:hover {
    color: rgba(200, 208, 224, 0.65);
}

/* Bob interrupt block */
#bob-block {
    background-color: rgba(240, 192, 64, 0.06);
    border-left: 2px solid #f0c040;
    padding: 6px 10px;
    margin: 4px 0;
}

#bob-header {
    color: #f0c040;
    font-size: 10px;
    letter-spacing: 1px;
}

#bob-body {
    color: #c8d0e0;
    font-size: 10px;
}

/* Warden shutdown line */
#warden-line {
    color: #8899aa;
    font-size: 10px;
    font-style: italic;
}
```

- [ ] **Step 2: Verify CSS parses cleanly**

```bash
python3 -c "
import gi; gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gdk
p = Gtk.CssProvider()
p.load_from_path('/home/johnny/BrainLab-Networking/streamerbox/themes/ghost.css')
print('CSS OK')
"
```
Expected: `CSS OK` (GTK will warn on unknown properties but not raise).

- [ ] **Step 3: Commit**

```bash
cd ~/BrainLab-Networking && git add streamerbox/themes/ghost.css
git commit -m "feat: add Ghost register GTK CSS theme"
```

---

## Task 3: Create `dossier.py` — WY amber startup window

**Files:**
- Create: `streamerbox/dossier.py`

- [ ] **Step 1: Create `dossier.py`**

```python
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
from gi.repository import Gtk, Gdk, GLib, Pango
import theme


class DossierWindow(Gtk.Window):
    """
    Full-screen amber terminal that types out the WY dossier sequence.
    Performs real system checks (channels, yt-dlp, IPC socket) inline.
    Calls on_complete() when the sequence ends.
    """
    CHAR_DELAY_MS = 18      # ms per character (typewriter cadence)
    LINE_DELAY_MS = 120     # ms pause between lines
    FINAL_HOLD_MS = 900     # ms hold after last line before calling on_complete
    IPC_POLL_MS   = 100     # ms between IPC socket readiness polls

    def __init__(self, channels, player, on_complete):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self._channels  = channels
        self._player    = player
        self._on_complete = on_complete

        self._lines = list(theme.DOSSIER_LINES)  # copy — we mutate suffix
        self._line_idx = 0
        self._char_idx = 0
        self._current_text = ""
        self._waiting_for_ipc = False
        self._ipc_start = None

        self._apply_style()
        self._build_ui()
        self.show_all()
        self.fullscreen()

        GLib.timeout_add(400, self._tick)  # brief pause before typing starts

    def _apply_style(self):
        css = f"""
        window {{ background-color: {theme.COLORS['amber_void']}; }}
        #dossier-text {{
            color: {theme.COLORS['amber']};
            font-family: "JetBrains Mono", "Monospace", monospace;
            font-size: 13px;
        }}
        #dossier-fault {{
            color: {theme.COLORS['crimson']};
            font-family: "JetBrains Mono", "Monospace", monospace;
            font-size: 13px;
        }}
        """.encode()
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

        # One label per line, added dynamically as each line completes
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

    # ------------------------------------------------------------------
    # System checks
    # ------------------------------------------------------------------
    def _check_channels(self) -> bool:
        return self._channels.count() > 0

    def _check_yt_dlp(self) -> bool:
        return shutil.which("yt-dlp") is not None

    def _check_ipc(self) -> bool:
        return self._player.ipc_socket_ready()

    def _resolve_check(self, check: str) -> str | None:
        """
        Returns " OK" / " FAULT" for synchronous checks.
        Returns None for "ipc" (handled async via polling).
        """
        if check == "channels":
            return "  OK" if self._check_channels() else "  FAULT"
        if check == "yt_dlp":
            return "  OK" if self._check_yt_dlp() else "  FAULT"
        if check == "ipc":
            return None  # async — see _poll_ipc
        return ""

    # ------------------------------------------------------------------
    # Animation loop
    # ------------------------------------------------------------------
    def _tick(self) -> bool:
        """GLib callback — drives the typewriter character by character."""
        if self._line_idx >= len(self._lines):
            GLib.timeout_add(self.FINAL_HOLD_MS, self._finish)
            return False

        line = self._lines[self._line_idx]
        full_text = line["text"]
        check     = line.get("check")
        suffix    = line.get("suffix", "")

        # --- IPC async path ---
        if check == "ipc" and not self._waiting_for_ipc:
            # Type the line text first (without suffix), then wait for IPC
            if self._char_idx < len(full_text):
                self._char_idx += 1
                self._current_label.set_text(full_text[:self._char_idx])
                return True
            # Full line text done — now poll for IPC
            self._waiting_for_ipc = True
            self._ipc_start = time.time()
            GLib.timeout_add(self.IPC_POLL_MS, self._poll_ipc)
            return False  # pause main tick; _poll_ipc will resume

        if self._waiting_for_ipc:
            return False  # still waiting

        # --- Synchronous line ---
        if self._char_idx == 0 and check and check != "ipc":
            resolved = self._resolve_check(check)
            self._lines[self._line_idx]["suffix"] = resolved
            suffix = resolved

        display = full_text + suffix
        if self._char_idx < len(display):
            self._char_idx += 1
            self._current_label.set_text(display[:self._char_idx])
            return True

        # Line complete — move to next
        self._advance_line()
        return True

    def _poll_ipc(self) -> bool:
        """Poll until IPC socket is ready (up to 10s), then resume tick."""
        if self._player.ipc_socket_ready():
            suffix = "  OK"
            full   = self._lines[self._line_idx]["text"] + suffix
            self._current_label.set_text(full)
            self._waiting_for_ipc = False
            self._advance_line()
            GLib.timeout_add(self.LINE_DELAY_MS, self._tick)
            return False

        if time.time() - self._ipc_start > 10.0:
            full = self._lines[self._line_idx]["text"] + "  FAULT"
            self._current_label.set_name("dossier-fault")
            self._current_label.set_text(full)
            self._waiting_for_ipc = False
            self._advance_line()
            GLib.timeout_add(self.LINE_DELAY_MS, self._tick)
            return False

        return True  # keep polling

    def _advance_line(self):
        self._line_idx += 1
        self._char_idx = 0
        if self._line_idx < len(self._lines):
            self._current_label = self._new_label()
        GLib.timeout_add(self.LINE_DELAY_MS, lambda: None)  # natural pause handled by tick

    def _finish(self) -> bool:
        self.destroy()
        self._on_complete()
        return False
```

- [ ] **Step 2: Sanity-import check**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -c "import dossier; print('dossier OK')"
```
Expected: `dossier OK`

- [ ] **Step 3: Commit**

```bash
cd ~/BrainLab-Networking && git add streamerbox/dossier.py
git commit -m "feat: add WY Dossier startup window (dossier.py)"
```

---

## Task 4: Wire dossier into `main.py`

**Files:**
- Modify: `streamerbox/main.py`

- [ ] **Step 1: Read current main.py top-level imports and main() function** (already done above — captured in plan)

- [ ] **Step 2: Replace `main.py`**

```python
# streamerbox/main.py
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from channels import ChannelManager
from player import MpvPlayer
from overlay import StreamerOverlay
from dossier import DossierWindow


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

    # Realize the video DrawingArea so mpv can embed into it
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
    overlay.hide()  # hidden until dossier completes

    # Start mpv embedded (idle — first URL loaded after dossier via IPC)
    player.start(wid=wid)

    # Watchdog: restart mpv if it crashes or IPC dies
    def watchdog():
        if _quitting[0]:
            return False
        if not player.is_alive() or player.has_ipc_failed():
            ch = channels.get(overlay._current_idx)
            if ch:
                player.restart(ch.url)
        return True

    GLib.timeout_add(2000, watchdog)

    def on_dossier_complete():
        """Called by DossierWindow when the sequence finishes."""
        overlay.show_all()
        overlay.start_ui()
        overlay.start_load()

    # Show the WY dossier — it polls IPC readiness internally and calls
    # on_dossier_complete() when done. The dossier destroys itself on completion.
    DossierWindow(channels=channels, player=player, on_complete=on_dossier_complete)

    Gtk.main()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify import chain is clean**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -c "
import main
print('main.py imports OK')
"
```
Expected: `main.py imports OK` (no errors)

- [ ] **Step 4: Run full test suite**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m pytest tests/ -v
```
Expected: all 39 existing tests + 5 theme tests = **44 passed**

- [ ] **Step 5: Commit**

```bash
cd ~/BrainLab-Networking && git add streamerbox/main.py
git commit -m "feat: wire WY dossier into startup sequence (main.py)"
```

---

## Task 5: Update `overlay.py` — Ghost strings, CSS, Bob triggers, Warden, OSD

**Files:**
- Modify: `streamerbox/overlay.py`

This is the largest single task. Work through it in sub-steps.

### 5a — CSS path + theme import

- [ ] **Step 1: Replace the top of overlay.py (lines 1-11)**

```python
import os
import time
import random
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import threading
from search import search as do_search, search_playlists as do_search_playlists
import theme

THEME_PATH   = os.path.join(os.path.dirname(__file__), "themes/ghost.css")
NOSIGNAL_PATH = os.path.join(os.path.dirname(__file__), "assets/nosignal.png")
```

### 5b — Add session_start and Bob timer to `__init__`

- [ ] **Step 2: In `StreamerOverlay.__init__`, after `self._stall_recovery_active = False`, add:**

```python
        self._session_start = time.time()
        self._bob_milestone_fired = False
        self._stall_attempt_count = 0  # tracks second-attempt Bob trigger
        GLib.timeout_add(7_200_000, self._bob_session_milestone)  # 2hr = 7,200,000ms
```

### 5c — Replace now-playing idle string

- [ ] **Step 3: In `_build_bar`, line 108, change:**

```python
        self._now_playing = Gtk.Label(label="✦ NO SIGNAL")
```
to:
```python
        self._now_playing = Gtk.Label(label=theme.GHOST["now_playing_idle"])
```

### 5d — Wire OSD to all action handlers

Find each handler and add a `self._player.show_text(...)` call using the Ghost string registry.

- [ ] **Step 4: `_toggle_pause` — add OSD after toggling**

Find `_toggle_pause`. After the pause state is flipped and the button label updated, add:

```python
        osd = theme.GHOST["osd_pause"] if self._paused else theme.GHOST["osd_resume"]
        self._player.show_text(osd)
```

- [ ] **Step 5: `_change_channel` — add OSD after channel resolves**

In `_change_channel`, after `self._now_playing.set_text(...)`, add:

```python
        ch = self._channels.get(self._current_idx)
        if ch:
            self._player.show_text(theme.ghost_channel(ch.id, ch.name))
```

- [ ] **Step 6: Seek OSD — in `_on_key` under Left/Right**

Replace:
```python
        if key == "Left":
            self._player.seek(-10)
            return True
        if key == "Right":
            self._player.seek(10)
            return True
```
With:
```python
        if key == "Left":
            self._player.seek(-10)
            self._player.show_text(theme.GHOST["osd_seek_back"])
            return True
        if key == "Right":
            self._player.seek(10)
            self._player.show_text(theme.GHOST["osd_seek_fwd"])
            return True
```

- [ ] **Step 7: Mute OSD**

Replace the mute key handler:
```python
        if key == "m":
            self._player.cycle_mute()
            return True
```
With:
```python
        if key == "m":
            self._player.cycle_mute()
            self._player.show_text(theme.GHOST["osd_muted"])
            return True
```

- [ ] **Step 8: Node nav OSD (playlist prev/next)**

In `_playlist_prev` and `_playlist_next`, add after the IPC call:
```python
        self._player.show_text(theme.GHOST["osd_node_back"])   # _playlist_prev
        self._player.show_text(theme.GHOST["osd_node_fwd"])    # _playlist_next
```

- [ ] **Step 9: Toggle bar OSD**

In `_toggle_bar`, after toggling visibility:
```python
        visible = self._bar.get_visible()
        self._player.show_text(
            theme.GHOST["interface_visible"] if visible else theme.GHOST["interface_suppressed"]
        )
```

- [ ] **Step 10: Search open OSD**

In `_open_search`, at the top of the method:
```python
        self._player.show_text(theme.GHOST["osd_query_open"])
```

- [ ] **Step 11: Search result play OSD**

In `_play_search_result`, after setting the title/now-playing label:
```python
        self._player.show_text(theme.ghost_search_play(result.title))
```

- [ ] **Step 12: Save channel OSD**

In `_add_channel_dialog` where the status is checked:

```python
        status = self._channels.save_channel(url=url, name=name)
        if status == "ADDED":
            self._player.show_text(theme.GHOST["osd_catalog_confirmed"])
            msg = "> catalog entry confirmed"
        elif status == "ALREADY_EXISTS":
            self._show_bob("duplicate_add")
            msg = "> entry already indexed"
        else:
            msg = "> catalog fault — entry rejected"
```

### 5e — Wire Bob triggers

- [ ] **Step 13: Add `_show_bob` helper method**

Add this method to `StreamerOverlay`:

```python
    def _show_bob(self, trigger_key: str):
        """Display a Bob interrupt block in the now-playing area briefly."""
        lines = list(theme.BOB[trigger_key])
        if lines[0] is None:
            lines[0] = theme.bob_random_title()
        # Join all lines for mpv OSD (plain text)
        osd_text = "\n".join(f"> {l}" if not l.startswith(">") and not l.startswith("BOB") else l
                             for l in lines)
        self._player.show_text(osd_text, duration=6000)
```

- [ ] **Step 14: Bob — stall recovery trigger**

In the stall recovery method (where `yt-dlp -U` is called after a stall), increment the attempt counter and show Bob on the first and second recovery:

```python
        self._stall_attempt_count += 1
        if self._stall_attempt_count == 1:
            self._show_bob("stall_recovery")
        elif self._stall_attempt_count == 2:
            self._show_bob("second_attempt")
        # Reset after second attempt
        if self._stall_attempt_count >= 2:
            self._stall_attempt_count = 0
```

- [ ] **Step 15: Bob — zero search results**

In `_on_search_submit` (or wherever results are rendered), after confirming `len(self._search_results) == 0`:

```python
        if not self._search_results:
            self._show_bob("zero_results")
```

- [ ] **Step 16: Bob — random 1-in-20 nav quip**

In `_change_channel`, after the OSD channel string is shown:

```python
        if random.random() < 0.05:
            GLib.timeout_add(2500, lambda: self._show_bob("random_nav") or False)
```

- [ ] **Step 17: Bob — 2hr session milestone**

Add this method to `StreamerOverlay`:

```python
    def _bob_session_milestone(self) -> bool:
        if not self._bob_milestone_fired:
            self._bob_milestone_fired = True
            self._show_bob("session_milestone")
        return False  # fire once only
```

### 5f — Warden shutdown line

- [ ] **Step 18: Add Warden line to quit handler in `overlay.py`**

Find the method that handles quit (connected via `on_quit` or destroy). Add before `self._on_quit()` is called (e.g. on `q` key):

```python
        # Warden speaks on shutdown
        self._now_playing.set_text(theme.WARDEN_SHUTDOWN)
        while Gtk.events_pending():
            Gtk.main_iteration()
        import time as _time; _time.sleep(1.2)
        self._on_quit()
```

Ensure this only fires from the keyboard `q` and the QUIT button, not from watchdog restarts. The `_on_quit` callback in `main.py` already has a `_quitting` guard.

### 5g — Node status in status bar

- [ ] **Step 19: Update `on_mpv_event` to use Ghost node string**

In the section of `on_mpv_event` that updates playlist position display, replace whatever `ITEM N/M` or similar string with:

```python
        if self._playlist_count > 0:
            node_str = theme.ghost_node_status(self._playlist_pos + 1, self._playlist_count)
            GLib.idle_add(self._time_label.set_text, node_str)
```

- [ ] **Step 20: Run full test suite**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m pytest tests/ -v
```
Expected: **44 passed, 0 failed**

- [ ] **Step 21: Commit**

```bash
cd ~/BrainLab-Networking && git add streamerbox/overlay.py
git commit -m "feat: wire Ghost strings, Bob triggers, Warden shutdown into overlay.py"
```

---

## Task 6: Verify `show_text` supports duration parameter in `player.py`

**Files:**
- Modify: `streamerbox/player.py` (if needed)

- [ ] **Step 1: Check current `show_text` signature**

```bash
cd ~/BrainLab-Networking/streamerbox && grep -n "show_text" player.py
```

- [ ] **Step 2: If `show_text` does not accept a `duration` parameter, update it**

Find the method and ensure it accepts `duration` (in ms) with a default:

```python
    def show_text(self, text: str, duration: int = 3000):
        """Display text on mpv OSD via IPC show-text command."""
        self._send({"command": ["show-text", text, duration]})
```

- [ ] **Step 3: Run test suite**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m pytest tests/ -v
```
Expected: **44 passed**

- [ ] **Step 4: Commit if changed**

```bash
cd ~/BrainLab-Networking && git add streamerbox/player.py
git commit -m "fix: ensure show_text accepts duration parameter"
```

---

## Task 7: End-to-end smoke check and final commit

- [ ] **Step 1: Run full test suite one final time**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m pytest tests/ -v --tb=short
```
Expected: **44 passed, 0 failed**

- [ ] **Step 2: Syntax-check all modified files**

```bash
cd ~/BrainLab-Networking/streamerbox && python3 -m py_compile theme.py dossier.py overlay.py main.py player.py && echo "All files compile OK"
```
Expected: `All files compile OK`

- [ ] **Step 3: Push to GitHub**

```bash
cd ~/BrainLab-Networking && git push origin master
```

- [ ] **Step 4: Restart StreamerBox on Thought-Reliquary to verify live**

```bash
ssh johnny@192.168.4.100 'cd ~/BrainLab-Networking && git pull && systemctl --user restart streamerbox.service'
```

---

## Self-Review Checklist

| Spec requirement | Covered by |
|---|---|
| Ghost palette — void/signal/crimson/circuit | Task 2 (ghost.css), Task 5 (overlay imports theme) |
| WY Dossier amber register | Task 2 (ghost.css Bob/Warden extras not needed here), Task 3 (dossier.py) |
| Bob amber-gold register | Task 2 (ghost.css #bob-header), Task 5 (`_show_bob`) |
| Warden mist register | Task 2 (ghost.css #warden-line), Task 5 step 18 |
| Dossier real system checks (IPC/yt-dlp/channels) | Task 3 (`_resolve_check`, `_poll_ipc`) |
| FAULT in crimson on failed check | Task 3 (`_poll_ipc` fault path, `_resolve_check`) |
| Ghost string registry — all OSD strings | Task 1 (theme.py GHOST dict), Task 5 steps 4-12 |
| Bob 6 triggers | Task 1 (BOB dict), Task 5 steps 13-17 |
| Bob random title pool ≥ 10 | Task 1 (BOB_TITLES, 15 entries) |
| Bob `show_text` duration 6s | Task 5 step 13 (`_show_bob`), Task 6 |
| Warden shutdown — 1 trigger | Task 1 (WARDEN_SHUTDOWN), Task 5 step 18 |
| `theme.py` as single source of truth | Task 1, Task 5 (all hardcoded strings removed) |
| All 39 existing tests pass | Task 4 step 4, Task 5 step 20, Task 7 step 1 |
| `test_theme.py` covers registry completeness | Task 1 steps 1-4 |
| No new dependencies | Confirmed — all GTK/GLib/random are stdlib or already imported |
