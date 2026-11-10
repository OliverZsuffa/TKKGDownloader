# Request 005: Fix verified YouTube Music downloads

## Status

Proposed. Reproduction received from Oliver on 2026-11-10. No implementation changes have been made.

## Objective

Make TKKGDownloader reliably download the exact audio sources published by TKKGData, including episode 150, without relying on spotDL's failing YouTube Music playlist resolution.

## Observed failure

Oliver ran:

    py tkkg.py 150

The downloader loaded the verified episode 150 release and passed the official YouTube Music playlist together with the Spotify album to spotDL. spotDL reported that it found 40 songs, but YouTube downloads failed with repeated errors:

    AudioProviderError: YT-DLP download error - https://music.youtube.com/watch?v=None

The process continued slowly and was interrupted by Oliver after eight tracks had been marked complete.

The traceback ends in `KeyboardInterrupt`. This is the user's interruption, not the root failure.

## Initial diagnosis

The TKKGData mapping itself passed validation and contains 40 verified individual YouTube Music URLs with video IDs. The downloader currently constructs a combined playlist and Spotify album query in `build_playlist_query()`, then sends it to spotDL 4.5.2.

The observed `watch?v=None` URL indicates that spotDL's YouTube extraction path is attempting to download an entry for which it did not obtain a video ID. This is a provider integration failure after playlist discovery, not evidence that the published playlist URL or the 40 source mappings are invalid.

The current fallback is also not a reliable recovery path: it sends individual YouTube Music watch URLs through spotDL's same YouTube provider integration. It may therefore encounter the same extraction defect. This must be tested rather than assumed.

## User experience

The existing command remains:

    py tkkg.py 150

The downloader should report which verified source and download method it is using, show useful progress, stop promptly on a failed track, and never create a merged MP3 from an incomplete download. The user should not have to manually repair metadata or provide URLs already stored in TKKGData.

## Functional requirements

1. Use only the verified track mappings published by TKKGData. Do not perform text search or substitute unverified audio.
2. Download the exact YouTube video IDs or URLs from the validated track records.
3. Do not depend on spotDL successfully resolving a YouTube Music playlist entry to a video ID.
4. Preserve the Spotify metadata pairing as the authoritative source for track identity, expected order, and naming.
5. Validate that every expected track was downloaded exactly once, in contiguous order, before merging.
6. Keep the dynamic track count. Do not hardcode 40 or assume every episode has the same number of tracks.
7. Preserve the existing CLI, episode ranges, output naming, overwrite protection, confirmation behaviour, FFmpeg merge, and per episode failure reporting.
8. Keep temporary downloads isolated and clean them up after success or failure.
9. Provide actionable errors that identify the failed track and method. Do not silently continue with a partial set.
10. Retain a fallback only if it uses an independently verified download path. Do not retry the same failing spotDL YouTube extraction path under a different query shape without evidence that it works.
11. Keep Windows support and avoid requiring users to install a separate tool manually when it can be invoked through the pinned project environment.

## Constraints

- TKKGData remains the single source of truth for episode and provider metadata.
- TKKGDownloader remains a read only consumer.
- No changes to TKKGData or TKKGTracker are required for this fix unless testing reveals a genuine source data defect.
- Do not weaken validation or accept unverified matches to make a download appear successful.
- Do not change the output format or merge semantics.

## Out of scope

- New audio source scraping or enrichment.
- Changes to the TKKGData schema.
- Changes to TKKGTracker.
- Downloading episodes without a complete verified mapping.
- A general media player or GUI.

## Acceptance criteria

- [ ] A focused test reproduces and documents the current spotDL failure mode or establishes a deterministic regression fixture for it.
- [ ] A verified individual YouTube Music track can be downloaded through the selected method on Windows.
- [ ] Episode 150 downloads all 40 tracks from the exact TKKGData video IDs without a `watch?v=None` failure.
- [ ] Track order and completeness are validated dynamically from TKKGData.
- [ ] A failed or missing track prevents merging and reports its track number.
- [ ] A successful download produces one playable MP3 with all expected tracks in order.
- [ ] Existing output protection, confirmation, range handling, and CLI behaviour remain intact.
- [ ] Automated tests pass on CI.
- [ ] README and Knowledge Base document the selected download method and its requirements.
- [ ] Oliver completes a real Windows end to end test for episode 150.

## Open questions

- Does the pinned spotDL 4.5.2 fail specifically on OLAK YouTube Music playlist entries, or does it also fail for direct individual `music.youtube.com/watch?v=VIDEO_ID` URLs?
- Can the installed yt-dlp version download the verified individual video IDs directly and reliably on Windows?
- Does the direct yt-dlp path need browser cookies or another explicit authentication configuration in the user's environment?
