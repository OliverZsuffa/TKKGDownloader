# Request 007: Spotisaver action button workflow

## Problem

The Spotisaver page now loads the expected album and complete tracklist, but the downloader does not reach the actual download controls. The page's visible `button.btn-playlist-download` labelled `Download Playlist` only invokes `scrollToActionButtons()`. It scrolls the page to the real action buttons and does not itself download a file.

The current implementation searches immediately for a button or link with an accessible name matching album download wording. It therefore misses the page's intermediate scroll control and may also miss icon-only or differently labelled action controls.

## Proposed implementation

1. After album and tracklist verification, first locate the actual playlist download control using `#downloadAllBtn` and verify its visible label is `Download entire playlist`.
2. If that control is already visible, click it directly. Do not click the scroll control or perform unnecessary scrolling.
3. Only if the actual download control is not visible, locate `button.btn-playlist-download` with visible text `Download Playlist`, click it through normal Playwright interaction, and wait a bounded time for `#downloadAllBtn` to become visible. Do not use fixed sleeps.
4. Add concise diagnostics for visible buttons and links if the expected download action still cannot be found. Include tag, visible text, title, aria-label, class, href, and download attributes.
5. Before clicking, report which actual download control was selected. Verify a real browser download event and non-empty saved file.
6. Preserve current album and tracklist validation, ZIP safety checks, track matching, one-episode limit, and existing FFmpeg merge workflow.
7. Add mocked unit tests for direct button priority, scroll fallback selection, and missing or hidden controls. Do not perform real downloads in CI.
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
