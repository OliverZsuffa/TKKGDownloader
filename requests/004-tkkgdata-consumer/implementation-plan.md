# Implementation plan: Make TKKGDownloader a TKKGData consumer

**Status:** Approved by Oliver on 2026-11-09. Implementation in progress.

## Architecture boundary

TKKGData owns the canonical episode catalogue, scraping, provider discovery, verification, and publication. TKKGDownloader is a read-only consumer. It owns only CLI behaviour, audio download execution, downloaded-file validation, FFmpeg merging, output naming, overwrite protection, and local files.

## 1. Dataset client

1. Fetch data/dataset-metadata.json and data/episodes.json from TKKGData at the start of each CLI invocation.
2. Support schema major version 1.x.
3. Validate the dataset metadata episode count against the returned array.
4. Validate unique contiguous episode numbers, titles, and all fields required by the tracker-compatible episode record.
5. Preserve optional audio_release metadata in the Episode object.
6. Do not cache an independent dataset. A network or validation failure produces a clear error.
7. Do not request TKKGTracker or scrape any source.

## 2. Verified audio source validation

For a requested episode, require audio_release.verification.status == verified.

Validate:
- Spotify album ID and canonical album URL.
- Spotify album title and positive track count.
- YouTube Music individual track list and count.
- matched_track_count.
- Contiguous one-based track numbering.
- Each Spotify track ID against its Spotify track URL.
- Each YouTube Music video ID against its song URL.
- Optional playlist ID against its playlist URL and playlist track count.

Reject incomplete, unverified, ambiguous, mismatched, or out-of-order source metadata before starting downloads.

## 3. Download strategy

1. Prefer the verified YouTube Music playlist paired with the Spotify album URL using spotDL's documented manual pairing format.
2. If the playlist is missing or the playlist download fails, fall back to each verified YouTube Music song URL paired with its exact Spotify track URL.
3. Do not search Spotify, search YouTube Music, resolve first-track metadata, or use unverified text queries.
4. Use the existing MP3 format, bitrate, output template, and temporary working directories.
5. Validate that the downloaded MP3 files equal the expected track count and contain the exact contiguous sequence 1..N.
6. Require one album output folder. Never merge partial, duplicated, or reordered downloads.

The dataset's verified individual track records are the source of truth for expected count and track ordering. Never hardcode 40 or trust an inconsistent provider summary without the actual matched records.

## 4. Merge and output

Preserve:
- One output MP3 per episode.
- Existing output naming.
- FFmpeg stream-copy attempt and re-encode fallback.
- Atomic temporary output handling.
- Existing-file protection and --overwrite.
- Confirmation prompt and --yes behaviour.
- Inclusive episode ranges and per-episode failure reporting.
- Windows compatibility.

Do not change the CLI syntax or introduce a new runtime framework.

## 5. Missing data and failures

- Missing episode: clear TKKGData lookup error.
- Dataset unavailable, malformed, unsupported, or inconsistent: stop before download.
- Missing verified audio_release: clear message that audio mapping must be added in TKKGData.
- Invalid Spotify or YouTube Music IDs/URLs: reject before download.
- Playlist unavailable or playlist download fails: try exact individual track pairs.
- Individual track download failure: report the exact track and stop that episode.
- Wrong number, duplicate, or reordered MP3 files: do not merge.
- No unverified search fallback and no write-back to TKKGData.

## 6. Automated tests

Test:
- TKKGData metadata and episode JSON retrieval.
- Supported and unsupported schema versions.
- Metadata count mismatch, malformed JSON, HTTP failure, missing episode, duplicate or gapped numbering.
- Verified and unverified audio releases.
- Playlist ID and URL consistency.
- Spotify track ID and URL consistency.
- YouTube Music video ID and URL consistency.
- Track count and contiguous order validation.
- Playlist pairing as the preferred path.
- Individual track pairing as fallback.
- Playlist failure followed by successful individual track fallback.
- Missing verified mapping and incomplete download rejection.
- Existing CLI, episode range parsing, file ordering, merge, and overwrite behaviour.

All network and subprocess operations are mocked. Automated tests do not download real audio.

## 7. Windows manual verification

1. Run py tkkg.py --help.
2. Run episode 150 after TKKGData has a verified mapping.
3. Confirm the selected Spotify album and YouTube Music source are displayed.
4. Confirm the playlist pairing is attempted first.
5. Confirm individual exact track pairs are used if the playlist fails.
6. Confirm all expected MP3 tracks are present in contiguous order.
7. Confirm the merged MP3 plays and contains the complete episode.
8. Test a second episode with a different track count.
9. Test a short episode range.
10. Verify existing output is skipped by default and replaced only with --overwrite.
11. Verify missing or incomplete mappings fail clearly without unverified search.

## 8. Cutover and cleanup

- TKKGData is already published at the stable main endpoint.
- Replace the TKKGTracker URL and independent Spotify discovery with the TKKGData client.
- Remove the old Spotify resolver after the new client and source validation tests pass.
- Update README, project instructions, knowledge base, and request notes.
- Merge only after automated checks pass and the changed-file review confirms that only the intended downloader responsibilities changed.
