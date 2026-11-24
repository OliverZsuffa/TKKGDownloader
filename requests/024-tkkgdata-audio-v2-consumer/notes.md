# Request 024 implementation notes

## Approval

Oliver approved Request 024 on 2026-11-24.

## Contract confirmed

The current TKKGData publication exposes:

- Dataset metadata schema version 1.0.0.
- Episode audio release schema version 2.
- Independent `spotify` and `youtube_music` release objects and verification records.
- Spotify album metadata nested under `spotify.album`.
- YouTube Music album and playlist metadata as separate optional objects.
- A separate `data/audio-unavailable.json` registry, version 1, currently identifying episodes 19, 20 and 37.

The combined audio release status can be `partial` while an individual provider is verified. Consumer selection therefore checks the selected provider's own verification state and verified count.

## Changes made

- Replaced the legacy shared track mapping validator with provider-specific schema v2 plan builders.
- Added independent Spotify album, track ID, URL, disc position, ordering, count and verification checks.
- Added independent YouTube Music video ID, watch URL, optional album and playlist identity, ordering, count and verification checks.
- Normalized Spotify's source disc and track positions into a contiguous import sequence while retaining source positions for metadata-based matching.
- Routed yt-dlp to the YouTube Music plan and Spotisaver to the Spotify plan.
- Changed final MP3 album metadata to use the selected provider's verified album title when available.
- Added loading and validation of the published known-unavailable registry.
- Added tests for unequal provider counts, provider-only availability, partial combined status, invalid IDs and URLs, Spotify multi-disc ordering, and unavailable episode handling.
- Replaced the CI live-data smoke test's episode 150 fixed 40-track assumption with episode 218's independent 25 Spotify and 35 YouTube Music tracklists.
- Updated the integration guide, README and technical decision 004.

## Verification

GitHub Actions run [45413572404](https://github.com/OliverZsuffa/TKKGDownloader/actions/runs/45413572404) completed successfully on the Request 024 pull request.

Passed steps:
- Project dependency installation.
- Python compilation for source and test modules.
- Live TKKGData provider contract smoke test.
- Episode 218 check: 25 Spotify tracks and 35 YouTube Music tracks.
- Known-unavailable registry checks for episodes 19, 20 and 37.
- Full unit test suite, including synthetic FFmpeg integration tests.

Real Windows downloads, Spotisaver browser import, final MP3 playback, and end-to-end verification on the user's Windows environment have not been performed in this environment. They remain required before declaring the full operational acceptance criteria complete.
