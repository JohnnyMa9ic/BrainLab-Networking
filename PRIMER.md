# BrainLab Session Primer — 2026-03-23

Pick up here in the next session.

---

## Machine: Thought-Reliquary
- Ubuntu 24.04, X11 (Wayland disabled), 2-in-1 tablet/laptop
- IP: `192.168.4.100` — SSH + TigerVNC (port 5900)
- Display panel is physically inverted in chassis:
  - `unflip` alias = `xrandr --rotate inverted` (visually correct)
  - `flip` alias = `xrandr --rotate normal` (tablet mode)
- mpv + yt-dlp installed, configured at `~/.config/mpv/mpv.conf`

---

## What Was Done This Session

1. **mpv streaming setup** — configured `~/.config/mpv/mpv.conf` for optimal streaming
2. **Tablet rotation** — diagnosed inverted panel, added `flip`/`unflip` aliases to `~/.bashrc`
3. **StreamerBox** — full brainstorm → design → plan cycle completed

---

## StreamerBox — Ready to Build

A CRT-styled ambient anime/YouTube player. Cyberpunk/synthwave theme. Runs at boot.

### Key files
| Path | What it is |
|---|---|
| `~/BrainLab-Networking/docs/superpowers/specs/2026-03-23-streamerbox-design.md` | Full design spec |
| `~/BrainLab-Networking/docs/superpowers/plans/2026-03-23-streamerbox.md` | Implementation plan (9 tasks, TDD) |
| `~/.config/streamerbox/cookies.txt` | YouTube Premium + Crunchyroll cookies (already seeded) |
| `~/.config/streamerbox/channels.yaml` | **NEEDS FILLING** — add real playlist URLs |

### Dependencies — all installed
- `python3-gi`, `python3-pytest`, `python3-yaml`, `python3-pillow`, `xdotool`, `mpv`, `yt-dlp`

### To start building
In the next session, say:
> "Let's implement the StreamerBox plan using subagent-driven development"

The plan at `~/BrainLab-Networking/docs/superpowers/plans/2026-03-23-streamerbox.md` is the source of truth. Use the `superpowers:subagent-driven-development` skill.

### Before first run
Fill in real URLs in `~/.config/streamerbox/channels.yaml`:
```yaml
channels:
  - id: 1
    name: Cowboy Bebop
    url: https://www.youtube.com/playlist?list=<real_id>
  - id: 2
    name: Ghost in the Shell SAC
    url: https://www.crunchyroll.com/series/GY5VW29G6/ghost-in-the-shell-stand-alone-complex
```

---

## BrainLab-Networking Repo State

```
git log --oneline -5

03ada70 Add StreamerBox implementation plan
f5b62e2 Add Crunchyroll account support to StreamerBox spec
87bfd06 Update StreamerBox spec — resolve review blockers + add subtitles
3cdef37 Add StreamerBox design spec
035a4fe Fix tablet rotation aliases — panel is physically mounted inverted
```
