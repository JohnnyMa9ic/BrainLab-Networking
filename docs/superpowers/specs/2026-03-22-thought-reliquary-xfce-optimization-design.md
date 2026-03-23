# Thought-Reliquary: XFCE Optimization Design

**Date:** 2026-03-22
**Machine:** Thought-Reliquary — Ubuntu 24.04 LTS (`192.168.4.100`)
**Goal:** Optimize as a VNC remote desktop node accessed from Mac Mini via Finder, with command-line video streaming capability.

---

## Context

Thought-Reliquary is accessed from a Mac Mini via VNC (Finder → Go → Connect to Server → `vnc://192.168.4.100`). The machine runs x11vnc on X11 (Wayland disabled) as the stable remote access solution. The goal is to maximize desktop responsiveness over VNC and add YouTube/anime streaming from the terminal.

### Constraints
The following are established and must not be changed:
- `~/.config/autostart/x11vnc.desktop` — x11vnc autostart
- `~/.vnc/passwd` — VNC password
- `/etc/gdm3/custom.conf` — Wayland disabled (`WaylandEnable=false`)
- Firewall rules — ports 22 (SSH), 5900 (VNC), 3389 (RDP)
- x11vnc package and configuration

### Pre-verified State
XFCE is already installed on this machine (`xfce4`, `xfce4-goodies`, `xfce4-session` — all confirmed installed during prior xrdp testing). No XFCE installation step is required. `xfce4-session` is present, which guarantees XDG autostart processing (including `x11vnc.desktop`).

---

## Design

### 1. Switch Default Session to XFCE

**What:** Update GDM's user session preference to `xfce` so the desktop that x11vnc captures is XFCE instead of GNOME Shell.

**How:** Edit `/var/lib/AccountsService/users/johnny`. This file may or may not exist:
- If it exists: set `Session=xfce` under the `[User]` stanza
- If it does not exist: create it with the following content:
  ```
  [User]
  Session=xfce
  SystemAccount=false
  ```

**Why XFCE over GNOME for VNC:**
- GNOME Shell uses a Mutter compositor with GPU-accelerated effects; x11vnc captures raw framebuffer pixels, so those effects add overhead with no visual benefit to the VNC client
- XFCE uses ~150MB RAM vs GNOME's ~450MB at idle
- XFCE renders simpler UI primitives, producing smaller screen diffs per frame — VNC only sends changed regions, so simpler UI = fewer bytes per update = lower latency

