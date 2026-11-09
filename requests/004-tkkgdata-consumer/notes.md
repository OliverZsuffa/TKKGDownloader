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

TKKGData now publishes a verified audio_release mapping for episode 150. It contains 40 Spotify track records, the official YouTube Music playlist, and 40 ordered individual YouTube Music song URLs paired with exact Spotify track URLs. The downloader's live CI smoke test validates this complete mapping without downloading audio.

## Latest main branch verification

- The CI consolidation was merged in pull request #5 as commit 55672e77de901c966f68d05e40b0ca68dc274a7e.
- GitHub Actions run 42708792876 passed the consolidated Tests workflow on main. This includes project installation, compileall, the live TKKGData contract smoke test, and all unit tests.
- Updated the project overview and technical decisions to remove obsolete descriptions of TKKGTracker as the data source and of independent Spotify discovery.

## Latest live dataset verification

GitHub Actions run 42711885293 passed on main after the episode 150 mapping was published. The smoke test:
- Fetched 243 TKKGData episode records.
- Validated episode 150's real audio_release with the production downloader validator.
- Confirmed 40 contiguous individual Spotify and YouTube Music pairs.
- Confirmed the exact official playlist URL and Spotify album pairing.
- Confirmed 40 individual fallback queries can be constructed.

## Remaining verification

- No real audio download or FFmpeg merge was run in CI.
- TKKGData currently has no verified audio_release record in its initial catalogue snapshot. Episode 150 must first pass live audio enrichment and be written to TKKGData before the downloader can produce it.
- Windows manual tests for episode 150, a different track count, range processing, playback, and overwrite protection remain pending.
