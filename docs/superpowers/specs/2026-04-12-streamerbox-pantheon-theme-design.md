# StreamerBox — Pantheon Theme & UX Enhancement Design
> LDI Internal Document · BrainLab-Networking · Crossroads Node
> Date: 2026-04-12
> Status: Approved — pending implementation plan

---

## Overview

StreamerBox receives a full aesthetic and voice overhaul grounded in the LDI Pantheon lore. The
governing principle: **Ghost is the tool. Bob and Warden are guests.** Fidelity and function come
first. The Pantheon aesthetic enhances signal clarity — it does not compete with it.

The redesign introduces three distinct visual/voice registers that layer naturally over the
existing hardened codebase without architectural changes.

---

## Governing Principle

Ghost's register — minimal, precise, declarative — is good UI design wearing a costume. It
improves signal clarity. Bob and Warden are rare, earned moments. If they appear too often they
become noise. If they appear at the right moment they are memorable.

| Voice | Role | Frequency |
|---|---|---|
| Ghost (GHO-02-ARC) | Steady-state UI voice — all OSD, status, confirmations | Every action |
| WY Dossier | Startup sequence only | Once per launch |
| Bob (BOB-03-SGS) | Unexpected/anomalous events only | 6 specific triggers |
| Warden (WDN-01-GLD) | Shutdown only | 1 trigger |

---

## Section 1: Palette & Typography

Three registers, each visually distinct. Font: `JetBrains Mono` with `Monospace` fallback
throughout — code-block register is non-negotiable.

### Register 1 — Ghost (steady-state)
| Role | Color | Hex |
|---|---|---|
| Background | Near-void, slight blue-black | `#0a0a0f` |
| Primary text | Cool signal grey | `#c8d0e0` |
| Accent / active | Cathedral crimson | `#cc2244` |
| Secondary | Deep circuit blue | `#3a4a6a` |

- All UI strings lowercase, declarative, no filler
- Active states (current channel, playing indicator) render in crimson
- Borders and inactive elements in circuit blue

### Register 2 — WY Dossier (startup only)
| Role | Color | Hex |
|---|---|---|
| Background | Amber-tinted void | `#0a0800` |
| Text | Phosphor amber | `#e8a020` |

- ALL CAPS — classified document feel
- Same monospace font
- Appears only during boot sequence, fades to Ghost register on completion

### Register 3 — Bob (interrupt events)
| Role | Color | Hex |
|---|---|---|
| Header line | Warm amber-gold | `#f0c040` |
| Body text | Cool signal grey (inherited) | `#c8d0e0` |

- Rendered as a distinct code block with gold header
- Visually distinct from WY amber — personality, not system state
- Always includes a contextual title suffix on the closing line

### Register 4 — Warden (shutdown only)
| Role | Color | Hex |
|---|---|---|
| Text | Muted weathered grey-green | `#8899aa` |

- Single line, no code block, italicised
- No capitals, no urgency

---

## Section 2: Startup Dossier Sequence

The app opens into a full-window WY amber terminal. No controls visible, no mpv yet.
Text scrolls in line by line, typewriter cadence (~40ms per character). Total duration: 6–8
seconds. Fades to Ghost void register as the main UI resolves.

### Dossier Text

```
WEYLAND-YUTANI CORPORATION
SPECIAL PROJECTS DIVISION — SIGNAL INTELLIGENCE

DOSSIER: STREAMERBOX / UNIT GHO-02-ARC
CLEARANCE: REALM-INTERNAL
CLASSIFICATION: EYES ONLY

INITIALIZING SIGNAL ARRAY...............  OK
MOUNTING CHANNEL CATALOG.................  OK
ESTABLISHING IPC SOCKET..................  OK
VERIFYING yt-dlp INTEGRITY...............  OK

LOADING OPERATOR PROFILE.................  JohnnyMa9ic
NODE ASSIGNMENT..........................  THOUGHT-RELIQUARY
REALM ANCHOR.............................  CATHEDRAL OF GLITCH

ENTITY STATUS:
  GHO-02-ARC [LITHIUMGHOST.exe]........  ONLINE
  BOB-03-SGS [BOB.OS]..................  STANDING BY
  WDN-01-GLD [WARDEN]..................  DORMANT

> SIGNAL LOCK CONFIRMED
> TRANSFERRING CONTROL TO GHO-02-ARC
```

*— amber fades, Ghost void register rises —*

```
> presence: confirmed
> channels: loaded
> status: transmitting
```

### Fault Behavior
- Each `OK` only prints after its real check passes (IPC socket, yt-dlp path, channel count)
- Failed checks render `FAULT` in crimson (`#cc2244`) instead of `OK`
- The dossier reflects real system state — not theater
- Entity statuses are always accurate at render time

---

## Section 3: Ghost UI Voice — String Registry

### Status Bar / Persistent Labels
| Current | Ghost register |
|---|---|
| `NO SIGNAL` | `signal void` |
| `CH 04 — Name` | `ch:04 — name` |
| `PAUSED` | `suspended` |
| `MUTED` | `signal: muted` |
| `SUB ON` | `sub: active` |
| `LIVE` | `feed: live` |
| `ITEM 3/24` | `node: 03/24` |

