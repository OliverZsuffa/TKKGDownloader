# Request 024: Implementation plan

## Status

Approved by Oliver. Implementation in progress.

## Goal

Migrate the downloader's internal data model from the former shared Spotify and YouTube Music track mapping to provider-specific plans derived from TKKGData audio release schema version 2.

The migration must be structural, not a collection of compatibility fallbacks. Each provider must be validated against its own canonical release and tracklist.

## Current repository assumptions to remove

The current code and tests contain assumptions that need to be located and removed where they conflict with the new contract:

- Spotify and YouTube Music track counts must agree.
- A shared matched count or shared track array represents both providers.
- YouTube Music tracks can be paired one to one with Spotify tracks.
- Downstream code can always read Spotify titles and numbering even when downloading YouTube Music.
- The CI smoke test for episode 150 is permanently defined as exactly 40 tracks.

The episode 150 test may retain a fixture with 40 tracks if it is intentionally testing a historical example. It must not act as a universal contract for all episodes or as evidence that the current provider list always has that count.

## Phase 1: Inspect and document the live contract

1. Inspect the current TKKGData published dataset, episode schema, audio release schema version 2, and known-unavailable registry.
2. Record the exact nesting and field names for:
   - Spotify release identity and album metadata.
   - Spotify verification and ordered track records.
   - YouTube Music release and playlist metadata.
   - YouTube Music verification and ordered track records.
   - Provider-specific counts and any release profile or discovery metadata needed by the consumer.
   - Known-unavailable episode records and their published reason.
3. Compare the live contract with the downloader's current dataset client and fixtures.
4. Add a concise contract note to the downloader knowledge base, including the distinction between dataset metadata schema `1.0.0` and audio release schema version 2.
5. Do not guess field names or registry paths. Derive them from the current TKKGData schema and published files.

**Deliverable:** a documented field mapping and a list of old assumptions to replace.

## Phase 2: Introduce provider-specific normalized plans

Create or refactor the internal model so that downstream components receive a selected provider plan rather than a mixed release object.

The normalized plan should expose only the information required by that provider's workflow, including:

- Provider identity.
- Episode identity and episode title.
- Provider-specific album or playlist identity and display metadata.
- Provider-specific ordered track records.
- Provider-specific expected track count.
- Provider-specific verification state.
- Track identifiers and exact verified URLs where applicable.
- Canonical titles, exact alternate titles and track numbers where applicable.

The model must not imply that a Spotify track and a YouTube Music track at the same index are the same segment.

Validation should be split into two levels:

1. Dataset validation: metadata schema version, episode array, episode count, unique episode numbers and contiguous episode numbering.
2. Provider release validation: audio release schema version, selected provider availability, verification, identifiers, URL consistency, count, unique track numbers and contiguous ordering.

A provider plan may be created only when that provider's own release is valid. A missing Spotify mapping must not prevent a valid YouTube Music plan, and vice versa.

**Likely areas:** `episodes.py`, `audio_sources.py`, dataset client modules, shared types and fixtures.

**Tests:**
- Valid v2 release with both providers.
- Valid Spotify only.
- Valid YouTube Music only.
- Missing selected provider.
- Unverified selected provider.
- Wrong release schema version.
- Invalid provider IDs or URLs.
- Duplicate, missing, non-contiguous or reordered track numbers.
- Provider counts differing without rejection.
- Dataset-level numbering and metadata validation remain independent.

## Phase 3: Migrate the default YouTube Music path

1. Build the default plan exclusively from the YouTube Music release.
2. Pass its exact ordered track list to yt-dlp.
3. Keep the current exact individual video URL behaviour.
4. Use YouTube Music titles and numbering for expected-file validation and any track-level diagnostics.
5. Require every expected YouTube Music track to exist, be non-empty and pass the existing integrity checks.
6. Merge only after the entire provider-specific list passes validation.
7. Ensure extra YouTube Music segments such as introduction, summary, closing song and outro are retained whenever present in the published tracklist.

**Likely areas:** `audio_sources.py`, `downloader.py`, `audio_diagnostics.py`, `metadata.py`.

**Tests:**
- Episode 218 yields exactly the 35 YouTube Music tracks in canonical order.
- A different Spotify count does not affect YouTube Music download validation.
- Exact video IDs and URLs are used.
- Missing, duplicate, empty or invalid downloaded files prevent merging.
- Existing range processing and per-episode error handling remain unchanged.

## Phase 4: Migrate the Spotisaver path

1. Build the Spotisaver plan exclusively from the verified Spotify release.
2. Continue constructing the album page from the canonical Spotify album ID.
3. Pass the Spotify tracklist and Spotify expected count to the existing import workflow.
4. Keep deterministic title and alternate-title matching tied to Spotify track records.
5. Preserve album identity checks, ZIP path safety, source checksums, manifest creation, metadata validation, diagnostics and merge safeguards.
6. Ensure YouTube Music track count and segmentation cannot affect Spotisaver import acceptance.
7. Keep the one-episode invocation restriction.

