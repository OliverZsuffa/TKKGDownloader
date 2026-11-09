# Testing plan: Request 004

**Status:** Planned only. No implementation or test execution has started.

## Dataset client
1. Load a valid TKKGData fixture.
   Expected: episode title, stable ID, and verified release metadata parse correctly.
2. Load an unsupported schema version.
   Expected: clear compatibility error.
3. Simulate invalid JSON, HTTP failure, and missing episode.
   Expected: clear errors and no silent fallback to unrelated data.
4. If a local cache is implemented, simulate a network failure.
   Expected: only a compatible validated cache is used.

## Source mapping
1. Resolve episode 150 from TKKGData.
   Expected: correct Spotify album, 40 actual Spotify track records, and verified YouTube Music playlist and individual song URLs where confirmed.
2. Test a different episode with a different number of tracks.
   Expected: expected count is derived dynamically.
3. Test missing playlist but complete individual song URLs.
   Expected: downloader follows the approved track-level path.
4. Test incomplete, duplicate, ambiguous, or reordered song mappings.
   Expected: downloader rejects the mapping rather than silently creating an incomplete episode.
5. Test an inconsistent provider summary count.
   Expected: actual validated track records determine completeness.

## Download and merge
1. Run a known episode on Windows.
   Expected: exact selected sources are shown and the correct tracks are downloaded in order.
2. Merge the downloaded tracks.
   Expected: one non-empty playable MP3 is produced.
3. Run a short range.
   Expected: one MP3 per episode and per-episode failure reporting.
4. Test existing output and --overwrite.
   Expected: existing output is protected unless explicitly overridden.
5. Test --yes.
   Expected: confirmation is skipped without changing source selection or validation.

## Regression
1. Run py -m unittest discover -s tests -v.
   Expected: all automated tests pass.
2. Confirm no runtime request is made to TKKGTracker's catalogue endpoint.
   Expected: shared episode data comes only from TKKGData.
3. Confirm no scraper or write-back code exists in TKKGDownloader.
   Expected: downloader is a read-only consumer.

## Actual observations
Record Oliver's Windows and playback observations here without replacing earlier results.
