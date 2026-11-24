"""Read-only episode metadata client for the published TKKGData dataset."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

EPISODES_URL = (
    "https://raw.githubusercontent.com/OliverZsuffa/"
    "TKKGData/main/data/episodes.json"
)
DATASET_METADATA_URL = (
    "https://raw.githubusercontent.com/OliverZsuffa/"
    "TKKGData/main/data/dataset-metadata.json"
)
AUDIO_UNAVAILABLE_URL = (
    "https://raw.githubusercontent.com/OliverZsuffa/"
    "TKKGData/main/data/audio-unavailable.json"
)
SUPPORTED_SCHEMA_MAJOR = "1."


@dataclass(frozen=True)
class Episode:
    number: int
    title: str
    audio_release: dict[str, Any] | None = None
    audio_unavailable_reason: str | None = None
    audio_unavailable_basis: str | None = None


def _fetch_json(url: str, timeout: int) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TKKGDownloader/0.2"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("TKKGData returned an empty or unexpected episode array.")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("TKKGData returned malformed episode records.")
    return payload


def parse_audio_unavailable(payload: Any) -> dict[int, dict[str, str]]:
    """Validate the separate, reviewed registry of known unavailable releases."""
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("TKKGData audio-unavailable registry has an unsupported structure or version.")
    entries = payload.get("episodes")
    if not isinstance(entries, dict):
        raise ValueError("TKKGData audio-unavailable registry has no episode mapping.")
    result: dict[int, dict[str, str]] = {}
    for raw_number, entry in entries.items():
        if not isinstance(raw_number, str) or not raw_number.isdigit() or int(raw_number) < 1:
            raise ValueError(f"TKKGData audio-unavailable registry has an invalid episode key: {raw_number!r}.")
        number = int(raw_number)
        if number in result or not isinstance(entry, dict):
            raise ValueError(f"TKKGData audio-unavailable entry for episode {number} is malformed.")
        status = entry.get("status")
        reason = entry.get("reason")
        basis = entry.get("basis")
        if status != "unavailable" or not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"TKKGData audio-unavailable entry for episode {number} is incomplete.")
        if basis is not None and (not isinstance(basis, str) or not basis.strip()):
            raise ValueError(f"TKKGData audio-unavailable entry for episode {number} has an invalid basis.")
        result[number] = {"reason": reason.strip(), "basis": basis or ""}
    return result


def parse_catalog(
    payload: Any,
    unavailable_payload: Any | None = None,
) -> dict[int, Episode]:
    unavailable = (
        parse_audio_unavailable(unavailable_payload)
        if unavailable_payload is not None else {}
    )
    episodes: dict[int, Episode] = {}
    for item in _records(payload):
        raw_number = item.get("number")
        title = item.get("title")
        try:
            number = int(raw_number)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"TKKGData contains an invalid episode number: {raw_number!r}") from exc
        if number < 1 or not isinstance(title, str) or not title.strip():
            raise ValueError(f"TKKGData contains an invalid record for episode {number}.")
        if number in episodes:
            raise ValueError(f"TKKGData contains duplicate episode number {number}.")
        for field in ("physical_releases", "tracks", "cast", "credits", "ratings", "sources", "listening_links"):
            if not isinstance(item.get(field), list):
                raise ValueError(f"TKKGData episode {number} is missing required array field {field}.")
        audio_release = item.get("audio_release")
        if audio_release is not None and not isinstance(audio_release, dict):
            raise ValueError(f"TKKGData episode {number} has malformed audio_release metadata.")
        unavailable_entry = unavailable.get(number, {})
        episodes[number] = Episode(
            number=number,
            title=title.strip(),
            audio_release=audio_release,
            audio_unavailable_reason=unavailable_entry.get("reason"),
            audio_unavailable_basis=unavailable_entry.get("basis") or None,
        )
    numbers = sorted(episodes)
    if numbers != list(range(1, numbers[-1] + 1)):
        raise ValueError("TKKGData episode numbering contains gaps.")
    unknown_unavailable = sorted(set(unavailable) - set(episodes))
    if unknown_unavailable:
        raise ValueError(
            "TKKGData audio-unavailable registry references unknown episodes: "
            + ", ".join(map(str, unknown_unavailable))
        )
    return episodes


def fetch_catalog(timeout: int = 20) -> dict[int, Episode]:
    try:
        metadata = _fetch_json(DATASET_METADATA_URL, timeout)
        if not isinstance(metadata, dict):
            raise ValueError("TKKGData dataset metadata has an unexpected structure.")
        schema_version = metadata.get("schema_version")
        if not isinstance(schema_version, str) or not schema_version.startswith(SUPPORTED_SCHEMA_MAJOR):
            raise ValueError(
                f"Unsupported TKKGData schema version: {schema_version!r}. "
                f"Supported versions start with {SUPPORTED_SCHEMA_MAJOR}."
            )
        payload = _fetch_json(EPISODES_URL, timeout)
        records = _records(payload)
        expected_count = metadata.get("episode_count")
        if expected_count != len(records):
            raise ValueError(
                f"TKKGData metadata reports {expected_count!r} episodes, "
                f"but the dataset contains {len(records)}."
            )
        unavailable_payload = _fetch_json(AUDIO_UNAVAILABLE_URL, timeout)
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not retrieve the TKKGData dataset: {exc}") from exc
    return parse_catalog(records, unavailable_payload)


def get_episode(catalog: dict[int, Episode], number: int) -> Episode:
    try:
        return catalog[number]
    except KeyError as exc:
        raise ValueError(f"Episode {number} was not found in the TKKGData dataset.") from exc
