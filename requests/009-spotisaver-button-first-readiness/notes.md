# Request 009 implementation notes

## Implemented

- Replaced the album title and full tracklist page-text gate with direct polling for `#downloadAllBtn`.
- Polling begins immediately after the page body becomes visible and repeats every second for up to 120 seconds.
- The button is accepted only when visible, enabled, and labelled `Download entire playlist`.
- The workflow clicks the real button immediately without scrolling.
- Progress is logged every 10 seconds while waiting.
- On timeout, the provider logs selector details, page title, a bounded body text preview, and visible buttons and links.
- Only after the main polling timeout may the intermediate `Download Playlist` scroll control be clicked. The provider then polls for the actual button for up to 15 additional seconds.
- The individual-track fallback remains available if no album button appears.
- Removed the obsolete album and all-track page-text readiness gate.
- Kept the canonical TKKGData album ID as the URL identity anchor.
- Kept strict downstream ZIP and MP3 validation unchanged.
- Changed the embedded JavaScript diagnostics to a raw Python string to avoid invalid escape warnings.

## Automated verification

Pending.

## Manual verification

A real Spotisaver download has not yet been run after this change. Oliver should run:

```powershell
py tkkg.py 150 --provider spotisaver
```

Confirm that the button is detected and clicked, the browser download event fires, all 40 archive tracks validate, and the merged MP3 plays correctly.
