# Request 009: Make Spotisaver readiness button-first

## Problem

The current workflow waits for the album title and every expected track title to appear in the page body before it inspects any download controls. The recent local run showed that the page opened successfully and the download button was visible, but the wait timed out after 120 seconds. Because control discovery happens after the wait, the program never attempted the visible button.

The run also emitted a Python SyntaxWarning because a JavaScript regular expression containing `\s` is embedded in a normal Python string.

## Proposed change

1. After navigation and body visibility, inspect the real album download control immediately.
2. If `#downloadAllBtn` is visible and has the expected label, do not wait for every track title in page text. The URL already comes from the verified Spotify album ID in TKKGData. Log that the button-first readiness path was selected and click the actual button directly, without scrolling.
3. Keep the album and archive validation safeguards. The downloaded archive must still be checked against all 40 expected tracks by the existing import and validation pipeline. If the control is absent, retain the existing album metadata wait and verification path, but capture page title, body text preview, and control inventory on timeout so the next failure is diagnosable.
4. Make `_verify_album_page` conditional on the same readiness mode: in button-first mode, rely on the verified album ID and strict downloaded archive validation rather than requiring every track title to be rendered in page text. Do not weaken archive track count, title matching, ZIP safety, or one-episode constraints.
5. Fix the JavaScript whitespace normalization string so Python no longer emits the invalid escape sequence warning.
6. Add tests for immediate button-first readiness, no unnecessary wait when the real button is visible, fallback metadata wait when it is not, and warning-free JavaScript regex source.
7. Update implementation notes, README if necessary, and Knowledge Base.

## Acceptance criteria

- A visible `#downloadAllBtn` is detected immediately after page readiness.
- When visible, Playwright attempts the button click without waiting 120 seconds and without scrolling.
- The downloaded archive still has to pass full validation against the canonical 40-track list before merging.
- If the button is not visible, the fallback path retains clear diagnostics and does not guess or click unrelated controls.
- Unit tests and GitHub Actions pass.
- No real download is performed in CI.

## Scope limits

No hidden APIs, private endpoints, direct media URL extraction, stealth settings, or access-control workarounds. Keep the browser visible and preserve all existing safety checks.