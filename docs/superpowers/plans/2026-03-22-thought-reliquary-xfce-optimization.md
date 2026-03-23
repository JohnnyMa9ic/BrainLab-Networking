# Thought-Reliquary XFCE Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch Thought-Reliquary from GNOME to XFCE session, disable compositor, remove broken wayvnc autostart, install yt-dlp + mpv, and commit a streaming reference guide.

**Architecture:** All changes are pre-session file edits and package installs, followed by a single logout/login to activate the new XFCE session. The x11vnc VNC pathway (autostart, password, port, firewall) is untouched throughout.

**Tech Stack:** Ubuntu 24.04, XFCE 4.18 (already installed), mpv (apt), yt-dlp (official binary), BrainLab-Networking git repo at `~/BrainLab-Networking`

**Spec:** `docs/superpowers/specs/2026-03-22-thought-reliquary-xfce-optimization-design.md`

---

## Pre-flight Checks

Before starting, verify nothing has changed since the spec was written:

- [ ] Confirm XFCE packages are installed:
  ```bash
  dpkg -l xfce4 xfce4-session xfce4-goodies | grep ^ii
  ```
  Expected: all three show `ii` status.

- [ ] Confirm x11vnc autostart is intact (do not modify, just verify):
  ```bash
  cat ~/.config/autostart/x11vnc.desktop
  ```
  Expected: file exists and contains `Exec=x11vnc`.

- [ ] Confirm wayvnc autostart exists (will be deleted in Task 3):
  ```bash
  cat ~/.config/autostart/wayvnc.desktop
  ```
  Expected: file exists.

---

## Task 1: Switch Default GDM Session to XFCE

**Files:**
- Create: `/var/lib/AccountsService/users/johnny` (requires sudo)

This file does not currently exist. Creating it tells GDM which desktop session to launch for the `johnny` user.

- [ ] **Step 1: Create the AccountsService user file**

  ```bash
  sudo tee /var/lib/AccountsService/users/johnny > /dev/null << 'EOF'
  [User]
  Session=xfce
  SystemAccount=false
  EOF
  ```

- [ ] **Step 2: Verify the file was written correctly**

  ```bash
  sudo cat /var/lib/AccountsService/users/johnny
  ```
  Expected output:
  ```
  [User]
  Session=xfce
  SystemAccount=false
  ```

- [ ] **Step 3: Set correct permissions**

  ```bash
  sudo chmod 644 /var/lib/AccountsService/users/johnny
  sudo chown root:root /var/lib/AccountsService/users/johnny
  ```

---

## Task 2: Disable XFCE Compositor (Pre-session)

**Files:**
- Create: `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml`

The file does not currently exist on this machine. Creating it before the first XFCE login ensures compositing is off from the start, without needing a live XFCE session.

> If the file already exists (e.g. from a prior XFCE session): find the `use_compositing` property and set `value="false"`. If the property is missing from an existing file, add `<property name="use_compositing" type="bool" value="false"/>` inside the `<property name="general">` block.

- [ ] **Step 1: Create the xfce4 config directory**

  ```bash
  mkdir -p ~/.config/xfce4/xfconf/xfce-perchannel-xml
  ```

- [ ] **Step 2: Write the xfwm4 config with compositing disabled**

  ```bash
  tee ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml > /dev/null << 'EOF'
  <?xml version="1.0" encoding="UTF-8"?>
  <channel name="xfwm4" version="1.0">
    <property name="general" type="empty">
      <property name="use_compositing" type="bool" value="false"/>
    </property>
  </channel>
  EOF
  ```

- [ ] **Step 3: Verify the file content**

  ```bash
  cat ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
  ```
  Expected: XML as written above, with `value="false"` on the `use_compositing` line.

---

## Task 3: Remove wayvnc Autostart

**Files:**
- Delete: `~/.config/autostart/wayvnc.desktop`

wayvnc fails silently on every login because Wayland is disabled. Removing the autostart entry cleans the boot sequence.

- [ ] **Step 1: Delete the autostart file**

  ```bash
  rm ~/.config/autostart/wayvnc.desktop
  ```

- [ ] **Step 2: Verify it's gone**

  ```bash
  ls ~/.config/autostart/
  ```
  Expected: `wayvnc.desktop` is no longer listed. `x11vnc.desktop` must still be present.