**Likely areas:** `spotisaver.py`, `audio_import.py`, `metadata.py`, `audio_diagnostics.py`.

**Tests:**
- Episode 218 yields exactly the 25 Spotify tracks in canonical order.
- A different YouTube Music count does not affect Spotify import validation.
- Spotify album identity and track matching remain strict.
- Existing queue state, retry and reload tests remain unchanged and pass.
- Existing ZIP, manifest, checksum and metadata tests remain unchanged in behaviour and pass.
- Invalid or incomplete imports never reach the merger.

## Phase 5: Handle known-unavailable records

1. Read the registry through the actual TKKGData publication mechanism established in Phase 1.
2. Keep the registry separate from episode identity and provider release data.
3. When an episode has a registry entry, report its known-unavailable status and reason.
4. Do not conflate known global unavailability with one provider lacking a verified release.
5. If only the selected provider is missing, report that provider-specific state and do not silently switch providers.
6. Keep normal processing for other episodes in an episode range.

**Tests:**
- Episodes 19, 20 and 37 report the registry reason.
- A provider-specific missing mapping is not labelled globally unavailable.
- A valid alternative provider remains selectable.
- A malformed or absent registry is handled according to the TKKGData publication contract without inventing unavailable entries.

## Phase 6: Update downstream metadata and diagnostics

Review all consumers of the old shared plan. In particular:

- `metadata.py`: preserve episode identity and title while using provider-specific album or track information only where appropriate.
- `audio_diagnostics.py`: report the selected provider, its expected count and its own track sequence.
- `audio_import.py`: remain Spotify-specific unless a genuinely shared abstraction is needed. Do not weaken its deterministic matching rules.
- `downloader.py`: never merge from a partially validated provider list.
- Logs and error messages: name the selected provider and distinguish missing metadata, invalid metadata, download failure and known unavailability.

Avoid unnecessary generalization. A small provider-specific interface is preferable to a generic abstraction that hides important differences.

## Phase 7: Replace brittle tests and update documentation

1. Replace universal assumptions that episode 150 always has 40 tracks.
2. Retain episode 150 as a regression case only where its explicit fixture remains useful.
3. Add episode 218 as the central independent-tracklist regression case with 25 Spotify tracks and 35 YouTube Music tracks.
4. Keep synthetic fixtures self-contained and deterministic. Do not make CI depend on live TKKGData changes or real downloads unless the existing test architecture explicitly supports a pinned publication fixture.
5. Update README and knowledge-base documentation to describe the provider-specific data contract.
6. Update technical decision 004. Its current requirement that Spotify count, YouTube Music count, matched count and actual list length all agree is obsolete. Replace it with independent provider validation and selected-provider completeness.
7. Update the request index and record implementation and verification results after approval and completion.

## Phase 8: Verification

### Automated

Run the complete test suite:

```powershell
py -m unittest discover -s tests -v
```

Also run any repository linting, type checks or CI commands already defined by the project. Do not introduce a new toolchain solely for this migration.

Verify that:
- Both provider plans are built from the correct nested data.
- Independent counts and segmentations are preserved.
- Invalid selected-provider data is rejected.
- A valid other provider remains usable.
- Known-unavailable episodes are reported accurately.
- No incomplete download can be merged.
- Existing CLI, Spotisaver, ZIP, metadata, diagnostics and merge regressions pass.

### Windows end to end

After automated tests pass, perform local checks with the current published TKKGData:

1. Download a suitable episode using the default YouTube Music provider.
2. Confirm the downloaded part count and order against the YouTube Music plan.
3. Merge, probe and listen to the result.
4. Download a suitable episode using Spotisaver.
5. Confirm imported files against the Spotify plan and manifest.
6. Merge, probe and listen to the result.
7. Confirm output naming, overwrite protection, temporary cleanup and logs.

Use episode 218 as a high-value regression case if both provider sources are currently usable. Do not assume availability without checking the current data and service.

Real downloads and listening checks must be reported separately from automated test results.

## Implementation sequence

1. Inspect and record the exact current TKKGData contract.
2. Add provider-specific normalized plans and validation.
3. Migrate and test YouTube Music.
4. Migrate and test Spotisaver.
5. Add known-unavailable reporting.
6. Update metadata, diagnostics, CI fixtures and documentation.
7. Run the full automated suite.
8. Complete Windows download, merge and playback checks.
9. Record results in this request's `notes.md`.
10. Present the changes for review and wait for explicit merge approval.

## Files expected to change

The exact list will be confirmed after Phase 1. Expected areas include:

- `src/tkkgdownloader/episodes.py`
- `src/tkkgdownloader/audio_sources.py`
- `src/tkkgdownloader/downloader.py`
- `src/tkkgdownloader/audio_import.py`
- `src/tkkgdownloader/spotisaver.py`
- `src/tkkgdownloader/metadata.py`
- `src/tkkgdownloader/audio_diagnostics.py`
- Relevant tests and fixtures.
- `docs/knowledge/technical-decisions.md`
- `README.md`
- `requests/README.md`

No production source files are changed by this planning request.
