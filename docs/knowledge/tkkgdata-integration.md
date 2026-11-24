# TKKGData integration

**Status: implemented for audio release schema version 2.**

## Ownership

TKKGData is the canonical source for episode metadata, provider release metadata, ordered Spotify and YouTube Music tracklists, verification evidence, and known-unavailable episode records.

TKKGDownloader is a read-only consumer. It owns CLI parsing, provider selection, audio download execution, downloaded-file validation, Spotisaver import, FFmpeg merging, output naming, overwrite protection, and local audio files.

## Published endpoints

- Episode array: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/episodes.json
- Dataset metadata: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/dataset-metadata.json
- Known unavailable registry: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/audio-unavailable.json

The dataset metadata schema is currently 1.x. The episode-level `audio_release` object has its own `schema_version`, currently version 2. These versions are validated separately.

The consumer validates the dataset episode count, record structure, unique contiguous episode numbering, titles, required arrays, and the versioned known-unavailable registry.

## Independent provider release contract

An audio release v2 contains independent `spotify` and `youtube_music` objects and provider-specific verification records.

Each provider owns its own album metadata, ordered tracklist, declared track count, IDs, URLs, and verification count. The consumer validates only the selected provider's complete release. It does not require equal Spotify and YouTube Music counts, matching titles, matching segment boundaries, or one-to-one track correspondence. The overall release can be `partial` while the selected provider is independently `verified`.

A provider is usable only when its provider-level verification status is `verified`, its verified count equals its own tracklist length, and all provider-specific identifiers, URLs, counts, and ordering are valid.

### YouTube Music

The default `yt-dlp` provider uses every exact verified YouTube Music video URL in the published order. It uses YouTube Music track titles and its own count for filenames, progress, validation, and merging. The optional playlist URL is metadata only and is not used to resolve audio.

### Spotify and Spotisaver

The `spotisaver` provider uses the canonical Spotify album ID as the album identity anchor and validates every imported file against the complete Spotify tracklist. Spotify's original disc and track positions are retained as source metadata. The importer assigns a contiguous one-based canonical sequence for deterministic file naming, manifests, and merging.

The existing Spotisaver browser workflow, queue handling, ZIP transfer, archive safety, deterministic title matching, manifest, checksums, diagnostics, metadata finalization, and merge safeguards remain in place.

## Known unavailable episodes

The consumer loads `data/audio-unavailable.json` separately from the episode array. Its reviewed entries currently identify episodes 19, 20 and 37 as unavailable for official digital rerelease. These are reported with their published reason. A missing or unverified provider mapping is not automatically treated as global unavailability, and the downloader never silently switches providers.

## Compatibility boundary

The CLI, episode range processing, output naming, automatic FFmpeg merge, overwrite protection, and local files remain TKKGDownloader responsibilities. No independent catalogue, source discovery, scraping, Spotify resolution, YouTube matching, or write-back belongs in this repository.
