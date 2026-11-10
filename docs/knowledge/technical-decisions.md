# Technical Decisions

## 001. Use TKKGData as the only metadata source

Episode identity and verified provider mappings are fetched from TKKGData. Validate the dataset metadata schema version, episode count, required record arrays, unique episode numbers, and contiguous numbering before using it.

Do not query TKKGTracker or keep an independent authoritative episode catalogue.

## 002. Do not perform source discovery in the downloader

TKKGData owns scraping, Spotify resolution, YouTube Music matching, source verification, provenance, and publication. The downloader only consumes verified identifiers and URLs. It must never use text search as a fallback or write corrections back to TKKGData.

## 003. Download exact verified YouTube video URLs directly

The default provider uses yt-dlp directly with each individual YouTube Music video URL and the exact video ID validated from TKKGData. Do not ask spotDL to resolve the playlist or individual song URLs. The previous spotDL 4.5.2 path attempted downloads with a YouTube URL containing a missing video ID.

## 004. Validate track integrity from the shared mapping

The Spotify track count, YouTube Music track count, matched count, and actual list length must agree. Track numbers must be contiguous and ordered. Validate each provider ID against its corresponding URL.

After downloading, require every expected MP3 file to exist and be non-empty. Never create a combined file from an incomplete or ambiguous download.

## 005. Preserve the command line contract

Keep commands such as py tkkg.py 150 and py tkkg.py 1-10. Preserve range handling, output naming, overwrite protection, per episode failure reporting, FFmpeg merging, and temporary file cleanup.

## 006. Keep downloads local

Downloaded audio and temporary files stay outside version control. The downloader never uploads audio or user data to TKKGData.

## 007. Spotisaver is an explicit one-episode browser provider

Spotisaver is selected explicitly with --provider spotisaver. Playwright launches visible Chromium and uses the public album page and normal rendered download controls. It first looks for the visible `#downloadAllBtn` control labelled `Download entire playlist` and clicks it directly. It only clicks `button.btn-playlist-download` labelled `Download Playlist` when the real action is not already visible. That intermediate control only scrolls to the action area. If the album action remains unavailable, the provider logs concise diagnostics for visible controls before considering individual track controls sequentially.

The provider waits up to 120 seconds for the site's client-side album lookup and complete tracklist to load, then verifies the album title and all expected track titles before starting. ZIP extraction rejects traversal paths and symlinks. Imported MP3 filenames must map uniquely to every expected TKKGData track. No merge occurs unless all tracks match.

Do not use private endpoints, stealth plugins, CAPTCHA bypasses, login bypasses, access-control workarounds, or unattended catalogue downloads. Stop when the site presents a restriction or its interface cannot be verified. Spotisaver's permission and limits are separate from technical implementation and must be respected.

## Verification status

Automated tests cover the data contract, CLI selection, safe ZIP import, filename matching, and downloader behaviour. Real Spotisaver download, FFmpeg merge, and playback remain separate end to end checks and must not be reported as passed until tested locally.
