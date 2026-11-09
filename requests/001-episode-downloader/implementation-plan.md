# Implementation Plan: Request 001

## Status

Implemented, automated tests passed, and merged into `main`. Real Windows integration verification remains pending.

## Implemented structure

```text
src/tkkgdownloader/
├── __init__.py
├── cli.py
├── downloader.py
├── episodes.py
├── merger.py
└── spotify.py
tests/
└── test_core.py
tkkg.py
pyproject.toml
```

## Implemented processing pipeline

1. Parse a single positive episode number or an inclusive range.
2. Fetch and parse the current TKKGTracker episode JSON.
3. Resolve the official episode title.
4. Build an album search query using the zero-padded episode number and title.
5. Invoke spotDL with the album query, MP3 output, a consistent 192 kbps bitrate, and an album based output directory.
6. Verify that MP3 files were created in exactly one album folder.
7. Sort files by their track number in the output filename and reject missing or duplicate track numbering.
8. Display the selected album and track list for user confirmation. The `--yes` flag skips this confirmation.
9. Merge with FFmpeg using stream copy first, with a 192 kbps MP3 re-encode fallback if stream copy fails.
10. Write to a temporary output and move it into place only after FFmpeg succeeds.
11. Continue processing later episodes if an episode in a requested range fails.

## Design notes

- No Spotify API credentials are required by the application. The query is passed to spotDL.
- spotDL uses Spotify metadata and searches YouTube for matching audio. It does not retrieve audio directly from Spotify.
- The TKKGTracker `tracks` array is not used to choose or order Spotify tracks.
- The album search query uses spotDL's documented `album:` search prefix.
- The application uses only the Python standard library at runtime. spotDL and FFmpeg are external prerequisites.
- The release confirmation currently occurs after spotDL has downloaded the tracks, but before the final merged MP3 is created.
- The application does not yet independently compare the selected release against multiple Spotify search candidates. The user should inspect the displayed album and track list before accepting it.

## Automated tests

The GitHub Actions unit test job passed on the final feature branch commit.

Run locally with:

```powershell
py -m unittest discover -s tests -v
```

## Manual verification still required

1. Run `python tkkg.py --help`.
2. Download one known episode and inspect the album name and track list.
3. Confirm the merged MP3 plays correctly and preserves the track order.
4. Run a short range and verify one output file per episode.
5. Verify overwrite protection and the `--overwrite` option.
