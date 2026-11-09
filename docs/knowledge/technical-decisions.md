# Technical Decisions

## 001. Use TKKGData as the only metadata source

Episode identity and verified provider mappings are fetched from TKKGData. Validate the dataset metadata schema version, episode count, required record arrays, unique episode numbers, and contiguous numbering before using it.

Do not query TKKGTracker or keep an independent authoritative episode catalogue.

## 002. Do not perform source discovery in the downloader

TKKGData owns scraping, Spotify resolution, YouTube Music matching, source verification, provenance, and publication. The downloader only consumes verified identifiers and URLs. It must never use text search as a fallback or write corrections back to TKKGData.

## 003. Prefer verified playlist pairing

Use the verified YouTube Music album playlist URL paired with the Spotify album URL when available. spotDL 4.5.2 supports this explicit pairing format.

If the playlist is missing or its download fails, use each verified YouTube Music song URL paired with its exact Spotify track URL. Do not infer a pairing from similar titles.

## 004. Validate track integrity from the shared mapping

The Spotify track count, YouTube Music track count, matched count, and actual list length must agree. Track numbers must be contiguous and ordered. Validate each provider ID against its corresponding URL.

After downloading, require the MP3 count and track numbering to match the validated mapping. Require exactly one album folder. Never create a combined file from an incomplete or ambiguous download.

## 005. Preserve the command line contract

Keep commands such as `py tkkg.py 150` and `py tkkg.py 1-10`. Preserve range handling, output naming, overwrite protection, per episode failure reporting, FFmpeg merging, and temporary file cleanup.

## 006. Keep downloads local

Downloaded audio and temporary files stay outside version control. The downloader never uploads audio or user data to TKKGData.

## Verification status

The TKKGData consumer migration and downloader CI consolidation are merged. The latest main branch workflow passed project installation, Python compilation, the live TKKGData contract smoke test, and the unit test suite.

Real audio download, FFmpeg merge, and playback remain separate end to end checks. They should only be reported as passed after an actual download test.
