# Request 006 implementation notes

## 2026-11-10

- Oliver approved implementation after confirming that Spotisaver had explicitly approved his intended use.
- Created branch feature/spotisaver-import from plan/spotisaver-import-workflow.
- Added visible Playwright browser provider, public album URL construction from TKKGData, album and track title checks, ZIP or sequential track downloads, safe archive extraction, exact filename matching, and one-episode CLI guard.
- Added synthetic tests for ZIP import, ordering, missing track, traversal, corrupt archive, empty MP3, and provider selection.
- Updated README and Knowledge Base.
- GitHub Actions passed project installation, Python compilation, the live TKKGData contract smoke test, and all 37 unit tests on commit 03fc8889c53bf95a5803ec7e19d49cb306d389de.
- Real Spotisaver browser behaviour and Windows playback remain unverified. Real Spotisaver behaviour and Windows playback remain unverified.


## Follow-up fix: delayed page data

Oliver tested episode 150 and confirmed that Chromium opened the album page but the program checked the page before Spotisaver finished loading its client-side album data. Added an explicit wait of up to 120 seconds for the expected album title and all 40 canonical track titles before verification. Added unit tests for episode-prefix handling and the wait contract. The browser remains visible during this wait.
