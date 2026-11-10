# Request 006: Spotisaver assisted source and MP3 import workflow

## Status

Proposed. Awaiting Oliver's approval.

## Objective

Investigate whether Spotisaver can be used as a user initiated source for occasional personal TKKG episode preparation, and make TKKGDownloader able to import and validate audio files that Oliver has independently and legitimately obtained.

The target use case is one episode occasionally, not continuous or catalogue wide downloading.

## Website findings

The official Spotisaver pages describe this workflow:

1. The user supplies a Spotify album, playlist, or track URL.
2. Spotisaver reads Spotify metadata such as titles, artists, album information, artwork, and track order.
3. It searches independent external sources for matching audio.
4. It offers matched MP3 files individually and, on the website, a ZIP option.
5. The user downloads files through the website.

Official documentation:
- https://spotisaver.net/en/album-downloader
- https://spotisaver.net/en/music-to-mp3
- https://spotisaver.online/en/terms

The website states that it does not download, rip, record, or access audio from Spotify. Spotify is used for metadata only. Audio is matched from independent external sources.

The current Terms of Service say the service is for personal, non-commercial use, require users to have the legal right to copy the content, and prohibit bulk downloading. The public feature page advertises album ZIP functionality, but that does not override the Terms of Service. A 40-track episode album must therefore not be automated or treated as permitted bulk use without explicit clarification or permission from Spotisaver and confirmation that the user has the necessary copying rights.

No public API or documented automation interface was found. Do not reverse engineer private endpoints, evade usage limits, automate website downloads, or bypass access controls.

## User experience

The intended eventual workflow, subject to the usage and rights conditions above, is:

1. Oliver runs `py tkkg.py 150`.
2. The downloader displays the Spotify album URL already stored in TKKGData and can open the public Spotisaver page in the browser for manual use.
3. The user independently obtains only files that the source permits them to copy and download.
4. The user passes a local MP3 or ZIP file path to TKKGDownloader for import.
5. The downloader validates the files against the verified Spotify track metadata in TKKGData.
6. The downloader merges a complete, validated episode using the existing FFmpeg pipeline.

The application must not log into Spotisaver, automate its download buttons, scrape hidden endpoints, or circumvent site limits.

## Functional requirements

1. Keep TKKGData as the sole source of truth for episode metadata and verified Spotify track identity, titles, order, and expected durations.
2. Add a user initiated browser handoff to the public Spotisaver album page using the Spotify album ID already present in TKKGData.
3. Do not claim that Spotisaver has a supported API. Do not automate its website or download actions.
4. Add an import path for user supplied local MP3 files and ZIP archives, independent of how the files were obtained.
5. Support an explicit input path, for example `py tkkg.py 150 --import-audio "C:\\path\\to\\files.zip"`, subject to CLI design review.
6. Safely inspect ZIP contents without extracting paths outside a temporary directory. Reject path traversal, unexpected file types, corrupt archives, and empty files.
7. Match imported files using embedded tags and filenames, with normalized title matching against TKKGData. Use duration as a secondary validation signal.
8. Do not silently guess when multiple files match one track or when a track is missing. Report the ambiguity and ask the user to correct the input.
9. Require the complete expected track set in the correct order before merging an episode. Track count must remain data driven and never hardcoded to 40.
10. Preserve the existing output naming, overwrite protection, confirmation behaviour, FFmpeg merge, and per episode error reporting.
11. Keep imported originals unchanged. Work on temporary copies and clean up temporary data after success or failure.
12. Keep the downloader read only with respect to TKKGData.
13. Document that the user is responsible for having the rights and permissions required to copy imported audio.
14. Do not automate multi-track downloads from Spotisaver unless Spotisaver explicitly confirms that the intended use is permitted and the user has the required rights.

## Out of scope

- Downloading audio directly from Spotify, Amazon Music, or YouTube Music.
- Recording protected streams or bypassing DRM or other technical protection.
- Reverse engineering undocumented Spotisaver endpoints.
- Automated browser clicking, scraping, or bulk downloading from Spotisaver.
- Changes to TKKGData or TKKGtracker.
- Searching for or substituting unverified audio sources.
- A general media player or GUI.

## Acceptance criteria

- [ ] A public Spotisaver album page can be opened through an explicit user action using the Spotify album ID from TKKGData.
- [ ] The CLI can import a user supplied local MP3 file set or ZIP archive.
- [ ] ZIP extraction is safe against path traversal and malformed archives.
- [ ] Imported tracks are matched to the exact expected metadata with deterministic rules.
- [ ] Missing, duplicate, ambiguous, corrupt, or unexpected files prevent merging and produce actionable errors.
- [ ] Track count and ordering are validated dynamically from TKKGData.
- [ ] The existing FFmpeg merge is reused only after complete validation.
- [ ] Tests cover successful imports, malformed ZIP files, unsafe paths, duplicate tracks, missing tracks, mismatched titles, duration mismatches, and no-merge-on-failure.
- [ ] README and Knowledge Base explain the import workflow and its source and rights limitations.
- [ ] No automated Spotisaver download or hidden endpoint integration is introduced.

## Open questions

- Will Spotisaver explicitly confirm that downloading all tracks from one 40-track album is allowed under its current Terms of Service?
- Does Oliver have a separate legal basis or authorization to make local copies of the specific TKKG recordings?
- Should import be exposed as a new flag on the existing command or as a separate `import` subcommand?
