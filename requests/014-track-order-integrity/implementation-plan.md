# Implementation plan: Request 014

## Goal

Harden the Spotisaver import boundary and make the exact source-to-track mapping auditable. R13 already validates source decoding, merge candidates, metadata, artwork, durations, and boundaries. R14 should focus narrowly on identity, ordering, and traceability.

## Current implementation findings

The current audio_import.py normalises Unicode and punctuation, but then checks whether the complete expected title is contained anywhere in the normalised filename. This is substring matching, not exact matching. It can create false matches when one title is contained in another.

The importer currently checks the number of MP3 files, unique matches, non-empty files, and unexpected files. It copies each matched source to a numbered filename. It does not retain a formal source-to-track manifest, compute source checksums, inspect embedded track tags, or verify that the copied numbered files remain byte-identical to their sources.

The merger sorts files by the numeric filename prefix. It does not receive or validate the import mapping that produced those names.

R13's diagnostic workflow already preserves source archives and files, performs full decoding, creates a PCM master and MP3 candidate, and produces boundary and metadata reports. R14 must reuse that infrastructure rather than duplicate it.

## 1. Inspect existing data and call paths

Before implementation:

- Trace the Spotisaver provider from downloaded archive through import_audio_files(), R13 diagnostics, and merge_tracks().
- Inspect the TKKGData track schema and real representative title strings already present in repository fixtures or checked-in test data.
- Identify the actual filename forms emitted by the current Spotisaver workflow from existing fixtures and documented logs. Do not make a real website request in tests.
- Confirm whether TKKGData already exposes a verified alternate-title field. Do not invent a new schema field as part of this request.
- Identify existing FFprobe helpers and reuse them for embedded metadata inspection where practical.

## 2. Implement conservative deterministic matching

Refactor filename normalisation into a documented helper with unit tests.

Matching rules:

- Normalise Unicode compatibility forms, diacritics, case, punctuation, and whitespace consistently.
- Compare the complete normalised title against the complete normalised filename stem after removing only explicitly supported structural wrappers.
- Structural wrapper parsing must be conservative, deterministic, and independently tested. It must not be implemented as substring containment.
- If more than one expected track resolves to the same normalised key, reject the canonical tracklist as ambiguous.
- If a source filename maps to zero or multiple expected tracks, reject the import and include the filename and candidate track information in the error.
- If multiple source files map to one expected track, reject.
- Do not use fuzzy string similarity or automatically choose the closest title.
- Do not add unverified aliases. If the dataset has an existing verified alternate-title field, support it with the same exact normalisation and collision checks.

The importer should build a complete mapping first. Only after the entire mapping passes validation should it create numbered copies. This avoids partially creating a misleading canonical track directory.

## 3. Validate canonical numbering and one-to-one coverage

Before matching:

- Require at least one expected track.
- Require integer, positive, unique track numbers.
- Require a contiguous one-based sequence from 1 through N.
- Require non-empty canonical titles.
- Reject duplicate normalised canonical titles unless an explicit verified alternate-title arrangement makes the mapping unambiguous.

After matching:

- Require exactly N source MP3s.
- Require every expected track to have exactly one source.
- Require every source MP3 to be used exactly once.
- Reject empty source files and unexpected files.
- Keep the existing safe ZIP extraction protections unchanged.

## 4. Generate the track manifest

Create a small dedicated manifest module or a focused set of helpers in the import layer, following existing project conventions.

Each manifest entry should include:

- Episode ID and canonical episode title where available.
- Expected track number and Spotify title.
- Original source filename and path relative to the import workspace.
- Canonical numbered filename and path relative to the workspace.
- Matching rule identifier.
- Source byte size and SHA-256.
- Embedded title, artist, album, track number, and disc number when available.
- Metadata probe status and warnings.

Use stable JSON output with UTF-8, deterministic key ordering, and a schema version. Do not include absolute machine-specific paths in the portable manifest. The diagnostic report may separately record the workspace location.

