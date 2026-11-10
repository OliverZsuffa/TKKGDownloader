# Implementation Plan: Request 007

## Implementation

- Add a direct lookup for Spotisaver's observed `#downloadAllBtn` control and require its visible label to identify it as `Download entire playlist`.
- Keep the generic semantic album-download lookup as a secondary path.
- Only when no actual album download control is visible, locate `button.btn-playlist-download` labelled `Download Playlist` and click it as a navigation action.
- Wait for `#downloadAllBtn` to become visible with a bounded Playwright wait. Do not add fixed sleeps.
- If the expected album action is still missing, log a compact list of visible buttons and links, including useful attributes, before attempting any individual track controls.
- Keep the existing Playwright download event and non-empty file verification unchanged.

## Tests

- Verify the visible full-playlist button is preferred.
- Verify a hidden full-playlist button is not selected.
- Verify the scroll navigation button is recognised only as a fallback.
- Verify unrelated navigation controls are rejected.
- Run the full unittest suite and repository CI. CI must not perform real audio downloads.

## Documentation

Update the request, README, request index, and Knowledge Base technical decision to record the direct-first workflow.

## Live verification

After CI passes, Oliver will run the provider locally against the public Spotisaver album page. A real download and merge are not claimed as verified by mocked tests.
