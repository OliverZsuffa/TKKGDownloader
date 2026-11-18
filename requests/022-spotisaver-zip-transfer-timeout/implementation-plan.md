# Implementation plan: Request 022

## Root cause

In `src/tkkgdownloader/spotisaver.py`, the CDP-owned ZIP persistence branch creates one deadline at `time.monotonic() + 30` and uses it while waiting for `Browser.downloadProgress` to report `completed`. This is a total-duration timeout, not an inactivity timeout. The supplied episode 142 log shows a 141.9 MB transfer had reached 49.7 MB (35%) after approximately 30 seconds, but the code raised the timeout and then closed Chromium. The same deadline is also reused for post-completion file stability checks, which can leave no time for that separate operation.

## Proposed changes

1. In `_download_click`, maintain transfer state for the matching CDP GUID:
   - last received byte count
   - last byte progress timestamp
   - latest known total byte count
   - latest CDP state
2. In the matching `Browser.downloadProgress` callback:
   - update the byte count and total
   - reset the progress timestamp only when received bytes increase
   - continue forwarding progress to the existing console reporter
   - record completion and cancellation distinctly
3. Replace the fixed 30-second completion deadline with a 120-second inactivity timeout. Continue pumping Playwright events while waiting. A transfer can take as long as necessary if bytes keep arriving.
4. If Chromium reports cancellation, fail immediately. If no bytes arrive for 120 seconds, fail with received bytes, total bytes if known, and inactivity duration in the diagnostic message.
5. Emit periodic diagnostic heartbeat entries during long transfers, including current byte counts and inactivity duration.
6. Once CDP reports completion, start a separate 30-second deadline for file existence, non-zero size, and stable-size checks.
7. Keep the existing Playwright `download.save_as()` fallback unchanged when CDP setup is unavailable.
8. Add deterministic unit tests using mocked CDP events and monotonic time. Cover a transfer longer than 30 seconds with continued progress, intermittent progress, inactivity timeout, explicit cancellation, and independent post-completion file verification.
9. Update README and the relevant Knowledge Base entry.

## Verification

- Run focused Spotisaver tests first.
- Run Python compilation.
- Run the complete unit test suite.
- Run the TKKGData contract smoke test.
- Run FFmpeg integration tests.
- Inspect Git diff and CI before requesting merge approval.

## Scope guard

Do not change queue retry policy, ZIP button selection, track processing, or audio merging. Do not perform a live Spotisaver download as part of automated tests.
