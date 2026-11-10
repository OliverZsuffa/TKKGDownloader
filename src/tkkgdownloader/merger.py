"""Merge ordered MP3 tracks into a single MP3 file with FFmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def track_number(path: Path) -> int:
    prefix = path.stem.split(" - ", 1)[0]
    if not prefix.isdigit():
        raise ValueError(f"Cannot determine track number from filename: {path.name}")
    return int(prefix)


def ordered_tracks(paths: list[Path]) -> list[Path]:
    if not paths:
        raise ValueError("No MP3 tracks were downloaded.")
    ordered = sorted(paths, key=track_number)
    numbers = [track_number(path) for path in ordered]
    if len(numbers) != len(set(numbers)):
        raise ValueError("The downloaded release contains duplicate track numbers.")
    return ordered


def _ffconcat_quote(path: Path) -> str:
    value = path.resolve().as_posix()
    return "'" + value.replace("'", "'\\''") + "'"


def merge_tracks(
    tracks: list[Path], output: Path, ffmpeg: str = "ffmpeg",
    diagnostics: dict[str, Any] | None = None,
) -> None:
    ordered = ordered_tracks(tracks)
    output.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output.with_suffix(".concat.txt")
    temporary_output = output.with_name(output.stem + ".partial.mp3")
    concat_file.write_text(
        "".join(f"file {_ffconcat_quote(track)}\n" for track in ordered),
        encoding="utf-8",
    )
    try:
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", str(temporary_output),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        attempts = [{
            "method": "stream_copy",
            "command": command,
            "returncode": result.returncode,
            "stderr": result.stderr,
        }]
        selected_method = "stream_copy"
        if result.returncode != 0:
            # Different MP3 stream parameters can prevent stream-copy concatenation.
            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c:a", "libmp3lame", "-b:a", "192k", str(temporary_output),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            selected_method = "reencode_192k_fallback"
            attempts.append({
                "method": selected_method,
                "command": command,
                "returncode": result.returncode,
                "stderr": result.stderr,
            })
        if diagnostics is not None:
            diagnostics.update({"attempts": attempts, "selected_method": selected_method})
        if result.returncode != 0:
            detail = (result.stderr or "FFmpeg returned an error.").strip()
            raise RuntimeError(f"FFmpeg could not merge the tracks: {detail}")
        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise RuntimeError("FFmpeg did not produce a valid output file.")
        temporary_output.replace(output)
    finally:
        concat_file.unlink(missing_ok=True)
        temporary_output.unlink(missing_ok=True)
