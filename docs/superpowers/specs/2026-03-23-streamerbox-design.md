# StreamerBox — Design Spec

**Date:** 2026-03-23
**Machine:** Thought-Reliquary (Ubuntu 24.04, X11 session — Wayland disabled)

---

## Vision

A standalone ambient TV experience for the lab. Boots into a default anime channel on login, plays continuously in the background. Feels like an old CRT TV with channel presets — flip channels with arrow keys, hit `/` to search for something new. Cyberpunk/synthwave aesthetic: magenta + cyan phosphor glow over a dark scanline background.

---

## Architecture

Three processes running together:

1. **mpv** — fills the screen via `--geometry` + `--no-border` (not `--fullscreen`). This is critical: using `--fullscreen` causes mpv to grab X11 keyboard focus, preventing the GTK overlay from receiving key events. `--geometry=1920x1080+0+0 --no-border` achieves the same visual result while leaving keyboard focus available for the overlay.
2. **StreamerBox overlay** — a GTK3 always-on-top transparent window sitting over mpv. Renders the channel strip and search UI. Holds keyboard focus and intercepts key events.
3. **yt-dlp** — invoked as a subprocess on demand for URL resolution and search. Not a daemon.

mpv and the overlay communicate via mpv's built-in IPC socket (`~/.config/streamerbox/mpv.sock`). The overlay sends JSON commands to change the playing URL; `player.py` runs a background thread to drain async events from the socket (playback state updates).

**Session note:** This machine runs X11 (Wayland disabled in `/etc/gdm3/custom.conf`). The GTK app is launched with `GDK_BACKEND=x11` set in the `.desktop` file to ensure GTK uses X11 even if Wayland is ever re-enabled.

---

## Components

| File | Responsibility |
|---|---|
| `main.py` | Entry point — launches mpv subprocess, starts GTK app, wires components together |
| `player.py` | mpv manager — spawns mpv with correct flags, sends IPC commands (loadfile, stop, seek), runs background thread to read IPC socket events, monitors subprocess health and restarts on crash |
| `channels.py` | Channel manager — loads and merges `channels.yaml` + `saved.yaml`, provides ordered channel list, handles saving new channels |
| `overlay.py` | GTK window — always-on-top transparent overlay, renders channel strip at bottom, captures keyboard input, triggers search |
| `search.py` | Search UI + yt-dlp integration — shows search modal, queries yt-dlp with `--dump-json`, parses results, returns channel candidates |

---

## Visual Design

**Theme:** Synthwave / Cyberpunk
- Background: deep purple-black (`#050008`)
- Primary colour: magenta (`#ff00ff`) with cyan (`#00ffff`) accents
- Text: `#ff66ff`
- Scanline effect: GTK CSS `repeating-linear-gradient` overlay widget
- Search modal: glow effect via GTK CSS `box-shadow`
- Font: monospace throughout

**Overlay behaviour:**
- Fades in when any overlay-consumed key is pressed; fades out after 3 seconds of inactivity during playback
- Channel strip sits at the bottom — current channel highlighted, adjacent channels visible at reduced opacity
- Search modal appears centre-screen when `/` or `Shift+F` is pressed

**Channel strip layout:**
```
✦ CH 04 — COWBOY BEBOP                          S01E03 · 14:22 / 24:00

[ 01 DBZ ]  [ 02 Trigun ]  [ 03 Akira ]  [ 04 Bebop ◄ ]  [ 05 GitS ]  [ + search ]

              ↑↓ CH  ·  / SEARCH  ·  Q QUIT
```

**No-signal graphic:** `assets/nosignal.png` is displayed full-screen by `overlay.py` whenever mpv has no active stream (on startup before first channel loads, or after a stream error before auto-advance). Dimensions: 1920x1080.

---

## Keyboard Controls

The overlay consumes the following keys (stops propagation to mpv):

| Key | Action |
|---|---|
| `↑` / `↓` | Change channel |
| `1`–`9` | Jump to channel by number |
| `/` or `Shift+F` | Open search (`f` lowercase passes through to mpv as fullscreen toggle) |
| `S` | Save current search result as a channel slot |
| `Enter` | Play selected search result |
| `Esc` | Close search / dismiss overlay |
| `Q` | Quit StreamerBox |

