# Implementation plan: Request 013

## Goal and operating model

Implement a one-time, reproducible diagnostic workflow for TKKG episode 150 using Spotisaver. The workflow must preserve every downloaded source file, compare the existing merger against a decoded PCM workflow, and produce enough evidence to identify whether the missing audio originates in a source track or at a merge boundary.

Run the actual download and media processing locally. GitHub Actions should run only automated tests and must not download the album or process the full episode.

## 1. Add an explicit persistent diagnostic workspace

- Add a narrowly scoped CLI option such as `--diagnostic-dir PATH`, available with `--provider spotisaver`.
- Keep the current temporary-directory behaviour unchanged when the option is omitted.
- When supplied, use the specified directory as a persistent workspace rather than wrapping the run in `TemporaryDirectory`.
- Keep the Spotisaver download directory, original ZIP, extracted raw files, validated numbered tracks, reports, PCM master, merge candidates, and boundary review in clearly named subdirectories.
- Do not delete or overwrite existing workspace contents. Fail with a clear message if the directory already contains files from another run, unless a deliberate resume mode is implemented and tested.
- Preserve the existing Spotisaver diagnostic log and include its path in the final summary.
- Keep the original ZIP even after successful extraction and validation.

Suggested workspace layout:

```text
episode-150-diagnostics/
  source/
    spotisaver-downloads/
      original-album.zip
    raw/
    tracks/
      01 - ...
      ...
      40 - ...
  reports/
    source-inspection.json
    source-inspection.txt
    merge-comparison.json
    boundary-analysis.json
  pcm/
    episode-150-master.wav
  candidates/
    episode-150-stream-copy.mp3
    episode-150-pcm-320k.mp3
  review/
    track-boundaries.wav
    boundary-index.txt
```

Adapt exact paths to the existing import implementation while preserving the separation between downloaded files and validated canonical tracks.

## 2. Inspect all source tracks before merging

Create a dedicated audio diagnostics module rather than adding analysis logic to the Spotisaver browser workflow.

For every validated track, run FFprobe and record at least:

- Canonical track number and title.
- File path and byte size.
- Container and audio codec.
- Duration from stream and format metadata where available.
- Bitrate, sample rate, channel count, and channel layout.
- Start time and stream time base where available.
- FFprobe exit status and parse errors.

Then run a complete FFmpeg decode of each source file to a null output with error reporting enabled. Capture standard error and exit status per track. A successful metadata probe is not a substitute for decoding the complete file.

Also calculate diagnostic indicators such as duration outliers, unusually small files, abrupt end-of-file behaviour, long digital silence, and large changes in level. Store measurements and flag suspicious cases for review. Do not automatically classify normal pauses, quiet dialogue, or intentional dramatic silence as corruption.

Use the same FFmpeg and FFprobe executables selected by the application. Include their version strings in the report so results are reproducible.

## 3. Generate independent merge candidates

Keep the existing `merge_tracks()` default behaviour unchanged. Add an optional diagnostics collector so the baseline run can report whether stream copy or the existing 192 kbit/s fallback was used, including each command and result.

### Candidate A: current stream-copy method

- Use the exact 40 validated tracks in canonical numeric order.
- Run the existing concat-demuxer stream-copy path.
- Write to the diagnostic candidates directory, never directly to the user's final episode path.
- Capture the exact command, FFmpeg version, exit status, standard error, output size, and duration.

### PCM master and Candidate B: decode, concatenate, encode once

- Decode all 40 MP3 tracks to a common PCM representation before concatenation.
- Use a consistent sample rate and channel count. Preserve the common native values when all tracks agree. If they differ, use the highest source sample rate and channel count so no source is downsampled or downmixed, and document the selected format.
- Use uncompressed PCM with sufficient precision for a transparent intermediate. Do not create a new lossy intermediate.
- Concatenate the decoded PCM segments in canonical order, with each segment beginning immediately after the preceding segment. Do not insert fades, crossfades, silence, or gaps.
- Save the lossless concatenated master as WAV.
- Encode the master once as MP3 at 320 kbit/s using a high quality encoder setting.
- Capture commands, elapsed time, exit status, output size, and duration.

Prefer an implementation that is robust on Windows and does not exceed command-line length limits. If separate per-track WAV files are used, ensure all have identical format parameters before concatenation. Estimate required temporary disk space before starting and stop with a clear message if available space is insufficient.

Do not assume Candidate B is automatically better. It is a comparison candidate whose quality and continuity must be verified.

## 4. Inspect the merged outputs

For both MP3 candidates and the PCM master:

- Run FFprobe and record duration, codec, bitrate, sample rate, channels, and file size.
- Fully decode each output to a null sink and capture all warnings and errors.
- Compare the merged duration with the sum of the decoded source durations.
- Explain expected differences caused by MP3 encoder delay and padding. Do not report a defect solely because MP3 duration differs by a few milliseconds.
- Check for unexpected gaps, overlaps, truncation, or large duration discrepancies.
- Confirm the output is readable from beginning to end.

A successful FFmpeg exit code, an existing file, or a plausible duration alone must never be considered sufficient validation.

## 5. Analyse all 39 track boundaries

Generate a boundary index with the cumulative start and end times of each source track.

For every transition:

- Extract a review excerpt that includes audio from the end of the preceding track and the beginning of the following track.
- Include enough context on both sides to hear whether dialogue, music, or effects are cut off. Use a configurable default of approximately 8 to 10 seconds on each side, shortened only when a source track is itself shorter.
- Label each excerpt with the two track numbers and the expected boundary timestamp in a companion text index.
- Assemble the excerpts in transition order into one review WAV or another lossless format.
- Analyse short-term silence, peak and RMS levels in the before and after excerpts. Treat these as flags for human review, not automatic repair instructions.

