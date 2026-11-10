# Request 014: Track ordering and source integrity verification

## Status

Proposed. Implementation requires Oliver's approval.

## Objective

Make Spotisaver imports fail safely whenever the downloader cannot establish an unambiguous mapping between every downloaded MP3 and the canonical TKKGData tracklist. Record the mapping and its evidence so that an episode can be audited and reproduced.

This request closes the gap between R13's audio and merge diagnostics and the earlier import stage. It does not duplicate R13's full decode, PCM master, merge comparison, metadata, artwork, or boundary review workflow.

## Scope

### 1. Deterministic track identification

- Replace substring-based filename matching with conservative deterministic matching.
- Normalise Unicode, accents, case, punctuation, whitespace, and common filename extensions consistently.
- Match a downloaded filename to a canonical Spotify title only when the complete normalised title is an exact match under the documented filename rules.
- Do not use fuzzy matching, partial title matching, or first-match-wins behaviour.
- Reject ambiguous matches, duplicate assignments, missing tracks, unexpected MP3 files, empty files, and canonical track number gaps or duplicates.
- If provider filenames contain a predictable wrapper such as a track number or a known suffix, support it only through an explicit, tested parsing rule that cannot make one title a substring match for another.
- Do not silently guess. If a filename cannot be mapped deterministically, stop before merging and preserve the source files and a clear diagnostic.
- Do not invent aliases. If the existing TKKGData schema can represent verified alternate source titles, use that existing field. Otherwise, report the unmatched filename and defer alias support rather than adding an unreviewed metadata convention.

### 2. Complete track manifest

Construct a machine-readable manifest for every successful Spotisaver import. Each entry must record:

- Canonical episode identity and track count.
- Expected track number and canonical Spotify title.
- Original downloaded filename and relative source path.
- Canonically numbered imported filename and relative path.
- Matching rule used.
- Source file size and SHA-256 checksum.
- Embedded title, artist, album, track number, and disc number when available.
- Embedded metadata probe status and any parsing warnings.

The manifest must preserve the exact mapping used by the merger. In R13 diagnostic mode, write it to the persistent diagnostic workspace and include it in the diagnostic reports. In normal mode, keep it in memory for validation and concise logging without creating unsolicited sidecar files beside the user's music.

### 3. Ordering and source integrity checks

- Validate that TKKGData supplies a unique, contiguous, one-based sequence of track numbers before import.
- Verify that each expected track is assigned exactly one source file and every downloaded MP3 is consumed exactly once.
- Verify the canonical numbered output list against the manifest immediately before merging.
- Check that copied canonical files have the same SHA-256 checksum as their original extracted source files.
- Flag repeated source checksums and suspiciously identical audio under different filenames. Exact file checksum duplicates are a hard failure unless the canonical dataset explicitly documents a legitimate duplicate.
- Read embedded track metadata where available. Record disagreements with the canonical track number or title as warnings, not automatic reassignment, because provider tags may themselves be incorrect.
- Do not claim that filename, ID3 tags, or checksums independently prove semantic audio content or that the TKKGData order is correct. They establish traceability and consistency, not editorial truth.
- Do not automatically reorder tracks based on ID3 tags, audio fingerprints, durations, or heuristics.

### 4. R13 integration

- Extend R13's persistent diagnostic report with the manifest, matching decisions, checksums, and integrity findings.
- Keep R13's existing audio diagnostics and candidate generation unchanged except where they need the manifest as their canonical input.
- Ensure the baseline and PCM candidate both use the same manifest-defined order.
- Include a clear pre-merge result: verified, warnings, or rejected.
- A rejected import must not reach the merger or produce a final episode file.

## Non-goals

- Rebuilding or replacing the R13 audio diagnostics.
- Automatically detecting every semantic audio ordering error.
- Reordering audio based on similarity or duration heuristics.
- Changing TKKGData's canonical track order without separate evidence and approval.
- Changing the YouTube Music provider unless shared validation code makes a narrowly scoped change necessary.
- Downloading real episodes in CI.
- Automatically repairing, trimming, normalising, or otherwise altering source audio.

## Acceptance criteria

- [ ] Substring collisions such as Teil 1 versus Teil 10 cannot produce a match.
- [ ] Exact normalised title matches succeed across documented harmless punctuation, case, and Unicode differences.
- [ ] Ambiguous, missing, duplicate, unexpected, and empty source files are rejected before merging.
- [ ] Canonical track numbers must be unique and contiguous from one.
- [ ] Every successful import produces a complete in-memory manifest.
- [ ] R13 diagnostic mode persists the manifest as JSON and includes it in the human-readable and machine-readable reports.
- [ ] The manifest records original and canonical paths, expected metadata, embedded metadata when available, matching rule, file size, and SHA-256.
- [ ] The copied canonical files are checksum-verified against the extracted originals.
- [ ] Repeated checksums and embedded metadata disagreements are reported with the defined severity.
- [ ] The merger consumes the exact manifest order and verifies that its input files still match the manifest.
- [ ] A rejected import cannot create or overwrite a merged episode.
- [ ] Automated tests cover matching collisions, normalisation, ambiguity, missing and extra files, duplicate checksums, metadata disagreements, canonical numbering, manifest generation, tampering between import and merge, and failure before merge.
- [ ] Existing R13 tests continue to pass.
- [ ] Existing normal YouTube Music behaviour remains unchanged.
- [ ] No real downloads or external website access are required by automated tests.
