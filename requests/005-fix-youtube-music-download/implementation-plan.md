# Implementation plan: Request 005

## Current implementation findings

The current pipeline is:

1. `validate_audio_release()` validates the published Spotify album, track count, ordered Spotify track URLs, individual YouTube Music URLs, and optional playlist.
2. `build_playlist_query()` combines the playlist URL and Spotify album URL with spotDL's `|` pairing syntax.
3. `_download_playlist()` invokes spotDL once for the combined query.
4. If that raises a RuntimeError, `_download_individual_tracks()` retries each individual YouTube Music URL paired with its Spotify track URL, again through spotDL.
5. Downloaded MP3 files are validated and merged with FFmpeg.

The current implementation therefore uses the same spotDL YouTube provider integration for both the playlist and individual fallback paths. The individual fallback is not an independent recovery mechanism.

The user's log confirms that spotDL discovers 40 songs but later attempts a YouTube URL with a missing video ID. The traceback's KeyboardInterrupt only records that the user stopped the process.

## Proposed technical approach

### Phase 1: Isolate the provider failure

1. Add focused tests around the existing playlist query and individual query construction.
2. Reproduce the current behaviour with the exact episode 150 playlist and one exact individual video URL, using the pinned spotDL 4.5.2 environment.
3. Capture the yt-dlp version installed with spotDL and inspect whether the failure is specific to playlist extraction or also affects direct watch URLs.
4. Keep this experiment bounded. Do not run a 40 track download during diagnosis.

### Phase 2: Implement an independent direct download path

Preferred direction, subject to Phase 1 confirmation:

1. Use yt-dlp directly for each validated individual YouTube video URL or video ID from TKKGData, rather than asking spotDL to resolve the playlist.
2. Invoke yt-dlp through the project's Python environment where possible, so Windows users do not need a separately installed executable.
3. Download one track at a time into a temporary track-specific directory or filename. Use the verified TKKGData track order for deterministic output names.
4. Extract or convert audio to MP3 at the existing 192 kbit/s target. Reuse FFmpeg where practical, but avoid a second lossy conversion if yt-dlp can produce the required MP3 directly.
5. Use the Spotify track metadata already paired in TKKGData for canonical track naming. Do not use an unverified title search.
6. Report track number, total count, elapsed time, and a clear failure reason. A failed track must stop the episode before merge.
7. Validate each resulting file exists and is non empty. After all tracks complete, validate exact count and contiguous order using the existing validation boundary.
8. Merge only after every track passes validation.

The playlist can remain useful as provenance and as a possible future optimized path, but it must not be the primary path until its behaviour is proven reliable. Do not silently retry spotDL's same failing YouTube extraction code as a fallback.

### Phase 3: Preserve compatibility

1. Keep the public CLI and all existing flags unchanged.
2. Keep episode range handling and per episode failure isolation unchanged.
3. Keep the existing confirmation prompt and `--yes` behaviour.
4. Keep overwrite protection, output filenames, and FFmpeg merge semantics unchanged.
5. Keep the downloader read only with respect to TKKGData.
6. Keep track count entirely data driven. No episode specific count or hardcoded 40.

### Phase 4: Tests

Automated tests should cover:

- Building download tasks from the verified ordered track records.
- Passing exact video IDs or URLs to yt-dlp without text search.
- Dynamic counts including a small fixture with a different number of tracks.
- Successful per track downloads and deterministic filenames.
- A missing video ID rejected before invoking the downloader.
- A non zero yt-dlp exit code identifying the failed track.
- Empty or missing output rejected.
- No merge after any failed track.
- Merge only after all tracks pass.
- Temporary directory cleanup.
- Existing confirmation, overwrite, range, and CLI behaviour.
- Windows friendly subprocess invocation.
- The current spotDL playlist failure fixture, ensuring the production path does not depend on it.

CI must use mocked downloads and must not fetch real copyrighted audio.

### Phase 5: Documentation and manual verification

1. Update README requirements and explain the actual download path.
2. Update the Knowledge Base technical decisions with the provider failure and chosen solution.
3. Record test results in this request's `notes.md`.
4. Run the following on Oliver's Windows machine after merge:

       py -m pip install -e .
       py tkkg.py 150

5. Verify that the final MP3 contains all 40 tracks in order and plays correctly.
6. Also test an episode with a different track count, a short range, and overwrite protection.

## Implementation boundaries

Expected production changes are concentrated in:

- `src/tkkgdownloader/downloader.py`
- `src/tkkgdownloader/audio_sources.py`, only if the normalized download task representation needs adjustment
- `tests/`, for provider invocation and download validation
- `pyproject.toml`, only if a direct yt-dlp dependency must be declared explicitly
- `README.md` and `docs/knowledge/`

Do not modify the TKKGData dataset or TKKGTracker.

## Approval gate

This document is a plan only. No production code has been changed. Wait for Oliver's explicit approval before implementation.
