# Notes: Request 004

## Planning findings
- TKKGDownloader currently retrieves episode metadata from TKKGTracker.
- The downloader resolves Spotify album metadata with spotDL and validates track numbering dynamically.
- Episode 150 returned 40 Spotify track records even though Spotify's summary count was inconsistent. The actual returned records must remain authoritative.
- The current spotDL text-based YouTube matching failed for many episode 150 tracks despite the user providing the official YouTube Music playlist.
- TKKGtracker request 009 and draft PR #14 explored storing both playlist and individual YouTube Music song URLs. This discovery belongs in TKKGData.
- The downloader should consume exact verified mappings and keep all downloading and merging local.

## Implementation status
Planning only. No downloader code, dependency, CLI, or download behaviour has been changed by this request.

## Test results
- GitHub Actions run 42695984257 completed successfully for draft PR #4.
- Project installation and the full unit test command passed.
- These are existing unit tests only. No real download, merge, or Windows playback test was run as part of this documentation request.
