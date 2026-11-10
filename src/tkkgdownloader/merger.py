"""Merge ordered MP3 tracks with format and duration validation."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
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


def _run(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _probe(path: Path, ffprobe: str) -> dict[str, Any]:
    result = _run([
        ffprobe, "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path),
    ])
    if result["returncode"] != 0:
        raise RuntimeError(f"FFprobe failed for {path.name}: {result['stderr'].strip()}")
    try:
        data = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"FFprobe returned invalid JSON for {path.name}.") from exc
    stream = next(
        (item for item in data.get("streams", []) if item.get("codec_type") == "audio"),
        None,
    )
    if stream is None:
        raise RuntimeError(f"No audio stream found in {path.name}.")
    duration = stream.get("duration") or data.get("format", {}).get("duration")
    if duration is None:
        raise RuntimeError(f"FFprobe did not report a duration for {path.name}.")
    return {
        "codec": stream.get("codec_name"),
        "sample_rate": int(stream["sample_rate"]) if stream.get("sample_rate") else None,
        "channels": int(stream["channels"]) if stream.get("channels") else None,
        "channel_layout": stream.get("channel_layout"),
        "duration_seconds": float(duration),
    }


def _decode(path: Path, ffmpeg: str) -> dict[str, Any]:
    return _run([
        ffmpeg, "-hide_banner", "-v", "error", "-xerror", "-i", str(path),
        "-map", "0:a:0", "-f", "null", "-",
    ])


def _validate_output(path: Path, ffmpeg: str, ffprobe: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError("FFmpeg did not produce a non-empty output file.")
    probe = _probe(path, ffprobe)
    decode = _decode(path, ffmpeg)
    if decode["returncode"] != 0:
        raise RuntimeError(f"Full decode validation failed: {decode['stderr'].strip()}")
    return {**probe, "size_bytes": path.stat().st_size}


def _write_concat(paths: list[Path], destination: Path) -> None:
    destination.write_text(
        "".join(f"file {_ffconcat_quote(path)}\n" for path in paths),
        encoding="utf-8",
    )


def _run_stream_copy(
    tracks: list[Path], concat_file: Path, temporary_output: Path, ffmpeg: str,
) -> dict[str, Any]:
    _write_concat(tracks, concat_file)
    return _run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", str(temporary_output),
    ])


def _run_pcm_merge(
    tracks: list[Path], temporary_output: Path, ffmpeg: str, ffprobe: str,
    workspace: Path,
) -> dict[str, Any]:
    source_info = [_probe(path, ffprobe) for path in tracks]
    sample_rate = max(item["sample_rate"] or 44100 for item in source_info)
    channels = max(item["channels"] or 2 for item in source_info)

    with tempfile.TemporaryDirectory(prefix="tkkg_pcm_", dir=workspace) as temp:
        pcm_dir = Path(temp)
        wavs: list[Path] = []
        conversions: list[dict[str, Any]] = []
        for index, source in enumerate(tracks, start=1):
            wav = pcm_dir / f"{index:04d}.wav"
            conversion = _run([
                ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(source),
                "-map", "0:a:0", "-ar", str(sample_rate), "-ac", str(channels),
                "-c:a", "pcm_s24le", str(wav),
            ])
            conversions.append(conversion)
            if conversion["returncode"] != 0 or not wav.is_file():
                raise RuntimeError(
                    f"PCM conversion failed for {source.name}: {conversion['stderr'].strip()}"
                )
            wavs.append(wav)

        concat_file = pcm_dir / "segments.txt"
        _write_concat(wavs, concat_file)
        master = pcm_dir / "master.wav"
        master_result = _run([
            ffmpeg, "-hide_banner", "-v", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c:a", "pcm_s24le", str(master),
        ])
        if master_result["returncode"] != 0 or not master.is_file():
            raise RuntimeError(f"PCM concatenation failed: {master_result['stderr'].strip()}")

        encode = _run([
            ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(master),
            "-c:a", "libmp3lame", "-b:a", "320k", str(temporary_output),
        ])
        if encode["returncode"] != 0:
            raise RuntimeError(f"320 kbit/s MP3 encoding failed: {encode['stderr'].strip()}")

        return {
            "method": "pcm_24bit_then_mp3_320k",
            "sample_rate": sample_rate,
            "channels": channels,
            "conversions": conversions,
            "master_command": master_result["command"],
            "encode_command": encode["command"],
        }


def _compatible_formats(source_info: list[dict[str, Any]]) -> bool:
    formats = {
        (
            item["codec"],
            item["sample_rate"],
            item["channels"],
            item["channel_layout"],
        )
        for item in source_info
    }
    return len(formats) == 1


def _duration_tolerance(track_count: int) -> float:
    """Allow MP3 frame padding and encoder delay without accepting large gaps."""
    return max(3.0, track_count * 0.1)


def merge_tracks(
    tracks: list[Path],
    output: Path,
    ffmpeg: str = "ffmpeg",
    diagnostics: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    ffprobe: str = "ffprobe",
    strategy: str = "auto",
) -> None:
    """Merge tracks safely. Auto mode validates stream copy and falls back to PCM."""
    if strategy not in {"auto", "pcm", "legacy"}:
        raise ValueError(f"Unsupported merge strategy: {strategy}")

    if manifest is not None:
        from .audio_import import validate_track_manifest
        ordered = validate_track_manifest(tracks, manifest)
    else:
        ordered = ordered_tracks(tracks)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(output.stem + ".partial.mp3")
    concat_file = output.with_suffix(".concat.txt")
    attempts: list[dict[str, Any]] = []
    selected_method: str | None = None
    expected_duration: float | None = None
    source_info: list[dict[str, Any]] = []

    try:
        if strategy in {"auto", "pcm"}:
            source_info = [_probe(path, ffprobe) for path in ordered]
            expected_duration = sum(item["duration_seconds"] for item in source_info)

        if strategy == "legacy":
            stream_result = _run_stream_copy(ordered, concat_file, temporary_output, ffmpeg)
            attempts.append({"method": "stream_copy", **stream_result})
            if stream_result["returncode"] == 0:
                selected_method = "stream_copy"
            else:
                fallback = _run([
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "concat", "-safe", "0", "-i", str(concat_file),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(temporary_output),
                ])
                attempts.append({"method": "reencode_192k_fallback", **fallback})
                if fallback["returncode"] == 0:
                    selected_method = "reencode_192k_fallback"
                else:
                    raise RuntimeError(f"FFmpeg could not merge tracks: {fallback['stderr'].strip()}")
        else:
            if strategy == "auto" and _compatible_formats(source_info):
                stream_result = _run_stream_copy(ordered, concat_file, temporary_output, ffmpeg)
                stream_attempt: dict[str, Any] = {"method": "stream_copy", **stream_result}
                if stream_result["returncode"] == 0:
                    try:
                        rendered = _validate_output(temporary_output, ffmpeg, ffprobe)
                        difference = rendered["duration_seconds"] - expected_duration
                        tolerance = _duration_tolerance(len(ordered))
                        stream_attempt.update({
                            "output_duration_seconds": rendered["duration_seconds"],
                            "duration_difference_seconds": difference,
                            "duration_tolerance_seconds": tolerance,
                            "decode_valid": True,
                        })
                        if abs(difference) <= tolerance:
                            selected_method = "stream_copy"
                        else:
                            stream_attempt["rejected_reason"] = "duration_mismatch"
                    except Exception as exc:
                        stream_attempt["rejected_reason"] = f"output_validation_failed: {exc}"
                attempts.append(stream_attempt)
            elif strategy == "auto":
                attempts.append({
                    "method": "stream_copy",
                    "skipped": True,
                    "reason": "source_audio_formats_are_incompatible",
                })

            if selected_method != "stream_copy":
                temporary_output.unlink(missing_ok=True)
                pcm_details = _run_pcm_merge(
                    ordered, temporary_output, ffmpeg, ffprobe, output.parent,
                )
                rendered = _validate_output(temporary_output, ffmpeg, ffprobe)
                difference = rendered["duration_seconds"] - expected_duration
                tolerance = _duration_tolerance(len(ordered))
                attempts.append({
                    **pcm_details,
                    "output_duration_seconds": rendered["duration_seconds"],
                    "duration_difference_seconds": difference,
                    "duration_tolerance_seconds": tolerance,
                    "decode_valid": True,
                })
                if abs(difference) > tolerance:
                    raise RuntimeError(
                        "PCM merged output duration differs from the source duration sum by "
                        f"{difference:.3f}s, exceeding the {tolerance:.3f}s tolerance."
                    )
                selected_method = "pcm_24bit_then_mp3_320k"

        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise RuntimeError("FFmpeg did not produce a valid output file.")

        if diagnostics is not None:
            diagnostics.update({
                "strategy": strategy,
                "attempts": attempts,
                "selected_method": selected_method,
                "source_formats": source_info,
                "source_duration_sum_seconds": expected_duration,
            })
        temporary_output.replace(output)
    except Exception:
        if diagnostics is not None:
            diagnostics.update({
                "strategy": strategy,
                "attempts": attempts,
                "selected_method": selected_method,
                "source_formats": source_info,
                "source_duration_sum_seconds": expected_duration,
            })
        raise
    finally:
        concat_file.unlink(missing_ok=True)
        temporary_output.unlink(missing_ok=True)
