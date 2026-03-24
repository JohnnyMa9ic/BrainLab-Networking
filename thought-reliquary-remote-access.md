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

## Important: Display is :1 (not :0)
On Ubuntu 24 with GDM, the GNOME user session runs on **display :1**.
GDM claims `:0` for its own greeter. Always use `-display :1` with x11vnc.

Confirm with: `ls /tmp/.X11-unix/` — should show `X1`

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

## Autostart File
Location: `~/.config/autostart/x11vnc.desktop`

```ini
[Desktop Entry]
Type=Application
Name=x11vnc
Exec=x11vnc -display :1 -auth /run/user/1000/gdm/Xauthority -rfbauth /home/johnny/.vnc/passwd -forever -loop -noxdamage -repeat -rfbport 5900 -shared
StartupNotify=false
Terminal=false
Hidden=false
```

## Manual Start (if VNC is unreachable after login)
SSH in and run:
```bash
x11vnc -display :1 -auth /run/user/1000/gdm/Xauthority -forever -rfbauth ~/.vnc/passwd -rfbport 5900 -shared &
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
| TigerVNC "Connection refused" | x11vnc not running | SSH in, run manual start command above |
| x11vnc `XOpenDisplay failed (:0)` | Wrong display — GDM uses :0, GNOME uses :1 | Use `-display :1` |
| x11vnc `XOpenDisplay failed (:1)` | Wrong auth file | Use `-auth /run/user/1000/gdm/Xauthority` |
| TigerVNC "No route to host" | Two VNC clients open simultaneously | Close macOS Screen Sharing before connecting TigerVNC |
| Boots into XFCE | XFCE became default session | Logout → choose Ubuntu at GDM gear icon |
| No gear icon at GDM | Click username first | Gear appears after clicking username, before password |

## Notes
- wayvnc was attempted but GNOME's Wayland compositor doesn't expose the screencopy protocol
- GNOME Remote Desktop (RDP) was attempted but credential storage via keyring was unreliable
- x11vnc on X11 is the stable solution for this machine
