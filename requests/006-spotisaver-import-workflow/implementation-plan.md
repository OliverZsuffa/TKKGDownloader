# Implementation plan: Request 006

## Phase 1: Confirm source constraints

1. Treat the public Spotisaver pages as documentation for a manual user workflow only.
2. Recheck the Terms of Service immediately before implementation because website rules can change.
3. Do not automate the site's interface, call undocumented endpoints, evade limits, or download audio from the service programmatically.
4. If Spotisaver provides written permission or a documented API for the intended one-album use, record that evidence and prepare a separate plan amendment before implementing any integration beyond browser handoff.
5. Do not assume that a streaming subscription grants permission to make permanent MP3 copies. Keep source acquisition outside the downloader until rights and site terms are clear.

## Phase 2: Browser handoff

1. Add a helper that builds the public Spotisaver album page URL from the Spotify album ID in the validated TKKGData release.
2. Offer an explicit command or prompt to open the page in the system browser.
3. Do not scrape the rendered page, inspect private API calls, automate clicks, or attempt to obtain audio URLs.
4. Keep this feature optional. The user can cancel and continue with another permitted source.

## Phase 3: Local audio import

1. Add a user supplied import path for MP3 files or a ZIP archive.
2. Validate the path and supported file types before processing.
3. Inspect ZIP members before extraction. Reject absolute paths, parent traversal, symlinks, nested archives unless explicitly supported, and unexpected file types.
4. Extract only into a newly created temporary directory.
5. Never modify or delete the user's source archive or original MP3 files.
6. Support common filename patterns and ID3 tags. Prefer exact Spotify track title and track number metadata from TKKGData.
7. Normalize punctuation, whitespace, and common filename decorations for matching, but do not use fuzzy matching to silently select between candidates.
8. Use duration as a secondary consistency check with a documented tolerance. Report rather than silently accept significant mismatches.
9. Require exactly one match for each expected track. Reject missing tracks, duplicate candidates, unexpected extras where they create ambiguity, and empty files.
10. Preserve dynamic track counts. Do not hardcode 40.

## Phase 4: Reuse the existing merge pipeline

1. Convert validated imported files into the same internal ordered track representation used by the current downloader.
2. Reuse the existing FFmpeg merge implementation.
3. Preserve output naming, overwrite protection, confirmation prompts, range behaviour, and per episode failure handling.
4. Never create a combined MP3 unless every expected track has passed validation.
5. Clean up only temporary working files.

## Phase 5: Tests

Add tests for:
- Building the Spotisaver URL from a verified Spotify album ID.
- Browser handoff being optional and user initiated.
- Importing an archive with correctly tagged MP3 files.
- Importing files with filename based track numbers.
- Dynamic track counts.
- ZIP path traversal and absolute path rejection.
- Corrupt ZIP archives and unsupported files.
- Empty files and missing tracks.
- Duplicate or ambiguous matches.
- Title and duration mismatches.
- No merge when validation fails.
- Successful merge in the exact TKKGData order.
- Source files remaining unchanged.
- Temporary directory cleanup.
- Existing CLI and overwrite behaviour remaining intact.

All automated tests must use synthetic audio fixtures or mocked media metadata. CI must not fetch or redistribute copyrighted recordings.

## Phase 6: Documentation and manual verification

1. Update README usage examples for local import.
2. Update the Knowledge Base with the source separation and import design.
3. Record the current Spotisaver terms and the no-automation boundary in request notes.
4. After implementation and merge, Oliver should test the import workflow with audio files he is entitled to copy.
5. Verify the resulting MP3 plays and contains every expected track in order.

## Expected files

Likely changes:
- `src/tkkgdownloader/cli.py` or the current CLI entry point
- `src/tkkgdownloader/audio_import.py` as a new isolated import module
- `src/tkkgdownloader/downloader.py` for integration with the existing merge pipeline
- `tests/`
- `README.md`
- `docs/knowledge/`

Exact paths must be confirmed against the current repository before implementation.

## Approval gate

This is a plan only. Do not modify production code until Oliver explicitly approves it. Any future proposal to automate Spotisaver downloads requires separate confirmation of the site's permission and a new approved plan amendment.
