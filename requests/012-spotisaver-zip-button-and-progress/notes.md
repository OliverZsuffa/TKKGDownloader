# Request 012 notes

## Initial evidence

Oliver supplied a live modal snapshot showing:

- Status `ZIP archive created.` and a completed progress bar.
- All 40 playlist tracks listed as successful in the mini-log.
- The archive ready card inside `#downloadModalBody`.
- A visible `Download ZIP` anchor with class `.zrc-cta`, rather than a button.
- The anchor is nested inside `.zip-ready-card` and has a direct download URL ending in `?direct=1`.
- The card also displays the album name, track count, archive size, and downloaded or failed counts.

This resolves the earlier uncertainty about the final control's element type. The previous implementation searched only for buttons, so it could miss the actual anchor and wait indefinitely despite the archive being ready.

## Follow-up implementation

- Updated `_find_zip_download_button` to find the accessible `Download ZIP` link inside the active modal.
- Added the exact observed `.zip-ready-card a.zrc-cta` selector as a narrowly scoped fallback.
- Verify that the link is visible, has an `href`, is not marked `aria-disabled`, and is unique before clicking.
- Retained compatibility with a real button in case the website changes its markup again.
- Added isolated tests for accessible link discovery, CSS fallback, hidden links, missing URLs, disabled links, ambiguous links, and button compatibility.
- The existing download listener, single-click guard, queue handling, ZIP validation, and merge pipeline remain unchanged.

## Verification

The follow-up is on branch `fix/spotisaver-zip-download-link` and awaits CI. Automated tests use mocked Playwright controls. A live browser download still needs to be confirmed locally.
