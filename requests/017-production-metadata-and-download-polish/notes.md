# R17 implementation notes

Implementation is in progress on branch `r17-download-polish-metadata`.

## Changes

- Added a shared metadata module for deterministic source cover extraction, ID3 writing, and readback verification.
- Updated diagnostic metadata handling to reuse the shared implementation.
- Updated normal Spotisaver downloads to merge into a temporary candidate, apply metadata and artwork, probe and fully decode the candidate, and only then atomically publish it.
- Added seconds-only ETA parsing.
- Replaced repeated queue busy messages with a cumulative queue waiting line.
- Added regression coverage for ETA formatting, queue output, and production metadata finalization.

## Verification

Pending automated test suite and CI results.
