import os
import yaml
from dataclasses import dataclass
from typing import Optional


@dataclass
class Channel:
    id: int
    name: str
    url: str


class ChannelManager:
    STATUS_ADDED = "ADDED"
    STATUS_ALREADY_EXISTS = "ALREADY_EXISTS"

    def __init__(self, channels_path: str = None, saved_path: str = None):
        home = os.path.expanduser("~")
        self._channels_path = channels_path or os.path.join(home, ".config/streamerbox/channels.yaml")
        self._saved_path = saved_path or os.path.join(home, ".config/streamerbox/saved.yaml")
        self.channels: list[Channel] = []
        self._reload()

    def _load_yaml(self, path: str) -> list[dict]:
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return data.get("channels") or []
        except FileNotFoundError:
            return []
        except yaml.YAMLError as e:
            print(f"WARNING: could not parse {path}: {e}")
            return []

    def _reload(self):
        base, saved = [], []
        for c in self._load_yaml(self._channels_path):
            try:
                base.append(Channel(**c))
            except (TypeError, KeyError) as e:
                print(f"WARNING: skipping malformed channel entry in channels.yaml: {c} ({e})")
        for c in self._load_yaml(self._saved_path):
            try:
                saved.append(Channel(**c))
            except (TypeError, KeyError) as e:
                print(f"WARNING: skipping malformed channel entry in saved.yaml: {c} ({e})")
        self.channels = base + saved

    def get(self, index: int) -> Optional[Channel]:
        if 0 <= index < len(self.channels):
            return self.channels[index]
        return None

    def count(self) -> int:
        return len(self.channels)

    def remove_channel(self, url: str) -> bool:
        """Remove a channel from saved.yaml. Returns True if removed, False if it's a base channel."""
        base_urls = set()
        for c in self._load_yaml(self._channels_path):
            try:
                base_urls.add(Channel(**c).url)
            except (TypeError, KeyError) as e:
                print(f"WARNING: skipping malformed channel entry in channels.yaml during removal: {c} ({e})")
        if url in base_urls:
            return False  # can't remove base channels here
        saved = [c for c in self._load_yaml(self._saved_path) if c.get("url") != url]
        with open(self._saved_path, "w") as f:
            yaml.dump({"channels": saved}, f)
        self._reload()
        return True

    def save_channel(self, name: str, url: str):
        os.makedirs(os.path.dirname(self._saved_path), exist_ok=True)
        existing_urls = {ch.url for ch in self.channels}
        if url in existing_urls:
            return self.STATUS_ALREADY_EXISTS
        next_id = max((ch.id for ch in self.channels), default=0) + 1
        saved = self._load_yaml(self._saved_path)
        saved.append({"id": next_id, "name": name, "url": url})
        with open(self._saved_path, "w") as f:
            yaml.dump({"channels": saved}, f)
        self._reload()
        return self.STATUS_ADDED
