# Request 022: Wait for the complete Spotisaver ZIP transfer

## Status

Proposed

## Objective

Prevent a valid, actively progressing Chromium ZIP download from being treated as failed merely because the transfer takes longer than 30 seconds after the browser download event.

## User experience

After Spotisaver creates the ZIP and the user clicks Download ZIP, the downloader continues waiting while Chromium transfers the file. Progress remains visible. The browser is closed only after the transfer completes, is explicitly cancelled, or has made no measurable progress for a generous inactivity period.

## Functional requirements

- Treat Playwright's browser download event as confirmation that the transfer has started, not that it has completed.
- Wait for the matching Chromium DevTools Protocol download GUID to reach the `completed` state.
- Do not impose a 30-second total transfer deadline.
- Track the last time `receivedBytes` increases and reset the inactivity timer whenever new bytes arrive.
- Use a configurable internal default inactivity threshold of 120 seconds. A transfer that is still making progress must not time out, regardless of total duration.
- Detect Chromium's explicit `canceled` state and fail with a clear diagnostic.
- On inactivity timeout, include the last received byte count, expected total when known, and time since the last progress event in the error and diagnostic log.
- Keep displaying ZIP transfer progress while waiting.
- After Chromium reports completion, separately wait for the downloaded file to exist, be non-empty, and have stable size. This file verification must have its own bounded timeout and must not reuse an already expired transfer deadline.
- Preserve the Playwright `save_as()` fallback when CDP events are unavailable.
- Never click Download ZIP more than once for the same ready archive.

## Constraints

- Keep Chromium open until the transfer has completed or a genuine failure condition has been reached.
- Do not retry or restart a ZIP transfer automatically after it has started.
- Do not weaken archive validation.
- Do not claim that a live Spotisaver transfer has been tested by automated CI.

## Out of scope

- Changes to Spotisaver queue retry behaviour.
- Changes to album track downloading or audio import and merging.
- Changes to the website interaction or download button selection.

## Acceptance criteria

- [ ] A simulated transfer lasting longer than 30 seconds completes successfully when byte progress continues.
- [ ] A transfer with intermittent progress resets its inactivity timer correctly.
- [ ] A transfer with no progress for the full inactivity threshold fails with useful diagnostics.
- [ ] An explicit Chromium cancellation fails immediately with a clear error.
- [ ] File stability verification starts a fresh bounded timeout after the CDP completed event.
- [ ] Existing CDP event correlation and Playwright fallback tests continue to pass.
- [ ] Full unit tests, compilation, TKKGData contract smoke test, and FFmpeg integration tests pass.
- [ ] README and Knowledge Base document the new transfer waiting behaviour.

## Open questions

- None.
