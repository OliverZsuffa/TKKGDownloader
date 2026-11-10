# R17 implementation notes

Implementation is complete on branch `r17-download-polish-metadata` and is available in [pull request #24](https://github.com/OliverZsuffa/TKKGDownloader/pull/24).

## Changes

- Added a shared metadata module for deterministic source cover extraction, ID3 writing, and readback verification.
- Updated diagnostic metadata handling to reuse the shared implementation.
- Updated normal Spotisaver downloads to merge into a temporary candidate, apply metadata and artwork, probe and fully decode the candidate, and only then atomically publish it.
- Added seconds-only ETA parsing.
- Replaced repeated queue busy messages with a cumulative queue waiting line.
- Added regression coverage for ETA formatting, queue output, and production metadata finalization.

## Verification

- Python compilation passed.\n- TKKGData contract smoke test passed.\n- All 112 unit and integration tests passed, including FFmpeg integration tests.\n- GitHub Actions run 42905743453 completed successfully.\n- An initial test run exposed five test failures. The implementation and tests were corrected, and the latest run passed.\n\n## Remaining verification\n\nA fresh real Spotisaver download is still required to confirm the source artwork and final output in the live workflow. The PR has not been merged.
