# Request 006: Spotisaver browser-assisted episode download

## Status
Approved by Oliver on 2026-11-10. Implementation is on branch feature/spotisaver-import.

## Objective

Add an occasional, user-initiated Spotisaver download workflow to TKKGDownloader. The intended use is to download one TKKG episode at a time for Oliver's personal listening, using the Spotify album metadata and track mapping already verified in TKKGData.

Oliver reports that Spotisaver explicitly approved this intended use, including browser automation. The implementation treats that as permission to use Spotisaver within the described scope, while continuing to respect its current terms, technical limits, and any restrictions displayed by the site.

## Existing data contract

TKKGData remains the sole source of truth for episode number and title, Spotify album ID and public album URL, verified track titles, track numbers, order, and expected durations. The downloader must not independently guess or rewrite canonical track metadata.

## Implemented workflow

1. Oliver runs the downloader for one episode, for example py tkkg.py 150 --provider spotisaver.
2. TKKGDownloader validates the episode's Spotify album ID and complete track mapping from TKKGData.
3. Playwright launches visible Chromium and opens the Spotisaver album page built from the album ID.
4. The provider verifies the visible album title and all expected track titles before starting.
5. It uses the website's normal visible album ZIP control when available. Otherwise, it downloads individual visible track controls sequentially.
6. Playwright captures normal browser download events and saves files to an isolated temporary directory.
7. ZIP files are safely extracted. Every MP3 filename must match exactly one expected TKKGData track title.
8. Only after every expected track has passed validation does the existing FFmpeg merge pipeline create the combined episode MP3.

Spotisaver mode accepts exactly one episode per invocation. There are no unattended catalogue-wide jobs, parallel album downloads, or automatic retries that could multiply requests.

## Browser automation requirements

- Playwright for Python with visible Chromium.
- Public album URL pattern: https://spotisaver.net/en/album/{spotify_album_id}/.
- Normal rendered page interactions and Playwright download events only.
- No undocumented private endpoints, hidden download APIs, stealth plugins, CAPTCHA bypass, login bypass, geographic restriction bypass, access-control workarounds, or anti-automation evasion.
- Downloads remain sequential.
- Stop when the site presents an access restriction, rate limit, CAPTCHA, login requirement, changed page structure, or unavailable download control.
- Do not store credentials, browser passwords, or session tokens in the repository.

## Download and validation requirements

- Prefer one ZIP download if the normal website interface exposes it.
- Otherwise download individual track MP3s sequentially.
- Keep downloads in a temporary directory, never the final output directory.
- Reject unsafe ZIP paths and symlinks.
- Require exactly one non-empty MP3 for every expected track.
- Match files by normalized canonical track title. Do not guess when a match is missing or ambiguous.
- Reuse the existing FFmpeg merger only after complete validation.
- Preserve output naming, overwrite protection, confirmation behaviour, and temporary-file cleanup.

## Acceptance criteria

- [x] CLI can select Spotisaver for one specified episode.
- [x] Spotify album ID is read from validated TKKGData.
- [x] Playwright launches a visible browser and opens the expected album page.
- [x] Album identity and all expected track titles are checked before download.
- [x] Normal browser download events are used.
- [x] ZIP and sequential individual MP3 download paths are implemented.
- [x] Spotisaver mode rejects multi-episode ranges.
- [x] ZIP traversal and symlink entries are rejected.
- [x] Imported MP3 files must match every expected TKKGData track title.
- [x] Missing, duplicate, ambiguous, corrupt, empty, or unexpected files prevent merging.
- [x] Existing FFmpeg merge and output safeguards are reused.
- [x] Automated tests cover ZIP import, matching, path traversal, corrupt archives, empty tracks, and CLI selection.
- [ ] CI passes.
- [ ] Oliver completes the first real Windows download and playback test for episode 150.

## Known limitation

The exact Spotisaver page selectors and its current download behaviour have not yet been validated against a live browser session in this environment. The first local run is the required end-to-end check. If the website changes its rendered interface, the provider stops with an error rather than using hidden endpoints or bypasses.
