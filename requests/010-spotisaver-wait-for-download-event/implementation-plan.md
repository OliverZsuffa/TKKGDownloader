# Implementation plan: Request 010

## Design

Replace the finite `page.expect_download(timeout=timeout_ms)` wait in `_download_click` with a download-event listener registered before the button is clicked. Registering first prevents a fast event from being missed. Click the selected control once, then wait for the listener to receive the event.

Use a short polling interval to keep the synchronous Playwright workflow responsive. Emit a timestamped heartbeat approximately every 15 seconds. The wait has no arbitrary elapsed-time limit. The existing button-readiness timeout remains finite and unchanged.

## Error handling

- Preserve the existing click-stage diagnostics.
- Treat Ctrl+C as cancellation. Let `KeyboardInterrupt` propagate after the existing `finally` block closes Chromium.
- Detect page or browser closure while waiting and raise a clear runtime error with the elapsed wait time.
- Do not retry the click, switch to track fallback, or close Chromium merely because the download is slow.
- Once the download event arrives, preserve the existing suggested-filename handling, `save_as`, non-empty file checks, and downstream strict track validation.

## Tests

Add mocked tests covering:
1. The listener is registered before the click.
2. The click is issued exactly once.
3. A download event arriving after multiple heartbeat intervals is accepted.
4. An event arriving immediately after the click is not missed.
5. A closed page before the event fails clearly.
6. Ctrl+C propagates and does not trigger fallback.
7. Existing file save and empty-file validation still apply.

Run the complete test suite and compile checks. Review the diff for unintended changes.

## Documentation

Update the README, request index, Knowledge Base technical decision, and request notes. Record that CI only mocks the browser event and that Oliver must rerun the command locally to verify Spotisaver's live behaviour.

## Delivery

Implement on a dedicated branch, open a pull request, inspect CI and the final diff, and wait for Oliver's explicit approval before merging.