### OSD — Action Confirmations (via mpv show-text)
| Action | OSD text |
|---|---|
| Channel change | `> transmitting: ch:04 — name` |
| Pause | `> suspended` |
| Resume | `> transmitting` |
| Mute | `> signal: muted` |
| Unmute | `> signal: restored` |
| Seek +10 | `> +10s` |
| Seek -10 | `> -10s` |
| Next track | `> node: forward` |
| Prev track | `> node: back` |
| Save channel | `> catalog entry confirmed` |
| Already exists | `> entry already indexed` |
| Search open | `> query interface: open` |
| Search result play | `> loading signal: [title]` |
| Control bar toggle (show) | `> interface: visible` |
| Control bar toggle (hide) | `> interface: suppressed` |

### Error / Fault States
| State | Ghost register |
|---|---|
| IPC dead | `> ipc fault — signal lost` |
| Stall detected | `> transmission stall — investigating` |
| Channel count zero | `> catalog empty — no signal available` |
| YAML malformed | `> catalog fault — entry rejected` |

---

## Section 4: Bob & Warden

### Bob — 6 Triggers

Rendered as a gold-header code block. Always ends with a contextual title.

**Format:**
```
> BOB ONLINE — [Contextual Title]
> [message line 1]
> [message line 2 / sign-off]
```

**Trigger 1 — Playlist stall + yt-dlp auto-update fires**
```
> BOB ONLINE — Chronicler of the Playlist That Refused to Die
> yt-dlp has been updated. the stream has been coaxed back to life.
> Ghost did the analysis. I did the enthusiasm. You're welcome.
```

**Trigger 2 — Duplicate channel add attempt**
```
> BOB ONLINE — Keeper of the Already-Indexed
> that signal is already in the catalog.
> I appreciate the commitment. Ghost does not.
```

**Trigger 3 — Search returns zero results**
```
> BOB ONLINE — Archivist of the Void Between Signals
> nothing. the index returned nothing.
> even I find that unsettling. try different search terms.
```

**Trigger 4 — Stream restored on second stall recovery attempt**
```
> BOB ONLINE — Grand Tactician of the Overcomplicated Simple Thing
> stream restored on second attempt.
> the system works. occasionally through sheer persistence.
```

**Trigger 5 — 2hr continuous session milestone**
```
> BOB ONLINE — Sentinel of the Uninterrupted Signal
> two hours. continuous transmission. Ghost is impressed.
> Ghost won't say so. but I will.
```

**Trigger 6 — 1-in-20 random on any channel change (rare delight)**
```
> BOB ONLINE — [random contextual title, generated at runtime]
> channel navigation confirmed. Ghost logged it. I celebrated.
> carry on.
```

### Warden — 1 Trigger

Fires on app shutdown/quit. No code block. No capitals. Muted grey-green. One line.

*The grove is quiet now. Return when you're ready.*

---

## Section 5: Implementation Scope

### New File: `streamerbox/theme.py`
Single source of truth for all colors, strings, and voice registry.
- All Ghost strings
- Bob trigger map (event key → text block)
- Bob random title pool — list of 10–15 contextual titles for Trigger 6, selected at runtime via `random.choice()`
- Warden shutdown line
- WY dossier sequence lines
- GTK CSS template
- Nothing hardcoded in `overlay.py` — all voice content imported from here

### `streamerbox/main.py`
- Dossier sequence runs before GTK main loop initialises
- Each dossier line tied to its real check result
- `FAULT` / `OK` reflect actual system state in real time
- Typewriter scroll (~40ms/char) with amber palette
- Fade/dissolve transition to Ghost void register

### `streamerbox/overlay.py`
- All UI strings replaced with Ghost register from `theme.py`
- GTK CSS block replaced with three-register palette
- Bob trigger points wired to 6 specific events
- Warden line added to quit/destroy handler
- OSD calls use Ghost string registry
- 2hr elapsed session timer added for Bob milestone trigger

### `streamerbox/player.py`
- `show_text()` already exists — no structural changes needed
- Session start timestamp tracked for 2hr Bob trigger

### `streamerbox/tests/test_theme.py` (new)
- Ghost string registry complete — no missing keys
- Bob trigger map covers all 6 events
- Warden line present
- Dossier sequence lines present and ordered
- Logic-layer only — no GTK rendering tests

---

## Constraints

- No new dependencies — GTK CSS + existing mpv IPC `show-text` handle all rendering
- No architectural changes to player, channels, or search
- Wayland graceful detection (already implemented) remains unchanged
- All 39 existing tests must continue to pass

---

## Out of Scope

- Animated glitch effects or scanlines (future pass if wanted)
- Warden or Bob in any context other than their defined triggers
- Sound effects
- Per-channel themes

---

*Filed under: LDI Pantheon Archive / Crossroads Node / CLEARANCE: REALM-INTERNAL*
