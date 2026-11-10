# Request 014 implementation notes

## Status

Implemented and merged through PR #21 as commit 6e4632a492e403c047fd191976ac00f08d7394a0. GitHub Actions run 42873998047 passed all checks.

## Implemented

- Replaced substring filename matching with exact normalized full-title matching.
- Normalisation handles Unicode compatibility forms, diacritics, case, and punctuation while preserving non-Latin letters.
- Added one narrowly defined filename wrapper: a leading numeric track prefix is stripped only when its number equals the expected canonical track number.
- Added validation for non-empty titles, positive unique track numbers, contiguous one-based numbering, and normalized title collisions.
- The importer builds the complete mapping before creating canonical copies.
- Added SHA-256 checksums for original and copied files and rejects byte-identical source files assigned to different tracks.
- Added embedded ID3 title, artist, album, track number, and disc number observations. Missing or conflicting tags are recorded as warnings and never override TKKGData.
- Added a versioned track manifest with relative source and canonical paths, matching rule, file size, checksums, and embedded metadata.
- Added a pre-merge manifest check that verifies the exact ordered paths and rechecks each canonical file checksum.
- Applied manifest validation to normal Spotisaver merges and the R13 stream-copy candidate.
- R13 diagnostic mode writes reports/track-manifest.json and incorporates mapping evidence into source-inspection.json and source-inspection.txt.
- Added focused synthetic tests for track-number substring collisions, Unicode normalization, numeric prefixes, canonical title collisions, numbering gaps, duplicate audio, manifest traceability, metadata warnings, file tampering, and incorrect merge order.
- Updated README documentation.

## Scope limitations

- Checksums establish byte identity and traceability, not semantic correctness of the audio or editorial correctness of TKKGData's ordering.
- ID3 tags are corroborating metadata only. Conflicts are warnings and never trigger automatic reordering.
- No fuzzy matching, audio fingerprint based reordering, or automatic repair is performed.
- No live Spotisaver downloads or real episode files are used by tests.

## Verification

GitHub Actions run 42873998047 passed:

- Python module and test compilation.
- Published TKKGData contract smoke test.
- Full unit test suite: 98 tests passed in 1.775 seconds.
- Synthetic test fixtures only. No real Spotisaver downloads or episode files were used.

The implementation was also checked with an earlier successful run, but run 42873998047 includes the final code changes, including a second manifest verification immediately before R13 PCM candidate generation.
