# Project Overview

## Purpose

TKKGDownloader is a Windows friendly Python command line tool that downloads a TKKG audio drama episode and merges its parts into one MP3 file.

## Responsibility boundary

TKKGData is the canonical source for episode metadata and verified provider mappings:
- Repository: https://github.com/OliverZsuffa/TKKGData
- Episode dataset: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/episodes.json
- Dataset metadata: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/dataset-metadata.json

TKKGDownloader is a read only consumer. It does not scrape sources, search Spotify or YouTube Music, maintain a second catalogue, or write metadata back to TKKGData.

## Download workflow

1. Fetch and validate the TKKGData dataset and schema version.
2. Resolve the requested episode number and official title.
3. Validate its verified Spotify album and ordered individual track mappings.
4. Use the default yt-dlp provider with exact verified YouTube Music video URLs, or explicitly select the Spotisaver browser provider.
5. For Spotisaver, open one canonical album in visible Chromium, poll for the real album download button, and use normal website download controls.
6. For Spotisaver, map every downloaded MP3 to one complete canonical title using exact normalized matching. Reject ambiguity, missing or extra tracks, duplicate audio, and invalid canonical numbering. Record the source mapping and checksums in a manifest, then verify the canonical files again immediately before merging.
7. Automatically merge the episode parts into a temporary MP3 with the R16 merger only after every track and its manifest entry have passed validation.
8. For normal Spotisaver downloads, extract available source artwork and consistent source tags, write episode metadata, read back and verify the metadata and original cover bytes, probe and fully decode the candidate, then publish it atomically to the final path.

Spotisaver mode is intentionally restricted to one episode per invocation. Its manifest remains in memory during normal downloads and is preserved as reports/track-manifest.json in R13 diagnostic mode. Embedded tags are corroborating evidence only and never override TKKGData. The final merged file receives verified episode and album metadata, plus only optional source tags that are consistent across the source tracks. It does not bypass site protections, use private endpoints, or run unattended catalogue downloads.

For a one-time quality investigation, the optional `--diagnostic-dir` mode preserves the Spotisaver archive and source tracks, inspects and fully decodes every source, compares the existing merge against a lossless PCM concatenation encoded once at 320 kbit/s, verifies embedded artwork and ID3 metadata, and creates a lossless review file for every track boundary. This mode runs locally and never replaces the normal episode output.

## Intended environment

- Windows and PowerShell
- Python 3.11 or later
- yt-dlp (installed through the project dependency)
- Playwright and its Chromium browser for Spotisaver mode
- FFmpeg
