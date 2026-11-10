# Request 012 notes

## Initial evidence

Oliver supplied a live modal snapshot from episode 150 showing:

- Status `Downloaded 30 of 40`.
- Progress bar value 75%.
- A pending entry for track 31 in the mini-log.
- ETA container `#est_timeModalBody` with template `Estimated time: {minutes}m {seconds}s`.
- Structured ETA spans using `data-eta-part="minutes"` and `data-eta-part="seconds"`.
- A keep-open notice.

A later console excerpt showed the processing state progressing through:

- `Downloaded 39 of 40` at 98%.
- `Creating ZIP archive... please wait...`.
- `ZIP archive created.` at 100%.
- A newly visible `Download ZIP` button inside the modal.

The browser download event had not yet occurred at the point of the supplied log. Oliver clarified that the final `Download ZIP` button must be clicked to trigger the actual browser download.

## Implementation status

Approved by Oliver on 2026-11-10. Implementation is on `implement/spotisaver-zip-button-progress`.

- Extended the modal snapshot with ETA text, template, minutes, seconds, track counter, progress percentage, and visible control diagnostics.
- Added ETA formatting and track progress parsing, plus a pip-style progress reporter that updates the same terminal line when interactive and uses periodic summaries otherwise.
- Added active-modal discovery of the unique visible, enabled `Download ZIP` button using accessible role/name lookup with exact rendered-text fallback.
- The final ZIP button is clicked once after the archive-ready status. The browser download listener remains registered from before the initial album request.
- Added focused unit tests for progress parsing, ETA formatting, progress rendering, ZIP button discovery, and the final ZIP click/download event sequence.

## Verification status

Automated tests and CI are pending. No live Spotisaver download has been performed with this implementation.

## Verification status

No code or tests have been changed for this request. The exact final ZIP button markup remains to be captured only if visible role/name discovery proves insufficient during implementation or local testing.


## Output refinement

Oliver requested a real terminal progress bar similar to pip, not repeated textual progress updates. The implementation plan now specifies an in-place updating bar showing completed/total tracks, percentage, and ETA. It must finish cleanly before stage messages, and non-interactive output should use concise periodic lines.

