"""Download verified TKKGData source pairings and merge them into one MP3."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .audio_sources import (
    build_individual_track_queries,
    build_playlist_query,
    validate_audio_release,
)
from .episodes import Episode
from .merger import merge_tracks, ordered_tracks


def _command(name: str) -> list[str]:
    executable = shutil.which(name)
    if executable:
        return [executable]
    if name == "spotdl":
        try:
            import spotdl  # noqa: F401
        except ImportError:
            pass
        else:
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


def _download_command(spotdl: list[str], query: str) -> list[str]:
    output_template = "{album}/{track-number} - {title}.{output-ext}"
    return [
        *spotdl, "download", query,
        "--format", "mp3",
        "--bitrate", "192k",
        "--output", output_template,
    ]


def _validate_downloaded_files(directory: Path, expected_count: int) -> list[Path]:
    tracks = ordered_tracks(list(directory.rglob("*.mp3")))
    if len(tracks) != expected_count:
        raise RuntimeError(
            f"Incomplete audio download: TKKGData verifies {expected_count} tracks, "
            f"but spotDL produced {len(tracks)} MP3 files. No combined file was created."
        )
    numbers = [int(track.stem.split(" - ", 1)[0]) for track in tracks]
    if numbers != list(range(1, expected_count + 1)):
        raise RuntimeError(
            "Downloaded track numbers are incomplete or out of order. "
            "No combined file was created."
        )
    album_dirs = {track.parent for track in tracks}
    if len(album_dirs) != 1:
        found = ", ".join(sorted(path.name for path in album_dirs)) or "none"
        raise RuntimeError(
            "The download did not produce exactly one album folder. "
            f"Found: {found}. No combined file was created."
        )
    return tracks


def _download_playlist(
    spotdl: list[str],
    query: str,
    directory: Path,
    expected_count: int,
    episode_number: int,
) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    result = _run_with_progress(
        _download_command(spotdl, query),
        stage=f"Downloading verified YouTube Music playlist for episode {episode_number}",
        cwd=directory,
    )
    if result != 0:
        raise RuntimeError(f"spotDL playlist download failed (exit code {result}).")
    return _validate_downloaded_files(directory, expected_count)


def _download_individual_tracks(
    spotdl: list[str],
    plan: dict,
    directory: Path,
    episode_number: int,
) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    track_queries = build_individual_track_queries(plan)
    for item in track_queries:
        result = _run_with_progress(
            _download_command(spotdl, item["query"]),
            stage=f"Downloading verified track {item['track_number']}/{plan['track_count']} for episode {episode_number}",
            cwd=directory,
        )
        if result != 0:
            raise RuntimeError(
                f"spotDL failed to download verified track {item['track_number']} "
                f"for episode {episode_number} (exit code {result})."
            )
    return _validate_downloaded_files(directory, plan["track_count"])


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

    try:
        plan = validate_audio_release(episode.audio_release)
    except ValueError as exc:
        raise RuntimeError(
            f"No usable verified audio source for episode {episode.number} in TKKGData: {exc}"
        ) from exc

    spotdl = _command("spotdl")
    ffmpeg = _command("ffmpeg")[0]
    print(f"Verified release: {plan['spotify_album_title']}", flush=True)
    print(f"Spotify album: {plan['spotify_album_url']}", flush=True)
    if plan["youtube_music_playlist_url"]:
        print(f"YouTube Music playlist: {plan['youtube_music_playlist_url']}", flush=True)
    print(f"Verified individual track links: {plan['track_count']}", flush=True)

    with tempfile.TemporaryDirectory(prefix=f"tkkg_{episode.number:03d}_") as temp:
        work_dir = Path(temp)
        tracks = None
        playlist_query = build_playlist_query(plan)
        if playlist_query:
            try:
                tracks = _download_playlist(
                    spotdl,
                    playlist_query,
                    work_dir / "playlist",
                    plan["track_count"],
                    episode.number,
                )
            except RuntimeError as exc:
                print(
                    f"Playlist download unavailable: {exc} "
                    "Falling back to the individually verified track URLs.",
                    flush=True,
                )

        if tracks is None:
            tracks = _download_individual_tracks(
                spotdl,
                plan,
                work_dir / "individual",
                episode.number,
            )

        print("Verified downloaded files:", flush=True)
        for track in tracks:
            print(f"  {track.name}", flush=True)

        if not assume_yes:
            if not sys.stdin.isatty():
                raise RuntimeError(
                    "Confirmation is required in non-interactive mode. "
                    "Review the verified source and rerun with --yes to accept it."
                )
            answer = input("Merge this verified release into one MP3? [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Cancelled. No combined MP3 was created.", flush=True)
                return None

        print(f"Merging {len(tracks)} tracks into one MP3...", flush=True)
        merge_tracks(tracks, final_path, ffmpeg=ffmpeg)
    print(f"Done: {final_path}", flush=True)
    return final_path
