# Request 007: Spotisaver action button workflow

## Problem

The Spotisaver page now loads the expected album and complete tracklist, but the downloader does not reach the actual download controls. The page's visible `button.btn-playlist-download` labelled `Download Playlist` only invokes `scrollToActionButtons()`. It scrolls the page to the real action buttons and does not itself download a file.

The current implementation searches immediately for a button or link with an accessible name matching album download wording. It therefore misses the page's intermediate scroll control and may also miss icon-only or differently labelled action controls.

## Proposed implementation

1. After album and tracklist verification, explicitly locate the playlist navigation control using the observed stable selector `button.btn-playlist-download`, with the visible text `Download Playlist` as a secondary check.
2. Click it through Playwright's normal visible interaction. Wait for the action area to become visible, using a bounded wait rather than a fixed sleep.
3. Add diagnostics for visible buttons and links in the action area. Log role, accessible name, visible text, title, aria-label, class, and relevant href/download attributes. Keep diagnostics concise and avoid dumping the entire page or unrelated content.
4. Identify the actual album ZIP action and individual track actions from the revealed action area. Prefer semantic role/name and explicit attributes, with observed DOM structure as a fallback. Do not guess that the scroll button is a download.
5. Before clicking a candidate, report which control was selected. After clicking, verify a real browser download event and non-empty saved file. If the site uses a different documented visible interaction, fail with the diagnostics instead of silently claiming success.
6. Preserve current album and tracklist validation, ZIP safety checks, track matching, one-episode limit, and existing FFmpeg merge workflow.
7. Add unit tests for selector choice, diagnostics formatting, and failure when no actual download control is found. Use mocked Playwright objects. Do not perform real downloads in CI.
8. Update README and Knowledge Base/request documentation.

## Scope and constraints

- Use only the public Spotisaver page and normal visible browser interactions.
- Do not use private endpoints, hidden APIs, direct media URL extraction, stealth settings, or access-control workarounds.
- Keep the browser visible for this workflow.
- Do not weaken album identity or track validation.
- The user will perform the live website test locally after the change.

## Acceptance criteria

- The program clicks `button.btn-playlist-download` only as a navigation/scroll action.
- It waits until the actual action area is visible before searching for download controls.
- Diagnostics make it clear which visible controls were found and why a candidate was or was not selected.
- A download is considered successful only after Playwright reports a download and the saved file is non-empty.
- All automated tests and repository CI checks pass.
