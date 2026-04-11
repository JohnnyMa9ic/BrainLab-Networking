# BrainLab Session Primer — 2026-04-11 (updated)

Pick up here in the next session.

---

## Machine: Thought-Reliquary
- Ubuntu 24.04, X11 (Wayland disabled), 2-in-1 tablet/laptop
- IP: `192.168.4.100` — SSH + TigerVNC (port 5900)
- **Display is `:0`** — after a system update, GNOME user session moved to `:0` (was `:1`)
- Display panel is physically inverted in chassis:
  - `unflip` alias = `xrandr --rotate inverted` (visually correct)
  - `flip` alias = `xrandr --rotate normal` (tablet mode)
- mpv + yt-dlp installed, configured at `~/.config/mpv/mpv.conf`
- Node.js 20.20.2 + npm 10.8.2 installed via NodeSource repo (replaced snap node 18)
- Codex CLI 0.120.0 installed globally (`sudo npm install -g @openai/codex`), authenticated

---

## Persistent Services (systemd user)

Both services survive SSH session close, restart on crash, start on GNOME login.

| Service | File | What it does |
|---|---|---|
| `x11vnc.service` | `~/.config/systemd/user/x11vnc.service` | VNC server on display `:0`, port 5900 |
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
- If VNC stops working: SSH in → `systemctl --user restart x11vnc.service`
- If display changes after an update, check `echo $DISPLAY` and update the service file + restart
- Clipboard sync works out of the box — if it stops, just restart x11vnc and reconnect TigerVNC

---

## SSH from Mac to Reliquary

Passwordless SSH is configured — Claude Code can SSH and SCP directly without user involvement:
```bash
ssh johnny@192.168.4.100 'command here'
scp /local/file johnny@192.168.4.100:/remote/path
```

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
| `~/BrainLab-Networking/streamerbox/assets/nosignal.png` | Standby screen — currently Lithium Dreams v3 (Gemini, magenta CRT + bonsai/skull) |

### Button layout
```
◀◀  |◀  −10  ▌▌/►  +10  ▶|  ▶▶  M
```
- `◀◀` / `▶▶` — previous/next **channel** (switches show)
- `|◀` / `▶|` — previous/next **track** within current playlist
- `▌▌` / `►` — pause / play
- `−10` / `+10` — seek 10 seconds
- `M` — mute

### Re-export cookies (when they expire, every few months)
```bash
yt-dlp --cookies-from-browser firefox \
       --cookies ~/.config/streamerbox/cookies.txt \
       --skip-download "https://www.youtube.com"
```

---

## Claude Code Session Protocol

GitHub (`JohnnyMa9ic/BrainLab-Networking`) is the single source of truth for BrainLab knowledge.

### Opening sequence (automatic)
A `SessionStart` hook at `~/.claude/hooks/session-start-primer.sh` fetches this PRIMER.md live from GitHub and injects it into Claude's context at the start of every session. No manual "read the PRIMER" needed.

### Closing handshake (every session)
At session end, Claude proactively:
1. Updates this PRIMER.md with any new facts, fixes, or state changes from the session
2. Commits: `Update PRIMER for YYYY-MM-DD session`
3. Pushes to GitHub

Supporting files on this machine:
- Hook script: `~/.claude/hooks/session-start-primer.sh`
- Claude instructions: `~/CLAUDE.md`
- Hook registered in: `~/.claude/settings.json` under `hooks.SessionStart`

---

## Known Working / Stable
- x11vnc persists after closing Mac terminal ✓
- StreamerBox persists after closing Mac terminal ✓
- TigerVNC connects without password prompt ✓
- Playlist track navigation (|◀/▶|) works correctly ✓
- Channel switching (◀◀/▶▶) works correctly ✓
- Standby screen: Lithium Dreams v3 (magenta CRT, bonsai + skull wireframes) ✓
- Claude Code session protocol (auto-PRIMER fetch + closing handshake) ✓
- StreamerBox: ADD CH button (dialog with name+URL), fullscreen hides bar + floating exit button ✓
- Clipboard sync via VNC works (x11vnc default, no extra flags needed) ✓
- OpenAI Codex plugin installed in Claude Code ✓ (`claude plugin marketplace add openai/codex-plugin-cc` + `claude plugin install codex@openai-codex`)
  - Note: `/plugin` is a CLI subcommand (`claude plugin ...`), NOT a chat slash command
  - Commands available after restart: `/codex:review`, `/codex:adversarial-review`, `/codex:rescue`, `/codex:status`, `/codex:result`, `/codex:cancel`
