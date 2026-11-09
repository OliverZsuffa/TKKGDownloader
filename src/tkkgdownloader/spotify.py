"""Resolve TKKG Spotify releases through their first chapter track."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from .episodes import Episode


def build_first_track_query(episode: Episode) -> str:
    """Return a text query intended to resolve the episode's first chapter."""
    return f"TKKG {episode.number:03d} {episode.title} Teil 01"


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("spotDL returned no track metadata.")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("spotDL returned malformed track metadata.")
    return payload


def resolve_album_metadata(payload: Any, episode: Episode) -> dict[str, Any]:
    """Validate a first-track lookup and return the Spotify album identity."""
    records = _records(payload)
    if len(records) != 1:
        raise ValueError(
            f"Expected exactly one first-track result, but spotDL returned {len(records)}."
        )

    track = records[0]
    artists = track.get("artists")
    artist = track.get("artist")
    if isinstance(artists, list) and artists:
        artist_names = [str(name) for name in artists]
    elif isinstance(artist, str):
        artist_names = [artist]
    else:
        artist_names = []

    if not any(name.strip().casefold() == "tkkg" for name in artist_names):
        raise ValueError("The first-track search did not resolve to an artist named TKKG.")

    expected_title = _normalise(f"{episode.number} {episode.title} Teil 01")
    actual_title = _normalise(str(track.get("name", "")))
    if actual_title != expected_title:
        raise ValueError(
            "The first-track search resolved to an unexpected track. "
            f"Expected '{episode.number} - {episode.title} - Teil 01', "
            f"received '{track.get('name', '')}'."
        )

    album_id = track.get("album_id")
    if not isinstance(album_id, str) or not re.fullmatch(r"[A-Za-z0-9]{22}", album_id):
        raise ValueError("The resolved first track has no valid Spotify album ID.")

    album_name = track.get("album_name")
    if not isinstance(album_name, str) or not album_name.strip():
        raise ValueError("The resolved first track has no album name.")

    return {
        "album_id": album_id,
        "album_name": album_name,
        "album_url": f"https://open.spotify.com/album/{album_id}",
    }


def _positive_int(value: Any, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"spotDL metadata is missing a valid {field}.") from exc
    if number < 1:
        raise ValueError(f"spotDL metadata contains an invalid {field}.")
    return number


def validate_album_metadata(payload: Any, album: dict[str, Any]) -> int:
    """Validate every returned album song and return the metadata record count."""
    records = _records(payload)
    album_id = album["album_id"]
    if any(record.get("album_id") != album_id for record in records):
        raise ValueError("The album metadata contains tracks from a different album.")

    track_numbers = [
        _positive_int(record.get("track_number"), "track_number")
        for record in records
    ]
    if len(set(track_numbers)) != len(track_numbers):
        raise ValueError("The album metadata contains duplicate track numbers.")

    expected_sequence = list(range(1, len(records) + 1))
    if sorted(track_numbers) != expected_sequence:
        raise ValueError(
            "The album metadata does not contain a complete track sequence "
            f"from 1 to {len(records)}."
        )

    return len(records)
