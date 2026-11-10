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

Keep the existing `merge_tracks()` implementation unchanged for the baseline candidate.

### Candidate A: current stream-copy method

- Use the exact 40 validated tracks in canonical numeric order.
- Run the existing concat-demuxer stream-copy path.
- Write to the diagnostic candidates directory, never directly to the user's final episode path.
- Capture the exact command, FFmpeg version, exit status, standard error, output size, and duration.

### PCM master and Candidate B: decode, concatenate, encode once

- Decode all 40 MP3 tracks to a common PCM representation before concatenation.
- Use a consistent sample rate and channel layout. Prefer the source's common native format when all tracks agree. If they differ, choose a documented common format that does not unnecessarily reduce the source material.
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
- Analyse short-term silence, peak and RMS levels, and abrupt waveform changes around the boundary. Treat these as flags for human review, not automatic repair instructions.

Also provide a way to inspect the full source tracks independently. Missing audio can occur inside a track, not only at a chapter boundary.

## 6. Produce a clear diagnostic report

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
- A conclusion separating confirmed source problems, merge-specific problems, and inconclusive observations.

The console should show meaningful stages and elapsed time without printing excessive per-second output. Long processing stages should report periodic progress or heartbeats.

## 7. Safety and failure handling

- Never modify the downloaded ZIP or source MP3 files.
- Never overwrite an existing final episode MP3.
- Write all generated files to temporary names first and rename only after each output passes validation.
- If a track fails to decode, retain all files and report the exact track and FFmpeg error. Do not silently skip it.
- If the PCM conversion or merge fails, retain completed diagnostic artifacts and report the failing stage.
- Check available disk space before large PCM operations.
- Handle Ctrl+C without deleting the persistent diagnostic workspace.
- Do not automatically delete large intermediate files after success. Cleanup requires Oliver's later approval.

## 8. Tests

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
- No source mutation and no overwrite of an existing final MP3.
- Ctrl+C preserving the diagnostic workspace.

Use short synthetic audio fixtures generated locally for unit tests. Tests must not contact Spotisaver or download real episode audio.

## 9. Local execution and acceptance

After implementation and approval:

1. Run the complete unit test suite and Python compilation.
2. Run CI and inspect the diff.
3. Execute the real episode 150 Spotisaver download locally with the persistent diagnostic directory.
4. Confirm all 40 tracks match TKKGData and all source files are retained.
5. Complete the full per-track decode and metadata inspection.
6. Generate both merge candidates, the PCM master, the reports, and all 39 boundary excerpts.
7. Review every flagged boundary and compare the transition review audio for all 39 boundaries.
8. Report the findings and recommend the best candidate. Do not overwrite or replace the user's existing episode file without explicit approval.
9. Keep the diagnostic workspace intact until Oliver confirms that the chosen file is satisfactory.

## Implementation boundaries

Expected changes are limited to the CLI argument handling, Spotisaver download workspace handling, a new audio diagnostics module, focused tests, and concise usage documentation. Do not change the default merge algorithm or TKKGData contract as part of this request.
