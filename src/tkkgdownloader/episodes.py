"""Episode metadata retrieval from TKKGTracker."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

EPISODES_URL = (
    "https://raw.githubusercontent.com/OliverZsuffa/"
    "TKKGtracker/main/data/episodes.json"
)


@dataclass(frozen=True)
class Episode:
    number: int
    title: str


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("episodes", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError("The episode catalog has an unexpected JSON structure.")


def parse_catalog(payload: Any) -> dict[int, Episode]:
    episodes: dict[int, Episode] = {}
    for item in _records(payload):
        raw_number = item.get("number")
        title = item.get("title")
        try:
            number = int(raw_number)
        except (TypeError, ValueError):
            continue
        if number < 1 or not isinstance(title, str) or not title.strip():
            continue
        episodes[number] = Episode(number=number, title=title.strip())
    if not episodes:
        raise ValueError("The episode catalog did not contain any valid episodes.")
    return episodes


def fetch_catalog(timeout: int = 20) -> dict[int, Episode]:
    request = urllib.request.Request(
        EPISODES_URL,
        headers={"User-Agent": "TKKGDownloader/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not retrieve the TKKGTracker episode catalog: {exc}") from exc
    return parse_catalog(payload)


def get_episode(catalog: dict[int, Episode], number: int) -> Episode:
    try:
        return catalog[number]
    except KeyError as exc:
        raise ValueError(f"Episode {number} was not found in the TKKGTracker catalog.") from exc
