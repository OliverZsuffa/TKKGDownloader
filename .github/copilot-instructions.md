# Repository instructions

## Start here
- Read README.md and docs/README.md.
- Read docs/knowledge/README.md and all relevant Knowledge Base documents before changing the project.
- Read the active request and its implementation plan before working on a feature.
- Read docs/decisions.md when a decision is relevant.

## Request and approval workflow
- A request defines expected behaviour and acceptance criteria. The implementation plan defines the technical approach.
- Do not implement a feature until Oliver has explicitly approved its implementation plan.
- Keep changes focused on the approved request.
- Add or update automated tests where practical and provide concrete manual test steps.
- Run relevant tests and build or validation commands. Never claim checks passed if they were not run.
- Record implementation decisions and actual test results in request notes.
- Update the Knowledge Base when a decision is reusable beyond one request.
- Use a dedicated branch for feature implementation.
- Do not force-push, merge, or deploy without Oliver's explicit approval.

## Target architecture
- TKKGData owns the canonical shared TKKG episode dataset, schema, source scraping, source discovery, verification, provenance, validation, and publication.
- TKKGDownloader consumes TKKGData read-only.
- TKKGDownloader remains responsible for CLI behaviour, audio download execution, track-file validation, FFmpeg merging, output naming, overwrite protection, and local files.
- It must not scrape TKKG sources, independently discover Spotify or YouTube Music mappings, maintain a competing episode catalogue, or write metadata back to TKKGData.
- It validates the TKKGData schema version and episode count before using the dataset.
- It downloads only verified Spotify and YouTube Music pairings. Prefer the verified playlist and Spotify album pair. Fall back to exact individual YouTube Music song and Spotify track URL pairs. Never use text search as a fallback.
- The published TKKGData dataset is available at the stable main branch endpoint. Keep the downloader compatible with schema version 1.x.
- Keep the current data path until the replacement is live and verified.

## Code quality
- Prefer simple, maintainable Python code and clear separation of responsibilities.
- Keep external command execution explicit and handle errors, missing dependencies, and interrupted downloads.
- Never silently select an ambiguous Spotify release or silently produce an incomplete output file.
- Never hardcode a track count. Validate the complete one-to-one source mapping and downloaded track sequence.
- Derive expected track count from validated actual track records, not a fixed count or inconsistent provider summary.
- Do not confuse archive chapter segmentation with provider album track divisions.
- Do not commit credentials, tokens, personal data, or downloaded audio files.
- Keep generated downloads and temporary merge files out of version control.
