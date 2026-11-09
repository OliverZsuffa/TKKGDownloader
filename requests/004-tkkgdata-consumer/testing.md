# Testing plan: Request 004

**Status:** Automated tests are being implemented. Real audio downloads and Windows playback remain manual.

## TKKGData client
1. Load a valid dataset and metadata fixture.
   Expected: episode titles and optional audio_release data parse correctly.
2. Load an unsupported schema version or mismatched episode count.
   Expected: clear compatibility error.
3. Load invalid JSON, malformed records, duplicate numbers, or numbering gaps.
   Expected: clear error before any download.
4. Simulate HTTP failure.
   Expected: clear TKKGData retrieval error and no fallback to TKKGTracker.

## Verified source mapping
1. Validate a complete verified Spotify and YouTube Music mapping.
   Expected: a download plan with Spotify album, playlist, and individual track pairs.
2. Test an absent playlist with complete individual track URLs.
   Expected: individual track fallback remains available.
3. Test unverified status, missing fields, invalid IDs, mismatched URLs, count mismatch, and reordered tracks.
   Expected: reject before running spotDL.
4. Test playlist download failure.
   Expected: attempt exact individual YouTube Music and Spotify track URL pairs.
5. Test individual track download failure.
   Expected: report the track and do not merge partial audio.

## Download and merge
1. Run episode 150 on Windows when its verified mapping is published.
   Expected: all 40 actual matched tracks download in order.
2. Run a second episode with a different track count.
   Expected: count derives from the verified data, not a constant.
3. Merge the downloaded tracks.
   Expected: one non-empty playable MP3 is produced.
4. Run a short episode range.
   Expected: one output per successful episode and per-episode failure reporting.
5. Test existing output and --overwrite.
   Expected: existing output is protected unless explicitly overridden.
6. Test --yes.
   Expected: confirmation is skipped without changing source selection or validation.

## Regression
1. Run py -m unittest discover -s tests -v.
   Expected: all tests pass.
2. Search downloader code for TKKGTracker, Spotify search, and YouTube Music search.
   Expected: no runtime source discovery remains.
3. Confirm there is no write-back, scraper, or competing catalogue.
   Expected: downloader is a read-only consumer.

## Actual observations
Automated test results will be recorded in notes.md. Windows download, merge playback, and overwrite observations remain pending until Oliver runs the downloader locally.