---

## Task 4: Install mpv

**Files:** system packages only

- [ ] **Step 1: Install mpv**

  ```bash
  sudo apt install -y mpv
  ```

- [ ] **Step 2: Verify installation**

  ```bash
  mpv --version
  ```
  Expected: version string starting with `mpv`.

---

## Task 5: Install yt-dlp (Official Binary)

**Files:**
- Create: `/usr/local/bin/yt-dlp`

Do not use `apt install yt-dlp` — the Ubuntu 24.04 repo version is stale and will fail on current YouTube.

- [ ] **Step 1: Download the official binary**

  ```bash
  sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp
  ```

- [ ] **Step 2: Verify checksum**

  ```bash
  cd /usr/local/bin && curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.sha256 | \
    sha256sum --check --ignore-missing
  ```
  Expected output: `yt-dlp: OK`

- [ ] **Step 3: Make executable**

  ```bash
  sudo chmod a+rx /usr/local/bin/yt-dlp
  ```

- [ ] **Step 4: Verify installation**

  ```bash
  yt-dlp --version
  ```
  Expected: a version string (e.g. `2026.01.xx`).

---

## Task 6: Write Streaming Reference Guide

**Files:**
- Create: `~/BrainLab-Networking/streaming-guide.md`

- [ ] **Step 1: Write the streaming guide**

  ```bash
  tee ~/BrainLab-Networking/streaming-guide.md > /dev/null << 'GUIDE'
  # Streaming Guide — Thought-Reliquary

  Play YouTube videos and anime streams directly from the terminal using `mpv` + `yt-dlp`.
  No browser required. mpv calls yt-dlp internally to resolve stream URLs.

  ---

  ## Basic Playback

  ```bash
  # Play a YouTube video
  mpv "https://www.youtube.com/watch?v=VIDEO_ID"

  # Play by full URL
  mpv "https://youtu.be/VIDEO_ID"
  ```

  ---

  ## Quality Selection

  ```bash
  # Best quality (default)
  mpv "URL"

  # Specific resolution
  mpv --ytdl-format="bestvideo[height<=1080]+bestaudio/best[height<=1080]" "URL"
  mpv --ytdl-format="bestvideo[height<=720]+bestaudio/best[height<=720]" "URL"
  mpv --ytdl-format="bestvideo[height<=480]+bestaudio/best[height<=480]" "URL"

  # Worst quality (lowest bandwidth)
  mpv --ytdl-format=worst "URL"
  ```

  ---

  ## Audio Only

  ```bash
  # Audio only (no video window)
  mpv --no-video "URL"

  # Download audio only with yt-dlp
  yt-dlp -x --audio-format mp3 "URL"
  ```

  ---

  ## Playlists

  ```bash
  # Play full YouTube playlist
  mpv "https://www.youtube.com/playlist?list=PLAYLIST_ID"

  # Start from a specific position in playlist
  mpv --playlist-start=5 "https://www.youtube.com/playlist?list=PLAYLIST_ID"

  # Shuffle playlist
  mpv --shuffle "https://www.youtube.com/playlist?list=PLAYLIST_ID"
  ```

  ---

  ## Anime Streaming

  yt-dlp supports 1000+ sites. Common anime sources:

  ```bash
  # Crunchyroll
  mpv "https://www.crunchyroll.com/watch/EPISODE_ID"

  # 9anime / similar sites
  mpv "https://9anime.to/watch/SHOW.ID/EPISODE"

  # Direct stream URL (m3u8)
  mpv "https://example.com/stream.m3u8"

  # List available formats before playing
  yt-dlp -F "URL"

  # Play a specific format by ID
  yt-dlp -f FORMAT_ID "URL"
  ```

  ---

  ## Useful mpv Keyboard Shortcuts

  | Key | Action |
  |-----|--------|
  | `Space` | Pause / Resume |
  | `←` / `→` | Seek 5 seconds back / forward |
  | `↑` / `↓` | Seek 1 minute forward / back |
  | `f` | Toggle fullscreen |
  | `q` | Quit |
  | `m` | Mute |
  | `9` / `0` | Volume down / up |
  | `s` | Screenshot |
  | `i` | Show stream info overlay |
  | `Shift+Left/Right` | Previous / next chapter |

  ---

  ## Update yt-dlp

  YouTube frequently changes its API. Keep yt-dlp current:

  ```bash
  sudo yt-dlp -U
  ```

  Or reinstall the binary:

  ```bash
  sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp && sudo chmod a+rx /usr/local/bin/yt-dlp
  ```

  ---

  ## Troubleshooting

  | Symptom | Fix |
  |---------|-----|
  | `ERROR: Unsupported URL` | Site may not be supported; try `yt-dlp -F "URL"` to check |
  | `HTTP Error 429` | Rate limited; wait and retry |
  | Video plays with no audio | Try `--ytdl-format=bestvideo+bestaudio` |
  | Buffering / slow stream | Lower quality: `--ytdl-format=worst` |
  | `yt-dlp: command not found` | Re-run install: `sudo curl -L ... -o /usr/local/bin/yt-dlp` |
  | YouTube login required | Use cookies: `--cookies-from-browser firefox` |
  GUIDE
  ```

