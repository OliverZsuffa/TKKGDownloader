# Technical Decisions

## Use episode metadata dynamically

Episode titles and numbering are retrieved from the TKKGTracker dataset instead of being hardcoded.

## Resolve albums through the first chapter track

Album text search failed for episode 150. The downloader now searches for the episode's first chapter track using the episode number, official title, and `Teil 01`. spotDL's metadata-only `save` operation resolves that track and provides its Spotify album ID. The downloader then uses the direct album URL.

The first-track result must identify artist TKKG, match the requested episode and first part, and contain a valid album ID. The album metadata must refer to the same album and provide a consistent track count.

## Validate album completeness

Use Spotify's `tracks_count` field as the expected album size. Do not use `list_length`, which may represent a broader playlist context. Require the album metadata record count and downloaded MP3 count to match the expected track count. Reject duplicate track numbers.

## Do not use TKKGTracker chapter entries as Spotify tracks

The dataset's `tracks` field is not a reliable representation of Spotify's release track list. Spotify release metadata determines which tracks are downloaded and merged.

## Produce one output file per episode

A requested range creates separate MP3 files, one for each episode, rather than combining multiple episodes into one file.

## Use spotDL for metadata resolution and audio matching

spotDL uses Spotify metadata and searches YouTube for matching audio. It does not download audio directly from Spotify. This distinction must be clear in user documentation.

## Confirm the selected release

The application displays the selected album folder and its downloaded tracks before creating the final merged MP3. The user can inspect the list or use `--yes` to accept it without a prompt.

## Merge conservatively

FFmpeg first attempts stream copy. If the MP3 streams are not compatible for direct concatenation, it retries with a 192 kbps MP3 re-encode.

## Protect existing outputs

Existing final files are skipped by default. The user must pass `--overwrite` to replace them.

## Validation status

The new album resolution flow passed its automated unit tests in GitHub Actions run #15 and was merged in pull request #2. Real Windows integration and playback testing remain outstanding.
