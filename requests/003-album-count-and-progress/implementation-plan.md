# Implementation Plan: Request 003

## Status

Proposed. Awaiting user approval before implementation.

## Problem

The Windows integration test for episode 150 resolved the correct Spotify album and spotDL returned 40 song metadata records. The downloader then rejected the result because the first-track metadata contained `tracks_count: 25`.

That field is not a reliable expected count for the metadata list returned by spotDL in this case. The observed album metadata save operation reported 40 songs, and the user confirmed that 40 is the correct episode track count.

The current implementation also provides too little feedback during slow spotDL operations. It prints a message before the command and the result after it finishes, but gives no indication that a long-running operation is still active.

## Proposed changes

### 1. Correct album metadata validation

- Stop using the first track's `tracks_count` as the expected number of album tracks.
- Treat the number of valid records returned by spotDL's album metadata save operation as the expected track count.
- Continue validating that every record belongs to the resolved Spotify album.
- Continue validating track numbers and rejecting duplicate or invalid numbering.
- Return the validated metadata record count from the validator.
- Compare the number of downloaded MP3 files against that validated count, so episode 150 expects 40 files.
- If spotDL exposes a separate list count such as `list_length`, log it for diagnostics where useful, but do not let the inconsistent `tracks_count` value reject an otherwise valid 40-record result.
- Keep the album identity and first-track checks unchanged.

### 2. Improve progress feedback

- Print clear, flushed stage messages before each potentially slow operation:
  1. Resolving the first track.
  2. Retrieving the complete album track list.
  3. Downloading the resolved number of tracks.
  4. Verifying downloaded files.
  5. Showing the track list and awaiting confirmation.
  6. Merging the tracks.
- While a spotDL subprocess is running, periodically print an elapsed-time heartbeat such as `Still working... (00:30 elapsed)`.
- Keep spotDL stdout and stderr connected to the terminal so any native spotDL progress output remains visible.
- Print the final exit status and elapsed duration when an operation finishes.
- Ensure progress messages appear immediately in PowerShell by flushing output.
- Do not add artificial progress percentages when spotDL does not expose reliable progress data.

### 3. Tests

- Add a regression test where the first-track metadata reports `tracks_count: 25` but the album metadata contains 40 valid records. Validation must accept all 40.
- Verify the validator returns 40 and the download completeness check expects 40.
- Keep rejection tests for empty metadata, wrong album IDs, invalid track numbers, and duplicate track numbers.
- Add tests for the progress runner where practical, including successful completion and non-zero exit status.
- Run the complete automated test suite and GitHub Actions.

## Scope and compatibility

- Preserve the existing command line interface, episode range support, overwrite protection, `--yes`, track ordering, confirmation, and FFmpeg merge behavior.
- Do not change the first-track lookup strategy.
- Do not change the output filename format.
- No changes to the downloaded audio format or bitrate.

## Manual verification

After approval and implementation, the user will run:

```powershell
git switch main
git pull
py tkkg.py 150
```

Verify that:
- The album metadata stage reports 40 tracks.
- The download stage clearly indicates activity during long waits.
- Exactly 40 MP3 files are found and listed in numeric order.
- The confirmation prompt appears.
- The merged MP3 is created and plays correctly.

A second episode and a range should be tested after episode 150 succeeds.

## Open implementation detail

The progress heartbeat should be implemented without swallowing or buffering spotDL's own terminal output. A subprocess polling loop with inherited stdout and stderr is the preferred approach. Heartbeat timing should be modest, for example every 10 seconds, and should not affect the subprocess.

