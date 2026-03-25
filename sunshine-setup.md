# Sunshine Game Streaming Setup — HP Victus → Mac Mini (LG Ultrawide)

## Summary
Full end-to-end Sunshine/Moonlight game streaming setup on an HP Victus laptop (Windows 11)
streaming to a Mac Mini client at 3440x1440 via NVENC H.265.

---

## Hardware
| Device | Role |
|---|---|
| HP Victus (Windows 11) | Sunshine host |
| Mac Mini | Moonlight client |
| LG Ultrawide (3440x1440) | Display connected to Mac Mini |

### GPU Configuration (Victus)
- **AMD Radeon (integrated)** — drives internal laptop display (DISPLAY1, 1920x1080)
- **NVIDIA GeForce RTX 2050** — drives external HDMI output (DISPLAY6, 3440x1440)
- Mux-less hybrid GPU: all display outputs route through AMD internally, but the HDMI port
  is physically wired to the NVIDIA GPU — this is critical to the configuration

---

## Final Working Configuration

### Sunshine Install Path
```
E:\Sunshine\
```

### E:\Sunshine\config\sunshine.conf
```
adapter_name = NVIDIA GeForce RTX 2050
dd_configuration_option = ensure_active
dd_hdr_option = disabled
encoder = nvenc
hevc_mode = 2
resolutions = [1920x1080, 2560x1440, 3440x1440, 3840x2160]
fps = [30, 60, 90, 100, 120]
output_name = \\.\DISPLAY6
```

### Moonlight (Mac Mini)
- Resolution: **Native** (must be set to Native, not Auto)
- Fullscreen: **Enabled** (Cmd+Enter to toggle)

### Windows Display Settings
- LG Ultrawide (DISPLAY6) set as **primary display**
- Laptop screen (DISPLAY1) set as secondary
- HDR: **Off** on both displays

### Sunshine Service
- Installed as Windows service: `SunshineService`
- Start type: `AUTO_START` (runs on boot automatically)

---

## Troubleshooting Log

### Issue 1: Wrong installer architecture
- **Symptom:** "This app can't run on your PC"
- **Cause:** Downloaded ARM64 installer on x64 machine
- **Fix:** Download x64 (standard) installer from Sunshine releases

### Issue 2: NVENC failing at startup
- **Symptom:** `Encoder [nvenc] is not supported on this GPU`
- **Cause:** Sunshine was capturing DISPLAY1 (AMD), not the NVIDIA output — NVENC requires
  capture and encode on the same adapter
- **Fix:** Set `adapter_name = NVIDIA GeForce RTX 2050` and `output_name = \\.\DISPLAY6`

### Issue 3: Black bars on both sides (pillarboxing)
- **Symptom:** Stream displayed with black bars on left and right on the Mac Mini
- **Cause:** Moonlight resolution set to Auto/1080p instead of Native 3440x1440
- **Fix:** Set Moonlight resolution to **Native** in app settings

### Issue 4: Display resolution change failing (error 1610)
- **Symptom:** `Failed to change display modes` / error code 1610
- **Cause:** Sunshine trying to change the laptop's internal 1080p screen to 3440x1440
- **Fix:** Set `output_name` to point at the correct HDMI display, not the internal screen

### Issue 5: Display number shifting
- **Symptom:** DISPLAY7, DISPLAY8, DISPLAY9, DISPLAY11 — number changed every restart
- **Cause:** Virtual Display Driver (VDD) being installed/restarted reassigns display numbers
- **Fix:** Uninstall VDD (not needed with physical HDMI), use physical HDMI connection instead

### Issue 6: DISPLAY6 not visible to AMD adapter
- **Symptom:** `output_name = \\.\DISPLAY6` ignored, still capturing at 1920x1080
- **Cause:** DISPLAY6 (HDMI) is registered under the NVIDIA adapter, not AMD
- **Fix:** Set `adapter_name = NVIDIA GeForce RTX 2050` — dxgi-info.exe confirms which
  adapter each display is under

### Issue 7: Border around stream (all sides)
- **Symptom:** Correct aspect ratio but black border around entire image
- **Cause:** Moonlight not in fullscreen mode
- **Fix:** Press Cmd+Enter in Moonlight, or enable fullscreen in settings

### Issue 8: Moonlight shows Victus as offline after hardwiring Victus to network
- **Symptom:** Moonlight on Mac Mini reports Victus offline despite device being powered on
- **Cause:** Two separate issues:
  1. mDNS/multicast doesn't bridge between wired (192.168.5.x) and WiFi (192.168.4.x) subnets
  2. Windows assigned the new Ethernet connection as a **Public network**, which blocks all
     inbound connections by default — Sunshine's ports were silently dropped
- **Fix:**
  1. Set Moonlight manual address to `192.168.5.85` via plist:
     `defaults write com.moonlight-stream.Moonlight "hosts.1.manualaddress" "192.168.5.85"`
  2. On Victus: change Ethernet network profile from **Public → Private**
     (Settings → Network & Internet → Ethernet → toggle "Make this PC discoverable")
- **Note:** This only needs to be done once — Windows remembers the profile per network

---

## Virtual Display Driver (VDD) — Not Used in Final Config
Attempted installation of `itsmikethetech/Virtual-Display-Driver` v25.7.23 to create a
virtual 3440x1440 display for capture without a physical monitor. Abandoned in favor of
physical HDMI connection. Key findings:

- VDD installs correctly but the December 2024 driver has a bug:
  `Input buffer is too small for target modes` — virtual display initializes at 800x600
  regardless of vdd_settings.xml contents
- Settings file location: `C:\VirtualDisplayDriver\vdd_settings.xml`
- The VDD Control app communicates via named pipe for runtime config changes
- On mux-less hybrid GPU laptops, the VDD cannot attach to the NVIDIA GPU's display pipeline

---

## Key Diagnostic Tools
```powershell
# Check which adapter/output each display is under
& 'E:\Sunshine\tools\dxgi-info.exe'

# List active displays with resolution
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens | Select-Object DeviceName, Bounds, Primary

# Live Sunshine log monitoring
Get-Content 'E:\Sunshine\config\sunshine.log' -Wait | Select-String 'Capture size|CLIENT|Error'

# Restart Sunshine service (admin PowerShell)
Restart-Service SunshineService
```
