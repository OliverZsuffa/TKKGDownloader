# Implementation Plan: Request 008

## Implementation

- Add a timestamped logging helper with local timezone timestamps, monotonic elapsed durations, and immediate console flushing.
- Instrument the browser lifecycle: launch, navigation, document visibility, album lookup, album verification, control discovery, download, save, validation, and browser shutdown.
- Inspect `#downloadAllBtn`, `#downloadAllBtnLabel`, and `button.btn-playlist-download` with match counts, visibility, visible text, and identifying attributes.
- Make the direct-first decision explicit in the log. Click the real album action without scrolling whenever it is already visible. Use the intermediate navigation control only as a fallback.
- Distinguish a click failure from a click that returned without producing a browser download event. Log the website's suggested filename, destination, saved byte size, and elapsed time.
- Log individual track fallback discovery and download progress.
- Report the exact failing workflow stage, preserve exception chaining, and print traceback context for actionable local diagnosis.
- Keep the browser visible, album and track verification intact, ZIP safety unchanged, and the one-episode limit unchanged. Do not add fixed sleeps, hidden APIs, direct media URL extraction, or access-control workarounds.

## Tests

- Mock selector inspection and verify visibility, text, and attributes are included in the diagnostic output.
- Mock a successful browser download and verify click, event, filename, and saved-size diagnostics.
- Run the full unittest suite and repository CI. Tests must not perform real audio downloads.

## Documentation

Update the README, request index, and Knowledge Base technical decision. Record test results and live-verification status in this request's notes.

## Live verification

A successful mocked test or CI run does not establish that Spotisaver currently initiates a real download. Oliver should run `py tkkg.py 150 --provider spotisaver` locally and share the console trace if the provider still fails.
