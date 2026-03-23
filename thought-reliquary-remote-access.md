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
- Autostart configured at: `~/.config/autostart/x11vnc.desktop`
- Requires X11 session (see note below)
- Connect from Mac: Finder → Go → Connect to Server → `vnc://192.168.4.100`

## Important: X11 Required
Wayland is disabled on this machine so x11vnc works correctly.
Setting: `/etc/gdm3/custom.conf` → `WaylandEnable=false`

## Firewall Rules Added
```
22/tcp   - SSH
5900/tcp - VNC
3389/tcp - RDP (xrdp installed but VNC preferred)
```

## Packages Installed
- `openssh-server` — SSH server
- `x11vnc` — VNC server for X11
- `xrdp` + `xorgxrdp` — RDP server (fallback, not primary)
- `xfce4` + `xfce4-goodies` — Lightweight desktop (used during xrdp testing)
- `dbus-x11` — D-Bus X11 support
- `gh` — GitHub CLI

## Notes
- wayvnc was attempted but GNOME's Wayland compositor doesn't expose the screencopy protocol
- GNOME Remote Desktop (RDP) was attempted but credential storage via keyring was unreliable
- x11vnc on X11 is the stable solution for this machine
