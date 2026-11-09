# Notes: Request 004

## Planning findings
- The previous downloader read episode numbers and titles from TKKGTracker and resolved Spotify metadata independently with spotDL.
- Episode 150 previously yielded 40 actual Spotify track records despite an inconsistent summary count. The new downloader must use the complete verified cross-provider track mapping.
- TKKGData now owns episode metadata, source scraping, Spotify and YouTube Music discovery, verification, schema, and publication.
- TKKGData Request 002 adds the exact Spotify track URL and ID to each individually verified YouTube Music song record.
- spotDL 4.5.2 supports pairing a YouTube Music album URL with a Spotify album URL, and a YouTube watch URL with its corresponding Spotify track URL.

## Implementation status

Implemented on this request branch:
- Replaced the TKKGTracker endpoint with TKKGData episode JSON and dataset metadata endpoints.
- Added schema major version, metadata count, record structure, duplicate number, numbering gap, title, and required array validation.
- Extended the Episode model to carry optional audio_release metadata.
- Added strict verification of Spotify album and track IDs against their URLs.
- Added strict verification of YouTube Music playlist and song IDs against their URLs.
- Added cross-provider track count and contiguous order validation.
- Implemented playlist and Spotify album pairing as the preferred download path.
- Implemented exact individual YouTube Music song and Spotify track URL pairs as fallback, including fallback after playlist download failure.
- Removed the independent Spotify resolver and all runtime text discovery.
- Added automated tests for data loading, schema compatibility, source selection, invalid mappings, playlist fallback, and download completeness.
- Preserved CLI syntax, range handling, output naming, overwrite protection, progress messages, FFmpeg merge, and local file behaviour.
- Updated README, project instructions, knowledge base, and approved decisions.
- Added GitHub Actions tests and a live TKKGData contract smoke test.

## Test results

GitHub Actions run 42699939555 passed:
- All 28 Python unit tests passed.
- The tests mock network and subprocess calls and do not download real audio.

GitHub Actions run 42699797937 also passed the project install, compileall, and 27 unit tests before the additional playlist type regression test was added.

GitHub Actions run 42700122396 passed:
- Project installation and Python module compilation passed.
- The live TKKGData smoke test fetched 243 records from the main endpoint and verified episode 150's title.
- All 28 unit tests passed.

The spotDL 4.5.2 source was inspected directly to confirm the supported manual pairing formats: YouTube Music album URL with Spotify album URL, and YouTube watch URL with Spotify track URL. No real audio download was performed in CI.

At the time of this note, the initial TKKGData catalogue contains no verified audio_release mapping yet. The audio enrichment workflow is being corrected and run separately. The downloader will correctly reject an episode until TKKGData contains a complete verified mapping.

## Remaining verification

- No real audio download or FFmpeg merge was run in CI.
- TKKGData currently has no verified audio_release record in its initial catalogue snapshot. Episode 150 must first pass live audio enrichment and be written to TKKGData before the downloader can produce it.
- Windows manual tests for episode 150, a different track count, range processing, playback, and overwrite protection remain pending.
