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
x11vnc autostart fires on GNOME login. If VNC is unreachable after a session switch,
SSH in and start it manually:
```bash
x11vnc -display :0 -auth guess -forever -rfbauth ~/.vnc/passwd -rfbport 5900 -shared &
```

## Firewall Rules
```
22/tcp   - SSH
5900/tcp - VNC
3389/tcp - RDP (xrdp installed but VNC preferred)
```

Full UFW status confirmed active with all rules above (IPv4 + IPv6).

## Packages Installed
- `openssh-server` — SSH server
- `x11vnc` — VNC server for X11
- `xrdp` + `xorgxrdp` — RDP server (fallback, not primary)
- `xfce4` + `xfce4-goodies` — Lightweight desktop (used during xrdp testing; not default session)
- `dbus-x11` — D-Bus X11 support
- `gh` — GitHub CLI

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| TigerVNC "Connection refused" | x11vnc not running | SSH in, start x11vnc manually |
| TigerVNC "No route to host" | Two VNC clients open simultaneously | Close macOS Screen Sharing before connecting TigerVNC |
| Boots into XFCE | XFCE became default session | Logout → choose Ubuntu at GDM gear icon |
| No gear icon at GDM | Click username first | Gear appears after clicking username, before password |

## Notes
- wayvnc was attempted but GNOME's Wayland compositor doesn't expose the screencopy protocol
- GNOME Remote Desktop (RDP) was attempted but credential storage via keyring was unreliable
- x11vnc on X11 is the stable solution for this machine
