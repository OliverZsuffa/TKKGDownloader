# Request 011: Retry Spotisaver after a queue rejection

## Status

Proposed

## Objective

Make the Spotisaver provider recover from an explicit queue rejection by closing the rejected download modal and submitting the normal album download request again after the website's stated wait period.

## User experience

When Spotisaver reports that all download slots are busy and asks the visitor to try again in 25 seconds, the downloader should keep the visible browser open, wait 30 seconds, close the queue modal, and click the normal `Download entire playlist` button again. It should repeat this only when another explicit queue rejection is returned. Once Spotisaver accepts the request and begins processing, the downloader should stop retrying and wait for the browser download event, even if processing takes several minutes.

## Functional requirements

- Keep the existing visible Chromium session and canonical album URL.
- Register the browser download event listener before the first click and keep it active across retries.
- Click the verified `#downloadAllBtn` once to start the first attempt.
- Detect the explicit queue rejection in the rendered `#downloadMiniLog`, especially the message that all download slots are busy and the instruction to try again in 25 seconds.
- On that rejection, wait 30 seconds from detection. Continue checking for a download event and modal state during the wait.
- After 30 seconds, re-read the modal. If the queue rejection is still the active state and no download event has arrived, click the modal's visible close control, normally `button[aria-label="Close"]`.
- Verify that the modal has closed before proceeding.
- Verify that `#downloadAllBtn` is visible and enabled, then click it once to submit a new attempt.
- Monitor the new attempt. If it is rejected by the queue again, repeat the same 30-second wait and close-and-reclick sequence.
- If the queue rejection clears and the page moves into actual playlist processing, do not close the modal or issue another click. Continue waiting for the download event without a fixed two-minute timeout.
- Never click while a modal is still open. Never issue overlapping or speculative clicks.
- Keep the browser open while waiting and processing. Ctrl+C must cancel cleanly through the existing browser cleanup.
- If the page closes, the close control is unavailable, the modal cannot be dismissed, or the album button does not become available after closing, fail with a clear diagnostic rather than guessing.
- Log each attempt number, queue rejection, 30-second wait, modal close, reclick, and eventual download event. Keep the 15-second heartbeat.
- Apply the same queue retry behaviour to individual-track fallback only if it uses the same explicit queue notice and normal visible controls.
- Preserve all existing archive safety, exact 40-track matching, non-empty file checks, and merge validation.

## Constraints

- Use only visible, rendered website controls and text.
- Do not inspect hidden endpoints or private media URLs.
- Do not bypass the queue, premium restrictions, or other access controls.
- Do not reload the page or restart Chromium between attempts.
- Retry only after the explicit queue-busy rejection. Do not retry generic errors or ambiguous stalled states.
- Keep the retry interval at 30 seconds for this change.

## Out of scope

- Changing the source provider or canonical TKKGData mappings.
- Changing the existing track matching or merge pipeline.
- Adding configurable retry settings or a separate retry command.
- Retrying arbitrary failures that are not explicit queue rejections.

## Acceptance criteria

- [ ] The initial album request is clicked exactly once.
- [ ] The download listener remains active across all attempts and cannot miss an immediate download event.
- [ ] An explicit queue rejection triggers a 30-second wait.
- [ ] If the queue rejection remains after 30 seconds, the modal is closed through its visible close control.
- [ ] The modal is confirmed closed before the album button is clicked again.
- [ ] The album button is verified visible and enabled before each retry click.
- [ ] Repeated explicit queue rejections cause repeated 30-second retry cycles.
- [ ] Once processing begins or a download event arrives, no further retry click is issued.
- [ ] No retry occurs for generic errors or a merely slow download.
- [ ] The browser remains open throughout queueing and processing.
- [ ] Ctrl+C exits cleanly.
- [ ] Failure to close the modal or recover the button produces a clear diagnostic.
- [ ] Existing strict archive and track validation remains unchanged.
- [ ] Unit tests cover queue detection, wait timing, modal closure, retry click ordering, repeated rejection, successful processing, delayed download events, and cancellation.
- [ ] Full CI passes.

## Open questions

- None. The supplied modal HTML identifies the visible close control and the user has explicitly requested a 30-second close-and-reclick retry.
