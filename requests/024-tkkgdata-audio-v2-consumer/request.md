# Request 024: Consume the independent TKKGData audio release format

## Status

Implementation complete. Automated verification passed. Local Windows end-to-end verification remains pending.

## Objective

Update TKKGDownloader to consume the current TKKGData audio release schema without losing provider-specific tracks or changing the downloader's established workflows.

TKKGData remains the only source of episode metadata and verified provider mappings. TKKGDownloader remains a read-only consumer.

## User experience

The existing commands and provider selection continue to work:

- `py tkkg.py 150` downloads the verified YouTube Music tracklist.
- `py tkkg.py 150 --provider spotisaver` imports the verified Spotify album through the existing Spotisaver browser workflow.
- Episode ranges continue to work with the default provider.
- Episodes known to have no official audio release are reported as known unavailable, with a useful explanation, rather than as an unexplained missing mapping or a failed download.

The selected provider uses its own complete, ordered tracklist. A difference in track count or segmentation between Spotify and YouTube Music is expected and must not cause rejection.

## Background

TKKGData has changed the structure of each episode's `audio_release` object to schema version 2. The dataset metadata schema remains version `1.0.0`. Provider release metadata and tracklists are now independent.

For example, episode 218 has 25 Spotify tracks and 35 YouTube Music tracks. The additional YouTube Music segments are valid provider-specific tracks and must all be downloaded and merged when YouTube Music is selected.

TKKGData also publishes a known-unavailable registry for episodes 19, 20 and 37. These episodes should be distinguished from episodes whose data is unexpectedly incomplete.

## Functional requirements

1. **Read the current contract**
   - Continue validating the published dataset metadata schema independently from the per-episode audio release schema.
   - Require and validate audio release schema version 2 for records using the new format.
   - Read the current provider-specific album, playlist and track data without relying on the former shared track mapping.
   - Validate each provider's identifiers, URLs, verification state, track count, track numbering and ordering against that provider's own records.
   - Do not require Spotify and YouTube Music to have equal track counts, matching track numbers, or one-to-one track correspondence.

2. **Build provider-specific download plans**
   - The default yt-dlp provider receives the verified YouTube Music release and its complete ordered tracklist.
   - The Spotisaver provider receives the verified Spotify album identity and its complete ordered Spotify tracklist.
   - Keep provider-specific titles, alternate titles, track numbers, counts and album metadata attached to the correct provider.
   - Normalize the external TKKGData format into an internal provider-specific plan so downstream download and import code does not need to understand unrelated provider fields.
   - A missing or unverified mapping for one provider must not invalidate a valid mapping for the other provider.

3. **Preserve YouTube Music download behaviour**
   - Continue using yt-dlp with the exact verified individual YouTube Music video URLs.
   - Do not introduce text search, playlist scraping, spotDL source resolution, or fallback discovery.
   - Download every track in the selected YouTube Music list, including introductions, summaries, story parts, songs and outros where present.
   - Validate the downloaded files against the selected YouTube Music tracklist only.
   - Do not truncate, pad, reorder or otherwise reshape the list to match Spotify.

4. **Preserve Spotisaver behaviour**
   - Continue to use the canonical Spotify album ID as the album identity anchor.
   - Validate the imported archive against every track in the selected Spotify tracklist only.
   - Preserve the existing browser workflow, queue state machine, retries, reload behaviour, diagnostics, ZIP transfer handling, archive safety, deterministic title matching, alternate-title handling, import manifest, checksums, metadata finalization and merge safeguards.
   - Keep Spotisaver restricted to one episode per invocation.

5. **Handle known unavailable audio**
   - Consume TKKGData's known-unavailable registry if it is part of the published dataset contract.
   - Report episodes 19, 20 and 37 as known unavailable with the published reason.
   - Do not interpret this registry as a second episode catalogue.
   - Do not mark an episode unavailable merely because a provider mapping is missing.
   - If the selected provider is unavailable but the other provider is verified, report the provider-specific distinction clearly.

6. **Preserve downstream correctness**
   - Update episode loading, source planning, download validation, Spotisaver import, diagnostics and metadata handling wherever they currently assume one shared tracklist.
   - Metadata and filenames must use the selected provider's correct track information where track-level data is required, while episode identity and episode title remain grounded in TKKGData.
   - Incomplete, ambiguous or invalid downloads must never be merged or published as a completed episode.
   - Preserve existing temporary-file cleanup and output protection.

7. **Preserve the public interface and ownership boundaries**
   - Keep existing CLI syntax, provider names, range handling, output naming, overwrite behaviour, per-episode failure reporting, FFmpeg processing and local-only storage.
   - Keep TKKGDownloader read-only with respect to TKKGData.
   - Do not add TKKGTracker dependencies, source discovery, scraping, Spotify resolution or YouTube matching.
   - Do not modify TKKGData or TKKGTracker as part of this request.

## Constraints

- TKKGData is authoritative for episode facts and verified provider data.
- Dataset metadata schema version and audio release schema version are separate contracts and must be validated separately.
- Spotify and YouTube Music are independent providers, not two views of one canonical tracklist.
- Provider-specific validation must be strict. Independent tracklists do not mean relaxed validation.
- Existing Spotisaver browser behaviour and safety constraints must remain intact.
- Real downloads and playback verification require local Windows testing. CI must use deterministic synthetic data and mocks.

## Out of scope

- Changes to TKKGData's schema, data, discovery or publication.
- Changes to TKKGTracker.
- New providers or new source-discovery mechanisms.
- Reworking the Spotisaver website interaction beyond changes strictly required to pass the correct Spotify-specific plan.
- Re-encoding or editorial correction of source recordings.
- Bulk Spotisaver downloads.

## Acceptance criteria

- [x] The current published TKKGData dataset loads and validates successfully.
- [x] Dataset metadata schema `1.0.0` and audio release schema version 2 are validated independently.
- [x] Episode 218 produces a YouTube Music plan containing all 35 verified tracks and a Spotisaver plan containing all 25 verified Spotify tracks.
- [x] Unequal provider track counts are accepted without cross-provider matching or truncation.
- [x] A valid provider remains usable when the other provider's mapping is missing or unverified.
- [x] Provider-specific invalid IDs, URLs, counts, duplicate numbers, gaps and ordering errors are rejected.
- [x] Episodes 19, 20 and 37 are reported as known unavailable using the published registry information.
- [x] Existing YouTube Music downloads still use exact verified individual video URLs.
- [x] Existing Spotisaver browser, ZIP, import, manifest, diagnostics and merge safeguards continue to pass their tests.
- [x] The hardcoded episode 150 expectation of exactly 40 tracks is replaced with contract-driven validation or a deliberately maintained fixture whose purpose is explicit.
- [x] Existing CLI commands, ranges, output handling and overwrite protections remain compatible.
- [x] The full automated test suite passes.
- [ ] At least one real YouTube Music episode download, merge and playback check is completed on Windows.
- [ ] At least one real Spotisaver episode download, import, merge and playback check is completed on Windows, subject to website availability.
- [x] No changes are made to TKKGData or TKKGTracker.

## Open questions

None. The registry endpoint and version 1 structure were confirmed against the current TKKGData publication.