**Rollback:** Set `Session=gnome` (or delete the file if it didn't exist before) to restore GNOME.

**x11vnc pathway:** Unaffected. `xfce4-session` processes `~/.config/autostart/x11vnc.desktop` via XDG autostart on every login. Display `:0`, port `5900`, and VNC password are identical.

---

### 2. Disable XFCE Compositor

**What:** Disable the XFCE built-in compositor (Xfwm4 compositing) via direct file edit.

**Why:** The compositor adds a compositing pass before writing to the framebuffer. Under VNC, the client never sees GPU-composited transparency or shadows — it only sees the final framebuffer. Disabling compositing eliminates this pass entirely, reducing CPU and memory usage and improving frame capture speed.

**How (file-edit, pre-session method):**

Check whether `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml` exists:

**Case A — file does not exist:** Create the directory path and write the file:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="use_compositing" type="bool" value="false"/>
  </property>
</channel>
```

**Case B — file exists with `use_compositing` property:** Set its `value` attribute to `"false"`.

**Case C — file exists but `use_compositing` property is absent:** Add the property inside the existing `<property name="general">` block:
```xml
<property name="use_compositing" type="bool" value="false"/>
```

**Note:** Do NOT use `xfconf-query` for this step. That tool writes through the running `xfconfd` daemon and only works inside an active XFCE session. The file-edit method works pre-session and is the reliable approach.

**Rollback:** Set the `use_compositing` value attribute back to `"true"`.

---

### 3. Remove wayvnc Autostart

**What:** Delete `~/.config/autostart/wayvnc.desktop`.

**Why:** wayvnc requires a Wayland compositor exposing the `wlr-screencopy` protocol. Wayland is disabled on this machine (required for x11vnc). wayvnc silently fails on every login, consuming startup time and producing journal errors.

**Rollback:** Recreate the file with this exact content:
```
[Desktop Entry]
Type=Application
Name=wayvnc
Exec=wayvnc
StartupNotify=false
Terminal=false
Hidden=false
```

---

### 4. Install yt-dlp + mpv

**What:** Install two tools:
- `yt-dlp` — command-line video stream extractor (YouTube, Twitch, anime sites, 1000+ sources)
- `mpv` — lightweight video player with native yt-dlp integration

**How:**

`mpv` via apt (version is current and stable):
```bash
sudo apt install mpv
```

`yt-dlp` via official binary — **do not use apt**; the Ubuntu 24.04 apt package is months out of date and will fail on current YouTube:
```bash
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
  -o /usr/local/bin/yt-dlp
# Verify checksum
curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.sha256 | \
  sha256sum --check --ignore-missing
sudo chmod a+rx /usr/local/bin/yt-dlp
```

**Usage pattern:** `mpv <url>` — mpv calls yt-dlp internally to resolve the stream URL, then plays it directly. No browser, no intermediate download for streaming use.

**Rollback:** `sudo apt remove mpv` and `sudo rm /usr/local/bin/yt-dlp`.

---

### 5. Documentation Artifact

**What:** Add `streaming-guide.md` to `~/BrainLab-Networking/` (repo root on Thought-Reliquary) with practical usage examples for YouTube and anime streaming from the terminal.

**Covers:** basic playback, quality selection, audio-only mode, playlist streaming, useful mpv keybindings, and common anime streaming sources.

**Commit** to the BrainLab-Networking repo after writing.

---

## Implementation Steps

> **Important:** Complete steps 1–5 fully before proceeding to step 6. Step 6 terminates the current session. Do not log out mid-step.

1. Edit `/var/lib/AccountsService/users/johnny` — set `Session=xfce` (create if absent)
2. Create or edit `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml` — set `use_compositing` to `false` (see Cases A/B/C above)
3. Delete `~/.config/autostart/wayvnc.desktop`
4. Install mpv: `sudo apt install mpv`
5. Install yt-dlp binary to `/usr/local/bin/yt-dlp` (with checksum verification)
6. Log out of current session and log back in (XFCE session loads, x11vnc autostarts)
   - VNC reconnect: wait ~10 seconds after logout, then reconnect via Finder as normal
   - If VNC is not reachable after 30 seconds, SSH in (`ssh johnny@192.168.4.100`) to check x11vnc status: `systemctl --user status x11vnc` or `ps aux | grep x11vnc`
7. Write `~/BrainLab-Networking/streaming-guide.md` and commit to repo

## Success Criteria

- **Human verification:** Mac Mini reconnects via Finder VNC after session restart (Finder → Go → Connect to Server → `vnc://192.168.4.100`)
- Desktop is XFCE (visible in window decorations/taskbar style)
- Compositing is off (run from within XFCE session): `xfconf-query -c xfwm4 -p /general/use_compositing` returns `false`
- `mpv https://www.youtube.com/watch?v=<id>` plays video
- `streaming-guide.md` committed to BrainLab-Networking repo

## Rollback Summary

| Change | Rollback |
|--------|----------|
| Session switch to XFCE | Set `Session=gnome` in AccountsService file (or delete if newly created) |
| Compositor disabled | Set `use_compositing` value to `"true"` in xfwm4.xml |
| wayvnc autostart removed | Recreate `~/.config/autostart/wayvnc.desktop` with content listed in Section 3 |
| mpv installed | `sudo apt remove mpv` |
| yt-dlp installed | `sudo rm /usr/local/bin/yt-dlp` |
