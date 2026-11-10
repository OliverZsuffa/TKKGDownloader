# Request 010: Wait for Spotisaver's queued album download

## Problem

The local run successfully finds and clicks the visible `#downloadAllBtn` control. Playwright reports that the click call returned, but no browser download event arrives within the current 120-second timeout. The provider then closes Chromium and fails.

Spotisaver does not necessarily start preparing the archive immediately. It can queue requests when all download slots are busy. The supplied modal HTML showed this state:

- The modal opens and displays the album title.
- `#downloadStatusText` says the playlist is downloading.
- `#downloadMiniLog` displays a notice: "Sorry, all download slots are busy right now."
- The notice asks the visitor to try again in 25 seconds.
- The user has observed that fetching a playlist can take approximately seven minutes.

The current implementation waits only for the browser download event. It does not report or interpret the queue state, and its 120-second event timeout is too short.

## Required behaviour

1. Keep the existing visible Chromium workflow and normal website button click.
2. Register the browser download-event listener before clicking the verified album download button. Click the button exactly once.
3. Keep Chromium open after the click. Do not use a fixed two-minute deadline for the browser download event.
4. While waiting, periodically inspect the rendered download modal, especially `#downloadStatusText`, `#downloadMiniLog`, `#downloadFailedBadge`, and any visible progress or retry controls.
5. Report meaningful status changes in the console. At minimum, distinguish:
   - Waiting for a download slot because the queue is busy.
   - The queue notice's stated retry delay, when it can be parsed.
   - Playlist processing or progress.
   - An explicit failure reported by the page.
   - Waiting for the browser download event after processing.
6. Emit a concise heartbeat approximately every 15 seconds even if the modal text has not changed.
7. Treat the stated 25-second delay as information from the page, not proof that an automatic retry will occur. The user's observation does not establish whether Spotisaver retries automatically. Do not automatically click the download button again or invent a retry control. Observe whether the page changes or exposes an explicit retry action, and log the result.
8. Do not close Chromium merely because the queue wait or playlist processing takes several minutes. The user observed a fetch taking approximately seven minutes.
9. Once the browser emits the download event, save the file and continue with the existing file validation and merge workflow.
10. If the user presses Ctrl+C, stop waiting, close the browser cleanly, and propagate the interruption rather than swallowing it.
11. If the browser page or browser itself closes unexpectedly before a download event, report that as a real failure with useful diagnostics. Do not wait forever after the browser is gone.
12. Keep a separate finite timeout for locating the album button. This request changes only the post-click wait and adds modal monitoring.
13. Apply equivalent waiting and status monitoring to the individual-track fallback where the same modal is used, without weakening track validation.

## Acceptance criteria

- The album button is clicked exactly once.
- The download listener is registered before the click, so an immediate event cannot be missed.
- There is no fixed 120-second timeout for the browser download event.
- The modal is inspected periodically while waiting.
- Queue notices and their stated retry delays are reported accurately.
- The program does not assume that a queue notice causes an automatic retry.
- The program does not issue another click unless a separately specified and approved retry behaviour is implemented later.
- Meaningful modal status changes and periodic heartbeats are logged.
- A download event arriving after more than two minutes, including after a wait of approximately seven minutes, is accepted.
- Ctrl+C exits cleanly and does not trigger a second click or fallback.
- Unexpected browser closure or an explicit page failure produces a clear diagnostic.
- Existing file saving, archive safety, exact track matching, and merge validation remain unchanged.
- Unit tests and GitHub Actions pass.
- CI uses mocked browser events and does not perform a live Spotisaver download.

## Scope limits

Do not change the website interaction beyond the existing normal rendered controls, inspect hidden endpoints, extract private media URLs, bypass access controls, or weaken existing validation. Keep Chromium visible. Do not add automatic repeated clicks in this request.
