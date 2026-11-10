# Request 007 implementation notes

## Implemented

- The provider now checks for the visible `#downloadAllBtn` control first and verifies the label `Download entire playlist`.
- If that control is already visible, it is clicked directly. The page is not scrolled unnecessarily.
- Only when the real action is unavailable does the provider click `button.btn-playlist-download` labelled `Download Playlist`, then wait up to 15 seconds for the actual button to become visible.
- If the album action remains unavailable, the provider logs up to 30 visible buttons and links with their identifying attributes before attempting individual track controls.
- The existing browser download event and non-empty file checks remain in place.

## Automated verification

GitHub Actions run 109 passed on 2026-11-10:

- Project installation: passed
- Python compilation: passed
- Published TKKGData contract smoke test: passed, 243 episodes and 40 verified tracks for episode 150
- Unit tests: passed, 43 tests

Run 108 exposed two test failures caused by over-escaped regular expressions. The patterns were corrected, and run 109 passed.

## Not yet verified

No live Spotisaver download was performed in CI. The next check is Oliver's local run of:

```powershell
py tkkg.py 150 --provider spotisaver
```

Confirm that the visible `Download entire playlist` button is clicked without first scrolling, that a non-empty archive is saved, all 40 tracks validate, and FFmpeg creates a playable merged MP3.

## Pull request

https://github.com/OliverZsuffa/TKKGDownloader/pull/9

The PR is open and has not been merged.
