# TKKGData integration

**Status: proposed in request 004. The integration is not implemented yet.**

## Target responsibility
TKKGData will own the canonical episode and provider release metadata. TKKGDownloader will consume that dataset read-only.

The downloader remains responsible for:
- CLI parsing and episode ranges.
- Download execution.
- Downloaded-file validation and ordering.
- FFmpeg merging.
- Output naming, overwrite protection, and local files.

It must not scrape episode sources, discover Spotify albums, or write metadata back to TKKGData.

## Audio source data
The planned contract includes Spotify album metadata and actual track records, plus verified YouTube Music playlist and individual song URLs where available. Track counts must be derived from actual validated track records rather than a potentially inconsistent provider summary.

## Migration dependency
Do not switch the production downloader until TKKGData publishes a validated dataset, stable endpoint, and documented schema compatibility policy. See request 004 for the complete plan and testing requirements.
