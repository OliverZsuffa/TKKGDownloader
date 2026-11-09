# Implementation Plan: Request 002

## Status

Approved by Oliver. Implementation completed on branch `fix/spotify-album-resolution`. Automated tests and GitHub Actions verification are pending. Real Windows integration verification is pending.

## Implementation summary

- Replaced the failed Spotify album text search with a first-chapter track lookup.
- Used spotDL's metadata-only `save` operation to resolve the first track and obtain its album ID.
- Validated the first-track artist, exact episode title and part number, album ID, album name, and track count.
- Resolved the album's complete metadata from its direct Spotify album URL before downloading.
- Validated album identity, metadata track count, and unique track numbers.
- Downloaded the resolved album URL and checked that the number of downloaded MP3 files matches Spotify's `tracks_count`.
- Kept numeric track ordering, confirmation, `--yes`, FFmpeg merging, range handling, and overwrite protection.

## Files changed

- `src/tkkgdownloader/spotify.py`
- `src/tkkgdownloader/downloader.py`
- `tests/test_core.py`

## Verification

- Automated tests: pending.
- GitHub Actions: pending.
- Manual Windows test with episode 150: pending.
- Manual test with a second episode: pending.
- Playback and range verification: pending.

## Notes

spotDL's `save` operation writes metadata to a JSON `.spotdl` file without downloading audio. The implementation uses that file for deterministic metadata validation. It deliberately uses Spotify's `tracks_count` field rather than `list_length`, which can describe a broader playlist context and did not match the album track count in the observed episode 150 metadata.

spotDL uses Spotify metadata and searches YouTube for matching audio. It does not download audio directly from Spotify.
