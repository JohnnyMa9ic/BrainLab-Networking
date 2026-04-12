# streamerbox/theme.py
"""
StreamerBox Pantheon Voice Registry
Single source of truth for all colors, strings, and voice content.

Registers:
  GHOST  — steady-state UI voice (every action)
  BOB    — anomalous/unexpected events (6 triggers)
  WARDEN — shutdown only (1 trigger)
  DOSSIER_LINES — WY amber startup sequence
  COLORS — palette constants
"""
import random

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
COLORS = {
    # Ghost register
    "void":        "#0a0a0f",
    "signal":      "#c8d0e0",
    "crimson":     "#cc2244",
    "circuit":     "#3a4a6a",
    # WY Dossier register
    "amber_void":  "#0a0800",
    "amber":       "#e8a020",
    # Bob register
    "bob_gold":    "#f0c040",
    # Warden register
    "warden_mist": "#8899aa",
}

# ---------------------------------------------------------------------------
# Ghost — steady-state UI strings
# ---------------------------------------------------------------------------
GHOST = {
    "now_playing_idle":      "signal void",
    "paused":                "suspended",
    "muted":                 "signal: muted",
    "sub_active":            "sub: active",
    "feed_live":             "feed: live",
    "interface_visible":     "> interface: visible",
    "interface_suppressed":  "> interface: suppressed",
    "osd_pause":             "> suspended",
    "osd_resume":            "> transmitting",
    "osd_muted":             "> signal: muted",
    "osd_unmuted":           "> signal: restored",
    "osd_seek_fwd":          "> +10s",
    "osd_seek_back":         "> -10s",
    "osd_node_fwd":          "> node: forward",
    "osd_node_back":         "> node: back",
    "osd_catalog_confirmed": "> catalog entry confirmed",
    "osd_already_indexed":   "> entry already indexed",
    "osd_query_open":        "> query interface: open",
    "osd_ipc_fault":         "> ipc fault — signal lost",
    "osd_stall":             "> transmission stall — investigating",
    "osd_catalog_empty":     "> catalog empty — no signal available",
    "osd_catalog_fault":     "> catalog fault — entry rejected",
}

def ghost_channel(idx: int, name: str) -> str:
    return f"> transmitting: ch:{idx:02d} — {name.lower()}"

def ghost_search_play(title: str) -> str:
    return f"> loading signal: {title.lower()}"

def ghost_node_status(pos: int, count: int) -> str:
    return f"node: {pos:02d}/{count:02d}"

# ---------------------------------------------------------------------------
# Bob — anomalous event quips
# ---------------------------------------------------------------------------
BOB_TITLES = [
    "Chronicler of the Channel Nobody Asked For",
    "Keeper of the Perfectly Timed Interruption",
    "Grand Archivist of the Signal Between Signals",
    "Annotator of the Uneventful Navigation Event",
    "Theoretical Cartographer of the Void",
    "Surveyor of the Transition Nobody Noticed",
    "Chief Inspector of the Unremarkable Frequency",
    "Etymologist of the Ghost's Silence",
    "Historian of the Moment Just Before This One",
    "Keeper of the Index Entry That Did Not Need Keeping",
    "Scribe of the Perfectly Routine Anomaly",
    "Librarian of the Catalog Entry Ghost Already Knew About",
    "Navigator of the Familiar Unfamiliar",
    "Chronicler of Things That Went Exactly as Expected",
    "Warden of the Moment Ghost Refused to Comment On",
]

BOB = {
    "stall_recovery": [
        "BOB ONLINE — Chronicler of the Playlist That Refused to Die",
        "yt-dlp has been updated. the stream has been coaxed back to life.",
        "Ghost did the analysis. I did the enthusiasm. You're welcome.",
    ],
    "duplicate_add": [
        "BOB ONLINE — Keeper of the Already-Indexed",
        "that signal is already in the catalog.",
        "I appreciate the commitment. Ghost does not.",
    ],
    "zero_results": [
        "BOB ONLINE — Archivist of the Void Between Signals",
        "nothing. the index returned nothing.",
        "even I find that unsettling. try different search terms.",
    ],
    "second_attempt": [
        "BOB ONLINE — Grand Tactician of the Overcomplicated Simple Thing",
        "stream restored on second attempt.",
        "the system works. occasionally through sheer persistence.",
    ],
    "session_milestone": [
        "BOB ONLINE — Sentinel of the Uninterrupted Signal",
        "two hours. continuous transmission. Ghost is impressed.",
        "Ghost won't say so. but I will.",
    ],
    "random_nav": [
        None,  # title injected at runtime via bob_random_title()
        "channel navigation confirmed. Ghost logged it. I celebrated.",
        "carry on.",
    ],
}

def bob_random_title() -> str:
    return f"BOB ONLINE — {random.choice(BOB_TITLES)}"

# ---------------------------------------------------------------------------
# Warden — shutdown only
# ---------------------------------------------------------------------------
WARDEN_SHUTDOWN = "The grove is quiet now. Return when you're ready."

# ---------------------------------------------------------------------------
# WY Dossier startup sequence
# ---------------------------------------------------------------------------
DOSSIER_LINES = [
    {"text": "WEYLAND-YUTANI CORPORATION",                                    "check": None},
    {"text": "SPECIAL PROJECTS DIVISION \u2014 SIGNAL INTELLIGENCE",          "check": None},
    {"text": "",                                                               "check": None},
    {"text": "DOSSIER: STREAMERBOX / UNIT GHO-02-ARC",                        "check": None},
    {"text": "CLEARANCE: REALM-INTERNAL",                                      "check": None},
    {"text": "CLASSIFICATION: EYES ONLY",                                      "check": None},
    {"text": "",                                                               "check": None},
    {"text": "INITIALIZING SIGNAL ARRAY...............  OK",                  "check": None},
    {"text": "MOUNTING CHANNEL CATALOG.................",                       "check": "channels"},
    {"text": "ESTABLISHING IPC SOCKET..................",                       "check": "ipc"},
    {"text": "VERIFYING yt-dlp INTEGRITY...............",                      "check": "yt_dlp"},
    {"text": "",                                                               "check": None},
    {"text": "LOADING OPERATOR PROFILE.................  JohnnyMa9ic",        "check": None},
    {"text": "NODE ASSIGNMENT..........................  THOUGHT-RELIQUARY",   "check": None},
    {"text": "REALM ANCHOR.............................  CATHEDRAL OF GLITCH", "check": None},
    {"text": "",                                                               "check": None},
    {"text": "ENTITY STATUS:",                                                 "check": None},
    {"text": "  GHO-02-ARC [LITHIUMGHOST.exe]........  ONLINE",               "check": None},
    {"text": "  BOB-03-SGS [BOB.OS]..................  STANDING BY",           "check": None},
    {"text": "  WDN-01-GLD [WARDEN]..................  DORMANT",               "check": None},
    {"text": "",                                                               "check": None},
    {"text": "> SIGNAL LOCK CONFIRMED",                                        "check": None},
    {"text": "> TRANSFERRING CONTROL TO GHO-02-ARC",                          "check": None},
]
