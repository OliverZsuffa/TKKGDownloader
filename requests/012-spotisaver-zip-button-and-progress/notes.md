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

Not implemented. This request and its implementation plan are awaiting Oliver's approval.

## Verification status

No code or tests have been changed for this request. The exact final ZIP button markup remains to be captured only if visible role/name discovery proves insufficient during implementation or local testing.


## Output refinement

Oliver requested a real terminal progress bar similar to pip, not repeated textual progress updates. The implementation plan now specifies an in-place updating bar showing completed/total tracks, percentage, and ETA. It must finish cleanly before stage messages, and non-interactive output should use concise periodic lines.
