# R17: Production metadata and download output polish

## Goal

Make normal Spotisaver downloads produce the same validated, artwork-bearing MP3 output as the successful diagnostic workflow, while fixing ETA display and making queue waiting and console progress concise.

## 1. Shared production metadata pipeline

- Extract reusable artwork extraction, metadata selection, metadata writing, and readback verification from `audio_diagnostics.py` into a production module, without changing the established diagnostic output format unnecessarily.
- Use the verified canonical track order when inspecting source metadata and artwork.
- Preserve the original image bytes and MIME type. Select the first valid embedded cover image in canonical track order, using the existing diagnostic selection rules.
- Set episode title, album title, track number, total track count, and only source-supported artist, album artist, genre, date, and other tags. Do not invent optional source metadata.
- Embed the selected cover in the final MP3 and verify the exact image bytes and all written metadata by reading the final file back.
- Missing artwork is a clearly reported metadata outcome, not a fabricated substitute. A metadata write or verification failure is a failed download.
- Keep the diagnostic workflow using the same shared implementation so diagnostic and production behaviour cannot drift.

## 2. Safe finalization

- Merge to a temporary candidate in the destination filesystem.
- Apply metadata and artwork to that candidate.
- Verify metadata and artwork, probe the output, and perform a complete FFmpeg decode.
- Publish the candidate to the final destination only after all validation succeeds.
- Preserve an existing final file if any stage of a replacement fails.
- Clean up temporary candidates on success, failure, and cancellation.

## 3. ETA handling

- Parse Spotisaver's visible ETA for seconds-only, minutes-and-seconds, and supported DOM variants.
- Format values consistently: `42s`, `1m 01s`, `12m 30s`.
- Hidden, malformed, stale, or out-of-range values must not be displayed.
- Do not estimate or extrapolate an ETA when the website does not provide one.
- Keep website ETA informational only. It must not affect queue retries, completion detection, or timeouts.

## 4. Queue waiting

- Preserve the existing queue retry state machine, retry interval, and cancellation behaviour.
- Replace repeated queue messages with one in-place status line, for example `Waiting for download slot... 2m 30s elapsed`.
- The elapsed waiting timer is cumulative across retries and never resets when another retry begins.
- Do not show a download progress bar or download ETA while waiting for a queue slot.
- Do not impose a new artificial timeout.
- On acceptance, finish the waiting line and print `Download slot acquired.` before starting download progress.
- For non-interactive output, avoid unbounded repeated lines. Emit at most one concise waiting summary before the next stage, with elapsed time.

## 5. Console output

- Retain the existing episode heading and concise stage reporting.
- Keep one in-place progress line in interactive terminals, with completed tracks, total tracks, percentage, and a valid website ETA when available.
- Do not print unchanged progress repeatedly. Preserve a restrained heartbeat for redirected output.
- Show archive preparation, archive transfer, track validation, merging, sample-rate normalisation when applicable, MP3 encoding, artwork embedding, and metadata verification as clear stages.
- Avoid printing repeated queue messages, raw website status, selectors, browser internals, temporary paths, or verbose track lists in normal output.
- Keep detailed diagnostics and tracebacks in the persistent per-run log.
- Preserve the existing default yt-dlp provider output unless shared functionality requires a separately tested change.

## 6. Tests

Add or update offline tests for:
- Cover extraction from any canonical source track and deterministic cover selection.
- Preservation of image bytes and MIME type.
- Metadata field selection, ID3 writing, readback, and artwork verification.
- Missing artwork reporting and metadata failure preventing publication.
- Existing destination preservation when replacement finalization fails.
- Complete decode and output validation before publication.
- ETA seconds-only, minutes-and-seconds, hidden, malformed, and stale values.
- Cumulative queue elapsed time across multiple retries.
- One updating queue line in interactive mode and bounded output in non-interactive mode.
- Transition from waiting to download progress.
- No misleading progress or ETA while queued.
- Existing queue retry, ZIP download, archive validation, R16 merger, and cancellation regression tests.

Tests must use fixtures and mocked browser interactions. Do not require network access or real retry delays.

## 7. Documentation and release

- Update README and the Knowledge Base to document production metadata finalization, artwork behaviour, concise queue waiting, ETA formatting, and diagnostic logs.
- Add a request record and implementation/testing notes.
- Run Python compilation and the complete test suite.
- Review the complete diff and CI results.
- Open a pull request from `r17-download-polish-metadata` to `main`.
- Do not merge until the implementation and CI results have been reviewed.

## Acceptance criteria

A normal Spotisaver download of an episode with source artwork produces a final MP3 whose cover and metadata are embedded and verified, with no partial final file on failure. The console shows a single cumulative queue waiting line, a correctly formatted ETA when supplied by Spotisaver, and concise progress and processing stages. Existing R16 audio validation and queue safeguards remain intact.
