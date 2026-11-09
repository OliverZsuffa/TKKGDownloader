# Implementation plan: Make TKKGDownloader a TKKGData consumer

**Status:** Proposed. Awaiting Oliver's explicit approval. Planning only.

## 1. Preconditions
1. Read TKKGData request 001 and its approved schema, example dataset, stable endpoint, and consumer documentation.
2. Confirm the dataset version and compatibility policy.
3. Confirm which fields are guaranteed for verified Spotify releases, playlist mappings, and individual song mappings.
4. Record the current main commit, test results, and Windows integration status.
5. Do not switch the production downloader until a valid TKKGData release is published.

## 2. Baseline audit
Inspect:
- src/tkkgdownloader/episodes.py for current TKKGTracker JSON retrieval and episode lookup.
- src/tkkgdownloader/spotify.py for spotDL metadata resolution and album selection.
- src/tkkgdownloader/downloader.py for downloads and file validation.
- src/tkkgdownloader/merger.py for FFmpeg merging and output safety.
- CLI parsing, tests, README, and knowledge-base decisions.
- Request 009 and TKKGtracker draft PR #14 for the source mapping design and known episode 150 evidence.

Record all current external calls and identify which become unnecessary when metadata comes from TKKGData.

## 3. TKKGData client
1. Add a small client that retrieves the stable latest JSON endpoint.
2. Validate dataset metadata and supported schema version.
3. Parse the requested episode by stable ID and series/episode number.
4. Validate the selected episode's required fields and any provider release used.
5. Avoid adding a heavy framework. Prefer the standard library unless the contract or tests justify a dependency.
6. Decide whether to fetch per invocation or use a bounded local cache. Do not create a second editable catalogue.
7. Provide clear errors for HTTP failure, invalid JSON, unsupported schema, missing episode, and missing verified source data.

## 4. Source selection and download flow
The intended flow is:
1. Parse episode number or inclusive range.
2. Load the matching TKKGData episode record.
3. Select the verified Spotify provider release intended for the requested edition.
4. Validate the album ID, canonical URL, artist/title evidence, and complete Spotify track records.
5. Select the associated verified YouTube Music playlist when present.
6. Use the playlist and Spotify album pairing if the installed spotDL version supports it reliably.
7. Where the playlist is unavailable or insufficient, use the verified individual YouTube Music song URLs if the chosen downloader path supports direct source URLs.
8. Preserve Spotify track order and require a complete one-to-one mapping before claiming the release is complete.
9. Display the selected release and track list clearly before final merge acceptance, preserving the current confirmation model where practical.
10. Download audio, validate downloaded track count and ordering, and merge with the existing FFmpeg process.
11. Write the completed file atomically and preserve overwrite protection.

Do not implement the exact spotDL invocation until a focused compatibility experiment proves the stored URLs are accepted by the installed version. If individual song URLs need yt-dlp or another tool, document the trade-off and obtain approval if it changes dependencies or user-visible behaviour.

## 5. Track integrity
- Never hardcode 40 tracks or another fixed count.
- Derive expected count from the actual validated Spotify track records in TKKGData.
- Validate unique, contiguous track numbering.
- Match each individual YouTube Music song record to the corresponding Spotify track by explicit stored relationship and verified evidence.
- Reject duplicate, missing, ambiguous, or out-of-order mappings unless the dataset explicitly models an edition-specific exception.
- Do not assume archive chapter records correspond to provider album tracks.
- Do not silently mix multiple Spotify or YouTube Music editions.

## 6. Missing data and fallback
Define explicit behaviour for:
- No TKKGData endpoint.
- Dataset unavailable but a compatible local cache exists.
- No episode record.
- Episode exists but no verified Spotify release.
- Spotify release exists but no playlist mapping.
- Playlist exists but individual song mappings are incomplete.
- Provider IDs or URLs fail validation.
- Downloaded file count differs from the verified track count.

Any fallback to spotDL text discovery must be clearly labelled as unverified, must require the approved user interaction, and must not be written back to the dataset. Decide whether fallback remains at all after testing exact mappings.

## 7. Preserve downloader responsibilities
Keep:
- CLI syntax and episode range support.
- User confirmation and --yes behaviour.
- Output directory and predictable filenames.
- FFmpeg stream-copy attempt and re-encode fallback.
- Atomic output handling.
- Existing-file protection and --overwrite.
- Per-episode failure reporting for ranges.
- Windows-friendly installation and usage.

Do not move download execution or local audio files into TKKGData.

## 8. Automated tests
Add fixtures for:
- Valid dataset and compatible schema.
- Unsupported schema version.
- Missing episode and missing verified release.
- Spotify album with dynamically sized track list.
- Episode 150's 40 actual Spotify track records.
- Verified YouTube Music playlist mapping.
- Individual song URLs linked to Spotify tracks.
- Missing, duplicate, ambiguous, or reordered mappings.
- Inconsistent provider summary count.
- HTTP failure and cache fallback if caching is implemented.
- Existing CLI, range processing, merge, and overwrite behaviour.

Mock network and subprocess calls. Tests must not download real audio.

## 9. Windows manual verification
1. Run py tkkg.py --help.
2. Run episode 150 using the published TKKGData record.
3. Confirm the selected Spotify release and YouTube Music source mapping.
4. Confirm all expected tracks are downloaded in order.
5. Confirm the merged MP3 plays and contains the complete episode.
6. Run a second episode with a different track count.
7. Run a short episode range and verify one output per episode.
8. Verify existing output is skipped by default and replaced only with --overwrite.
9. Test a missing or incomplete mapping and confirm the error is clear.

## 10. Cutover
1. Add the TKKGData client while retaining a testable old-source comparison during development.
2. Compare episode titles and IDs with the existing TKKGTracker source.
3. Verify episode 150 source resolution against the published mapping.
4. Verify at least one episode with a different track count and one episode with missing optional source metadata.
5. Switch the production client to TKKGData.
6. Remove the TKKGTracker metadata URL and independent Spotify discovery only after the new flow passes.
7. Update README, knowledge base, and request notes with actual results.

## 11. Definition of done
The downloader uses TKKGData as its only shared episode and verified release metadata source, does not scrape or mutate the dataset, preserves its local download and merge behaviour, and passes automated plus Windows end-to-end verification.
