# Request 018: Validate Spotisaver download slot acquisition

## Problem

The Spotisaver downloader can report "Download slot acquired" when the site's queue rejection notice disappears, even though the site has not confirmed that processing has started. The current implementation treats the disappearance of a rejection message as proof of acceptance. This creates a false success status.

## Expected behaviour

- An explicit "all download slots are busy" notice means the request is rejected or queued.
- The disappearance of that notice alone means the state is unconfirmed, not accepted.
- The downloader reports "Download slot acquired" only after observing positive evidence that Spotisaver has begun processing the request.
- Positive evidence must come from the visible modal, such as an explicit active download status, actual track progress, or ZIP creation starting or completing.
- While the state is unconfirmed, the downloader keeps monitoring the visible modal and does not claim success or submit another request.
- Existing queue retry behaviour remains limited to an explicit queue rejection that stays active for the configured wait period.
- If the browser download event arrives, the existing archive and track validation remains mandatory.

## Constraints

- Use only the visible Spotisaver interface and normal Playwright interactions.
- Do not use private endpoints, hidden APIs, stealth settings, or access-control workarounds.
- Preserve the current 30-second queue retry policy and its modal close and re-submit safeguards.
- Preserve the browser download event handling and all ZIP and track validation.
- Keep the default yt-dlp provider unchanged.
- Tests must use mocked modal snapshots and must not require network access or real waiting periods.

## Acceptance criteria

1. Clearing a queue rejection notice without any positive processing evidence never prints "Download slot acquired".
2. An explicit active download status or non-zero track progress reports acquisition exactly once.
3. "Creating ZIP archive" or "ZIP archive created" reports acquisition exactly once.
4. A queue rejection that remains active follows the existing retry policy.
5. A queue notice that clears into an unconfirmed state does not trigger a retry.
6. A browser download event without a prior visible positive state does not retroactively make the earlier slot-acquired message valid.
7. Unit tests cover transitions between rejected, unconfirmed, accepted, failed, and browser-download states.
