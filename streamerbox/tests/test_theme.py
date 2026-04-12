# streamerbox/tests/test_theme.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import theme

REQUIRED_GHOST_KEYS = [
    "now_playing_idle", "paused", "muted", "sub_active", "feed_live",
    "interface_visible", "interface_suppressed",
    "osd_pause", "osd_resume", "osd_muted", "osd_unmuted",
    "osd_seek_fwd", "osd_seek_back", "osd_node_fwd", "osd_node_back",
    "osd_catalog_confirmed", "osd_already_indexed", "osd_query_open",
    "osd_ipc_fault", "osd_stall", "osd_catalog_empty", "osd_catalog_fault",
]

REQUIRED_BOB_KEYS = [
    "stall_recovery", "duplicate_add", "zero_results",
    "second_attempt", "session_milestone", "random_nav",
]

def test_ghost_registry_complete():
    for key in REQUIRED_GHOST_KEYS:
        assert key in theme.GHOST, f"Missing Ghost key: {key}"
        assert isinstance(theme.GHOST[key], str)
        assert len(theme.GHOST[key]) > 0

def test_bob_trigger_map_complete():
    for key in REQUIRED_BOB_KEYS:
        assert key in theme.BOB, f"Missing Bob trigger: {key}"
        lines = theme.BOB[key]
        assert isinstance(lines, list)
        assert len(lines) >= 2
        if key == "random_nav":
            assert lines[0] is None, "random_nav index 0 must be None (sentinel)"
            for line in lines[1:]:
                assert isinstance(line, str) and len(line) > 0, \
                    f"random_nav line {line!r} must be a non-empty string"
        else:
            assert isinstance(lines[0], str) and lines[0] is not None and len(lines[0]) > 0, \
                f"BOB[{key!r}] index 0 must be a non-None, non-empty string (BOB ONLINE header)"

def test_bob_title_pool():
    assert hasattr(theme, "BOB_TITLES")
    assert isinstance(theme.BOB_TITLES, list)
    assert len(theme.BOB_TITLES) >= 10

def test_warden_line():
    assert hasattr(theme, "WARDEN_SHUTDOWN")
    assert isinstance(theme.WARDEN_SHUTDOWN, str)
    assert len(theme.WARDEN_SHUTDOWN) > 0

def test_dossier_sequence():
    assert hasattr(theme, "DOSSIER_LINES")
    assert isinstance(theme.DOSSIER_LINES, list)
    assert len(theme.DOSSIER_LINES) >= 10
    for item in theme.DOSSIER_LINES:
        assert isinstance(item, dict)
        assert "text" in item
        assert "check" in item
