# Implementation plan: Request 006

## Phase 1: Confirm scope and inspect the current codebase

1. Inspect the current CLI, TKKGData integration, track model, temporary-directory handling, FFmpeg merge path, dependencies, tests, and Knowledge Base conventions.
2. Record that Oliver reports explicit Spotisaver approval for the intended occasional, personal, one-episode-at-a-time browser automation workflow.
3. Keep the implementation within that reported permission and any narrower limits displayed by Spotisaver. Do not infer permission for catalogue-wide or unattended downloads.
4. Recheck the public Spotisaver workflow and current terms before implementation. If the site presents a restriction that conflicts with the reported approval, stop and ask for clarification rather than bypassing it.

## Phase 2: Playwright browser provider

1. Add Playwright for Python as a project dependency and document the one-time Chromium installation command.
2. Implement an isolated Spotisaver provider module. Do not mix browser logic into the canonical TKKGData parsing or FFmpeg merge code.
3. Build the album URL from the validated Spotify album ID in TKKGData.
4. Launch visible Chromium by default. Do not use stealth plugins, anti-detection modifications, or hidden browser contexts.
5. Navigate to the public album page and wait for the rendered album content to become ready.
6. Verify the displayed album identity and tracklist against the expected TKKGData release before initiating downloads. If the page cannot be reliably identified, stop.
7. Use stable, user-visible selectors where possible. Keep selectors in one provider module and provide clear diagnostics when the website changes.
8. Use Playwright's normal download event handling, such as `page.expect_download()`, to save files into a per-run temporary directory.
9. Prefer the website's advertised ZIP download when it is present and covered by the reported approval.
10. If ZIP is unavailable, download individual tracks sequentially only if that method is covered by the reported approval. Do not run concurrent downloads.
11. Keep the browser visible so Oliver can complete ordinary user interactions. Do not save credentials or session tokens.
12. If a CAPTCHA, login requirement, access denial, rate limit, cooldown, or other protection appears, pause or stop and report it. Never attempt to bypass it.
13. Add bounded timeouts and useful errors for navigation, album mismatch, incomplete tracklist, missing download controls, interrupted download, and browser closure.
14. Close the browser cleanly after success. On a recoverable manual interaction, allow the user to complete it before continuing or cancel.

## Phase 3: CLI integration

1. Add an explicit Spotisaver provider selection to the existing CLI, preferably `py tkkg.py 150 --provider spotisaver`, unless inspection shows a cleaner established pattern.
2. Preserve the current default behaviour unless the user explicitly selects Spotisaver or approves a later default-provider change.
3. Keep the command scoped to the requested episode or explicit episode range. Spotisaver automation must reject a range containing more than one episode in this initial implementation.
4. Print the episode, album ID, Spotisaver URL, expected track count, and a clear notice that one album is being processed.
5. Do not automatically retry a failed website download in a way that could exceed site limits.

## Phase 4: Import, validate, and merge

1. Pass the downloaded ZIP or individual MP3 paths to an isolated import and validation layer.
2. Safely inspect ZIP members before extraction. Reject absolute paths, parent traversal, symlinks, nested archives unless explicitly supported, corrupt archives, unsupported file types, and empty files.
3. Match tracks using track number and title metadata or filenames, normalized against TKKGData. Use duration as a secondary validation signal.
4. Require exactly one valid file for each expected track. Never hardcode 40 or any other album track count.
5. Report missing, duplicate, ambiguous, unexpected, corrupt, and mismatched files with track-specific diagnostics.
6. Do not merge unless the complete expected track set passes validation.
7. Reuse the existing FFmpeg merge implementation and preserve output naming, overwrite protection, confirmation behaviour, and per-episode failure handling.
8. Keep source downloads unchanged. Use temporary working copies and clean up temporary data after success or failure.

## Phase 5: Tests

Use mocked Playwright pages and synthetic audio fixtures. CI must not download copyrighted recordings or depend on Spotisaver availability.

Add tests for:
- Album URL construction from TKKGData.
- Visible browser launch configuration.
- Album identity and tracklist verification.
- ZIP download event handling.
- Sequential individual download event handling where enabled.
- Stop behaviour for CAPTCHA, login, access denial, cooldown, and rate-limit states.
- Timeouts, changed selectors, interrupted downloads, and browser closure.
- ZIP traversal, absolute paths, symlinks, corrupt archives, unsupported files, and empty files.
- Metadata and filename matching.
- Dynamic track counts and exact ordering.
- Missing, duplicate, ambiguous, unexpected, and mismatched tracks.
- Duration mismatch reporting.
- No merge when validation fails.
- Successful merge in canonical TKKGData order.
- Source file preservation and temporary-directory cleanup.
- Existing CLI behaviour and overwrite protection.

## Phase 6: Documentation and manual verification

1. Update README with Playwright installation, browser behaviour, CLI usage, and troubleshooting.
2. Update the Knowledge Base with the provider architecture and one-episode scope.
3. Record that Spotisaver permission was reported by Oliver and that the implementation must respect the precise approved scope and live site limits.
4. Run the full test suite and CI contract smoke test against live TKKGData metadata, without downloading audio.
5. Ask Oliver to run the first real episode 150 test locally.
6. Verify the downloaded files, merged MP3 playback, track order, and total duration.
7. Do not claim the real download works until Oliver confirms the manual Windows test.

## Expected implementation structure

Exact paths must be confirmed against the repository before implementation. Proposed separation:

- `src/tkkgdownloader/spotisaver.py`: Playwright provider, album page verification, browser download events.
- `src/tkkgdownloader/audio_import.py`: safe ZIP and MP3 import, matching, validation.
- `src/tkkgdownloader/cli.py` or current CLI entry point: provider selection and one-episode guard.
- Existing downloader and FFmpeg modules: reuse the established merge pipeline.
- `tests/`: mocked browser and synthetic media tests.
- `README.md` and `docs/knowledge/`: setup and workflow documentation.

## Approval gate

This is a plan only. Do not modify production code until Oliver explicitly approves this revised plan. The approval reported from Spotisaver is treated as applying only to the occasional, personal, one-episode-at-a-time workflow described in Request 006. Any broader automation requires separate confirmation and a plan revision.
