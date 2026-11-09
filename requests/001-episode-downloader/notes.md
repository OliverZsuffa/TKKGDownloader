# Request 001 Notes

## Initial implementation

- Implemented the Python CLI and direct `tkkg.py` entry point.
- Added dynamic episode metadata retrieval from TKKGTracker.
- Added spotDL album text search, MP3 output, track number sorting, release display, and confirmation.
- Added FFmpeg merging with stream copy and re-encoding fallback.
- Added range processing, overwrite protection, temporary file cleanup, and per episode error reporting.
- Added unit tests and a GitHub Actions test workflow.
- Added Windows installation and usage instructions.

## Follow-up fix: Request 002

The initial album text search failed for episode 150. Testing showed that spotDL could resolve a direct Spotify track URL and a direct Spotify album URL, while album text search did not find the release.

Request 002 replaces album text search with a generic first-track lookup. spotDL's metadata-only `save` operation resolves the first track, whose metadata supplies the Spotify album ID. The downloader then validates the album metadata and downloads by direct album URL.

The new flow validates that the first track belongs to TKKG and matches the requested episode and `Teil 01`. It validates the album ID, album identity, Spotify track count, and downloaded MP3 count. It does not use `list_length` as the album track count.

## Verification status

- Initial GitHub Actions unit tests passed before the follow-up fix.
- The user verified manually that spotDL 4.5.2 can resolve the episode 150 first-track Spotify URL and its direct album URL.
- Request 002 automated unit tests passed in GitHub Actions run #15.
- Pull request #2 was merged into `main`.
- Real end-to-end Windows download, merge, and playback using the new flow remain pending.
