# Implementation plan: Request 012

## Scope

Update `src/tkkgdownloader/spotisaver.py` and `tests/test_spotisaver.py`. Preserve the existing album click, persistent download listener, queue retry state machine, ZIP extraction, canonical track validation, and FFmpeg pipeline.

## 1. Extend the modal snapshot

Extend `_read_download_modal(page)` to return structured fields for:

- Current status text.
- Mini-log text and, where useful, individual success, pending, and failure entries.
- Failure badge and explicit failure state.
- Progress value and percentage.
- ETA visibility and rendered text.
- ETA template from `#est_timeModalBody[data-eta-template]`.
- ETA minutes and seconds from `[data-eta-part="minutes"]` and `[data-eta-part="seconds"]`.
- Visible controls in the active modal, including accessible names and button state.

Parse ETA as optional integer values. Validate minutes and seconds and format them as a human-readable remaining estimate. Do not retain stale ETA as if it were current when the website hides or clears the ETA element.

Parse `Downloaded N of M` from status text. Validate numeric values and ensure the displayed ratio is bounded sensibly. The progress bar is a secondary signal because the supplied example shows the website can change its progress value during ZIP creation.

## 2. Model archive creation and final download as separate states

Use explicit states or equivalent guarded transitions:

1. Album request submitted.
2. Queue rejected and retry countdown active.
3. Playlist processing.
4. ZIP archive creation.
5. ZIP archive ready.
6. Final ZIP button clicked.
7. Browser download event received.
8. Archive saved and validated.

The queue retry logic applies only to the explicit all-slots-busy rejection before processing. Once processing starts, do not re-enter queue retry logic based on ETA, progress stalls, or generic status changes.

When the status reports `ZIP archive created.`, inspect the active modal for a visible and enabled button with accessible name or rendered text `Download ZIP`. Scope discovery to the active modal. Prefer Playwright role/name discovery where reliable, with a rendered-text fallback. Verify uniqueness, visibility, and enabled state before clicking.

Do not hardcode a guessed CSS selector. Log the active modal's visible button diagnostics if discovery fails. If the website markup proves role/name discovery insufficient, request the exact live button HTML and then add a narrowly scoped selector.

## 3. Preserve the download event listener

Register the download listener before the first album action, as in the current implementation. Keep it registered through every queue retry and all processing states.

After archive-ready detection:

- Click the verified `Download ZIP` control exactly once.
- Do not close the modal.
- Do not click the original album button again.
- Continue waiting for the already registered download event.
- On event receipt, save the archive using the existing safe handling.
- Continue the current ZIP validation and merge pipeline without weakening any checks.

The event may arrive immediately after the click, so listener registration must not be moved later.

## 4. Improve progress output

Introduce a small formatting/reporting layer rather than scattering print statements through polling code.

Default output should be concise and human-readable. Emit a line when a meaningful state changes, and a short heartbeat every 15 seconds. Include available values such as track count, percentage, ETA, current phase, attempt number, and elapsed time.

Example:

```text
[Spotisaver] Downloading tracks: 30/40 (75%). ETA 1m 32s
[Spotisaver] Downloading tracks: 35/40 (88%). ETA 48s
[Spotisaver] Creating ZIP archive
[Spotisaver] ZIP ready. Starting browser download
[Spotisaver] ZIP saved: album.zip (42.8 MB)
[Spotisaver] Validated 40/40 tracks. Merging MP3
```

Retain detailed diagnostics for selector decisions, modal transitions, retry decisions, event timing, save details, and failures. Avoid printing the full mini-log repeatedly. If the project already has a verbose flag or logging abstraction, integrate with it. Otherwise do not add a new CLI option as part of this request.

## 5. Failure handling

- If ZIP-ready status appears but no unique visible enabled ZIP button is found, raise a specific error with modal status, visible button list, and relevant selector diagnostics.
- If the click fails, report the selected control and attempt stage.
- If the browser download event does not arrive, continue waiting while the page remains open, with concise heartbeats.
- Preserve page-closure detection and Ctrl+C cleanup.
- Do not treat a completed progress bar or ETA reaching zero as proof of download completion.
- Do not change archive validation or accept a partial archive.

## 6. Tests

Add focused tests for:

- ETA extraction from the supplied DOM structure.
- Missing, hidden, malformed, and changing ETA values.
- Track counter and progress percentage parsing.
- ETA formatting.
- Status transition from final track completion to ZIP creation to ZIP ready.
- ZIP button discovery scoped to the active modal.
- Hidden, disabled, missing, and ambiguous ZIP buttons.
- Listener registration before the first click and persistence through queue retries.
- Exactly one final ZIP-button click after archive creation.
- No premature download wait completion before the ZIP button click.
- Delayed browser download event after the final click.
- No duplicate ZIP click on repeated polls or heartbeats.
- Page closure and Ctrl+C cancellation.
- Existing archive validation and merge gating remain unchanged.

Use mocked Playwright objects and a controllable wait mechanism. Tests must not use real network requests or real 30-second sleeps.

## 7. Documentation and verification

Update README, request index, Knowledge Base technical decisions, and request notes to explain the two-stage website workflow: playlist processing creates the archive, then the visible ZIP button triggers the actual browser download.

Run Python compilation and the full unit suite. Inspect the diff and CI. Open a pull request from `plan/spotisaver-zip-button-and-progress` to `main`. Do not merge until Oliver explicitly approves.
