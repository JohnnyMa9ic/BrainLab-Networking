import os
import tempfile
import yaml
import pytest
from channels import Channel, ChannelManager


def make_yaml(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def test_channel_model():
    ch = Channel(id=1, name="Bebop", url="https://example.com")
    assert ch.id == 1
    assert ch.name == "Bebop"
    assert ch.url == "https://example.com"


def test_load_channels_yaml(tmp_path):
    path = make_yaml(tmp_path, "channels.yaml", {
        "channels": [
            {"id": 1, "name": "Bebop", "url": "https://yt.com/1"},
            {"id": 2, "name": "GitS", "url": "https://cr.com/2"},
        ]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {"channels": []})
    mgr = ChannelManager(channels_path=path, saved_path=saved)
    assert len(mgr.channels) == 2
    assert mgr.channels[0].name == "Bebop"


def test_saved_channels_appended_after_base(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": 1, "name": "Bebop", "url": "https://yt.com/1"}]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {
        "channels": [{"id": 2, "name": "Akira", "url": "https://yt.com/2"}]
    })
    mgr = ChannelManager(channels_path=base, saved_path=saved)
    assert len(mgr.channels) == 2
    assert mgr.channels[1].name == "Akira"


def test_save_new_channel_assigns_next_id(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": 1, "name": "Bebop", "url": "https://yt.com/1"}]
    })
    saved_path = str(tmp_path / "saved.yaml")
    with open(saved_path, "w") as f:
        yaml.dump({"channels": []}, f)
    mgr = ChannelManager(channels_path=base, saved_path=saved_path)
    mgr.save_channel(name="Akira", url="https://yt.com/2")
    assert len(mgr.channels) == 2
    assert mgr.channels[1].id == 2


def test_save_duplicate_url_silently_skipped(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": 1, "name": "Bebop", "url": "https://yt.com/1"}]
    })
    saved_path = str(tmp_path / "saved.yaml")
    with open(saved_path, "w") as f:
        yaml.dump({"channels": []}, f)
    mgr = ChannelManager(channels_path=base, saved_path=saved_path)
    mgr.save_channel(name="Bebop Again", url="https://yt.com/1")
    assert len(mgr.channels) == 1


def test_get_channel_by_index(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [
            {"id": 1, "name": "A", "url": "https://a.com"},
            {"id": 2, "name": "B", "url": "https://b.com"},
        ]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {"channels": []})
    mgr = ChannelManager(channels_path=base, saved_path=saved)
    assert mgr.get(0).name == "A"
    assert mgr.get(1).name == "B"
    assert mgr.get(2) is None  # out of bounds returns None


def test_channel_count(tmp_path):
    base = make_yaml(tmp_path, "channels.yaml", {
        "channels": [{"id": i, "name": f"CH{i}", "url": f"https://{i}.com"} for i in range(1, 6)]
    })
    saved = make_yaml(tmp_path, "saved.yaml", {"channels": []})
    mgr = ChannelManager(channels_path=base, saved_path=saved)
    assert mgr.count() == 5
