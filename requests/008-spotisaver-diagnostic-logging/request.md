# Request 008: Spotisaver diagnostic logging

## Problem

The Spotisaver provider opens Chromium, but the last local run appeared to stop without clicking any download control. Current console output does not expose enough intermediate state to identify whether the workflow is waiting for album data, failing to find a button, choosing the wrong control, or getting stuck during the click/download event.

## Proposed implementation

1. Add timestamped, flushed progress messages for every major stage: browser launch, navigation start/completion, document readiness, album data wait start/completion, album verification, download-control discovery, click attempt, download event, save, and file validation.
2. For each relevant selector, log count, visibility, label/text, and identifying attributes. Specifically inspect `#downloadAllBtn`, `#downloadAllBtnLabel`, and `button.btn-playlist-download`.
3. Log the direct-first decision explicitly. If the actual download button is visible, click it without scrolling. Only use the intermediate scroll button if the real button is absent or hidden.
4. If neither path succeeds, log a bounded inventory of visible buttons and links, including tag, text, id, class, aria-label, title, href, and download attribute.
5. Wrap the click and download wait in explicit diagnostic handling. Distinguish click failure, download-event timeout, save failure, and empty file. Log the suggested filename, destination, and byte size after a successful save.
6. Log individual track fallback progress with track number, title, button discovery, click, and download result.
7. Include elapsed durations and preserve the original exception details and traceback context in the final error. Do not silently swallow errors.
8. Keep browser visible, preserve current album/track verification and ZIP safety, and do not add fixed sleeps or unnecessary scrolling.
9. Add mocked tests for selector diagnostics and download-stage reporting where practical. Run the full unit suite and CI. No real audio downloads in CI.
10. Update README, Knowledge Base, request index, and implementation notes.

## Constraints

- Use only normal visible Playwright interactions with the public page.
- Do not use hidden APIs, private endpoints, direct media URL extraction, stealth settings, or access-control workarounds.
- Do not weaken album identity or track validation.
- Keep the one-episode-per-invocation limit.

## Acceptance criteria

- A local run prints a clear, timestamped trace of each stage and every selector decision.
- It is unambiguous whether the direct button was found and clicked, whether the scroll fallback was used, and whether a browser download event fired.
- Failures identify the exact stage and include useful diagnostics.
- All automated tests and CI checks pass.
