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

- GitHub Actions unit tests passed on the final feature branch commit.
- Pull request #1 was merged into `main`.
- Real spotDL and FFmpeg download and playback have not yet been tested in the user's Windows environment.
- The first real test should use one episode before attempting a range.
- Do not consider audio matching and final playback fully verified until that manual test succeeds.

## Remaining work

- Run `python tkkg.py 1` on Windows.
- Inspect the selected release and track list.
- Confirm the merged MP3 plays correctly and preserves the expected order.
- Run a short episode range.
- Address any integration issues found.
