"""spotDL integration and episode-level download orchestration."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .episodes import Episode
from .merger import merge_tracks, ordered_tracks
from .spotify import build_album_query


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
    query = build_album_query(episode)

    with tempfile.TemporaryDirectory(prefix=f"tkkg_{episode.number:03d}_") as temp:
        work_dir = Path(temp)
        output_template = "{album}/{track-number} - {title}.{output-ext}"
        command = [
            *spotdl, "download", query,
            "--format", "mp3",
            "--bitrate", "192k",
            "--output", output_template,
        ]
        print(f"Searching for: {query}")
        result = subprocess.run(command, cwd=work_dir, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"spotDL failed for episode {episode.number} (exit code {result.returncode})."
            )

        tracks = ordered_tracks(list(work_dir.rglob("*.mp3")))
        album_dirs = {track.parent for track in tracks}
        if len(album_dirs) != 1:
            found = ", ".join(sorted(path.name for path in album_dirs)) or "none"
            raise RuntimeError(
                "The search did not resolve to exactly one album folder. "
                f"Found: {found}. No combined file was created."
            )
        album_name = next(iter(album_dirs)).name
        print(f"Found release: {album_name}")
        print(f"Tracks ({len(tracks)}):")
        for track in tracks:
            print(f"  {track.name}")

        if not assume_yes:
            if not sys.stdin.isatty():
                raise RuntimeError(
                    "Confirmation is required in non-interactive mode. "
                    "Review the release and rerun with --yes to accept it."
                )
            answer = input("Merge this release into one MP3? [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Cancelled. No combined MP3 was created.")
                return None

        merge_tracks(tracks, final_path, ffmpeg=ffmpeg)
    print(f"Done: {final_path}")
    return final_path
