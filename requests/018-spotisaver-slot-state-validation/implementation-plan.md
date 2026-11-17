# Implementation plan: Request 018

## Scope

Correct the queue state interpretation in `src/tkkgdownloader/spotisaver.py`. The false positive is in `_download_click`: when `queue_started` is set and the busy notice disappears, the current code immediately reports slot acquisition. That transition is not evidence that Spotisaver accepted the request.

## Proposed changes

1. Introduce a small, explicit classification helper for the visible modal snapshot. It should distinguish:
   - `rejected`: the visible status or mini-log explicitly says all download slots are busy.
   - `accepted`: the visible status or mini-log explicitly indicates active downloading, reports track progress, or says ZIP creation has started or completed.
   - `unconfirmed`: neither condition is met.
   - `failed`: the existing explicit failure detector reports a failure.
2. In `_download_click`, keep the existing queue retry timer active only while the explicit busy rejection remains visible. If the notice disappears, clear the retry timer but remain in the unconfirmed state. Do not print a success message, reset the browser request, or click again.
3. Report "Download slot acquired." only on the first transition to accepted. Guard the transition so the message is emitted once, even if progress and ZIP status are both visible on successive polls.
4. Continue monitoring in the unconfirmed state. Preserve page-close handling, explicit failure handling, browser download event handling, heartbeat logging, cancellation, and the existing retry safeguards.
5. Ensure a browser download event is treated as completion of a browser transfer, not as proof that the earlier queue request was accepted. File validation and archive validation remain separate downstream checks.
6. Add focused tests for the state classifier and the queue state machine using fake pages and deterministic modal snapshots. Cover a cleared queue notice with no active status, explicit active status, non-zero progress, ZIP creation, a persistent queue rejection, a cleared queue notice followed by a later acceptance, and explicit failure.
7. Update the request notes, README if needed, request index, and Knowledge Base technical decisions with the corrected state semantics.

## Verification

- Run the complete unittest suite.
- Run Python compilation.
- Run the repository CI workflow.
- Do not perform a real Spotisaver download in CI.
- Leave the live website test to Oliver after the PR is ready.

## Out of scope

- Changing the retry interval or retry policy.
- Changing download button selection.
- Changing the website interaction method.
- Changing ZIP extraction, audio validation, or FFmpeg merging.
