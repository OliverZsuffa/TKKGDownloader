# Request 015: Robust Spotisaver track identity

## Goal

Identify downloaded tracks reliably when providers use different filename conventions or arbitrary filenames, without weakening one-to-one identity validation.

## Behaviour

1. Exact normalized filename matching.
2. Exact matching after removing known provider wrappers.
3. Exact embedded ID3 title matching.
4. Embedded album identity plus track number matching, only when the album exactly matches verified TKKGData metadata.
5. Explicit alternate titles when supplied by trusted track metadata.
6. No fuzzy automatic assignment. Unresolved or ambiguous files are rejected with useful diagnostics.

The manifest records the matching rule and evidence. Existing source count, safe extraction, duplicate audio, checksum, and merge ordering protections remain mandatory.

## Logging

Create and flush a persistent diagnostic log before launching the browser. Verify that the log exists and report the real filesystem error if creation fails.

## Acceptance criteria

- Spotisaver wrapper filenames map exactly.
- Track 1 and track 10 remain distinct.
- Arbitrary filenames can be identified from exact title tags or verified album plus track number.
- Wrong album tags and unsupported arbitrary filenames are rejected.
- Track number alone never identifies a file.
- Matching evidence appears in the manifest.
- Existing integrity tests and full suite pass.
- Real episode downloads are not run in CI.
