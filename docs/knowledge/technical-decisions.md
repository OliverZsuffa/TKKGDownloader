# Technical Decisions

## Initial decisions

### Use episode metadata dynamically

Episode titles and numbering are retrieved from the TKKGTracker dataset instead of being hardcoded.

### Search by episode number and title

The search query includes the zero-padded episode number and official title. The current implementation passes an `album:` query to spotDL.

### Do not use TKKGTracker chapter entries as Spotify tracks

The dataset's `tracks` field is not a reliable representation of Spotify's release track list. Spotify release metadata determines which tracks are downloaded and merged.

### Produce one output file per episode

A requested range creates separate MP3 files, one for each episode, rather than combining multiple episodes into one file.

### Use spotDL for metadata resolution and audio matching

spotDL accepts Spotify metadata queries and searches YouTube for matching audio. It does not download audio directly from Spotify. This distinction must be clear in user documentation.

### Confirm the selected release

The current implementation displays the selected album folder and its downloaded tracks before creating the final merged MP3. The user can inspect the list or use `--yes` to accept it without a prompt. This is a basic safeguard, not a fully independent comparison of multiple candidate Spotify releases.

### Merge conservatively

FFmpeg first attempts stream copy. If the MP3 streams are not compatible for direct concatenation, it retries with a 192 kbps MP3 re-encode.

### Protect existing outputs

Existing final files are skipped by default. The user must pass `--overwrite` to replace them.

## Validation status

The application and unit tests are implemented. Real spotDL and FFmpeg integration behavior still requires testing in the target Windows environment.
