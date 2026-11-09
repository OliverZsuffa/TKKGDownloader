# Request 001: Download TKKG episodes as MP3

## Status

Implementation complete on `feature/001-episode-downloader`. Verification pending.

## Objective

Create a Python command line tool that takes one TKKG episode number or an episode range and produces one MP3 file for each requested episode.

## Intended usage

```powershell
python tkkg.py 1
python tkkg.py 1-10
python tkkg.py 125
```

## Implemented requirements

- [x] Accept a single episode number or an inclusive range.
- [x] Retrieve the latest episode metadata from TKKGTracker.
- [x] Resolve the official episode number and title.
- [x] Search using the episode number and official title.
- [x] Do not use TKKGTracker's `tracks` array for Spotify track selection.
- [x] Use spotDL to resolve and download the selected release tracks.
- [x] Sort tracks by track number before merging.
- [x] Merge tracks with FFmpeg into one MP3 per episode.
- [x] Verify that MP3 files exist and that the final output is non-empty.
- [x] Use a predictable output filename containing the episode number and title.
- [x] Process ranges episode by episode and report failures.
- [x] Protect existing output files unless `--overwrite` is passed.
- [x] Add automated tests for core parsing, metadata, query construction, and track ordering.
- [x] Document Windows installation and usage.

## Important limitation

spotDL uses Spotify metadata and searches YouTube for matching audio. It does not download audio directly from Spotify. The current implementation shows the selected album and track list for confirmation, but it does not independently compare multiple candidate Spotify releases. Manual inspection is required.

## Remaining acceptance checks

- [ ] Confirm automated tests pass in GitHub Actions.
- [ ] Test a real single episode with the user's Windows installation.
- [ ] Confirm the selected release and track order are correct.
- [ ] Confirm the merged MP3 plays correctly.
- [ ] Test a short episode range.
- [ ] Verify overwrite protection and `--overwrite`.
