"""Shared production MP3 artwork and metadata handling."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, ID3, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TRCK


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
            index = 2
            while index + 9 < len(data):
                if data[index] != 0xFF:
                    index += 1
                    continue
                marker = data[index + 1]
                length = int.from_bytes(data[index + 2:index + 4], "big")
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    return int.from_bytes(data[index + 7:index + 9], "big"), int.from_bytes(data[index + 5:index + 7], "big")
                index += 2 + length
    except (IndexError, ValueError):
        pass
    return None, None


def _extract_artwork(tracks: list[Path], artwork_dir: Path) -> dict[str, Any]:
    """Extract source covers in canonical order and select the first valid image."""
    artwork_dir.mkdir(parents=True, exist_ok=True)
    found: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    saved_hashes: set[str] = set()
    for path in tracks:
        for picture_index, picture in enumerate(_id3(path).getall("APIC"), start=1):
            data = bytes(picture.data)
            if not data:
                continue
            mime = picture.mime or "application/octet-stream"
            if mime not in {"image/jpeg", "image/png"}:
                continue
            if mime == "image/jpeg" and not data.startswith(b"\xff\xd8"):
                continue
            if mime == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
                continue
            digest = hashlib.sha256(data).hexdigest()
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
            if digest not in saved_hashes:
                extension = ".jpg" if mime == "image/jpeg" else ".png"
                target = artwork_dir / (
                    f"cover-source-track-{int(path.stem.split(' - ', 1)[0]):02d}-"
                    f"{picture_index:02d}{extension}"
                )
                target.write_bytes(data)
                record["path"] = str(target)
                saved_hashes.add(digest)
                if chosen is None:
                    chosen = {**record, "path": str(target)}
            else:
                record["duplicate_of_sha256"] = digest
            found.append(record)
    result = {
        "artwork_found": chosen is not None,
        "pictures": found,
        "selected": chosen,
        "selection_policy": "first valid embedded JPEG or PNG in canonical track order; every distinct source image is preserved for review",
    }
    (artwork_dir / "cover-info.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def _write_metadata(
    mp3: Path,
    episode: Any,
    plan: dict[str, Any],
    tracks: list[Path],
    artwork: dict[str, Any],
) -> dict[str, Any]:
    """Write and read back all supported episode, source, and cover metadata."""
    tags = ID3()
    title = f"TKKG {episode.number:03d}: {episode.title}"
    album = plan.get("spotify_album_title")
    values: dict[str, Any] = {
        "title": {"value": title, "source": "TKKGData episode number and title"},
    }
    if album:
        values["album"] = {"value": album, "source": "TKKGData verified Spotify album title"}
    fields = [
        ("artist", "TPE1", TPE1),
        ("album_artist", "TPE2", TPE2),
        ("genre", "TCON", TCON),
        ("date", "TDRC", TDRC),
    ]
    tags.add(TIT2(encoding=3, text=title))
    if album:
        tags.add(TALB(encoding=3, text=album))
    for key, frame, frame_type in fields:
        value = _consistent_source_tag(tracks, frame)
        if value:
            values[key] = {
                "value": value,
                "source": f"consistent embedded {key.replace('_', ' ')} tag across source tracks",
            }
            tags.add(frame_type(encoding=3, text=value))
    tags.add(TRCK(encoding=3, text="1/1"))
    selected = artwork.get("selected")
    expected_image = None
    if selected:
        expected_image = Path(selected["path"]).read_bytes()
        tags.add(APIC(
            encoding=3, mime=selected["mime"], type=3,
            desc="Cover", data=expected_image,
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
    expected = {"title": title, "track": "1/1", "artwork_count": 1 if selected else 0}
    if album:
        expected["album"] = album
    for key in ("artist", "album_artist", "genre", "date"):
        if key in values:
            expected[key] = values[key]["value"]
    for key, value in expected.items():
        if verified[key] != value:
            raise RuntimeError(f"Final MP3 metadata read-back failed for {key}: {verified[key]!r}")
    if selected:
        pictures = readback.getall("APIC")
        if not pictures or bytes(pictures[0].data) != expected_image:
            raise RuntimeError("Final MP3 cover artwork does not match the extracted source image.")
        if pictures[0].mime != selected["mime"]:
            raise RuntimeError("Final MP3 cover artwork MIME type does not match the source image.")
    return {
        "fields": values,
        "readback": verified,
        "artwork_embedded": bool(selected),
        "artwork_verified": bool(selected),
        "verified": True,
    }


def finalize_metadata(
    mp3: Path,
    episode: Any,
    plan: dict[str, Any],
    tracks: list[Path],
    artwork_dir: Path,
) -> dict[str, Any]:
    artwork = _extract_artwork(tracks, artwork_dir)
    result = _write_metadata(mp3, episode, plan, tracks, artwork)
    result["artwork"] = artwork
    return result
