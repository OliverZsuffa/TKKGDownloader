# R15 implementation notes

## Changes

- Added exact filename matching after conservative removal of the known Spotisaver wrapper.
- Added exact embedded ID3 title fallback.
- Added embedded album plus track number fallback. Both values must match verified album identity and expected track number.
- Added support for explicit alternate_titles metadata with collision validation.
- Recorded matching evidence and matched title key in the import manifest.
- Kept fuzzy matching out of automatic assignment and retained one-to-one, duplicate hash, checksum, and manifest ordering checks.
- Diagnostic logger now writes and flushes an initialization record and verifies the persistent file exists before browser startup.
- Added synthetic tests for provider wrappers, arbitrary filenames with exact title tags, album plus track metadata, wrong album identity, and unresolved files.

## Verification

The GitHub pull request contains the implementation and synthetic regression tests. The real episode 150 archive remains on Oliver's computer and has not been processed by CI. A local Windows run against that archive is still required to verify the real Spotisaver filename mapping and the diagnostic log behaviour. Real audio decoding, merge candidate generation, and listening remain separate end to end checks.

## Limitations

- Exact embedded title matching assumes the title tag is meaningful. Conflicting embedded metadata is retained as a warning and does not override a successful filename match.
- Album plus track number matching requires exact album identity.
- Arbitrary filenames with no useful metadata remain unidentifiable and are rejected.
- Fuzzy similarity is not used to assign tracks.
