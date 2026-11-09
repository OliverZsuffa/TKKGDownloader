# TKKGData integration

**Status: implemented on the Request 004 branch.**

## Ownership

TKKGData is the canonical source for episode metadata, verified Spotify album metadata, YouTube Music playlist and song URLs, provider track relationships, and verification evidence.

TKKGDownloader is a read-only consumer. It owns CLI parsing, audio download execution, downloaded-file validation, FFmpeg merging, output naming, overwrite protection, and local audio files.

## Published endpoints

- Episode array: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/episodes.json
- Dataset metadata: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/dataset-metadata.json

The current supported schema major version is 1.x. The client validates the metadata episode count, record structure, unique contiguous episode numbering, titles, and required arrays.

## Verified audio source selection

A downloadable episode must contain audio_release with verification.status set to verified.

The release contains:
- Spotify album ID, URL, title, and actual matched track count.
- An optional verified YouTube Music playlist URL and track count.
- Individual YouTube Music song URLs and video IDs.
- The exact Spotify track URL and ID paired with each YouTube Music song.
- Track numbering and verification evidence.

The downloader validates all IDs against their URLs, validates the cross-provider counts, and requires a contiguous one-based track sequence.

## Download order

1. Prefer the verified YouTube Music playlist paired with its Spotify album URL.
2. If the playlist is unavailable or the playlist download fails, use the exact individual YouTube Music song URL paired with its Spotify track URL.
3. Never perform Spotify or YouTube Music text searches.
4. Never write corrections back to TKKGData.
5. Reject incomplete or unverified mappings and incomplete downloads before merging.

spotDL documents manual matching as YouTubeURL|SpotifyURL and supports pairing YouTube Music playlists or albums with corresponding Spotify lists. Its current implementation also accepts individual YouTube watch URLs paired with Spotify track URLs.

## Compatibility boundary

The CLI, episode range processing, output naming, confirmation behaviour, overwrite protection, FFmpeg merge, and local files remain TKKGDownloader responsibilities. No scraper, shared catalogue, or provider discovery belongs in this repository.
