# Technical Decisions

## 001. Use TKKGData as the only metadata source

Episode identity and verified provider mappings are fetched from TKKGData. Validate the dataset metadata schema version, episode count, required record arrays, unique episode numbers, and contiguous numbering before using it.

Do not query TKKGTracker or keep an independent authoritative episode catalogue.

## 002. Do not perform source discovery in the downloader

TKKGData owns scraping, Spotify resolution, YouTube Music matching, source verification, provenance, and publication. The downloader only consumes verified identifiers and URLs. It must never use text search as a fallback or write corrections back to TKKGData.

## 003. Download exact verified YouTube video URLs directly

Use yt-dlp directly with each individual YouTube Music video URL and the exact video ID validated from TKKGData. Do not ask spotDL to resolve the playlist or individual song URLs. The previous spotDL 4.5.2 path discovered the playlist tracks but attempted downloads with a YouTube URL containing a missing video ID (watch?v=None).

The verified Spotify track records remain authoritative for track identity, canonical filenames, and ordering. The playlist URL is retained as source provenance but is not part of the download execution path.

Invoke yt-dlp from the project Python environment when its executable is not on PATH. Extract MP3 at 192 kbit/s and write each track to a deterministic track-number-prefixed filename.

## 004. Validate track integrity from the shared mapping

The Spotify track count, YouTube Music track count, matched count, and actual list length must agree. Track numbers must be contiguous and ordered. Validate each provider ID against its corresponding URL.

After downloading, require every expected MP3 file to exist and be non-empty. Require the MP3 count and track numbering to match the validated mapping. Require exactly one album folder. Never create a combined file from an incomplete or ambiguous download.

The Spotify track count, YouTube Music track count, matched count, and actual list length must agree. Track numbers must be contiguous and ordered. Validate each provider ID against its corresponding URL.

After downloading, require the MP3 count and track numbering to match the validated mapping. Require exactly one album folder. Never create a combined file from an incomplete or ambiguous download.

## 005. Preserve the command line contract

Keep commands such as `py tkkg.py 150` and `py tkkg.py 1-10`. Preserve range handling, output naming, overwrite protection, per episode failure reporting, FFmpeg merging, and temporary file cleanup.

## 006. Keep downloads local

Downloaded audio and temporary files stay outside version control. The downloader never uploads audio or user data to TKKGData.

## Verification status

The TKKGData consumer migration and downloader CI consolidation are merged. The latest main branch workflow passed project installation, Python compilation, the live TKKGData contract smoke test, and the unit test suite. The direct yt-dlp implementation is being validated separately in Request 005.

Real audio download, FFmpeg merge, and playback remain separate end to end checks. They should only be reported as passed after an actual download test.
