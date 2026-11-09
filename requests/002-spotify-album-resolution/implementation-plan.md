# Implementation Plan: Request 002

## Status

Plan proposed. No application code has been changed. Implementation requires Oliver's approval.

## Problem

The current downloader builds an album search query:

```text
album:TKKG {episode number} {official episode title}
```

This fails for real releases, including episode 150, because spotDL does not find the album through its text search. Testing established that spotDL can resolve a direct Spotify track URL and a direct Spotify album URL. The first track's metadata contains the album ID and the album URL.

For episode 150, the successful metadata lookup identified:

- Album: `150/Heiße Nächte im Dezember`
- Album ID: `0ZqyFeMXxCyIJvYptGlnn1`
- First track: `150 - Heiße Nächte im Dezember - Teil 01`
- Spotify reports `tracks_count: 25`

The returned album metadata was not ordered by track number. The existing track ordering logic must therefore remain in place.

## Objective

Replace fragile album text search with a generic two-stage Spotify resolution process. The solution must work for arbitrary episodes and must not hardcode episode 150 or any Spotify IDs.

## Proposed processing pipeline

1. Retrieve the episode title from TKKGTracker as today.
2. Build a search query for the episode's first chapter track, using the episode number, official title, and `Teil 01`.
3. Use spotDL's metadata-only `save` operation to resolve that query to a Spotify track. Do not download audio at this stage.
4. Parse the resulting spotDL metadata and validate that exactly one suitable track was resolved. Confirm that the artist is TKKG, the track title identifies the requested episode and first part, and an album ID is present. If the result is ambiguous or incomplete, stop with a useful error rather than selecting an arbitrary release.
5. Read the album ID from the resolved track metadata and construct `https://open.spotify.com/album/{album_id}`.
6. Pass that direct album URL to spotDL's download operation, retaining the existing MP3 format, 192 kbps bitrate, temporary working directory, and album based output layout.
7. Discover the downloaded MP3 files and sort them by numeric track number using the existing ordering helper.
8. Validate the downloaded release before merging:
   - Exactly one album folder must have been downloaded.
   - Track numbers must be valid and unique.
   - Where spotDL metadata provides a reliable album track count, compare it with the number of downloaded files and fail clearly if they differ.
   - Do not use `list_length` as the album track count. The observed response included `tracks_count: 25` and `list_length: 40`, so the latter is not a reliable validation field for this purpose.
9. Display the resolved album name and ordered track list, then retain the existing confirmation prompt and `--yes` behavior.
10. Merge with the existing FFmpeg logic and preserve output naming, range handling, overwrite protection, temporary file cleanup, and per episode error reporting.

## Files expected to change

- `src/tkkgdownloader/spotify.py`
  - Replace the album query builder with a first track query builder.
  - Add focused helpers for validating resolved track metadata and constructing the album URL.
- `src/tkkgdownloader/downloader.py`
  - Add a metadata resolution step using spotDL's `save` command.
  - Parse the generated `.spotdl` metadata file or captured output, depending on the verified spotDL 4.5.2 behavior.
  - Download from the resolved direct album URL rather than a text album query.
  - Add album track count validation without relying on `list_length`.
- `tests/test_core.py`
  - Test first track query construction.
  - Test metadata parsing and rejection of invalid, ambiguous, or mismatched results.
  - Test album URL construction.
  - Test track count validation, including the distinction between `tracks_count` and `list_length`.
  - Test command construction using mocked subprocess calls so unit tests do not require Spotify or YouTube access.

Other files should only change if implementation reveals a concrete need.

## Compatibility and constraints

- Keep the existing CLI syntax and options unchanged.
- Keep the current Python and external dependency model. Do not add a Spotify API credential requirement.
- Keep spotDL as the metadata resolver and audio matching/downloading tool. It uses Spotify metadata and searches YouTube for matching audio; it does not download audio directly from Spotify.
- Do not hardcode episode-specific Spotify track IDs, album IDs, or titles.
- Do not use TKKGTracker chapter entries as the Spotify track list.
- Do not alter the merger unless a test exposes a directly related defect.
- Keep the confirmation safeguard. The user must be able to inspect the selected release before the final merged file is created.

## Verification plan

### Automated tests

- Run `py -m unittest discover -s tests -v`.
- Mock spotDL calls and metadata files. Tests must not depend on live Spotify or YouTube services.
- Verify failure handling for no result, malformed metadata, wrong episode, wrong artist, missing album ID, and incomplete album downloads.
- Verify that tracks are merged in numeric track order even if metadata or filesystem discovery is unordered.

### Manual Windows integration

Using the existing installation with Python 3.12, spotDL 4.5.2, and FFmpeg 6.0:

1. Run `py tkkg.py 150`.
2. Confirm the resolver identifies the album `150/Heiße Nächte im Dezember` through its first track and album ID, without using the failed album text search.
3. Confirm spotDL downloads the album and the application reports the expected track count and ordered list.
4. Accept the release and verify the resulting MP3 plays correctly from beginning to end.
5. Test at least one different episode to verify that the resolution is generic.
6. Test a short episode range and confirm one output per episode.
7. Recheck existing output protection and `--overwrite`.

A manual test is successful only if the selected album is correct, the downloaded track set is complete, and the merged audio plays in the intended order.

## Out of scope

- Replacing spotDL or implementing direct audio extraction.
- Adding a Spotify Web API client or credentials.
- Changing the CLI interface or output naming.
- Automatically choosing between multiple candidate releases without a reliable match.
- Changing unrelated download, merge, or packaging behavior.

## Approval gate

Do not implement until Oliver explicitly approves this plan. After approval, implement on a feature branch, run automated tests, perform the available integration checks, open a pull request, merge only after review, and update the Knowledge Base with the final behavior and verification results.
