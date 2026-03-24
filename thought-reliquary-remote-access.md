# Thought-Reliquary Remote Access Setup

Machine: **Thought-Reliquary** (Ubuntu 24.04, `192.168.4.100`)

## What's Configured

### SSH
- Package: `openssh-server`
- Port: `22`
- Enabled and starts automatically on boot
- Connect: `ssh johnny@192.168.4.100`

### VNC (x11vnc)
- Package: `x11vnc`
- Port: `5900`
- Password stored at: `~/.vnc/passwd`
- Autostart: systemd user service at `~/.config/systemd/user/x11vnc.service`
- Linger enabled (`loginctl enable-linger johnny`) — survives session cycles
- Service survives SSH session close; restarts automatically if it crashes
- Requires X11 session (see note below)
- Connect from Mac: **TigerVNC** → `192.168.4.100` (no port suffix)

## VNC Client — Mac Mini
- **App:** TigerVNC (`brew install --cask tigervnc-viewer`)
- **Address:** `192.168.4.100` — no port suffix, no colon notation
- **Clipboard sync:** Works automatically — copy/paste flows both directions
- **Note:** macOS built-in Screen Sharing has weak clipboard support; TigerVNC is preferred
- **Note:** RealVNC Connect now requires an account/subscription — avoid

## Important: X11 Required
Wayland is disabled on this machine so x11vnc works correctly.
Setting: `/etc/gdm3/custom.conf` → `WaylandEnable=false`

## Important: GNOME is the Correct Session
XFCE was installed during xrdp testing and may appear as a session option at GDM.
Always select **Ubuntu (GNOME)** at login — not XFCE.

### If XFCE Loads by Mistake
1. Open terminal in XFCE
2. Run: `xfce4-session-logout --logout`
3. At GDM login screen: click username → gear icon (bottom right) → select **Ubuntu**
4. Log in normally

### Setting GNOME as Default via Command Line
```bash
sudo bash -c 'echo "[Desktop]\nSession=gnome" > /var/lib/AccountsService/users/johnny'
sudo reboot
```

## x11vnc After Session Switch
x11vnc runs as a systemd user service and restarts automatically. If VNC is unreachable
after a session switch, SSH in and restart the service:
```bash
systemctl --user restart x11vnc.service
systemctl --user status x11vnc.service
```

## Firewall Rules
```
22/tcp   - SSH
5900/tcp - VNC
```

Full UFW status confirmed active with all rules above (IPv4 + IPv6).

## Packages Installed
- `openssh-server` — SSH server
- `x11vnc` — VNC server for X11
- `fail2ban` — SSH brute-force protection
- `xrdp` + `xorgxrdp` — RDP server (installed but disabled; VNC preferred)
- `xfce4` + `xfce4-goodies` — Lightweight desktop (used during xrdp testing; not default session)
- `dbus-x11` — D-Bus X11 support
- `gh` — GitHub CLI

## System Optimizations
- **fail2ban** — running, SSH jail active, starts on boot
- **xrdp** — disabled and stopped; port 3389 closed in firewall
- **vm.swappiness** — set to 10 (from 60) via `/etc/sysctl.d/99-swappiness.conf`; better for 15GB RAM machine
- **ModemManager** — disabled (not needed on desktop)
- **iio-sensor-proxy** — stopped (not needed on desktop, static unit)
  - Note: disabling this (along with Wayland) means auto screen-rotation is unavailable in tablet mode
  - Use `flip` / `unflip` aliases in `~/.bashrc` to manually rotate 180° via xrandr

## Tablet Mode (2-in-1)
This machine is a 2-in-1 tablet/laptop. When used in tablet mode (screen flipped), the display appears upside down because:
1. Wayland is disabled (required for x11vnc) — GNOME auto-rotate only works on Wayland
2. iio-sensor-proxy is disabled — the accelerometer service is not running

**Workaround — manual rotation aliases in `~/.bashrc`:**
```bash
alias flip='xrandr --output $(xrandr | grep " connected" | awk "{print \$1}") --rotate normal'
alias unflip='xrandr --output $(xrandr | grep " connected" | awk "{print \$1}") --rotate inverted'
```
- `unflip` — restore normal orientation (uses xrandr `inverted` — panel is physically mounted upside down in chassis)
- `flip` — rotate for tablet mode (uses xrandr `normal`)

**Note:** The display panel is physically mounted inverted in this chassis. xrandr `inverted` = visually correct. xrandr `normal` = visually upside down.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| TigerVNC "Connection refused" | x11vnc not running | `ssh johnny@192.168.4.100` → `systemctl --user restart x11vnc` |
| TigerVNC "No route to host" | Two VNC clients open simultaneously | Close macOS Screen Sharing before connecting TigerVNC |
| Boots into XFCE | XFCE became default session | Logout → choose Ubuntu at GDM gear icon |
| No gear icon at GDM | Click username first | Gear appears after clicking username, before password |

## Notes
- wayvnc was attempted but GNOME's Wayland compositor doesn't expose the screencopy protocol
- GNOME Remote Desktop (RDP) was attempted but credential storage via keyring was unreliable
- x11vnc on X11 is the stable solution for this machine
- xrdp remains installed but is disabled; remove with `sudo apt remove xrdp xorgxrdp` if no longer needed
