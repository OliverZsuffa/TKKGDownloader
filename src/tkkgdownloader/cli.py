"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .downloader import download_episode
from .episodes import fetch_catalog, get_episode


def parse_episode_spec(value: str) -> list[int]:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("Enter an episode number or range, e.g. 1 or 1-10.")
    if "-" in value:
        parts = value.split("-")
        if len(parts) != 2 or not all(part.strip().isdigit() for part in parts):
            raise argparse.ArgumentTypeError("Invalid range. Use the format 1-10.")
        start, end = (int(part.strip()) for part in parts)
        if start < 1 or end < 1 or end < start:
            raise argparse.ArgumentTypeError("The range must be positive and its end must not precede its start.")
        if end - start > 499:
            raise argparse.ArgumentTypeError("A single run is limited to 500 episodes.")
        return list(range(start, end + 1))
    if not value.isdigit() or int(value) < 1:
        raise argparse.ArgumentTypeError("Episode number must be a positive integer.")
    return [int(value)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tkkg",
        description="Download a TKKG episode as one MP3 file.",
    )
    parser.add_argument("episodes", type=parse_episode_spec, help="Episode number or inclusive range, e.g. 1 or 1-10")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory (default: ./output)")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files.")
    parser.add_argument("--yes", action="store_true", help="Accept the Spotify release selected by spotDL without prompting.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        catalog = fetch_catalog()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    failures = 0
    completed = 0
    for number in args.episodes:
        try:
            episode = get_episode(catalog, number)
            print(f"\n=== TKKG {episode.number:03d}: {episode.title} ===")
            result = download_episode(
                episode,
                args.output_dir,
                overwrite=args.overwrite,
                assume_yes=args.yes,
            )
            if result is not None:
                completed += 1
        except Exception as exc:
            failures += 1
            print(f"ERROR episode {number}: {exc}", file=sys.stderr)

    print(f"\nFinished. Created or already present: {completed}. Failed: {failures}.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
