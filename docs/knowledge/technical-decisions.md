# Technical Decisions

## Use episode metadata dynamically

Episode titles and numbering are retrieved from the TKKGTracker dataset instead of being hardcoded.

## Resolve albums through the first chapter track

Album text search failed for episode 150. The downloader now searches for the episode's first chapter track using the episode number, official title, and `Teil 01`. spotDL's metadata-only `save` operation resolves that track and provides its Spotify album ID. The downloader then uses the direct album URL.

The first-track result must identify artist TKKG, match the requested episode and first part, and contain a valid album ID. The album metadata must refer to the same album. The expected track count is derived dynamically from the complete set of song records returned by spotDL's album metadata save operation. The returned track numbers must form a complete sequence from 1 through the number of records, with no duplicates or invalid numbers. Do not rely on Spotify's inconsistent `tracks_count` field. The downloaded MP3 count must match this validated record count.

## Validate album completeness

Derive the expected album size from all song records returned by spotDL's album metadata operation. Require track numbers to form a complete sequence from 1 through the record count, with no duplicates or invalid numbers. Require the downloaded MP3 count to match that validated count. Do not use Spotify's inconsistent `tracks_count` field as the expected size.

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

## Album count and progress feedback

The album track count is derived from all song records returned by spotDL's album metadata operation, not Spotify's `tracks_count` field. Track numbers must form a complete sequence from 1 through the record count. spotDL subprocesses retain terminal output and are accompanied by flushed stage messages and elapsed-time heartbeat messages every 10 seconds.

Request 003 was merged in pull request #3. Automated unit tests passed in GitHub Actions. The first Windows integration test confirmed that episode 150 metadata resolves to 40 tracks and passes validation. The download stage then failed to find YouTube Music matches for many tracks, even though the user supplied the official YouTube Music album playlist. The user stopped the run before completion. End-to-end download, merge, and playback remain unverified. Investigate pairing the official YouTube Music album URL with the corresponding Spotify album URL for exact matching, rather than relying on text search.