- [ ] **Step 2: Verify the file was written**

  ```bash
  head -5 ~/BrainLab-Networking/streaming-guide.md
  ```
  Expected: first 5 lines of the guide.

- [ ] **Step 3: Commit all changes to BrainLab-Networking**

  ```bash
  cd ~/BrainLab-Networking
  git add streaming-guide.md
  git commit -m "$(cat <<'EOF'
  Add streaming guide and XFCE optimization spec

  yt-dlp + mpv reference for YouTube and anime streaming from terminal
  on Thought-Reliquary.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 7: Activate XFCE Session

> **Warning:** This step terminates the current desktop session. Complete Tasks 1–7 fully before proceeding. After logout, reconnect from Mac Mini via Finder → Go → Connect to Server → `vnc://192.168.4.100`.

- [ ] **Step 1: Log out of the current session**

  From the terminal (safest method):
  ```bash
  gnome-session-quit --logout --no-prompt
  ```
  Or via the GNOME system menu → Log Out.

- [ ] **Step 2: Reconnect from Mac Mini**

  On the Mac Mini: Finder → Go → Connect to Server → `vnc://192.168.4.100` → Connect.
  Wait ~10–15 seconds after logout before attempting reconnect.

- [ ] **Step 3: If VNC is not reachable after 30 seconds**

  SSH in from Mac Mini to diagnose:
  ```bash
  ssh johnny@192.168.4.100
  ps aux | grep x11vnc
  ```
  If x11vnc is not running, start it manually:
  ```bash
  x11vnc -display :0 -rfbauth ~/.vnc/passwd -forever -loop -noxdamage \
    -repeat -rfbport 5900 -shared -bg -o /tmp/x11vnc.log
  ```

---

## Task 8: Post-login Verification

Run these checks after reconnecting via VNC in the new XFCE session.

- [ ] **Step 1: Confirm XFCE is the active session**

  The desktop should show XFCE window decorations and a panel/taskbar. Or check via terminal:
  ```bash
  echo $XDG_CURRENT_DESKTOP
  ```
  Expected: `XFCE`

- [ ] **Step 2: Confirm compositor is off**

  ```bash
  xfconf-query -c xfwm4 -p /general/use_compositing
  ```
  Expected: `false`

- [ ] **Step 3: Test mpv with a YouTube URL**

  ```bash
  mpv "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  ```
  Expected: video plays. Press `q` to quit.

- [ ] **Step 4: Confirm yt-dlp is current**

  ```bash
  yt-dlp --version
  ```
  Expected: version string printed without error.

- [ ] **Step 5: Confirm x11vnc is running**

  ```bash
  ps aux | grep x11vnc | grep -v grep
  ```
  Expected: x11vnc process listed on port 5900.

---

## Rollback

If anything goes wrong, revert each change individually:

| Change | Rollback Command |
|--------|-----------------|
| Session switch | `sudo sed -i 's/Session=xfce/Session=gnome/' /var/lib/AccountsService/users/johnny` |
| Compositor config | `rm ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml` |
| wayvnc autostart | Recreate `~/.config/autostart/wayvnc.desktop` (content in spec Section 3) |
| mpv | `sudo apt remove mpv` |
| yt-dlp | `sudo rm /usr/local/bin/yt-dlp` |
