"""Safe, deterministic import and auditable validation of Spotisaver MP3 downloads."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import stat
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from mutagen.id3 import ID3


def _normalize(value: str) -> str:
    """Normalise harmless filename differences without permitting partial matches."""
    value = unicodedata.normalize("NFKC", value).casefold()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return "".join(char for char in value if char.isalnum())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tag_value(tags: ID3, frame: str) -> str | None:
    values = tags.getall(frame)
    if not values:
        return None
    value = getattr(values[0], "text", None)
    return str(value[0]).strip() if value else None


def _read_embedded_metadata(path: Path) -> tuple[dict[str, str | None], str, list[str]]:
    fields = {
        "title": "TIT2",
        "artist": "TPE1",
        "album": "TALB",
        "track_number": "TRCK",
        "disc_number": "TPOS",
    }
    try:
        tags = ID3(path)
    except Exception as exc:
        return ({key: None for key in fields}, "unavailable", [f"ID3 metadata unavailable: {type(exc).__name__}"])
    values = {key: _tag_value(tags, frame) for key, frame in fields.items()}
    return values, "read", []


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


def _validate_expected_tracks(expected_tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not expected_tracks:
        raise RuntimeError("TKKGData supplied no expected audio tracks.")
    numbers: list[int] = []
    normalized_titles: dict[str, int] = {}
    for track in expected_tracks:
        number = track.get("track_number")
        title = track.get("spotify_title")
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise RuntimeError(f"TKKGData contains an invalid track number: {number!r}.")
        if not isinstance(title, str) or not title.strip():
            raise RuntimeError(f"TKKGData track {number} has an empty or invalid Spotify title.")
        key = _normalize(title)
        if not key:
            raise RuntimeError(f"TKKGData track {number} has a title that cannot be normalised.")
        if key in normalized_titles:
            other = normalized_titles[key]
            raise RuntimeError(
                f"TKKGData tracks {other} and {number} have colliding normalised titles. "
                "The source mapping is ambiguous."
            )
        normalized_titles[key] = number
        numbers.append(number)
    if len(numbers) != len(set(numbers)):
        raise RuntimeError("TKKGData contains duplicate track numbers.")
    if sorted(numbers) != list(range(1, len(numbers) + 1)):
        raise RuntimeError("TKKGData track numbers must form a contiguous one-based sequence.")
    return sorted(expected_tracks, key=lambda item: item["track_number"])


def _filename_candidates(path: Path, expected_number: int) -> list[tuple[str, str]]:
    """Return exact title candidates after removing recognised provider wrappers."""
    stem = path.stem.strip()
    candidates: list[tuple[str, str]] = [(stem, "exact_normalized_filename")]
    wrapped = re.sub(r"^TKKG\s*[-_.]+\s*", "", stem, flags=re.I)
    wrapped = re.sub(r"\s*\(SPOTISAVER\)\s*$", "", wrapped, flags=re.I)
    if wrapped != stem:
        candidates.append((wrapped, "exact_normalized_filename_after_provider_wrapper"))
    prefix = re.match(r"^\s*(\d{1,3})\s*[._-]+\s*(.+)$", wrapped)
    if prefix and int(prefix.group(1)) == expected_number:
        candidates.append((prefix.group(2), "exact_normalized_title_after_matching_track_prefix"))
    unique: dict[str, str] = {}
    for value, rule in candidates:
        key = _normalize(value)
        if key:
            unique.setdefault(key, rule)
    return [(key, rule) for key, rule in unique.items()]


def _metadata_track_number(value: str | None) -> int | None:
    if not value:
        return None
    match = re.match(r"^\s*(\d+)(?:\s*/\s*\d+)?\s*$", value)
    return int(match.group(1)) if match else None


def _metadata_identity_matches(metadata: dict[str, str | None], number: int, album_title: str | None) -> bool:
    """Require both a track number and matching album identity for tag fallback."""
    tagged_number = _metadata_track_number(metadata.get("track_number"))
    tagged_album = _normalize(metadata.get("album") or "")
    expected_album = _normalize(album_title or "")
    return bool(tagged_number == number and expected_album and tagged_album == expected_album)


def _track_title_keys(track: dict[str, Any]) -> set[str]:
    values = [track.get("spotify_title")]
    aliases = track.get("alternate_titles", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    if isinstance(aliases, list):
        values.extend(aliases)
    return {_normalize(value) for value in values if isinstance(value, str) and _normalize(value)}


def import_audio_files(
    files: list[Path],
    expected_tracks: list[dict],
    destination: Path,
    *,
    manifest_out: dict[str, Any] | None = None,
    episode_number: int | None = None,
    episode_title: str | None = None,
    album_title: str | None = None,
) -> list[Path]:
    """Import tracks only after an exact, one-to-one filename mapping is established."""
    expected = _validate_expected_tracks(expected_tracks)
    destination.mkdir(parents=True, exist_ok=True)
    raw_dir = destination / "raw"
    raw_dir.mkdir()
    mp3s = _collect_mp3s(files, raw_dir)
    expected_count = len(expected)
    if len(mp3s) != expected_count:
        raise RuntimeError(
            f"Spotisaver returned {len(mp3s)} MP3 files, but TKKGData verifies "
            f"{expected_count} tracks. No combined file was created."
        )

    mappings: list[tuple[dict[str, Any], Path, str, dict[str, Any]]] = []
    metadata_cache = {source: _read_embedded_metadata(source) for source in mp3s}
    for track in expected:
        number = track["track_number"]
        title_keys = _track_title_keys(track)
        matches: list[tuple[Path, str, dict[str, Any]]] = []
        for source in mp3s:
            metadata, metadata_status, metadata_warnings = metadata_cache[source]
            filename_matches = [
                (rule, key) for key, rule in _filename_candidates(source, number)
                if key in title_keys
            ]
            if filename_matches:
                rule, matched_key = filename_matches[0]
                matches.append((source, rule, {
                    "evidence": "filename_title",
                    "matched_title_key": matched_key,
                    "metadata": metadata,
                    "metadata_status": metadata_status,
                    "metadata_warnings": metadata_warnings,
                }))
                continue
            tagged_title = _normalize(metadata.get("title") or "")
            if tagged_title and tagged_title in title_keys:
                matches.append((source, "exact_embedded_title", {
                    "evidence": "embedded_title",
                    "matched_title_key": tagged_title,
                    "metadata": metadata,
                    "metadata_status": metadata_status,
                    "metadata_warnings": metadata_warnings,
                }))
                continue
            if _metadata_identity_matches(metadata, number, album_title):
                matches.append((source, "verified_album_and_track_metadata", {
                    "evidence": "embedded_album_and_track_number",
                    "matched_title_key": None,
                    "metadata": metadata,
                    "metadata_status": metadata_status,
                    "metadata_warnings": metadata_warnings,
                }))
        if len(matches) != 1:
            raise RuntimeError(
                f"Could not uniquely identify source for track {number}/{expected_count} "
                f"({track['spotify_title']}). Found {len(matches)} candidates. "
                "Filename, exact embedded title, and verified album plus track number "
                "were checked. Fuzzy matching is never automatic."
            )
        source, rule, evidence = matches[0]
        if source.stat().st_size == 0:
            raise RuntimeError(f"Downloaded track {number} is empty.")
        mappings.append((track, source, rule, evidence))

    assigned = [source for _, source, _, _ in mappings]
    if len(set(assigned)) != len(mp3s) or set(assigned) != set(mp3s):
        raise RuntimeError("Spotisaver source files do not map one-to-one to the canonical tracklist.")

    source_hashes: dict[str, str] = {}
    for track, source, _, _ in mappings:
        digest = _sha256(source)
        if digest in source_hashes:
            raise RuntimeError(
                f"Tracks {source_hashes[digest]} and {track['track_number']} contain byte-identical source files. "
                "No merge was made because duplicate audio requires explicit review."
            )
        source_hashes[digest] = str(track["track_number"])

    validated: list[Path] = []
    entries: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for track, source, rule, evidence in mappings:
        number = track["track_number"]
        target = destination / f"{number:02d} - {track['spotify_title']}.mp3"
        shutil.copy2(source, target)
        source_hash = _sha256(source)
        target_hash = _sha256(target)
        if source_hash != target_hash:
            raise RuntimeError(f"Checksum mismatch after copying source track {number}. No merge was made.")
        metadata = evidence["metadata"]
        metadata_status = evidence["metadata_status"]
        metadata_warnings = evidence["metadata_warnings"]
        entry_warnings = list(metadata_warnings)
        if metadata.get("title") and _normalize(metadata["title"]) != _normalize(track["spotify_title"]):
            entry_warnings.append(
                f"Embedded title differs from canonical title: {metadata['title']!r}"
            )
        if metadata.get("track_number"):
            embedded_number = re.match(r"^\s*(\d+)", metadata["track_number"])
            if embedded_number and int(embedded_number.group(1)) != number:
                entry_warnings.append(
                    f"Embedded track number {metadata['track_number']!r} differs from canonical number {number}"
                )
        if entry_warnings:
            warnings.append({"track_number": number, "warnings": entry_warnings})
        entries.append({
            "track_number": number,
            "canonical_title": track["spotify_title"],
            "source_filename": source.name,
            "source_path": source.resolve().relative_to(destination.resolve()).as_posix(),
            "canonical_filename": target.name,
            "canonical_path": target.resolve().relative_to(destination.resolve()).as_posix(),
            "matching_rule": rule,
            "matching_evidence": evidence["evidence"],
            "matched_title_key": evidence["matched_title_key"],
            "size_bytes": source.stat().st_size,
            "source_sha256": source_hash,
            "canonical_sha256": target_hash,
            "embedded_metadata": metadata,
            "metadata_status": metadata_status,
            "warnings": entry_warnings,
        })
        validated.append(target)

    manifest = {
        "schema_version": 1,
        "episode": {
            "number": episode_number,
            "title": episode_title,
            "album_title": album_title,
        },
        "track_count": expected_count,
        "status": "warnings" if warnings else "verified",
        "warnings": warnings,
        "tracks": entries,
        "_workspace_root": str(destination.resolve()),
    }
    if manifest_out is not None:
        manifest_out.clear()
        manifest_out.update(manifest)
    return validated


def validate_track_manifest(tracks: list[Path], manifest: dict[str, Any]) -> list[Path]:
    """Verify that merger inputs still match the exact imported manifest order and bytes."""
    entries = manifest.get("tracks")
    root_value = manifest.get("_workspace_root")
    if not isinstance(entries, list) or not isinstance(root_value, str):
        raise RuntimeError("Spotisaver track manifest is missing or malformed.")
    root = Path(root_value).resolve()
    expected_paths = [ (root / entry["canonical_path"]).resolve() for entry in entries ]
    supplied_paths = [path.resolve() for path in tracks]
    if supplied_paths != expected_paths:
        raise RuntimeError("Merger inputs do not match the exact manifest-defined track order.")
    numbers = [entry.get("track_number") for entry in entries]
    if numbers != list(range(1, len(entries) + 1)):
        raise RuntimeError("Track manifest numbering is incomplete or out of order.")
    for path, entry in zip(supplied_paths, entries):
        if not path.is_file() or _sha256(path) != entry.get("canonical_sha256"):
            raise RuntimeError(
                f"Track manifest integrity check failed for {entry.get('canonical_filename', path.name)}. "
                "The source file changed after import. No merge was made."
            )
    return [Path(path) for path in supplied_paths]


def serializable_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return the portable JSON form without the runtime-only workspace path."""
    return {key: value for key, value in manifest.items() if not key.startswith("_")}
