# Request 009: Poll Spotisaver for the album download button

## Problem

The current workflow waits for the album title and every expected track title to appear in the page body before inspecting any download controls. The recent local run showed that the page opened successfully and the download button was visible, but the metadata wait timed out after 120 seconds. Because control discovery happened after that wait, the program never attempted the visible button.

The run also emitted a Python SyntaxWarning because a JavaScript regular expression containing `\s` was embedded in a normal Python string.

## Required workflow

1. Open visible Chromium and navigate to the canonical Spotisaver album URL built from the verified Spotify album ID in TKKGData.
2. Wait only until the page body is visible.
3. Immediately check for `#downloadAllBtn`.
4. If it is not yet present and visible, wait one second and check again. Repeat for up to 120 seconds.
5. Accept the control only when it is visible, enabled, and its text matches `Download entire playlist`.
6. As soon as it is ready, click it directly. Do not scroll first and do not wait for all 40 track titles to appear in the page text.
7. If the 120-second polling period expires, log the page title, a bounded body text preview, selector state, and visible control inventory. Only then may the existing `button.btn-playlist-download` navigation control be used, followed by a short additional poll for the real download button.
8. If the album download control remains unavailable, retain the existing sequential individual-track fallback. Do not select unrelated controls.
9. Validate the downloaded ZIP or MP3 files against every expected track from TKKGData. Require the exact expected count, unique filename matches, non-empty files, safe ZIP paths, and no unexpected audio files before merging.
10. Fix the JavaScript whitespace normalization string so Python emits no invalid escape SyntaxWarning.

## Acceptance criteria

- The first check for `#downloadAllBtn` happens immediately after the page body becomes visible.
- The button is rechecked every second for up to 120 seconds.
- A visible, enabled button with the expected label is clicked immediately without scrolling or waiting for track titles.
- The 40-track archive validation remains strict and unchanged.
- Timeout diagnostics explain what appeared on the page and which controls were visible.
- Individual track fallback remains limited to the normal visible website controls.
- Unit tests and GitHub Actions pass.
- CI performs no real Spotisaver download.

## Scope limits

No hidden APIs, private endpoints, direct media URL extraction, stealth settings, CAPTCHA bypasses, login bypasses, or access-control workarounds. Keep the browser visible and preserve all existing safety checks.
