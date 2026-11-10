# Request 013: Make Spotisaver console output concise

## Status

Approved. Implementation and verification in progress.

## Objective

Replace the current verbose Spotisaver terminal output with a clean, user focused progress display. The normal console should communicate only what the user needs to know about the download. Browser internals and diagnostics must not be printed during a normal successful run.

## Desired normal output

Use this as the target interaction, adapting messages to the actual state:

```text
TKKG 148: Fieser Trick beim Finale

Opening browser...
Browser opened.
Starting download...
Waiting for queue...
Queue busy. Retrying in 30 seconds.
Downloading...
[████░░░░░░░░░░░░░░░]  8/40 tracks  20%  ETA 5m 20s
```

After the browser has prepared the archive:

```text
All tracks downloaded. Preparing archive...
Archive ready. Downloading...
Archive downloaded. Validating tracks...
All 40 tracks validated.
Merging MP3...
Done: output/TKKG 148 - Fieser Trick beim Finale.mp3
```

Exact wording can be refined during implementation, but the output must remain short and understandable.

## Normal console requirements

1. Print the episode title once.
2. Print short stage messages only when a meaningful state transition occurs:
   - Opening browser.
   - Browser opened.
   - Starting the download request.
   - Waiting for the queue, including a retry countdown when the site explicitly rejects the request.
   - Downloading, once Spotisaver accepts the request.
   - Preparing the archive, when that stage is reached.
   - Downloading the completed archive through the browser.
   - Validating tracks.
   - Merging MP3.
   - Final output path on success.
3. During track processing, render one in-place progress bar in interactive terminals. Include completed tracks, total tracks, percentage, and the ETA read from Spotisaver's visible browser UI when available.
4. Update the same line. Do not print a new line for every poll. Do not show a second progress indicator for the same work.
5. In non-interactive terminals, print concise progress updates periodically rather than flooding output.
6. Never print CSS selectors, button names, accessible labels, DOM attributes, raw modal contents, full mini-logs, browser event internals, or per-poll timestamps in normal output.
7. Do not print the name or text of the website button that was clicked. A generic message such as "Starting download..." is sufficient.
8. Do not print temporary directory paths or internal browser download paths.
9. Keep the output path of the final MP3 visible.
10. Do not show an ETA unless it is available and valid from the rendered website UI. Do not calculate a misleading ETA from a single progress sample.

## Diagnostics

Move detailed diagnostic output to a log file for the current run, stored outside the temporary download directory so it remains available after success or failure. The log should include timestamps, browser and selector diagnostics, modal snapshots, retry decisions, download event details, exception traces, and temporary paths.

On failure, print a short actionable error to the console and tell the user where the diagnostic log was saved. Do not dump the complete traceback or DOM diagnostics into the normal console unless required to explain an unrecoverable setup issue.

Do not introduce a verbose CLI flag unless the existing architecture requires it. Normal output should be concise by default.

## Behaviour to preserve

- Visible Chromium browser interaction.
- No scrolling just to reach the album download control.
- Existing queue rejection detection and 30 second retry behaviour.
- Retry only after an explicit queue rejection that remains active.
- No retry after processing has begun.
- Persistent browser download listener.
- Final ZIP control clicked exactly once after archive creation.
- Waiting for the actual browser download event without an arbitrary fixed timeout.
- Existing archive safety checks and exact TKKGData track validation.
- Automatic FFmpeg merging after successful validation.
- Existing output overwrite protection.
- Ctrl+C handling and browser cleanup.

## Acceptance criteria

- [ ] A normal successful run contains only short stage messages, a single progress bar, and the final MP3 path.
- [ ] No selector names, button names, DOM attributes, raw status text, full mini-log, or per-poll timestamps appear in normal output.
- [ ] The queue retry is communicated in plain language with its wait duration.
- [ ] The transition from queue waiting to accepted downloading is clear.
- [ ] The progress bar updates in place and includes tracks, percentage, and website ETA when available.
- [ ] Missing or invalid ETA is handled without stale or invented estimates.
- [ ] Archive creation and the subsequent browser ZIP transfer are communicated as distinct stages.
- [ ] Detailed diagnostics are saved to a persistent per-run log file.
- [ ] On failure, the console reports a concise explanation and the diagnostic log location.
- [ ] Existing retry, download, validation, merge, and cancellation behaviour remains unchanged.
- [ ] Unit tests cover concise output, hidden diagnostics, progress rendering, retry messages, archive stages, and failure log reporting.
- [ ] Python compilation and the full CI suite pass.
