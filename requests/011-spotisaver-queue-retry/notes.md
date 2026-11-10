# Request 011 implementation notes

## Implemented

- Kept one browser download listener registered across all attempts.
- Added explicit detection of the visible all-download-slots-busy queue rejection.
- Waits 30 seconds from the first detection while continuing to monitor the page.
- Rechecks the modal immediately before retrying.
- Closes the visible modal using its accessible Close button and confirms that the modal is no longer visible.
- Verifies that the original album download button is visible and enabled before clicking it again.
- Repeats the same sequence only after another explicit queue rejection.
- If the queue notice clears into processing, continues waiting without another click.
- Generic stalls and other failures do not trigger retries.
- Preserves the same retry control for individual-track fallback downloads.
- Keeps the existing no-fixed-timeout browser download wait, heartbeat, Ctrl+C handling, save checks, ZIP validation, exact track matching, and merge gating.

## Tests added or updated

- Queue notice clears before the retry deadline, so no retry is issued.
- Queue rejection remains active for 30 seconds, then modal closure is confirmed before a second click.
- Download listener remains active and receives the eventual download event on the second attempt.
- Generic slow processing does not trigger a retry.
- Existing queue parsing, failure detection, cancellation, and download validation tests remain in place.

## Verification

- GitHub Actions run 42811984143 passed: project installation, Python compilation, TKKGData contract smoke test, and all 55 unit tests.
- PR #14 was squash merged into main as `baadeb5a7d092e85096a5d7c9d7d4f0fcf01585f`.
- CI mocks the page and browser events. It does not make a live Spotisaver request.
- Oliver must rerun the downloader locally to verify actual queue rejection, modal closure, repeated attempts, and the final download.
