# Request 014 implementation notes

## Status

Implementation committed on branch request-014-track-order-integrity. Automated verification is pending.

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

Pending GitHub Actions results. Do not treat the implementation as complete until the full existing suite and CI checks pass.