Also provide a way to inspect the full source tracks independently. Missing audio can occur inside a track, not only at a chapter boundary.

## 6. Extract cover artwork and write final metadata

### Artwork extraction

- Inspect embedded artwork in all 40 source MP3 files using FFprobe.
- Extract the attached picture from a source part, preferably the first track when it contains valid artwork.
- If the first track has no artwork, inspect the remaining parts and select a valid embedded cover from one of them.
- If multiple parts contain different artwork, record the differences and select the cover that is consistent with the episode or album. Do not download an unrelated replacement or generate new artwork.
- Preserve the extracted image unchanged in the workspace and record its source track, format, dimensions, file size, and checksum.
- If no part contains embedded artwork, report that clearly and do not silently substitute another image.

### Metadata

- Populate the final MP3's ID3 tags from verified episode and album metadata in TKKGData, supplemented by source tags only where appropriate.
- Include title, album, artist and album artist when available, and genre, date, and other fields only when supported by reliable source metadata.
- Set the track number to 1 of 1 for the merged episode file if the tag format supports it. Preserve the original part track numbers in the diagnostic report rather than confusing them with the single merged episode.
- Embed the selected cover as the ID3 attached picture.
- Apply tags to the final encoded MP3 candidate, not to the lossless PCM master.
- Read the tags and attached picture back from the completed MP3 and verify their values, image integrity, and presence.
- Record the metadata source for each populated field. Do not invent missing values or alter the source tracks.

Use a suitable maintained Python metadata library if one is not already present in the project. Keep metadata writing isolated and covered by tests.

## 7. Produce a clear diagnostic report

Create both JSON and readable text reports.

The report must include:

- Episode identity and canonical track count.
- Source filenames and canonical order.
- FFmpeg and FFprobe versions.
- Per-track metadata and full-decode results.
- Any suspicious duration, size, silence, level, or decode findings.
- Baseline stream-copy command and result.
- PCM conversion parameters and master duration.
- Re-encoded candidate command and result.
- Output integrity and duration comparisons.
- All 39 boundary timestamps and review excerpt locations.
- Artwork source track, extracted image details, checksum, and final embedded-artwork verification.
- Final ID3 metadata values, their sources, and read-back validation.
- A conclusion separating confirmed source problems, merge-specific problems, and inconclusive observations.

The console should show meaningful stages and elapsed time without printing excessive per-second output. Long processing stages should report periodic progress or heartbeats.

## 8. Safety and failure handling

- Never modify the downloaded ZIP or source MP3 files.
- Never overwrite an existing final episode MP3.
- Write all generated files to temporary names first and rename only after each output passes validation.
- If a track fails to decode, retain all files and report the exact track and FFmpeg error. Do not silently skip it.
- If the PCM conversion or merge fails, retain completed diagnostic artifacts and report the failing stage.
- Check available disk space before large PCM operations.
- Handle Ctrl+C without deleting the persistent diagnostic workspace.
- Do not automatically delete large intermediate files after success. Cleanup requires Oliver's later approval.

## 9. Tests

Add automated tests for:

- Persistent diagnostic directory creation and collision protection.
- Existing temporary-directory behaviour when no diagnostic directory is supplied.
- Correct canonical ordering of all 40 tracks.
- FFprobe JSON parsing, missing fields, malformed output, and nonzero exit codes.
- Full-decode success and failure handling.
- Duration and metadata outlier reporting.
- PCM format consistency and conversion command construction.
- PCM concatenation order and output validation.
- Stream-copy and re-encoded candidate generation.
- Duration comparison with a defined tolerance.
- Boundary timestamp calculation and excerpt indexing.
- Report generation with failed and suspicious tracks.
- Artwork extraction when present on the first track, another track, multiple tracks, or no track.
- Cover image integrity and metadata read-back validation.
- ID3 metadata writing from verified values, including missing optional fields.
- No source mutation and no overwrite of an existing final MP3.
- Ctrl+C preserving the diagnostic workspace.

Use short synthetic audio fixtures generated locally for unit tests. Tests must not contact Spotisaver or download real episode audio.

## 10. Local execution and acceptance

After implementation and approval:

1. Run the complete unit test suite and Python compilation.
2. Run CI and inspect the diff.
3. Execute the real episode 150 Spotisaver download locally with the persistent diagnostic directory.
4. Confirm all 40 tracks match TKKGData and all source files are retained.
5. Complete the full per-track decode and metadata inspection.
6. Generate both merge candidates, the PCM master, the reports, and all 39 boundary excerpts.
7. Extract and inspect cover artwork from the source parts, then embed and verify it in the selected final MP3.
8. Apply and verify episode metadata from TKKGData and reliable source tags.
9. Review every flagged boundary and compare the transition review audio for all 39 boundaries.
10. Report the findings and recommend the best candidate. Do not overwrite or replace the user's existing episode file without explicit approval.
11. Keep the diagnostic workspace intact until Oliver confirms that the chosen file is satisfactory.

## Implementation boundaries

Expected changes are limited to the CLI argument handling, Spotisaver download workspace handling, a new audio diagnostics module, artwork extraction and ID3 metadata handling, focused tests, and concise usage documentation. Do not change the default merge algorithm or TKKGData contract as part of this request.
