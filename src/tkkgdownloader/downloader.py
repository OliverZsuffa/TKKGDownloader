"""spotDL integration and episode-level download orchestration."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .episodes import Episode
from .merger import merge_tracks, ordered_tracks
from .spotify import (
    build_first_track_query,
    resolve_album_metadata,
    validate_album_metadata,
)


def _command(name: str) -> list[str]:
    executable = shutil.which(name)
    if executable:
        return [executable]
    if name == "spotdl" and importlib.util.find_spec("spotdl"):
        return [sys.executable, "-m", "spotdl"]
    raise RuntimeError(
        f"Could not find {name!r}. Install it and make sure it is available on PATH."
    )


def _safe_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    return re.sub(r"\s+", " ", value).strip(" .") or "Untitled"


def _format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def _run_with_progress(
    command: list[str],
    *,
    stage: str,
    cwd: Path | None = None,
    heartbeat_seconds: int = 10,
) -> int:
    """Run a command with inherited terminal output and periodic elapsed-time updates."""
    print(f"{stage}...", flush=True)
    started_at = time.monotonic()
    process = subprocess.Popen(command, cwd=cwd)
    while True:
        try:
            return_code = process.wait(timeout=heartbeat_seconds)
            break
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - started_at
            print(
                f"{stage} is still running ({_format_elapsed(elapsed)} elapsed).",
                flush=True,
            )

    elapsed = time.monotonic() - started_at
    print(
        f"{stage} finished with exit code {return_code} "
        f"({_format_elapsed(elapsed)} elapsed).",
        flush=True,
    )
    return return_code


def _read_spotdl_file(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read spotDL metadata file: {exc}") from exc
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise RuntimeError("spotDL created an invalid metadata file.")
    return payload


def _save_metadata(
    spotdl: list[str], query: str, save_path: Path, *, episode_number: int
) -> list[dict[str, Any]]:
    result = _run_with_progress(
        [*spotdl, "save", query, "--save-file", str(save_path)],
        stage=f"Retrieving metadata for episode {episode_number}",
    )
    if result != 0:
        raise RuntimeError(
            f"spotDL metadata lookup failed for episode {episode_number} "
            f"(exit code {result})."
        )
    return _read_spotdl_file(save_path)


def download_episode(
    episode: Episode,
    output_dir: Path,
    *,
    overwrite: bool = False,
    assume_yes: bool = False,
) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / (
        f"TKKG {episode.number:03d} - {_safe_filename(episode.title)}.mp3"
    )
    if final_path.exists() and not overwrite:
        print(f"SKIP  {final_path.name} already exists. Use --overwrite to replace it.")
        return final_path

    spotdl = _command("spotdl")
    ffmpeg = _command("ffmpeg")[0]
    query = build_first_track_query(episode)

    with tempfile.TemporaryDirectory(prefix=f"tkkg_{episode.number:03d}_") as temp:
        work_dir = Path(temp)
        first_track_file = work_dir / "first-track.spotdl"
        print(f"Resolving first track: {query}", flush=True)
        first_track_records = _save_metadata(
            spotdl, query, first_track_file, episode_number=episode.number
        )
        try:
            album = resolve_album_metadata(first_track_records, episode)
        except ValueError as exc:
            raise RuntimeError(f"Could not identify the correct Spotify release: {exc}") from exc

        album_file = work_dir / "album.spotdl"
        print(f"Resolved release: {album['album_name']}", flush=True)
        print(f"Spotify album: {album['album_url']}", flush=True)
        album_records = _save_metadata(
            spotdl, album["album_url"], album_file, episode_number=episode.number
        )
        try:
            expected_count = validate_album_metadata(album_records, album)
        except ValueError as exc:
            raise RuntimeError(f"Spotify album metadata validation failed: {exc}") from exc
        print(
            f"Validated {expected_count} tracks in the album metadata.",
            flush=True,
        )

        output_template = "{album}/{track-number} - {title}.{output-ext}"
        command = [
            *spotdl, "download", album["album_url"],
            "--format", "mp3",
            "--bitrate", "192k",
            "--output", output_template,
        ]
        result = _run_with_progress(
            command,
            stage=f"Downloading all {expected_count} album tracks",
            cwd=work_dir,
        )
        if result != 0:
            raise RuntimeError(
                f"spotDL download failed for episode {episode.number} "
                f"(exit code {result})."
            )

        print("Verifying downloaded files...", flush=True)
        tracks = ordered_tracks(list(work_dir.rglob("*.mp3")))
        album_dirs = {track.parent for track in tracks}
        if len(album_dirs) != 1:
            found = ", ".join(sorted(path.name for path in album_dirs)) or "none"
            raise RuntimeError(
                "The download did not produce exactly one album folder. "
                f"Found: {found}. No combined file was created."
            )
        if len(tracks) != expected_count:
            raise RuntimeError(
                f"Incomplete album download: spotDL returned {expected_count} album "
                f"tracks, but downloaded {len(tracks)} MP3 files. "
                "No combined file was created."
            )

        album_name = next(iter(album_dirs)).name
        print(f"Found release: {album_name}", flush=True)
        print(f"Tracks ({len(tracks)}), in numeric order:", flush=True)
        for track in tracks:
            print(f"  {track.name}", flush=True)

        if not assume_yes:
            if not sys.stdin.isatty():
                raise RuntimeError(
                    "Confirmation is required in non-interactive mode. "
                    "Review the release and rerun with --yes to accept it."
                )
            answer = input("Merge this release into one MP3? [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Cancelled. No combined MP3 was created.", flush=True)
                return None

        _run_with_progress(
            [ffmpeg, "-version"],
            stage="Checking FFmpeg",
            heartbeat_seconds=10,
        )
        print(f"Merging {len(tracks)} tracks into one MP3...", flush=True)
        merge_tracks(tracks, final_path, ffmpeg=ffmpeg)
    print(f"Done: {final_path}", flush=True)
    return final_path
