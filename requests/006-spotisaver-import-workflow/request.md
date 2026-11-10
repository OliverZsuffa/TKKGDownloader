# Request 006: Spotisaver browser-assisted episode download

## Status

Proposed. Awaiting Oliver's approval of the revised implementation plan.

## Objective

Add an occasional, user-initiated Spotisaver download workflow to TKKGDownloader. The intended use is to download one TKKG episode at a time for Oliver's personal listening, using the Spotify album metadata and track mapping already verified in TKKGData.

Oliver states that Spotisaver has explicitly approved this intended use, including browser automation. This permission is user-reported and has not been independently verified in this repository. Implementation must stay within the exact scope Spotisaver approved and its current technical and usage limits.

## Existing data contract

TKKGData remains the sole source of truth for:
- Episode number and title.
- Spotify album ID and public album URL.
- Verified track titles, track numbers, order, and expected durations.
- Verified individual source metadata already published in the dataset.

The downloader must not independently guess or rewrite canonical track metadata.

## Proposed Spotisaver workflow

1. Oliver runs the downloader for one episode, for example `py tkkg.py 150`.
2. TKKGDownloader validates the episode's Spotify album ID and complete track mapping from TKKGData.
3. Playwright launches a visible Chromium browser and opens the Spotisaver album page generated from that album ID.
4. The browser workflow waits for the album page to finish loading and verifies that the displayed album and tracklist correspond to the expected episode.
5. It uses the normal, visible website interface to initiate the website's advertised download option. Prefer the site's ZIP download if it is available and covered by the reported permission. Otherwise download individual tracks sequentially, only if that method is also covered by the permission.
6. Playwright captures the browser's normal download events and saves the resulting file or files into an isolated temporary working directory.
7. The downloader validates the downloaded archive and audio files against TKKGData.
8. Only after every expected track has passed validation does the existing FFmpeg merge pipeline create the combined episode MP3.

This is intended for one explicitly requested episode per invocation. No unattended catalogue-wide jobs, parallel album downloads, background monitoring, or automatic retries that could multiply requests.

## Browser automation requirements

1. Use Playwright for Python, preferably its synchronous API unless the existing codebase gives a clear reason to use asynchronous Playwright.
2. Launch a visible Chromium browser by default so Oliver can observe the workflow and complete any ordinary user interaction.
3. Use the public album URL pattern `https://spotisaver.net/en/album/{spotify_album_id}/`, with the album ID taken from validated TKKGData rather than hardcoded.
4. Use normal rendered-page interactions and Playwright download events. Do not call undocumented private endpoints or reconstruct hidden download APIs.
5. Do not evade CAPTCHA, login requirements, geographic restrictions, access controls, download limits, or anti-automation protections. If any such control appears, stop and ask Oliver to handle the issue manually or cancel.
6. Keep downloads sequential. Respect any displayed cooldowns, rate limits, per-account limits, and the specific scope of Spotisaver's approval.
7. Do not store Spotisaver credentials, browser passwords, or session tokens in the repository or application configuration. If authentication is required, let Oliver handle it interactively in the visible browser.
8. Add clear timeouts and actionable errors for page load failure, changed page structure, missing album, missing track matches, unavailable download controls, interrupted downloads, and browser closure.
9. Do not silently fall back to another source if Spotisaver fails. Report the failure and preserve the existing explicit source selection behaviour.
10. Make browser automation opt-in through a clear provider option if that is the least disruptive CLI design. The implementation plan must confirm the final command syntax against the existing CLI.

## Download and validation requirements

1. Prefer one ZIP download for the requested album if the website offers it and the reported permission covers it.
2. If the ZIP option is unavailable, individual track downloads may be used sequentially only if covered by the permission.
3. Store browser downloads in a temporary directory. Do not write partial tracks into the final output directory.
4. Safely inspect ZIP contents before extraction. Reject absolute paths, parent traversal, symlinks, nested archives unless explicitly supported, corrupt archives, unsupported file types, and empty files.
5. Match tracks deterministically using track number and title metadata or filename, normalized against TKKGData. Use duration as a secondary validation signal.
6. Do not silently guess when multiple files match one track or when a track is missing.
7. Require exactly one valid file for every expected track. Track count must be data-driven and never hardcoded to 40.
8. Preserve the original downloaded files until validation and merging finish. Clean up temporary data on success or failure.
9. Reuse the existing FFmpeg merge pipeline only after complete validation.
10. Preserve output naming, overwrite protection, confirmation behaviour, and per-episode error reporting.

## Scope and safeguards

- One episode per explicit user invocation.
- Personal, non-commercial use as stated by Oliver.
- Browser automation only within the scope Spotisaver explicitly approved.
- Respect Spotisaver's current terms, written approval, displayed limits, and rate limits.
- No bulk catalogue scraping or unattended downloads.
- No reverse engineering of private endpoints.
- No DRM circumvention or extraction from Spotify, Amazon Music, or YouTube Music.
- No changes to TKKGData or TKKGtracker.
- The downloader remains read-only with respect to TKKGData.

## Acceptance criteria

- [ ] The CLI can select Spotisaver for one specified episode.
- [ ] The Spotify album ID is read from validated TKKGData.
- [ ] Playwright launches a visible browser and opens the correct Spotisaver album page.
- [ ] The workflow verifies the expected album and tracklist before starting a download.
- [ ] The workflow captures normal browser download events without private endpoint calls.
- [ ] ZIP download is supported where available and permitted.
- [ ] Sequential individual downloads are supported only where permitted.
- [ ] The workflow stops safely when a CAPTCHA, access restriction, limit, or unexpected interaction is encountered.
- [ ] Downloaded files are validated deterministically against all expected TKKGData tracks.
- [ ] Missing, duplicate, ambiguous, corrupt, or unexpected files prevent merging and produce actionable errors.
- [ ] The existing FFmpeg merge is reused only after complete validation.
- [ ] Tests cover browser workflow using mocked pages/download events, archive validation, matching, failure handling, and no-merge-on-failure.
- [ ] CI does not download or redistribute copyrighted recordings and does not depend on Spotisaver being available.
- [ ] README and Knowledge Base document setup, usage, limitations, and the user-reported permission scope.

## Open implementation decisions

- Whether the current CLI should use `--provider spotisaver` or a dedicated subcommand.
- Whether Spotisaver's ZIP download is available for the target album in the normal browser workflow.
- Whether the browser should close automatically after a successful download or remain open for inspection. Default proposal: close only the Playwright-launched browser after downloads have completed, unless an error requires user intervention.
