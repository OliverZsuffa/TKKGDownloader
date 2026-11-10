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

## Download execution

1. Validate the complete ordered track mapping from TKKGData.
2. Invoke yt-dlp directly for each exact YouTube Music video URL. Do not ask spotDL to resolve a playlist or song.
3. Use the paired Spotify track metadata for deterministic track naming and ordering.
4. Extract MP3 at 192 kbit/s into an isolated temporary album directory.
5. Require every expected file to exist and be non-empty, and validate the complete track count and contiguous numbering before merging.
6. Never perform Spotify or YouTube Music text searches. Never write corrections back to TKKGData.

The playlist URL remains provenance metadata. The direct track URLs are the execution inputs. This avoids the spotDL 4.5.2 failure observed during episode 150, where playlist resolution reached a download URL with a missing video ID (watch?v=None).

## Compatibility boundary

The CLI, episode range processing, output naming, confirmation behaviour, overwrite protection, FFmpeg merge, and local files remain TKKGDownloader responsibilities. No scraper, shared catalogue, or provider discovery belongs in this repository.