Use the existing FFprobe executable selection and JSON output if embedded tag inspection is already available. If probing tags fails, preserve the import mapping but record the probe failure as a warning, unless the file itself fails the existing required audio validation.

## 5. Verify copied files and merger inputs

After copying each source to its canonical numbered destination:

- Compute the destination SHA-256 and compare it with the source checksum.
- Reject any mismatch.
- Store the canonical file checksum in the manifest.

Immediately before merging:

- Validate that the supplied track list corresponds exactly to the manifest's canonical sequence.
- Verify unique, contiguous track numbers again.
- Verify each merger input exists and its checksum still matches the manifest.
- Pass the manifest-defined ordered paths to the merger rather than independently sorting an arbitrary list.
- Keep a compatibility path for existing non-Spotisaver callers if required, but do not weaken Spotisaver manifest validation.

The merge function should fail before invoking FFmpeg if the manifest and actual files disagree.

## 6. Integrity findings and severity

Use clear, stable statuses:

- Verified: all mandatory identity, coverage, numbering, and checksum checks pass.
- Warnings: non-fatal embedded metadata is missing or disagrees with the canonical title or track number; record the exact values. Duplicate checksums should be treated as a rejection by default, with an exception only if the canonical dataset explicitly documents the duplicate.
- Rejected: missing, extra, ambiguous, duplicate-mapped, empty, non-contiguous, modified, or otherwise unverifiable input.

Do not describe checksum equality as proof that the audio content is semantically correct. It proves byte identity between the downloaded source and the copied canonical file. Likewise, embedded metadata is corroborating evidence, not an authority for track order.

## 7. Integrate with R13 diagnostics

- Write reports/track-manifest.json in the persistent R13 diagnostic workspace.
- Add a readable manifest summary and integrity status to the existing source inspection reports.
- Include all matching decisions, source and canonical checksums, embedded tag observations, and warnings.
- Ensure R13's stream-copy and PCM workflows consume the exact same manifest order.
- Keep R13's existing source decode, PCM, metadata, artwork, and boundary behaviour unchanged.
- If import validation is rejected, write the failure evidence where possible and do not start merging.

For normal Spotisaver runs without R13 diagnostic mode, create and validate the manifest in memory only. Do not create extra sidecar files in the user's music folder.

## 8. Tests

Add focused synthetic tests for:

- Exact match after harmless case, punctuation, accent, and Unicode normalisation.
- Teil 1 and Teil 10 collision prevention.
- Prefixes and suffixes that are explicitly supported by structural parsing.
- Unsupported wrappers and ambiguous titles rejected.
- Two canonical titles with the same normalised key rejected.
- Duplicate source files and duplicate assignments rejected.
- Missing and unexpected MP3 files rejected.
- Empty MP3 files rejected.
- Non-positive, duplicate, missing, and non-contiguous canonical track numbers rejected.
- Stable manifest schema and deterministic JSON output.
- Source and destination checksum equality.
- Modified canonical copy rejected before merge.
- Repeated source checksum reported or rejected according to the defined rule.
- Missing and disagreeing embedded metadata recorded as warnings.
- Manifest ordering passed unchanged to the merger.
- No FFmpeg invocation after any rejected validation.
- R13 diagnostic workspace receives the manifest and report additions.
- Normal imports do not create sidecar files.
- Existing R13 and YouTube Music tests remain green.

Use synthetic filenames, small generated audio fixtures, and mocked FFprobe output. Tests must not contact Spotisaver or download real recordings.

## 9. Documentation and completion

- Update README Spotisaver validation documentation to describe exact matching, fail-closed behaviour, and manifest availability in diagnostic mode.
- Update the R13 diagnostic usage documentation to list the new manifest report.
- Record the implementation, test results, and any known limitations in the R14 notes file.
- Run the full unit test suite and existing CI checks.
- Do not process or overwrite episodes 149 or 150 as part of automated implementation tests.
- Do not change TKKGData ordering or metadata in this request.
