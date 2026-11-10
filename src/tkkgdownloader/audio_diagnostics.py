"""Quality-first diagnostics and independent merge candidates for a TKKG release."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, ID3, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TRCK


def _run(command: list[str], *, timeout: int | None = None) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def _tool_version(executable: str) -> str:
    result = _run([executable, "-version"])
    return (result["stdout"] or result["stderr"]).splitlines()[0] if result["returncode"] == 0 else "unavailable"


def _probe(path: Path, ffprobe: str) -> dict[str, Any]:
    result = _run([
        ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)
    ])
    if result["returncode"] != 0:
        raise RuntimeError(f"FFprobe failed for {path.name}: {result['stderr'].strip()}")
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"FFprobe returned malformed JSON for {path.name}.") from exc


def _decode(path: Path, ffmpeg: str) -> dict[str, Any]:
    return _run([
        ffmpeg, "-hide_banner", "-v", "error", "-xerror", "-i", str(path),
        "-map", "0:a:0", "-f", "null", "-"
    ])


def _id3(path: Path) -> ID3:
    try:
        return ID3(path)
    except Exception:
        return ID3()


def _tag_text(tags: ID3, frame: str) -> str | None:
    values = tags.getall(frame)
    if not values:
        return None
    value = getattr(values[0], "text", None)
    return str(value[0]).strip() if value else None


def _consistent_source_tag(tracks: list[Path], frame: str) -> str | None:
    values = {_tag_text(_id3(path), frame) for path in tracks}
    values.discard(None)
    return next(iter(values)) if len(values) == 1 else None


def _image_dimensions(data: bytes, mime: str) -> tuple[int | None, int | None]:
    try:
        if mime == "image/png" and data[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        if mime == "image/jpeg" and data[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                length = int.from_bytes(data[i + 2:i + 4], "big")
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
                i += 2 + length
    except (IndexError, ValueError):
        pass
    return None, None


def _extract_artwork(tracks: list[Path], artwork_dir: Path) -> dict[str, Any]:
    artwork_dir.mkdir(parents=True, exist_ok=True)
    found: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    for path in tracks:
        for picture in _id3(path).getall("APIC"):
            data = bytes(picture.data)
            if not data:
                continue
            digest = hashlib.sha256(data).hexdigest()
            mime = picture.mime or "application/octet-stream"
            width, height = _image_dimensions(data, mime)
            record = {
                "source_track": path.name,
                "mime": mime,
                "description": picture.desc,
                "size_bytes": len(data),
                "sha256": digest,
                "width": width,
                "height": height,
            }
            found.append(record)
            if chosen is None:
                extension = {"image/jpeg": ".jpg", "image/png": ".png"}.get(mime, ".img")
                target = artwork_dir / f"cover-original{extension}"
                target.write_bytes(data)
                chosen = {**record, "path": str(target)}
    result = {
        "artwork_found": bool(found),
        "pictures": found,
        "selected": chosen,
        "selection_policy": "first valid embedded picture in canonical track order",
    }
    (artwork_dir / "cover-info.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _write_metadata(mp3: Path, episode: Any, plan: dict[str, Any], tracks: list[Path], artwork: dict[str, Any]) -> dict[str, Any]:
    tags = ID3()
    title = f"TKKG {episode.number:03d}: {episode.title}"
    album = plan.get("spotify_album_title")
    values: dict[str, Any] = {
        "title": {"value": title, "source": "TKKGData episode number and title"},
        "album": {"value": album, "source": "TKKGData verified Spotify album title"},
    }
    fields = [
        ("artist", "TPE1", "artist"),
        ("album_artist", "TPE2", "album artist"),
        ("genre", "TCON", "genre"),
        ("date", "TDRC", "recording date"),
    ]
    frames = {"TPE1": TPE1, "TPE2": TPE2, "TCON": TCON, "TDRC": TDRC}
    for key, frame, label in fields:
        value = _consistent_source_tag(tracks, frame)
        if value:
            values[key] = {"value": value, "source": f"consistent embedded {label} tag across source tracks"}
    tags.add(TIT2(encoding=3, text=title))
    if album:
        tags.add(TALB(encoding=3, text=album))
    for key, frame, _ in fields:
        if key in values:
            tags.add(frames[frame](encoding=3, text=values[key]["value"]))
    tags.add(TRCK(encoding=3, text="1/1"))
    selected = artwork.get("selected")
    if selected:
        image_path = Path(selected["path"])
        tags.add(APIC(
            encoding=3, mime=selected["mime"], type=3,
            desc="Cover", data=image_path.read_bytes()
        ))
    tags.save(mp3, v2_version=3)

    readback = ID3(mp3)
    verified = {
        "title": _tag_text(readback, "TIT2"),
        "album": _tag_text(readback, "TALB"),
        "artist": _tag_text(readback, "TPE1"),
        "album_artist": _tag_text(readback, "TPE2"),
        "genre": _tag_text(readback, "TCON"),
        "date": _tag_text(readback, "TDRC"),
        "track": _tag_text(readback, "TRCK"),
        "artwork_count": len(readback.getall("APIC")),
    }
    expected = {
        "title": title, "album": album, "track": "1/1",
        "artwork_count": 1 if selected else 0,
    }
    for key, value in expected.items():
        if verified[key] != value:
            raise RuntimeError(f"Final MP3 metadata read-back failed for {key}: {verified[key]!r}")
    if selected and bytes(readback.getall("APIC")[0].data) != Path(selected["path"]).read_bytes():
        raise RuntimeError("Final MP3 cover artwork does not match the extracted source image.")
    return {"fields": values, "readback": verified, "verified": True}


def _audio_stream(probe: dict[str, Any]) -> dict[str, Any]:
    return next((stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"), {})


def _duration(probe: dict[str, Any]) -> float:
    stream = _audio_stream(probe)
    value = stream.get("duration") or probe.get("format", {}).get("duration")
    return float(value) if value is not None else 0.0


def _inspect_sources(tracks: list[Path], ffmpeg: str, ffprobe: str, reports: Path) -> tuple[list[dict[str, Any]], list[float]]:
    records: list[dict[str, Any]] = []
    durations: list[float] = []
    for index, path in enumerate(tracks, start=1):
        probe = _probe(path, ffprobe)
        stream = _audio_stream(probe)
        decode = _decode(path, ffmpeg)
        duration = _duration(probe)
        durations.append(duration)
        silence = _run([
            ffmpeg, "-hide_banner", "-nostats", "-i", str(path),
            "-af", "silencedetect=noise=-60dB:d=5", "-f", "null", "-"
        ])
        record = {
            "track_number": index,
            "title": path.stem.split(" - ", 1)[-1],
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "duration_seconds": duration,
            "codec": stream.get("codec_name"),
            "bit_rate": stream.get("bit_rate") or probe.get("format", {}).get("bit_rate"),
            "sample_rate": stream.get("sample_rate"),
            "channels": stream.get("channels"),
            "channel_layout": stream.get("channel_layout"),
            "start_time": stream.get("start_time"),
            "decode_returncode": decode["returncode"],
            "decode_stderr": decode["stderr"],
            "silence_diagnostic": silence["stderr"],
            "probe": probe,
        }
        records.append(record)
        print(f"Inspected track {index}/{len(tracks)}: {path.name}", flush=True)
    positive = [item for item in durations if item > 0]
    median = sorted(positive)[len(positive) // 2] if positive else 0
    for record in records:
        flags = []
        if record["decode_returncode"] != 0:
            flags.append("full_decode_failed")
        if median and abs(record["duration_seconds"] - median) > max(30, median * 0.2):
            flags.append("duration_outlier")
        if record["size_bytes"] < 16_384:
            flags.append("unusually_small_file")
        if "silence_start" in record["silence_diagnostic"]:
            flags.append("long_silence_detected_review_required")
        record["flags"] = flags
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "source-inspection.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["Source inspection", ""]
    for item in records:
        lines.append(
            f'{item["track_number"]:02d}. {item["filename"]} | {item["duration_seconds"]:.3f}s | '
            f'{item["codec"]} | {item["size_bytes"]} bytes | decode exit {item["decode_returncode"]} | '
            f'flags: {", ".join(item["flags"]) or "none"}'
        )
    (reports / "source-inspection.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return records, durations


def _concat_file(paths: list[Path], target: Path) -> None:
    def quote(path: Path) -> str:
        return "'" + path.resolve().as_posix().replace("'", "'\\''") + "'"
    target.write_text("".join(f"file {quote(path)}\n" for path in paths), encoding="utf-8")


def _validate_output(path: Path, ffmpeg: str, ffprobe: str) -> dict[str, Any]:
    probe = _probe(path, ffprobe)
    decode = _decode(path, ffmpeg)
    if decode["returncode"] != 0:
        raise RuntimeError(f"Full decode validation failed for {path.name}: {decode['stderr'].strip()}")
    return {
        "path": str(path), "size_bytes": path.stat().st_size,
        "duration_seconds": _duration(probe),
        "codec": _audio_stream(probe).get("codec_name"),
        "bit_rate": _audio_stream(probe).get("bit_rate") or probe.get("format", {}).get("bit_rate"),
        "sample_rate": _audio_stream(probe).get("sample_rate"),
        "channels": _audio_stream(probe).get("channels"),
        "decode_returncode": decode["returncode"],
        "decode_stderr": decode["stderr"],
    }


def _make_boundaries(tracks: list[Path], durations: list[float], ffmpeg: str, review: Path) -> list[dict[str, Any]]:
    review.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    boundaries: list[dict[str, Any]] = []
    elapsed = 0.0
    for index in range(len(tracks) - 1):
        left, right = tracks[index], tracks[index + 1]
        left_duration = durations[index]
        timestamp = elapsed + left_duration
        before = review / f"boundary-{index + 1:02d}-before.wav"
        after = review / f"boundary-{index + 1:02d}-after.wav"
        before_start = max(0.0, left_duration - 10.0)
        for source, output, start, length in (
            (left, before, before_start, left_duration - before_start),
            (right, after, 0.0, min(10.0, durations[index + 1])),
        ):
            result = _run([
                ffmpeg, "-hide_banner", "-v", "error", "-y", "-ss", f"{start:.6f}",
                "-i", str(source), "-t", f"{length:.6f}", "-vn",
                "-acodec", "pcm_s24le", str(output)
            ])
            if result["returncode"] != 0 or not output.is_file():
                raise RuntimeError(f"Could not create boundary excerpt for {source.name}: {result['stderr']}")
        clips.extend((before, after))
        boundaries.append({
            "boundary": index + 1,
            "from_track": left.name,
            "to_track": right.name,
            "expected_timestamp_seconds": round(timestamp, 6),
            "before_excerpt": str(before),
            "after_excerpt": str(after),
        })
        elapsed = timestamp
    concat = review / "boundary-concat.txt"
    _concat_file(clips, concat)
    output = review / "track-boundaries.wav"
    result = _run([ffmpeg, "-hide_banner", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "pcm_s24le", str(output)])
    if result["returncode"] != 0:
        raise RuntimeError(f"Could not assemble boundary review: {result['stderr']}")
    (review / "boundary-index.txt").write_text(
        "\n".join(
            f'{b["boundary"]:02d}. {b["from_track"]} -> {b["to_track"]} at {b["expected_timestamp_seconds"]:.3f}s'
            for b in boundaries
        ) + "\n", encoding="utf-8"
    )
    concat.unlink(missing_ok=True)
    for clip in clips:
        clip.unlink(missing_ok=True)
    return boundaries


def run_episode_diagnostics(
    episode: Any, plan: dict[str, Any], tracks: list[Path], workspace: Path,
    *, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe",
) -> Path:
    """Preserve source files and build validated comparison candidates and reports."""
    tracks = sorted(tracks, key=lambda item: int(item.stem.split(" - ", 1)[0]))
    if len(tracks) != plan["track_count"]:
        raise RuntimeError(f"Expected {plan['track_count']} canonical tracks, received {len(tracks)}.")
    if [int(path.stem.split(" - ", 1)[0]) for path in tracks] != list(range(1, len(tracks) + 1)):
        raise RuntimeError("Canonical track numbering is incomplete or out of order.")
    for path in tracks:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty source track: {path}")

    reports = workspace / "reports"
    pcm_dir = workspace / "pcm"
    candidates = workspace / "candidates"
    review = workspace / "review"
    artwork_dir = workspace / "artwork"
    for folder in (reports, pcm_dir, candidates, review, artwork_dir):
        folder.mkdir(parents=True, exist_ok=True)

    versions = {"ffmpeg": _tool_version(ffmpeg), "ffprobe": _tool_version(ffprobe)}
    source_records, durations = _inspect_sources(tracks, ffmpeg, ffprobe, reports)
    failed = [item for item in source_records if item["decode_returncode"] != 0]
    if failed:
        raise RuntimeError(
            "At least one source track failed a complete decode. All source files and reports were retained. "
            f"See {reports / 'source-inspection.txt'}"
        )

    artwork = _extract_artwork(tracks, artwork_dir)
    stream_copy = candidates / f"episode-{episode.number:03d}-stream-copy.mp3"
    if stream_copy.exists():
        raise FileExistsError(stream_copy)
    from .merger import merge_tracks
    merge_tracks(tracks, stream_copy, ffmpeg=ffmpeg)
    stream_result = _validate_output(stream_copy, ffmpeg, ffprobe)

    rates: dict[int, int] = {}
    channels: dict[int, int] = {}
    for item in source_records:
        try:
            rate = int(item["sample_rate"])
            channel_count = int(item["channels"])
            rates[rate] = rates.get(rate, 0) + 1
            channels[channel_count] = channels.get(channel_count, 0) + 1
        except (TypeError, ValueError):
            continue
    sample_rate = max(rates, key=rates.get) if rates else 44100
    channel_count = max(channels, key=channels.get) if channels else 2
    pcm_bytes = int(sum(durations) * sample_rate * channel_count * 3)
    free_bytes = shutil.disk_usage(workspace).free
    if free_bytes < pcm_bytes * 3:
        raise RuntimeError(
            f"Insufficient free disk space for PCM processing. Estimated temporary need: "
            f"{pcm_bytes * 3:,} bytes; available: {free_bytes:,} bytes."
        )

    segments_dir = pcm_dir / "segments"
    segments_dir.mkdir(exist_ok=True)
    wavs: list[Path] = []
    for index, path in enumerate(tracks, start=1):
        wav = segments_dir / f"{index:02d}.wav"
        result = _run([
            ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(path),
            "-map", "0:a:0", "-ar", str(sample_rate), "-ac", str(channel_count),
            "-c:a", "pcm_s24le", str(wav)
        ])
        if result["returncode"] != 0:
            raise RuntimeError(f"PCM conversion failed for {path.name}: {result['stderr']}")
        wavs.append(wav)
    pcm_list = pcm_dir / "segments.txt"
    _concat_file(wavs, pcm_list)
    master = pcm_dir / f"episode-{episode.number:03d}-master.wav"
    if master.exists():
        raise FileExistsError(master)
    result = _run([
        ffmpeg, "-hide_banner", "-v", "error", "-y", "-f", "concat", "-safe", "0",
        "-i", str(pcm_list), "-c:a", "pcm_s24le", str(master)
    ])
    if result["returncode"] != 0:
        raise RuntimeError(f"PCM master concatenation failed: {result['stderr']}")
    pcm_list.unlink(missing_ok=True)
    for wav in wavs:
        wav.unlink(missing_ok=True)
    segments_dir.rmdir()
    master_result = _validate_output(master, ffmpeg, ffprobe)

    encoded = candidates / f"episode-{episode.number:03d}-pcm-320k.mp3"
    if encoded.exists():
        raise FileExistsError(encoded)
    result = _run([
        ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(master),
        "-c:a", "libmp3lame", "-b:a", "320k", "-q:a", "0", str(encoded)
    ])
    if result["returncode"] != 0:
        raise RuntimeError(f"320 kbit/s MP3 encoding failed: {result['stderr']}")
    encoded_result = _validate_output(encoded, ffmpeg, ffprobe)
    metadata = _write_metadata(encoded, episode, plan, tracks, artwork)
    encoded_result["metadata"] = metadata
    boundaries = _make_boundaries(tracks, durations, ffmpeg, review)

    expected_duration = sum(durations)
    comparison = {
        "episode": {"number": episode.number, "title": episode.title},
        "track_count": len(tracks),
        "tool_versions": versions,
        "pcm_parameters": {"sample_rate": sample_rate, "channels": channel_count, "sample_format": "pcm_s24le"},
        "source_duration_sum_seconds": expected_duration,
        "stream_copy": stream_result,
        "pcm_master": master_result,
        "pcm_320k_mp3": encoded_result,
        "duration_differences_seconds": {
            "stream_copy_vs_sources": stream_result["duration_seconds"] - expected_duration,
            "pcm_master_vs_sources": master_result["duration_seconds"] - expected_duration,
            "pcm_mp3_vs_sources": encoded_result["duration_seconds"] - expected_duration,
        },
        "artwork": artwork,
        "boundaries": boundaries,
        "source_flags": [
            {"track": item["filename"], "flags": item["flags"]}
            for item in source_records if item["flags"]
        ],
        "conclusion": (
            "All source tracks decoded successfully. Compare both independently validated candidates "
            "and listen to the lossless boundary review before selecting a final file."
        ),
        "outputs": {
            "source_tracks": [str(path) for path in tracks],
            "pcm_master": str(master),
            "stream_copy": str(stream_copy),
            "pcm_mp3": str(encoded),
            "boundary_review": str(review / "track-boundaries.wav"),
        },
    }
    report_path = reports / "merge-comparison.json"
    report_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    (reports / "boundary-analysis.json").write_text(json.dumps(boundaries, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = [
        f'TKKG {episode.number:03d}: {episode.title}',
        f'Source tracks: {len(tracks)}',
        f'Source duration sum: {expected_duration:.3f}s',
        f'Stream copy: {stream_result["duration_seconds"]:.3f}s, {stream_result["size_bytes"]} bytes',
        f'PCM master: {master_result["duration_seconds"]:.3f}s, {master_result["size_bytes"]} bytes',
        f'320 kbit/s MP3: {encoded_result["duration_seconds"]:.3f}s, {encoded_result["size_bytes"]} bytes',
        f'Artwork: {"embedded and verified" if artwork["artwork_found"] else "not present in source parts"}',
        f'Metadata: {"verified" if metadata["verified"] else "not verified"}',
        f'Boundary review: {len(boundaries)} transitions',
        f'Report: {report_path}',
    ]
    (reports / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary), flush=True)
    return report_path
