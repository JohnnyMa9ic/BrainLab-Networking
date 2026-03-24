import json
import pytest
from unittest.mock import patch, MagicMock
from search import parse_ytdlp_result, SearchResult, is_auth_error


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
