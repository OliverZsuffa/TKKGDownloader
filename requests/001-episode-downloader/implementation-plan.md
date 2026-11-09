# Implementation Plan: Request 001

## Status

Proposed. No implementation is authorized until the user approves this plan.

## 1. Technical baseline

- Python command line application.
- spotDL for resolving and downloading the selected Spotify tracks.
- FFmpeg for lossless concatenation where the downloaded files have compatible codecs and stream parameters. Otherwise use a controlled conversion step and document the quality implications.
- Standard library for argument parsing, HTTP access, temporary directories, file handling, and logging unless a dependency is justified.

## 2. Proposed structure

```text
tkkgdownloader/
├── .github/
│   └── copilot-instructions.md
├── docs/
│   └── knowledge/
├── requests/
│   ├── README.md
│   ├── TEMPLATE.md
│   └── 001-episode-downloader/
│       ├── request.md
│       ├── implementation-plan.md
│       └── notes.md
├── src/
│   └── tkkgdownloader/
│       ├── __init__.py
│       ├── cli.py
│       ├── episodes.py
│       ├── spotify.py
│       ├── downloader.py
│       └── merger.py
├── tests/
├── output/
├── .gitignore
├── README.md
└── pyproject.toml
```

The exact module boundaries may be adjusted after validating the spotDL interface.

## 3. Processing pipeline

1. Parse a single positive episode number or an inclusive range.
2. Fetch the current TKKGTracker episode JSON from the repository's raw GitHub URL.
3. Validate the response and locate each requested episode by its number.
4. Build a Spotify search query from the zero-padded episode number and official title.
5. Search Spotify and inspect candidate albums and tracks.
6. Select the best matching release only when the evidence is sufficiently clear. If multiple plausible releases remain, present the candidates and require a selection rather than guessing.
7. Obtain the ordered track list from the selected Spotify release.
8. Download the selected tracks with spotDL into an episode-specific temporary directory.
9. Verify each expected track is present and map downloads to the selected track order. Do not rely on filesystem enumeration order.
10. Merge the tracks with FFmpeg.
11. Verify the final output and move it atomically into the output directory.
12. Report the result and continue with the next episode in a requested range even if one episode fails.

## 4. Spotify and spotDL investigation

Before implementation, validate the currently installed spotDL version and its supported command interface. Determine whether it can accept a Spotify album URL or an ordered list of track URLs and whether it exposes enough metadata to verify downloaded tracks.

Compare practical approaches for Spotify search and release discovery. Prefer an approach that does not require the user to create or maintain Spotify API credentials. If this is not possible, document the tradeoffs and ask before introducing credentials or another external service.

The search query must include both episode number and official title. Candidate selection should consider title, episode number, album metadata, track count, and track titles. The dataset's `tracks` array must not be used as Spotify track metadata.

## 5. Reliability

- Use timeouts and clear errors for metadata retrieval.
- Cache metadata during a single run so a range does not repeatedly fetch the same JSON.
- Keep downloads and intermediate files in temporary episode-specific directories.
- Validate process exit codes and expected files.
- Do not leave a partial final MP3 at the final output path.
- Avoid overwriting existing outputs by default.
- Record failed episodes in the final summary.

## 6. Testing plan

Automated tests should cover:

- Single-number and range parsing, including invalid and reversed ranges.
- Episode lookup, missing episode handling, and malformed metadata.
- Spotify search query construction.
- Candidate ranking and ambiguity handling.
- Track ordering independent of download completion or filesystem order.
- Missing tracks and failed spotDL or FFmpeg processes.
- Output naming, overwrite protection, and cleanup behavior.

Tests should mock network and external process calls. A separate manual integration test should use one episode and the user's installed spotDL and FFmpeg.

## 7. Manual verification

1. Run the tool for one known episode.
2. Confirm the displayed episode title matches TKKGTracker.
3. Confirm the selected Spotify release and its track list belong to that episode.
4. Confirm the merged MP3 plays from beginning to end and preserves track order.
5. Run a short episode range and verify one output per episode.
6. Simulate or inspect a failed episode and confirm the final report identifies it without corrupting other outputs.

## 8. Documentation and completion

- Add installation and usage instructions.
- Document spotDL and FFmpeg prerequisites.
- Document output naming and overwrite behavior.
- Record actual test commands and results in `notes.md`.
- Update the Knowledge Base with validated architectural decisions and operational details.

## 9. Approval gate

This plan is not authorization to implement. Begin feature implementation only after explicit user approval. If investigation reveals a material change in dependencies, authentication, or user interaction, update this plan and request approval again.
