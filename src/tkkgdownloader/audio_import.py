"""Safe import and deterministic validation of Spotisaver MP3 downloads."""

from __future__ import annotations

import re
import shutil
import stat
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def _safe_extract(archive: Path, destination: Path) -> list[Path]:
    extracted: list[Path] = []
    root = destination.resolve()
    try:
        with zipfile.ZipFile(archive) as zipped:
            members = zipped.infolist()
            if not members:
                raise RuntimeError("Spotisaver ZIP archive is empty.")
            for member in members:
                name = member.filename.replace("\\", "/")
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or not path.parts:
                    raise RuntimeError(f"Unsafe path in Spotisaver ZIP: {member.filename!r}")
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise RuntimeError(f"Symlink in Spotisaver ZIP is not allowed: {member.filename!r}")
                target = (root / Path(*path.parts)).resolve()
                if target != root and root not in target.parents:
                    raise RuntimeError(f"Unsafe path in Spotisaver ZIP: {member.filename!r}")
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if target.suffix.lower() != ".mp3":
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                extracted.append(target)
    except zipfile.BadZipFile as exc:
        raise RuntimeError("Spotisaver returned a corrupt ZIP archive.") from exc
    return extracted


def _collect_mp3s(files: list[Path], destination: Path) -> list[Path]:
    collected: list[Path] = []
    for file in files:
        if not file.is_file():
            raise RuntimeError(f"Spotisaver download is missing: {file}")
        if file.suffix.lower() == ".zip":
            collected.extend(_safe_extract(file, destination))
        elif file.suffix.lower() == ".mp3":
            copied = destination / file.name
            if copied.exists():
                raise RuntimeError(f"Duplicate downloaded filename: {file.name}")
            shutil.copy2(file, copied)
            collected.append(copied)
        else:
            raise RuntimeError(f"Unsupported Spotisaver download type: {file.name}")
    return collected


def import_audio_files(files: list[Path], expected_tracks: list[dict], destination: Path) -> list[Path]:
    """Import downloaded MP3s and require an exact filename-to-track match."""
    destination.mkdir(parents=True, exist_ok=True)
    raw_dir = destination / "raw"
    raw_dir.mkdir()
    mp3s = _collect_mp3s(files, raw_dir)
    expected_count = len(expected_tracks)
    if len(mp3s) != expected_count:
        raise RuntimeError(
            f"Spotisaver returned {len(mp3s)} MP3 files, but TKKGData verifies "
            f"{expected_count} tracks. No combined file was created."
        )

    normalized_names = [(path, _normalize(path.stem)) for path in mp3s]
    validated: list[Path] = []
    used: set[Path] = set()
    for track in expected_tracks:
        number = track["track_number"]
        expected_title = _normalize(track["spotify_title"])
        matches = [
            path for path, filename in normalized_names
            if path not in used and expected_title and expected_title in filename
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Could not uniquely match Spotisaver's downloaded filename to track "
                f"{number}/{expected_count} ({track['spotify_title']}). "
                "The files were preserved in the temporary directory and no merge was made."
            )
        source = matches[0]
        if source.stat().st_size == 0:
            raise RuntimeError(f"Downloaded track {number} is empty.")
        target = destination / f"{number:02d} - {track['spotify_title']}.mp3"
        target.write_bytes(source.read_bytes())
        used.add(source)
        validated.append(target)

    if len(used) != len(mp3s):
        raise RuntimeError("Spotisaver returned unexpected extra audio files. No merge was made.")
    return validated
