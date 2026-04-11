import json
import pytest
from unittest.mock import patch, MagicMock
from search import parse_ytdlp_result, SearchResult, is_auth_error, search, search_playlists


def make_ytdlp_json(title="Test Video", url="https://yt.com/watch?v=abc", duration=1200):
    return json.dumps({
        "title": title,
        "webpage_url": url,
        "duration": duration,
        "extractor": "youtube",
    })


def test_parse_result_extracts_title():
    result = parse_ytdlp_result(make_ytdlp_json())
    assert result.name == "Test Video"


def test_parse_result_extracts_url():
    result = parse_ytdlp_result(make_ytdlp_json())
    assert result.url == "https://yt.com/watch?v=abc"


def test_parse_result_returns_none_on_bad_json():
    result = parse_ytdlp_result("not json at all")
    assert result is None


def test_parse_result_returns_none_on_missing_url():
    data = json.dumps({"title": "Test"})
    result = parse_ytdlp_result(data)
    assert result is None


def test_is_auth_error_sign_in():
    assert is_auth_error("ERROR: Sign in to confirm your age") is True


def test_is_auth_error_premium():
    assert is_auth_error("This video is only available for Premium members") is True


def test_is_auth_error_members_only():
    assert is_auth_error("members only content") is True


def test_is_auth_error_403():
    assert is_auth_error("HTTP Error 403: Forbidden") is True


def test_is_auth_error_normal_error():
    assert is_auth_error("ERROR: Unable to extract video URL") is False


@patch("search.subprocess.run")
def test_search_parses_successful_results(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="\n".join([
            make_ytdlp_json(title="Video One", url="https://yt.com/watch?v=1"),
            make_ytdlp_json(title="Video Two", url="https://yt.com/watch?v=2"),
        ]),
        stderr="",
    )

    results, err = search("lofi", max_results=2)

    assert err == ""
    assert [r.name for r in results] == ["Video One", "Video Two"]
    cmd = mock_run.call_args.args[0]
    assert cmd[-1] == "ytsearch2:lofi"


@patch("search.subprocess.run")
def test_search_returns_empty_result_message(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    results, err = search("missing")

    assert results == []
    assert err == "NO SIGNAL — no results"


@patch("search.subprocess.run")
def test_search_returns_error_on_nonzero_exit(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")

    results, err = search("broken")

    assert results == []
    assert err == "ERROR — boom"


@patch("search.subprocess.run")
def test_search_playlists_parses_successful_results(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=make_ytdlp_json(title="Playlist One", url="https://yt.com/playlist?list=1"),
        stderr="",
    )

    results, err = search_playlists("mixes", max_results=3)

    assert err == ""
    assert results == [SearchResult(name="Playlist One", url="https://yt.com/playlist?list=1")]
    cmd = mock_run.call_args.args[0]
    assert "--playlist-end=3" in cmd
    assert cmd[-1].startswith("https://www.youtube.com/results?search_query=mixes&sp=EgIQAw%3D%3D")


@patch("search.subprocess.run")
def test_search_playlists_returns_empty_result_message(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    results, err = search_playlists("empty")

    assert results == []
    assert err == "NO SIGNAL — no results"


@patch("search.subprocess.run", side_effect=OSError("no yt-dlp"))
def test_search_playlists_returns_error_on_subprocess_exception(mock_run):
    results, err = search_playlists("fail")

    assert results == []
    assert err == "yt-dlp error: no yt-dlp"
