# Implementation plan: Request 011

## Scope

Modify the post-click state machine in `src/tkkgdownloader/spotisaver.py`. Keep the current browser launch, album readiness polling, rendered button selection, download listener, file saving, and strict archive validation.

## State machine

Model the album download as a sequence of attempts with one persistent download-event listener.

1. Register the download event listener before the first click.
2. Verify the normal album download button is visible and enabled, then click it once.
3. Poll for the browser download event and inspect the rendered modal at the existing short interval.
4. When the explicit queue-busy notice appears, record the attempt number and start a 30-second retry countdown.
5. During the countdown, continue polling for the download event and modal state. If the download event arrives, stop immediately and save it. If the queue notice clears and the page transitions to playlist processing, cancel the retry and continue waiting.
6. At 30 seconds, take a fresh modal snapshot. Retry only if the explicit queue-busy notice is still present and no download event has arrived.
7. Locate the visible close button inside the active modal using its accessible label. Click it once and wait for the modal to become hidden.
8. Confirm `#downloadAllBtn` is visible and enabled. If it is not available, fail with diagnostics including the current page title, modal state, and button selector state.
9. Click the album button once and return to step 3. Keep the same listener active.
10. On a download event, save the file using the existing suggested filename handling and continue existing validation.

Do not retry on a generic error, a missing status, a stalled progress indicator, or a long processing period. Do not reload the page, restart Chromium, or click while the modal remains open.

## Modal and selector handling

Reuse or extend the current modal snapshot helper. It must distinguish the explicit all-slots-busy notice from normal status text and final failure text. Add helpers where appropriate for:

- Detecting the queue rejection reliably from rendered mini-log text.
- Locating and clicking the visible modal close button.
- Waiting for the active modal to become hidden.
- Rechecking the album download button's visibility and enabled state.

The supplied modal uses `button[aria-label="Close"]`. Scope the selector to the visible modal rather than selecting unrelated page controls.

## Logging

Use timestamped, flushed logs for:
- Attempt number and click.
- Queue rejection and stated retry instruction.
- Countdown start and completion.
- Decision to retry or continue processing.
- Modal close action and confirmation.
- Album button readiness and next click.
- Download event receipt and elapsed time.

Retain the existing 15-second heartbeat without flooding the console.

## Cancellation and failure handling

Allow `KeyboardInterrupt` to propagate so the existing `finally` block closes Chromium. Detect page closure during the countdown and between retries. If the close button is absent, the modal does not close, or the album button cannot be made ready, raise a specific provider error with the last observed modal snapshot. Never fall back to an individual track after an ambiguous queue state.

## Tests

Extend `tests/test_spotisaver.py` with mocked Playwright tests for:

1. Listener registration before the first click.
2. Exactly one initial click.
3. Explicit queue rejection starts a 30-second wait.
4. A download event during the wait wins and prevents a retry.
5. A queue notice clearing into processing prevents a retry.
6. A still-active queue rejection closes the modal after the wait.
7. The modal is confirmed closed before the next click.
8. The album button is checked for visibility and enabled state before retry.
9. Repeated queue rejections create sequential retry cycles.
10. A generic failure or stalled progress does not trigger a retry.
11. A delayed download event after a retry is saved correctly.
12. Missing close control, modal-close timeout, or unavailable album button fails clearly.
13. Ctrl+C propagates and does not cause another click.
14. Existing file saving and archive validation remain intact.

Use a controllable fake clock or mocked wait helper so tests do not sleep for real 30-second intervals.

## Documentation

Update the README, request index, Knowledge Base technical decisions, and request notes to describe explicit queue retries. State clearly that the retry is triggered only by the visible queue rejection, not by generic slowness or errors. Record that CI mocks the website and that live queue behaviour still requires local verification.

## Verification and delivery

Run the full unit suite and compilation checks. Inspect the final diff and CI results. Open a pull request from `plan/spotisaver-queue-retry` to `main`. Do not merge until Oliver explicitly approves.
