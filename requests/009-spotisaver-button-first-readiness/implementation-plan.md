# Request 009 implementation plan

## Implementation

- Replace the page-text readiness gate with a Playwright polling helper that checks `#downloadAllBtn` immediately and then every 1,000 ms.
- Require the button to be visible, enabled, and labelled `Download entire playlist`.
- Keep the default polling timeout at 120,000 ms and log progress every 10 seconds without flooding the console.
- Click the button directly as soon as it is ready. Do not scroll and do not require the album title or all track titles to be present in the rendered page text.
- If the button does not appear within the polling window, log selector diagnostics, page title, a bounded body preview, and visible controls.
- Only after the main polling timeout, optionally click the visible `button.btn-playlist-download` scroll control and poll for the real button for a further 15 seconds.
- If no album action appears, retain the existing individual-track download fallback using normal visible controls.
- Keep the canonical Spotify album ID from TKKGData as the page identity anchor.
- Preserve strict downstream ZIP and MP3 validation in `audio_import.import_audio_files`. The expected track count, unique title matching, non-empty file checks, ZIP path safety, and rejection of extra tracks remain unchanged.
- Remove the obsolete page-body metadata readiness and verification helpers from the active provider implementation.
- Make the embedded JavaScript diagnostic source a raw Python string to avoid invalid escape warnings.

## Tests

- Test that the polling helper returns as soon as the expected button becomes visible.
- Test that it retries at the configured interval and returns no control on timeout.
- Test that hidden or disabled controls are not accepted.
- Test that the page diagnostics source compiles without SyntaxWarning.
- Retain archive import tests for exact count, title matching, empty files, corrupt ZIPs, and path traversal.
- Run the complete unittest suite and Python compilation in CI.

## Manual verification

Run `py tkkg.py 150 --provider spotisaver` locally. Confirm the logs show immediate polling, the number of seconds until the button appears, a direct click without scrolling, a browser download event, and the saved archive. Then confirm all 40 tracks validate, the merged MP3 is produced, and playback works. CI must not attempt a real download.
