# Request 004: Make TKKGDownloader a TKKGData consumer

## Status
Awaiting approval. Planning only. No downloader implementation is authorized yet.

## Objective
Change TKKGDownloader so it consumes episode and verified release metadata from TKKGData. It should no longer retrieve its episode catalogue from TKKGTracker or independently discover Spotify albums and YouTube Music sources.

TKKGDownloader remains a focused local download and merge application.

## Context
TKKGData is being established as the single source of truth for structured TKKG episode information, source discovery, Spotify and YouTube Music release mappings, provenance, validation, and publication.

Current behaviour:
- TKKGDownloader retrieves episode numbers and titles from TKKGtracker's published episodes JSON.
- It resolves Spotify album metadata through spotDL, currently by finding the first track and deriving the album ID.
- It derives the expected track count from the actual records returned by spotDL because Spotify's summary track count has been inconsistent.
- It uses spotDL to find matching YouTube audio, but the user has encountered failures for many tracks despite having the official YouTube Music album playlist.
- The TKKGtracker request 009 and draft PR #14 explored storing both a verified YouTube Music playlist and individual song URLs. This discovery belongs in TKKGData.

Relevant project history:
- Request 001 implemented the episode downloader.
- Request 002 replaced album text search with first-track metadata lookup.
- Request 003 improved dynamic track-count validation and progress feedback.
- These behaviours must be preserved where still useful, but shared metadata discovery moves to TKKGData.

## User experience
The user continues to run commands such as:

    py tkkg.py 150
    py tkkg.py 1-10

The downloader resolves the requested episode and verified source release from TKKGData, clearly reports the selected release and tracks, downloads the audio, merges it into one MP3 per episode, and protects existing output files by default.

## Functional requirements
1. Retrieve episode identity and official title from the published TKKGData dataset.
2. Retrieve verified Spotify album metadata and track records from TKKGData.
3. Retrieve verified YouTube Music playlist URL and individual song URLs from TKKGData when available.
4. Prefer verified exact source mappings over independent text search.
5. Never write discovered or corrected metadata back to TKKGData from the downloader.
6. Do not silently substitute an unverified release or incomplete track list.
7. Validate dataset version and record structure before using the data.
8. Handle network failures with a clear error. A small local cache may be used only if its freshness and version behaviour are explicitly designed and documented.
9. Keep the current command line interface, episode range handling, FFmpeg merge, output naming, overwrite protection, and per-episode failure reporting.
10. Keep the implementation Windows-friendly and avoid introducing a heavy runtime dependency solely to read JSON.

## Scope

### Included
- Audit current metadata and download pipeline.
- Replace the TKKGTracker catalogue endpoint with the TKKGData endpoint.
- Add a small TKKGData client and contract validation.
- Adapt source selection to use verified Spotify and YouTube Music mappings.
- Test spotDL's supported playlist pairing and direct individual-track handling before choosing the final invocation.
- Keep dynamic completeness checks based on actual validated track records.
- Add explicit behaviour for episodes with missing or incomplete verified audio mappings.
- Add fixtures and automated tests for data loading, schema compatibility, track selection, and error handling.
- Update README, project instructions, and knowledge base.
- Coordinate the migration with TKKGData request 001 and TKKGTracker request 010.

### Not included
- Scraping official TKKG pages, Spotify, or YouTube Music.
- Discovering or verifying provider mappings.
- Publishing or correcting the shared dataset.
- Merging multiple episodes into one file.
- Changing FFmpeg output behaviour or unrelated CLI features.
- Storing audio files in the repository.
- Writing data corrections back to TKKGData.

## Constraints
- The downloader must not maintain an independent episode catalogue.
- The downloader must not assume one release or fixed number of tracks per episode.
- Spotify's summary track count must not be treated as authoritative when actual track records are available.
- Only verified provider mappings from TKKGData may be treated as exact sources.
- Any fallback for episodes without verified mappings must be explicit, user-visible, and must not update the dataset.
- Do not remove the current data path until the TKKGData endpoint and contract are live and verified.

## Acceptance criteria
- [ ] Episode metadata is loaded from the TKKGData dataset.
- [ ] The downloader validates dataset version and required fields.
- [ ] A verified Spotify album mapping is used without a new Spotify text search.
- [ ] A verified YouTube Music playlist mapping can be paired with the Spotify album when supported by the installed tool.
- [ ] Verified individual YouTube Music song URLs are available to the downloader as a track-level source mapping.
- [ ] Track order and completeness are validated from actual track records, not a hardcoded count or inconsistent summary field.
- [ ] Missing, ambiguous, or invalid mappings produce a clear actionable error or the explicitly approved fallback.
- [ ] The downloader never writes to or scrapes TKKGData sources.
- [ ] Existing CLI commands, output naming, range processing, FFmpeg merge, and overwrite protection continue to work.
- [ ] Automated tests pass.
- [ ] Windows manual tests cover episode 150, a second episode with different track count, a short range, merge playback, and overwrite protection.
- [ ] README and knowledge base describe TKKGDownloader as a TKKGData consumer.

## Dependencies
- TKKGData request 001 must publish a validated dataset and stable consumer contract.
- TKKGData must store verified Spotify album and track records plus YouTube Music playlist and individual song URLs where available.
- TKKGTracker request 010 is coordinated but is not a runtime dependency for the downloader once TKKGData is published.

## Open questions
- Which exact spotDL version and invocation support pairing the stored YouTube Music playlist with the Spotify album reliably?
- Can spotDL accept the individual YouTube Music song URLs directly while preserving Spotify metadata and track order, or is a different supported download path required?
- Should the downloader cache the latest dataset locally, or fetch it on each invocation? The simplest reliable option should be selected after inspecting the existing client and failure modes.
- What should happen when an episode has verified Spotify metadata but only some YouTube Music song URLs are verified?
