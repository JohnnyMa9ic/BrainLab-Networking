# StreamerBox — Design Spec

**Date:** 2026-03-23
**Machine:** Thought-Reliquary (Ubuntu 24.04)

---

## Vision

A standalone ambient TV experience for the lab. Boots into a default anime channel on login, plays continuously in the background. Feels like an old CRT TV with channel presets — flip channels with arrow keys, hit `/` to search for something new. Cyberpunk/synthwave aesthetic: magenta + cyan phosphor glow over a dark scanline background.

---

## Architecture

Three processes running together:

1. **mpv** — fullscreen video playback, controlled via a Unix IPC socket. mpv owns the screen entirely and handles all playback natively (buffering, quality selection, subtitles, seeking).
2. **StreamerBox overlay** — a GTK3 always-on-top transparent window sitting over mpv. Renders the channel strip and search UI. Captures keyboard input.
3. **yt-dlp** — invoked as a subprocess on demand for URL resolution and search. Not a daemon.

mpv and the overlay communicate via mpv's built-in IPC socket (`~/.config/streamerbox/mpv.sock`). The overlay sends JSON commands to change the playing URL; mpv reports playback state back.

---

## Components

| File | Responsibility |
|---|---|
| `main.py` | Entry point — launches mpv subprocess, starts GTK app, wires components together |
| `player.py` | mpv manager — spawns mpv with correct flags, sends IPC commands (loadfile, stop, seek), monitors subprocess health and restarts on crash |
| `channels.py` | Channel manager — loads and merges `channels.yaml` + `saved.yaml`, provides ordered channel list, handles saving new channels |
| `overlay.py` | GTK window — always-on-top transparent overlay, renders channel strip at bottom, captures keyboard input, triggers search |
| `search.py` | Search UI + yt-dlp integration — shows search modal, queries yt-dlp with `--dump-json`, parses results, returns channel candidates |

---

## Visual Design

**Theme:** Synthwave / Cyberpunk
- Background: deep purple-black (`#050008`)
- Primary colour: magenta (`#ff00ff`) with cyan (`#00ffff`) accents
- Text: `#ff66ff`
- Scanline effect: CSS repeating-linear-gradient overlay
- Search modal: glow effect (`box-shadow: 0 0 20px rgba(255,0,255,0.2)`)
- Font: monospace throughout

**Overlay behaviour:**
- Fades in when any key is pressed; fades out after 3 seconds of inactivity during playback
- Channel strip sits at the bottom — current channel highlighted, adjacent channels visible at reduced opacity
- Search modal appears centre-screen when `/` or `F` is pressed

**Channel strip layout:**
```
✦ CH 04 — COWBOY BEBOP                          S01E03 · 14:22 / 24:00

[ 01 DBZ ]  [ 02 Trigun ]  [ 03 Akira ]  [ 04 Bebop ◄ ]  [ 05 GitS ]  [ + search ]

              ↑↓ CH  ·  / SEARCH  ·  Q QUIT
```

---

## Keyboard Controls

| Key | Action |
|---|---|
| `↑` / `↓` | Change channel |
| `1`–`9` | Jump to channel by number |
| `/` or `F` | Open search |
| `S` | Save current search result as a channel slot |
| `Enter` | Play selected search result |
| `Esc` | Close search / dismiss overlay |
| `Q` | Quit StreamerBox |

mpv's native shortcuts (`Space`, `←→`, `f`, `m`, `i`) remain active during playback.

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

Both files are merged at startup by `channels.py`. IDs from `channels.yaml` take precedence; `saved.yaml` channels append after.

---

## YouTube Premium Authentication

YouTube Premium benefits (no ads, subscription content) are passed via a cookie file exported from Firefox.

**Cookie file location:** `~/.config/streamerbox/cookies.txt`

**One-time export command:**
```bash
yt-dlp --cookies-from-browser firefox \
       --cookies ~/.config/streamerbox/cookies.txt \
       --skip-download "https://www.youtube.com"
```

Run this once while logged into YouTube in Firefox. Re-run when cookies expire (typically every few months).

Cookies are passed to both mpv and yt-dlp at runtime:
- mpv: `--ytdl-raw-options=cookies=/home/johnny/.config/streamerbox/cookies.txt`
- yt-dlp: `--cookies ~/.config/streamerbox/cookies.txt`

---

## mpv Configuration

mpv is launched with:
```
--fullscreen
--really-quiet
--no-terminal
--input-ipc-server=~/.config/streamerbox/mpv.sock
--ytdl-path=/usr/local/bin/yt-dlp
--ytdl-format=bestvideo[height<=1080]+bestaudio/best[height<=1080]
--ytdl-raw-options=cookies=/home/johnny/.config/streamerbox/cookies.txt
--cache=yes
--demuxer-max-bytes=150MiB
--loop-playlist=inf
```

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
    └── nosignal.png

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
| Stream fails / bad URL | Overlay shows brief error, auto-advances to next channel |
| yt-dlp search returns nothing | Search modal shows "NO SIGNAL — no results" |
| mpv crashes | `player.py` detects dead subprocess, restarts mpv on same channel |
| Cookies expired | Overlay shows "AUTH REQUIRED" with re-export command |
| No network | mpv error caught, overlay shows "NO SIGNAL" in CRT style |

---

## Autostart

`~/.config/autostart/streamerbox.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=StreamerBox
Exec=python3 /home/johnny/streamerbox/main.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

Launches on GNOME login. mpv starts immediately on the first channel in `channels.yaml`.

---

## Setup Checklist

- [ ] Create `~/streamerbox/` and write app files
- [ ] Create `~/.config/streamerbox/channels.yaml` with initial channels
- [ ] Export YouTube cookies to `~/.config/streamerbox/cookies.txt`
- [ ] Install `python3-gi` (already installed on Thought-Reliquary)
- [ ] Create `~/.config/autostart/streamerbox.desktop`
- [ ] Test: launch manually, verify mpv starts fullscreen, overlay appears on keypress, channel switching works, search returns results
