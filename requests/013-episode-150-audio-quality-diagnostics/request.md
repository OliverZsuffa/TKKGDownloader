# Request 013: Diagnose and produce a high-quality Spotisaver merge

## Status

Implementation complete on PR #20. Automated verification passed; local episode processing and human review remain pending.

## Objective

Investigate the missing audio noticed while listening to TKKG episode 150, downloaded through Spotisaver, and produce a carefully validated final MP3. This is a one-time quality-focused operation. Processing time and temporary disk usage are secondary to preserving all available audio and producing a reliable result.

## User experience

Run episode 150 through the existing Spotisaver workflow, but retain the downloaded ZIP and all 40 individually validated MP3 tracks in a persistent diagnostic directory. Generate a detailed report and multiple merge candidates. Do not replace the existing episode file until the candidates have been checked and a final version has been selected.

The process must be allowed to run locally for as long as necessary. It must not depend on the 15-minute GitHub Actions execution window.

## Functional requirements

- Extract the embedded cover artwork from the downloaded part files. Inspect the available parts rather than assuming every part contains artwork. If multiple parts contain artwork, compare them and use a consistent valid cover from the episode. Preserve the extracted original image as a separate file.
- Embed the selected cover artwork in the final MP3 as standard ID3 attached-picture metadata.
- Write complete, accurate MP3 metadata using the canonical episode and album information available from TKKGData. At minimum include title, album, artist or album artist when supplied by the dataset, track number where meaningful for the merged episode, and genre or date only when supported by source metadata. Do not invent missing values.
- Verify the final ID3 tags and embedded cover after encoding by reading them back from the finished MP3. Record the metadata and artwork validation in the report.
- Keep the original source tags and artwork evidence in the diagnostic report. Do not modify source files.

- Use the canonical episode 150 metadata and exact 40-track order from TKKGData.
- Use the existing visible Spotisaver browser workflow and its current archive and track validation. Do not weaken or bypass any website controls or existing validation.
- Preserve the original downloaded ZIP, the extracted raw MP3 files, and the canonically numbered validated MP3 files.
- Inspect every source track with FFprobe and a full FFmpeg decode. Record duration, file size, bitrate, sample rate, channel count, stream information, and any decoder warnings or errors.
- Detect suspiciously short, empty, truncated, or otherwise anomalous tracks. Treat silence detection and waveform anomalies as diagnostic signals only. Do not automatically remove silence or alter source audio.
- Produce a candidate using the current stream-copy merge.
- Produce a candidate by decoding the tracks to a common PCM format, concatenating the decoded audio in canonical order, and encoding the complete result once as a 320 kbit/s MP3.
- Preserve a lossless PCM master of the concatenated audio for comparison. Use a consistent sample rate and channel layout derived from the source material. Document any required conversion.
- Compare candidate durations against the sum of decoded source durations, accounting for MP3 encoder delay and padding where applicable.
- Verify every candidate by decoding it fully again and checking for FFmpeg errors, unexpected duration differences, and file integrity.
- Generate a boundary review containing a short excerpt around each of the 39 track transitions, with clear track numbers and timestamps. Also generate a report that helps identify suspicious silence or discontinuities inside individual tracks.
- Never treat a successful FFmpeg exit code or a non-empty output file as sufficient proof of audio integrity.
- Keep all intermediate and diagnostic files until Oliver has confirmed that the final recording is satisfactory.
- Do not overwrite an existing final MP3 automatically.

## Constraints

- This operation is specifically for episode 150 and its 40 Spotisaver tracks.
- Run the long processing locally, not as a single GitHub Actions job subject to the 15-minute limit.
- Use FFmpeg and FFprobe for media inspection and processing.
- Do not fetch audio from a different provider during this diagnostic run.
- Do not alter, time-stretch, denoise, normalize, fade, or remove silence from the source audio.
- Do not infer that a long silent section is an error without listening and checking the original track.
- Keep the original downloaded files unchanged.
- Keep the existing normal downloader behaviour unchanged unless a narrowly scoped reusable diagnostic option is required.

## Out of scope

- Reworking the Spotisaver browser automation.
- Changing TKKGData metadata or track mappings.
- Automatically repairing damaged source recordings.
- Changing the default merge behaviour for all episodes before the episode 150 comparison establishes a clear benefit.
- Uploading large audio files or intermediate PCM files to GitHub.

## Acceptance criteria

- [ ] All 40 expected tracks are downloaded and validated against the canonical episode 150 tracklist.
- [ ] The original ZIP and all source MP3 files are retained in the diagnostic directory.
- [ ] A machine-readable and human-readable source inspection report is produced.
- [ ] Every source track completes a full decode check, with errors and warnings recorded.
- [ ] The current stream-copy candidate is generated.
- [ ] The decoded PCM concatenation master is generated in canonical order.
- [ ] A 320 kbit/s MP3 candidate is encoded from the PCM master.
- [ ] All candidates pass a full decode and integrity check.
- [ ] Duration and boundary diagnostics are produced for all 39 transitions.
- [ ] A boundary review file is generated so all transitions can be checked without searching the full episode.
- [ ] The report clearly distinguishes source defects from merge-related differences.
- [ ] No source file is modified and no existing final output is overwritten.
- [ ] The final recommendation is based on measured results and transition review, not just FFmpeg exit codes.
- [ ] All intermediate files remain available until Oliver approves cleanup.

