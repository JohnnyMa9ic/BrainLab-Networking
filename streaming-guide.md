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