The following keys are **forwarded to mpv** via IPC command or xdotool:

| Key | mpv action | Method |
|---|---|---|
| `Space` | Pause / resume | IPC: `cycle pause` |
| `←` / `→` | Seek 5 seconds | IPC: `seek -5` / `seek 5` |
| `m` | Mute | IPC: `cycle mute` |
| `j` | Cycle subtitle track | IPC: `cycle sub` |
| `f` | Toggle mpv fullscreen | xdotool: re-inject keypress to mpv window |
| `i` | Show stream info | xdotool: re-inject keypress to mpv window |

Keys that map to mpv IPC commands are sent via the socket directly. Keys with no IPC equivalent (`f`, `i`) are re-injected to the mpv window using `xdotool key --window <mpv_window_id> <key>`. The mpv window ID is retrieved at startup via `xdotool search --pid <mpv_pid>`.

**Subtitle support:** `j` cycles through available subtitle tracks (IPC `cycle sub`). mpv is launched with `--sub-auto=fuzzy` to auto-load external subtitle files if present alongside the video. For streams, embedded subtitles are used when available.

---

## mpv IPC — Observed Properties

`player.py` runs a background thread that connects to the IPC socket and sends observe_property commands for the following properties. Events are parsed and forwarded to the overlay via a thread-safe queue:

| Property | Used for |
|---|---|
| `time-pos` | Progress display in channel strip |
| `duration` | Progress display in channel strip |
| `media-title` | Channel name display (overrides config name if richer) |
| `playlist-pos` | Detect playlist advancement (auto-next episode) |
| `idle-active` | Detect when mpv has stopped playing (triggers no-signal state) |

---

## Channel Configuration

**`~/.config/streamerbox/channels.yaml`** — base channels, hand-edited:
```yaml
channels:
  - id: 1
    name: Dragon Ball Z
    url: https://www.youtube.com/playlist?list=PLAYLIST_ID
  - id: 2
    name: Cowboy Bebop
    url: https://www.youtube.com/playlist?list=PLAYLIST_ID
```

**`~/.config/streamerbox/saved.yaml`** — channels added via in-app search (same format, written by the app).

Both files are merged at startup by `channels.py`. IDs from `channels.yaml` take precedence. `saved.yaml` channels are appended after, with IDs assigned as `max(all_existing_ids) + 1` incrementally.

**Save semantics (`S` key):**
- New channel is appended to `saved.yaml` with `id = max(all_ids) + 1`
- If the same URL already exists in either file, the save is silently skipped (no duplicate)
- `channels.py` reloads and re-merges both files in-process immediately after writing — the new channel is navigable without restarting the app

---

## Authentication — YouTube Premium + Crunchyroll

Both services are authenticated via a single Firefox cookie file. The Netscape cookies.txt format holds sessions for all logged-in domains in one export — YouTube Premium and Crunchyroll are captured together as long as both are logged in at export time.

**Cookie file location:** `~/.config/streamerbox/cookies.txt`

**One-time export command (run while logged into both YouTube and Crunchyroll in Firefox):**
```bash
yt-dlp --cookies-from-browser firefox \
       --cookies ~/.config/streamerbox/cookies.txt \
       --skip-download "https://www.youtube.com"
```

This captures all active Firefox sessions. Re-run when cookies expire (typically every few months for both services).

Cookies are passed to both mpv and yt-dlp at runtime. Paths resolved via `os.path.expanduser("~")` — no hardcoded usernames:
- mpv: `--ytdl-raw-options=cookies=<expanded_home>/.config/streamerbox/cookies.txt`
- yt-dlp: `--cookies <expanded_home>/.config/streamerbox/cookies.txt`

**What this unlocks:**
- YouTube: no ads, Premium content, subscription access
- Crunchyroll: full library access, no ads, simulcast episodes

