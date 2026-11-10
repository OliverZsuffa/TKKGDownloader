"""Download verified TKKGData sources and merge them into one MP3."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .audio_sources import validate_audio_release
from .episodes import Episode
from .merger import merge_tracks, ordered_tracks
from .spotisaver import download_and_import, finish_console_output, report_stage


def _command(name: str) -> list[str]:
    executable = shutil.which(name)
    if executable:
        return [executable]
    if name == "yt-dlp":
        try:
            import yt_dlp  # noqa: F401
        except ImportError:
            pass
        else:
            return [sys.executable, "-m", "yt_dlp"]
    raise RuntimeError(
        f"Could not find {name!r}. Install the project dependencies and make sure "
        "the executable is available on PATH."
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
            print(f"{stage} is still running ({_format_elapsed(elapsed)} elapsed).", flush=True)
    elapsed = time.monotonic() - started_at
    print(
        f"{stage} finished with exit code {return_code} "
        f"({_format_elapsed(elapsed)} elapsed).",
        flush=True,
    )
    return return_code


def _validate_downloaded_files(directory: Path, expected_count: int) -> list[Path]:
    tracks = ordered_tracks(list(directory.rglob("*.mp3")))
    if len(tracks) != expected_count:
        raise RuntimeError(
            f"Incomplete audio download: TKKGData verifies {expected_count} tracks, "
            f"but yt-dlp produced {len(tracks)} MP3 files. No combined file was created."
        )
    numbers = [int(track.stem.split(" - ", 1)[0]) for track in tracks]
    if numbers != list(range(1, expected_count + 1)):
        raise RuntimeError("Downloaded track numbers are incomplete or out of order. No combined file was created.")
    album_dirs = {track.parent for track in tracks}
    if len(album_dirs) != 1:
        found = ", ".join(sorted(path.name for path in album_dirs)) or "none"
        raise RuntimeError(
            "The download did not produce exactly one album folder. "
            f"Found: {found}. No combined file was created."
        )
    for track in tracks:
        if track.stat().st_size == 0:
            raise RuntimeError(f"Downloaded track {track.name} is empty. No combined file was created.")
    return tracks


def _download_verified_tracks(yt_dlp: list[str], plan: dict, directory: Path, episode: Episode) -> list[Path]:
    album_dir = directory / _safe_filename(plan["spotify_album_title"])
    album_dir.mkdir(parents=True, exist_ok=True)
    for track in plan["tracks"]:
        number = track["track_number"]
        title = _safe_filename(track["spotify_title"])
        output_template = album_dir / f"{number:02d} - {title}.%(ext)s"
        command = [
            *yt_dlp, "--no-warnings", "--no-playlist", "--extract-audio",
            "--audio-format", "mp3", "--audio-quality", "192K",
            "--windows-filenames", "--output", str(output_template),
            track["youtube_music_url"],
        ]
        result = _run_with_progress(
            command,
            stage=f"Downloading verified track {number}/{plan['track_count']} for episode {episode.number}",
            cwd=directory,
        )
        if result != 0:
            raise RuntimeError(
                f"yt-dlp failed to download verified track {number}/{plan['track_count']} "
                f"for episode {episode.number} (exit code {result}). No combined file was created."
            )
        expected_file = album_dir / f"{number:02d} - {title}.mp3"
        if not expected_file.is_file() or expected_file.stat().st_size == 0:
            raise RuntimeError(
                f"yt-dlp reported success for verified track {number}/{plan['track_count']} "
                f"but did not produce the expected MP3 file {expected_file.name}. No combined file was created."
            )
    return _validate_downloaded_files(directory, plan["track_count"])


def download_episode(
    episode: Episode,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"TKKG {episode.number:03d} - {_safe_filename(episode.title)}.mp3"
    if final_path.exists() and not overwrite:
        print(f"SKIP  {final_path.name} already exists. Use --overwrite to replace it.")
        return final_path
    try:
        plan = validate_audio_release(episode.audio_release)
    except ValueError as exc:
        raise RuntimeError(f"No usable verified audio source for episode {episode.number} in TKKGData: {exc}") from exc

    yt_dlp = _command("yt-dlp")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Could not find 'ffmpeg'. Install FFmpeg and make sure it is available on PATH.")
    print(f"Verified release: {plan['spotify_album_title']}", flush=True)
    print(f"Spotify album: {plan['spotify_album_url']}", flush=True)
    print(f"Downloading {plan['track_count']} individually verified YouTube Music tracks.", flush=True)

    with tempfile.TemporaryDirectory(prefix=f"tkkg_{episode.number:03d}_") as temp:
        tracks = _download_verified_tracks(yt_dlp, plan, Path(temp), episode)
        print("Verified downloaded files:", flush=True)
        for track in tracks:
            print(f"  {track.name}", flush=True)
        print(f"Merging {len(tracks)} tracks into one MP3...", flush=True)
        merge_tracks(tracks, final_path, ffmpeg=ffmpeg)
    print(f"Done: {final_path}", flush=True)
    return final_path


def download_episode_spotisaver(
    episode: Episode,
    output_dir: Path,
    *,
    overwrite: bool = False,
    diagnostic_dir: Path | None = None,
) -> Path:
    """Download one episode through Spotisaver, optionally retaining a full diagnostic workspace."""
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"TKKG {episode.number:03d} - {_safe_filename(episode.title)}.mp3"
    if diagnostic_dir is not None:
        workspace = diagnostic_dir.expanduser().resolve()
        if workspace.exists() and any(workspace.iterdir()):
            raise FileExistsError(
                f"Diagnostic directory is not empty: {workspace}. "
                "Choose a new directory so no previous evidence is overwritten."
            )
        workspace.mkdir(parents=True, exist_ok=True)
        source_dir = workspace / "source"
        source_dir.mkdir()
        try:
            plan = validate_audio_release(episode.audio_release)
        except ValueError as exc:
            raise RuntimeError(
                f"No usable verified audio source for episode {episode.number} in TKKGData: {exc}"
            ) from exc
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            raise RuntimeError("Both 'ffmpeg' and 'ffprobe' must be available on PATH for diagnostics.")
        try:
            tracks = download_and_import(plan, source_dir, episode_number=episode.number)
            report_stage("Source tracks validated. Starting quality diagnostics...", "info")
            from .audio_diagnostics import run_episode_diagnostics
            report = run_episode_diagnostics(
                episode, plan, tracks, workspace, ffmpeg=ffmpeg, ffprobe=ffprobe
            )
            report_stage(f"Diagnostics complete. Report: {report}", "success")
            return report
        finally:
            finish_console_output()
    if final_path.exists() and not overwrite:
        print(f"SKIP  {final_path.name} already exists. Use --overwrite to replace it.")
        return final_path
    try:
        plan = validate_audio_release(episode.audio_release)
    except ValueError as exc:
        raise RuntimeError(f"No usable verified audio source for episode {episode.number} in TKKGData: {exc}") from exc

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Could not find 'ffmpeg'. Install FFmpeg and make sure it is available on PATH.")
    try:
        with tempfile.TemporaryDirectory(prefix=f"tkkg_{episode.number:03d}_spotisaver_") as temp:
            tracks = download_and_import(plan, Path(temp), episode_number=episode.number)
            report_stage("Merging MP3...", "info")
            merge_tracks(tracks, final_path, ffmpeg=ffmpeg)
        report_stage(f"Done: {final_path}", "success")
        return final_path
    finally:
        finish_console_output()
