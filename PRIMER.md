# BrainLab Session Primer — 2026-03-24

Pick up here in the next session.

---

## Machine: Thought-Reliquary
- Ubuntu 24.04, X11 (Wayland disabled), 2-in-1 tablet/laptop
- IP: `192.168.4.100` — SSH + TigerVNC (port 5900)
- **Display is `:1`** — GDM occupies `:0`, GNOME user session runs on `:1`
- Display panel is physically inverted in chassis:
  - `unflip` alias = `xrandr --rotate inverted` (visually correct)
  - `flip` alias = `xrandr --rotate normal` (tablet mode)
- mpv + yt-dlp installed, configured at `~/.config/mpv/mpv.conf`

---

## Persistent Services (systemd user)

Both services survive SSH session close, restart on crash, start on GNOME login.

| Service | File | What it does |
|---|---|---|
| `x11vnc.service` | `~/.config/systemd/user/x11vnc.service` | VNC server on display `:1`, port 5900 |
| `streamerbox.service` | `~/.config/systemd/user/streamerbox.service` | StreamerBox ambient player |

Manage with:
```bash
systemctl --user restart x11vnc.service
systemctl --user restart streamerbox.service
systemctl --user status x11vnc.service
```

Linger enabled (`loginctl enable-linger johnny`) — services survive session cycles.

---

## TigerVNC — Mac Mini

- **App:** `~/Applications/Reliquary VNC.app` (pinned to Dock, Spotlight: "Reliquary VNC")
- **Password file:** `~/.vnc/passwd_reliquary` (copied from Linux, auto-used by app)
- **No password prompt** — launches and connects directly
- If VNC stops working: `ssh johnny@192.168.4.100` → `systemctl --user restart x11vnc`

---

## StreamerBox

A CRT-styled ambient anime/YouTube player. Runs as a systemd user service.

### Code location
- `~/streamerbox/` → symlink to `~/BrainLab-Networking/streamerbox/`
- To update: `cd ~/BrainLab-Networking && git pull && systemctl --user restart streamerbox.service`

### Key files
| Path | What it is |
|---|---|
| `~/BrainLab-Networking/streamerbox/` | Source code (symlinked to `~/streamerbox/`) |
| `~/.config/streamerbox/channels.yaml` | Channel list — add/edit playlist URLs here |
| `~/.config/streamerbox/cookies.txt` | YouTube Premium + Crunchyroll cookies |

### Button layout
```
◀◀  |◀  −10  ▌▌/►  +10  ▶|  ▶▶  M
```
- `◀◀` / `▶▶` — previous/next **channel** (switches show)
- `|◀` / `▶|` — previous/next **track** within current playlist
- `▌▌` / `►` — pause / play
- `−10` / `+10` — seek 10 seconds
- `M` — mute

### Playlist navigation
Uses explicit `playlist-pos` index tracking via mpv IPC. Stall detector suppressed during user navigation (`_user_nav_time` flag, 3s window).

### Re-export cookies (when they expire, every few months)
```bash
yt-dlp --cookies-from-browser firefox \
       --cookies ~/.config/streamerbox/cookies.txt \
       --skip-download "https://www.youtube.com"
```

---

## BrainLab-Networking Repo State

```
git log --oneline -5

47a3068 Fix playlist nav icons: use |◀ and ▶| instead of ⏮/⏭
b873ee0 Fix icon confusion: ⏮/⏭ for playlist nav, ► for play (not ▶)
8ec39a7 Fix playlist navigation: track position explicitly, suppress stall on user nav
bf35520 Fix x11vnc display: :0 → :1; document GDM display layout
24d96b5 Fix x11vnc: replace autostart .desktop with systemd user service
```

---

## Known Working / Stable
- x11vnc persists after closing Mac terminal ✓
- StreamerBox persists after closing Mac terminal ✓
- TigerVNC connects without password prompt ✓
- Playlist track navigation (|◀/▶|) works correctly ✓
- Channel switching (◀◀/▶▶) works correctly ✓
