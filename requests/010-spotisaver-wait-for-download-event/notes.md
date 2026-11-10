# Request 010 implementation notes

## Implemented

- Registered the Playwright download event listener before clicking the selected website control.
- Clicked the control exactly once and replaced the fixed 120-second browser event timeout with an indefinite wait while the page remains open.
- Added periodic inspection of the rendered modal status, mini log, failure badge, progress indicator, and visible modal controls.
- Recognised the supplied queue busy message and parsed retry delays expressed in seconds or minutes.
- Reported queue state, retry delay, modal changes, progress, and a 15-second heartbeat.
- Kept queue notices separate from final failures.
- Did not assume automatic retry and did not issue a second click.
- Added clean Ctrl+C propagation and a clear error if the page closes before the event.
- Applied the same wait function to album and individual track download controls.
- Preserved filename handling, save validation, ZIP safety, exact track matching, and merge gating.

## Verification

- Added unit tests for listener registration order, exactly one click, queue delay parsing, queue notice handling, delayed event delivery, explicit failure, page closure, and Ctrl+C.
- CI uses mocked page events and modal snapshots. It does not perform a live Spotisaver download.
- Live queue behaviour and a full seven-minute download remain to be verified by Oliver locally.
