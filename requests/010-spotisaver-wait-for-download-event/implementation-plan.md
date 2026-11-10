# Implementation plan: Request 010

## Design

Keep the existing visible Playwright browser and the verified normal website button interaction.

Register a browser download-event listener before clicking `#downloadAllBtn`. Click the selected control exactly once. Replace the finite `page.expect_download(timeout=timeout_ms)` wait with a loop that waits for the registered event while periodically checking the page state.

The loop should have no arbitrary elapsed-time limit while the page and browser remain open. Poll at a short interval and emit a timestamped heartbeat approximately every 15 seconds.

## Modal monitoring

Inspect the rendered DOM, not hidden endpoints. Read the following elements when present:

- `#downloadStatusText` for the current status.
- `#downloadMiniLog` for queue notices, explanatory messages, and errors.
- `#downloadFailedBadge` for failure state.
- `#downloadProgressWrap` and `#downloadProgress` for visible progress.
- Visible controls in the modal that may communicate a retry or continue action.

Log only when the meaningful status changes, plus the periodic heartbeat. Include the elapsed time.

Recognise the queue notice shown in the supplied HTML, including the message that all download slots are busy and the stated retry delay. Parse a delay such as 25 seconds when possible and report it as the website's instruction.

The user is unsure whether the website automatically retries. Therefore, do not assume that it does. Do not click the album download button again, and do not click a guessed retry control. After the stated delay, continue observing the modal and report whether its text, progress, or available controls change. If a clearly labelled retry control is present, report it in the diagnostics but leave interaction behaviour unchanged in this request. Any automatic retry action should be a separate, explicitly approved change after live behaviour is understood.

Detect explicit page failure messages and surface them as clear errors with the relevant modal text. Do not mistake the queue busy notice itself for a final failure.

## Waiting and error handling

- Keep the browser open throughout queueing and playlist processing, even if this takes several minutes.
- Do not use the old 120-second download-event timeout.
- Continue waiting for the browser download event after the page reports that playlist processing has started or completed.
- Detect page or browser closure and fail clearly with elapsed time and the last known modal state.
- Treat Ctrl+C as cancellation. Let `KeyboardInterrupt` propagate after the existing `finally` block closes Chromium.
- Do not retry the click, switch to track fallback, or close Chromium merely because the download is slow.
- Once the download event arrives, preserve suggested-filename handling, `save_as`, non-empty file checks, and downstream strict track validation.

## Tests

Add mocked tests covering:

1. The download listener is registered before the click.
2. The click is issued exactly once.
3. A download event arriving immediately is not missed.
4. A download event arriving after multiple heartbeat intervals is accepted.
5. A queue busy notice is recognised and its retry delay is reported.
6. The queue notice is not treated as a final failure.
7. The program continues monitoring after the stated retry delay without issuing another click.
8. Modal status changes and progress are logged without flooding the console.
9. An explicit page failure is surfaced clearly.
10. A closed page before the event fails clearly and includes the last known status.
11. Ctrl+C propagates and does not trigger fallback.
12. Existing file saving and empty-file validation still apply.

Run the complete test suite and compile checks. Review the diff for unintended changes.

## Documentation

Update the README, request index, Knowledge Base technical decision, and request notes. Document the queue monitoring behaviour and explicitly state that automatic retry is not assumed. Record that CI only mocks browser events and modal states. Oliver must rerun the command locally to verify the live Spotisaver behaviour.

## Delivery

Implement on the existing dedicated branch, open or update the pull request, inspect CI and the final diff, and wait for Oliver's explicit approval before merging.
