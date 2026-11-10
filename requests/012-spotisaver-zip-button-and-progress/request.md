# Request 012: Complete Spotisaver ZIP download and improve progress output

## Status

Proposed. Awaiting Oliver's approval before implementation.

## Objective

Complete the Spotisaver album workflow after the website finishes preparing its ZIP archive, and make long-running downloads easier to monitor from the terminal.

## User experience

After the playlist has been processed, Spotisaver displays a final `Download ZIP` button in the existing modal. The downloader must click this visible button to trigger the actual browser download. The browser download event is not expected when the playlist processing finishes; it is expected only after the ZIP button is clicked.

While processing, show a concise progress line with the number of tracks downloaded, percentage, current status, and estimated remaining time when available. Keep detailed diagnostics available for troubleshooting without flooding the normal console output.

## Functional requirements

- Keep the existing visible Chromium page, modal monitoring, queue retry behaviour, and persistent browser download listener.
- Extend the modal snapshot to read the ETA element `#est_timeModalBody`, its `data-eta-template`, and the rendered `[data-eta-part="minutes"]` and `[data-eta-part="seconds"]` values.
- Treat ETA as an optional, changing estimate. Display it when both values are available and valid. Do not use ETA as a completion signal, retry trigger, or hard timeout because it may change or disappear.
- Parse the track counter from statuses such as `Downloaded 30 of 40`. Read progress percentage from the rendered progress element and use it as supplementary information, not as the sole completion criterion.
- Preserve the visible mini-log and use it to diagnose completed, pending, or failed tracks. Avoid dumping the full mini-log on every poll.
- Recognise the final archive-ready state, including status text such as `ZIP archive created.`.
- In that state, locate the visible, enabled button inside the active modal whose rendered accessible name or text is `Download ZIP`. Do not assume an exact selector until confirmed from the live page. Use robust role/text-based discovery scoped to the active modal, and log selector diagnostics if it cannot be found.
- Click `Download ZIP` exactly once for each successfully created archive. Do not close the modal or re-click the original album button at this stage.
- Keep the browser download event listener registered before the first album click and active through queue retries, processing, ZIP creation, and the final ZIP-button click. This prevents missing a fast download event.
- After clicking `Download ZIP`, wait for the browser download event without imposing an arbitrary short timeout. Save the file using the existing download handling and continue safe ZIP extraction and strict canonical track validation.
- Do not report success merely because the status says the ZIP was created. Success requires the actual browser download event, a saved non-empty archive, successful validation of every expected track, and the existing merge checks.
- Detect an explicit website failure state and unexpected page closure as before. If the archive-ready state appears but the ZIP button is missing, disabled, or cannot be clicked, fail with useful modal and control diagnostics rather than clicking an unrelated control.
- Keep Ctrl+C cancellation and browser cleanup reliable.

## Console output

Provide three complementary aspects of output:

1. A live terminal progress bar for ordinary use, similar to pip. Update the same console line in place using carriage return or an equivalent terminal-aware mechanism. Show a visual bar, completed/total tracks, percentage, and ETA when available. Example:

   ```text
   Spotisaver  [███████████████░░░░░]  30/40 tracks  75%  ETA 1m 32s
   ```

   When processing completes, finish the progress line cleanly before switching to short stage messages. In non-interactive output, use concise periodic progress lines instead. Do not emit a new progress line for every poll.

2. A readable stage summary for meaningful state transitions, for example:
   - `[Spotisaver] Opening album 150: Heiße Nächte im Dezember`
   - `[Spotisaver] Queue busy. Retrying in 30 seconds (attempt 1)`
   - `[Spotisaver] Downloading tracks: 30/40 (75%). ETA 1m 32s`
   - `[Spotisaver] Creating ZIP archive`
   - `[Spotisaver] ZIP ready. Starting browser download`
   - `[Spotisaver] ZIP saved: <filename> (<size>)`
   - `[Spotisaver] Validated 40/40 tracks. Merging MP3`
3. Detailed timestamped diagnostics for troubleshooting. Retain useful selector counts, modal state changes, retry decisions, click stages, download event timing, filename, file size, and exception details. Avoid repeating the entire mini-log or unchanged selector details every second. If a verbose/debug switch already exists, use it; otherwise keep concise progress as the default and detailed diagnostics on meaningful transitions and failures. Do not add a new CLI option unless the existing architecture makes it clearly necessary.

- Keep the 15-second heartbeat, but make it concise and include current progress and ETA where available.

## Constraints

- Use only visible, rendered page text and controls. Do not inspect hidden endpoints or private media URLs.
- Do not bypass queue, premium restrictions, or other website access controls.
- Do not change canonical TKKGData mappings, track matching rules, ZIP safety checks, or FFmpeg merge semantics.
- Treat ETA as informational only.
- Do not assume the final button's DOM selector from its label alone. Discover it through visible accessible role/name or rendered text, then verify it is unique, visible, and enabled.

## Out of scope

- Changing provider selection or the canonical metadata source.
- Downloading individual tracks as a workaround for a failed final ZIP action.
- Adding arbitrary download timeouts or using ETA to force retries.
- Reworking the full CLI interface or adding unrelated logging configuration.

## Acceptance criteria

- [ ] Modal snapshots include ETA text and structured minutes/seconds when present.
- [ ] ETA changes are reflected in readable progress output and missing/invalid ETA is handled safely.
- [ ] Track count and percentage are displayed accurately when available.
- [ ] Progress output remains concise and does not repeatedly print the full mini-log.
- [ ] The final `ZIP archive created.` state is detected.
- [ ] The visible, enabled `Download ZIP` control is found inside the active modal.
- [ ] The final ZIP button is clicked exactly once after archive creation.
- [ ] The existing download listener catches the browser download event triggered by that final button.
- [ ] No false success is reported before the archive is actually saved and validated.
- [ ] Missing or ambiguous ZIP controls produce actionable diagnostics.
- [ ] Queue retry behaviour from Request 011 remains unchanged.
- [ ] Existing ZIP safety, exact track matching, and merge validation remain unchanged.
- [ ] Unit tests cover ETA parsing, progress parsing, archive-ready detection, ZIP button discovery and click ordering, delayed download events, missing controls, and cancellation.
- [ ] Compilation and full CI pass.

## Open questions

- The exact DOM markup and selector for the final `Download ZIP` button are not yet available. Start with visible role/name or text discovery scoped to the active modal. If that is insufficient during local testing, ask Oliver to capture the button element HTML from the live modal and refine the selector.