**Crunchyroll URL format for `channels.yaml`:**
```yaml
- id: 3
  name: One Piece
  url: https://www.crunchyroll.com/series/GRMG8ZQZR/one-piece
- id: 4
  name: Jujutsu Kaisen
  url: https://www.crunchyroll.com/series/GRDQPM1ZY/jujutsu-kaisen
```

yt-dlp resolves Crunchyroll series and episode URLs the same way as YouTube playlists — series URLs enumerate all episodes, `--loop-playlist=inf` cycles them continuously.

---

## mpv Configuration

mpv is launched by `player.py` with flags constructed at runtime (paths expanded via `os.path.expanduser`):

```
--geometry=1920x1080+0+0
--no-border
--really-quiet
--no-terminal
--sub-auto=fuzzy
--input-ipc-server=<home>/.config/streamerbox/mpv.sock
--ytdl-path=/usr/local/bin/yt-dlp
--ytdl-format=bestvideo[height<=1080]+bestaudio/best[height<=1080]
--ytdl-raw-options=cookies=<home>/.config/streamerbox/cookies.txt
--cache=yes
--demuxer-max-bytes=150MiB
--loop-playlist=inf
```

All paths containing `<home>` are resolved via `os.path.expanduser("~")` in `player.py` when constructing the `Popen` argument list — `~` is never passed literally to avoid shell-expansion issues with `shell=False`.

Note: `--fullscreen` is intentionally omitted. `--geometry` + `--no-border` fills the screen without grabbing keyboard focus.

The existing `~/.config/mpv/mpv.conf` settings remain for standalone mpv use; StreamerBox passes its flags directly on the command line to avoid conflicts.

---

## File Structure

```
~/streamerbox/
├── main.py
├── player.py
├── channels.py
├── overlay.py
├── search.py
├── themes/
│   └── cyberpunk.css
└── assets/
    └── nosignal.png       # 1920x1080, shown when no stream is active

~/.config/streamerbox/
├── channels.yaml
├── saved.yaml
└── cookies.txt

~/.config/autostart/
└── streamerbox.desktop
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Stream fails / bad URL | `idle-active` IPC event detected → overlay shows error briefly → auto-advances to next channel after 3s |
| yt-dlp search returns nothing | Search modal shows "NO SIGNAL — no results" |
| mpv crashes | `player.py` detects dead subprocess via `poll()`, restarts mpv on same channel |
| Cookies expired / auth error | yt-dlp stderr contains "Sign in", "Premium", "members only", or HTTP 403 → overlay shows "AUTH REQUIRED — run: yt-dlp --cookies-from-browser firefox..." |
| Generic playback error | All other yt-dlp non-zero exits → overlay shows "PLAYBACK ERROR" with raw stderr message truncated to 80 chars |
| No network | mpv `idle-active` event → overlay shows "NO SIGNAL" with nosignal.png |

---

## Autostart

`~/.config/autostart/streamerbox.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=StreamerBox
Exec=bash -c 'GDK_BACKEND=x11 exec python3 "$HOME/streamerbox/main.py"'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

`GDK_BACKEND=x11` ensures GTK uses X11 even if Wayland is ever re-enabled on this machine. `$HOME` is expanded by bash at runtime — no hardcoded username in the `.desktop` file.

Launches on GNOME login. mpv starts immediately on the first channel in `channels.yaml`.

---

## Setup Checklist

- [ ] Create `~/streamerbox/` and write app files
- [ ] Create `~/.config/streamerbox/channels.yaml` with initial channels
- [ ] Log into both YouTube and Crunchyroll in Firefox, then export cookies to `~/.config/streamerbox/cookies.txt`
- [ ] Install `python3-gi` (already installed on Thought-Reliquary)
- [ ] Install `xdotool` (`sudo apt install xdotool`) — required for key forwarding to mpv
- [ ] Create `~/.config/autostart/streamerbox.desktop`
- [ ] Create `assets/nosignal.png` (1920x1080)
- [ ] Test: launch manually, verify mpv fills screen, overlay appears on keypress, channel switching works, search returns results, YouTube Premium plays without ads, Crunchyroll content plays without ads, subtitle toggle works with `j`
