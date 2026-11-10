# TKKGData integration

**Status: implemented.**

## Ownership

TKKGData is the canonical source for episode metadata, verified Spotify album metadata, YouTube Music playlist and song URLs, provider track relationships, and verification evidence.

TKKGDownloader is a read-only consumer. It owns CLI parsing, audio download execution, downloaded-file validation, FFmpeg merging, output naming, overwrite protection, and local audio files.

## Published endpoints

- Episode array: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/episodes.json
- Dataset metadata: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/dataset-metadata.json

The current supported schema major version is 1.x. The client validates the metadata episode count, record structure, unique contiguous episode numbering, titles, and required arrays.

## Verified audio source selection

A downloadable episode must contain audio_release with verification.status set to verified. The release contains Spotify album metadata, optional YouTube Music playlist metadata, individual YouTube Music song URLs, exact Spotify track pairings, track numbering, and verification evidence.

The downloader validates all IDs against their URLs, validates cross-provider counts, and requires a contiguous one-based track sequence.

## Download execution

The default provider invokes yt-dlp directly for each exact YouTube Music video URL and writes MP3 files to a temporary directory.

The optional Spotisaver provider opens the public album page in visible Chromium through Playwright. It verifies the album identity and track titles, uses normal website download controls, imports the resulting ZIP or MP3 files, and requires an exact filename match for every expected track before merging.

The playlist URL remains provenance metadata. Neither provider performs text search or writes corrections back to TKKGData.

## Compatibility boundary

The CLI, episode range processing, output naming, automatic FFmpeg merge, overwrite protection, and local files remain TKKGDownloader responsibilities. No independent catalogue or source discovery belongs in this repository.
