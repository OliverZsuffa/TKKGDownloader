# Request 001 Notes

## Implementation

- Implemented the Python CLI and direct `tkkg.py` entry point.
- Added dynamic episode metadata retrieval from TKKGTracker.
- Added spotDL album search using the episode number and official title.
- Added MP3 output, track number sorting, release display, and confirmation.
- Added FFmpeg merging with stream copy and re-encoding fallback.
- Added range processing, overwrite protection, temporary file cleanup, and per episode error reporting.
- Added unit tests and a GitHub Actions test workflow.
- Added Windows installation and usage instructions.

## Technical findings

- spotDL accepts album search queries using the `album:` prefix.
- spotDL uses Spotify metadata to locate matching audio on YouTube. It does not download audio directly from Spotify.
- FFmpeg is used both by spotDL and by the final merge stage.

## Verification status

- Code and test files have been committed to the feature branch.
- GitHub Actions and local unit test results have not yet been confirmed.
- Real download and playback have not been tested in the user's Windows environment.
- Do not consider the first release fully verified until a real single episode and a short range have been tested.

## Remaining work

- Verify the CI run.
- Perform a manual test with the user's installed spotDL and FFmpeg.
- Inspect whether the selected album and track list are correct for a real episode.
- Address any issues found before merging into `main`.
