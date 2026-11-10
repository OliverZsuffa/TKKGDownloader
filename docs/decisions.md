# Approved decisions

## 001. TKKGData owns shared metadata

Oliver approved the three-repository migration on 2026-11-09. TKKGData owns episode metadata, source scraping, provider discovery, verification, provenance, validation, and publication. TKKGDownloader consumes the published dataset read-only.

## 002. No independent source discovery in the downloader

The downloader must not query TKKGTracker, search Spotify, search YouTube Music, scrape provider pages, or write corrections back to TKKGData. It downloads only verified source pairings from the dataset.

## 003. Download exact verified YouTube video URLs directly

Use yt-dlp directly with the exact individual YouTube Music video URLs and IDs validated from TKKGData. Do not resolve playlists through spotDL. The playlist remains provenance metadata. Spotify track metadata controls canonical names and ordering.

## 004. Dynamic track integrity

Track count and order come from the complete validated cross-provider track mapping. Do not hardcode 40 tracks or rely on an inconsistent provider summary without the actual matched track records.
