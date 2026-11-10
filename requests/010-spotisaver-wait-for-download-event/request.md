# Request 010: Wait for Spotisaver to start the browser download

## Problem

The local run successfully finds and clicks the visible `#downloadAllBtn` control. Playwright reports that the click call returned, but no browser download event arrives within the current 120-second timeout. The provider then closes Chromium and fails.

The timeout is not measuring the file transfer. It is measuring how long Spotisaver takes to initiate a browser download after the click. Spotisaver may take substantially longer than two minutes to prepare the album archive.

## Required behaviour

1. Keep the existing visible Chromium workflow and normal website button click.
2. After clicking the verified album download button, keep the browser open and wait for the browser's download event without a fixed two-minute deadline.
3. Emit a concise progress message periodically while waiting, so it is clear that the program is still active.
4. Do not click the button again while waiting. A single click must initiate at most one album download.
5. Once the browser emits the download event, save the file and continue with the existing file validation and merge workflow.
6. If the user presses Ctrl+C, stop waiting, close the browser cleanly, and propagate the interruption rather than swallowing it.
7. If the browser page or browser itself closes unexpectedly before a download event, report that as a real failure with useful diagnostics. Do not wait forever after the browser is gone.
8. Keep a separate finite timeout for locating the album button. This request changes only the post-click wait for the download event.
9. Apply the same wait behaviour to the individual-track fallback, without weakening track validation.

## Acceptance criteria

- The album button is clicked exactly once.
- There is no fixed 120-second timeout for the browser download event.
- While waiting, the console reports that it is still waiting at a reasonable interval.
- A download event arriving after more than two minutes is accepted.
- A download event arriving immediately is handled without a race.
- Ctrl+C exits cleanly and does not trigger a second click or fallback.
- Unexpected browser closure produces a clear error rather than an endless wait.
- Existing file saving, archive safety, exact track matching, and merge validation remain unchanged.
- Unit tests and GitHub Actions pass.
- CI uses mocked browser events and does not perform a live Spotisaver download.

## Scope limits

Do not change the website interaction, inspect hidden endpoints, extract private media URLs, bypass access controls, or weaken existing validation. Keep Chromium visible and use only the normal rendered website controls.
