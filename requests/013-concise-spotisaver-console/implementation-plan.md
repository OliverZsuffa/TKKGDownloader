# Implementation plan: Request 013

## 1. Separate user output from diagnostics

Refactor the current `_log` usage in `src/tkkgdownloader/spotisaver.py` into two explicit channels:

- A concise console reporter for meaningful user facing stage changes and progress.
- A timestamped diagnostic logger writing to a persistent per-run log file.

Do not merely silence selected messages. Ensure every browser and DOM diagnostic is routed to the file logger, including selector inspection and exception details. The diagnostic file must be created before browser launch and stored in a stable location outside the temporary download workspace. Use a predictable application log directory under the user's local application data directory on Windows, with a sensible platform appropriate fallback. Include the episode number and a timestamp in the filename. Do not overwrite previous run logs.

The logger must close cleanly after success, failure, or cancellation. If creating the log file fails, report that briefly and continue with concise console output where safe.

## 2. User facing stage reporter

Add a small reporter with explicit methods for stage changes, progress updates, and completion. Avoid direct `print` calls in the browser workflow except through this reporter.

Use concise messages such as:

- Opening browser...
- Browser opened.
- Starting download...
- Waiting for queue...
- Queue busy. Retrying in 30 seconds.
- Downloading...
- Preparing archive...
- Archive ready. Downloading...
- Archive downloaded. Validating tracks...
- All 40 tracks validated.
- Merging MP3...
- Done: <final output path>

Do not print the website button label, selector, page URL, browser event details, temporary paths, or raw website status. Print the episode heading once in the existing top level workflow and avoid duplicating the release title in the provider.

## 3. Progress display

Reuse the existing progress parsing and ETA extraction where possible. Improve the reporter so it:

- Updates a single terminal line in place when stdout is interactive.
- Displays completed/total tracks, percentage, and the currently visible website ETA.
- Does not print unchanged progress repeatedly.
- Does not render a percentage only as if it were a track count when the track counter is unavailable. Show only information that is actually known.
- Clears stale ETA when the website hides it or supplies invalid values.
- Finishes the progress line before any stage message.
- Emits concise periodic progress lines in non-interactive output, no more frequently than the existing 15 second heartbeat.
- Does not invent ETA from elapsed time or extrapolate from a single sample.

The website's visible ETA remains informational only and must not influence retries, completion, or timeouts.

## 4. Queue and browser stages

Keep the current queue state machine and retry safeguards. Report only the user relevant transition. For example, after the first explicit queue rejection, show that the queue is busy and the next retry will happen in 30 seconds. Do not expose attempt numbers unless they are needed to explain a repeated retry.

Once the site accepts the request and processing begins, show "Downloading..." and start the progress display. Do not keep printing queue status or generic heartbeat messages while the track counter is advancing.

Report archive preparation and the final browser archive transfer as separate stages. Do not expose the internal ZIP button name or click details.

## 5. Failure handling

Catch failures at the appropriate workflow boundary. The console should show a concise error message and the path to the diagnostic log. The diagnostic log should retain the traceback, last modal snapshot, selector state, and relevant browser state. Preserve Ctrl+C behaviour and ensure the log handler and browser close in cleanup paths.

Do not suppress meaningful errors or claim success before the archive has been saved, validated, and merged.

## 6. Downloader integration

Inspect `src/tkkgdownloader/downloader.py` and remove redundant verbose provider preamble lines such as the repeated Spotify and Spotisaver URLs and internal track validation narration. Keep the episode heading and a short statement that the verified track count is being processed if useful. The final output path remains visible.

Do not change the default yt-dlp provider's output unless shared logging changes are necessary and separately covered by tests.

## 7. Tests

Update `tests/test_spotisaver.py` and relevant downloader tests to cover:

- User facing stage messages are concise and contain no selector, button label, DOM attribute, raw status, or temporary path.
- Diagnostic messages are written to the log file rather than stdout.
- Log files are unique per run and survive temporary workspace cleanup.
- Progress updates overwrite one line in interactive mode.
- Non-interactive progress output is periodic and concise.
- Track count, percentage, and ETA appear when available.
- Missing, hidden, and invalid ETA values are not shown or retained as stale data.
- Queue rejection and retry are communicated plainly without verbose diagnostics.
- Accepted processing transitions to a single progress display.
- Archive creation and final browser download are distinct stages.
- Failure output includes a concise error and diagnostic log location.
- Existing listener ordering, queue retry, ZIP click, archive validation, merging, and cancellation tests continue to pass.

Use mocked browser objects and controllable time. Tests must not use real network access or real 30 second waits.

## 8. Documentation and verification

Update README and Knowledge Base logging documentation to describe concise console output and persistent diagnostic logs. Run Python compilation and all unit tests. Inspect the complete diff and CI results. Open a pull request for review. Do not merge until Oliver approves.
