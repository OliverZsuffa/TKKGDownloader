# Technical Decisions

## Initial decisions

### Use episode metadata dynamically

Episode titles and numbering must be retrieved from the TKKGTracker dataset instead of being hardcoded.

### Search Spotify by episode number and title

Search terms must include both the episode number and the official episode title to reduce incorrect matches.

### Do not use TKKGTracker chapter entries as Spotify tracks

The dataset's `tracks` field is not a reliable representation of Spotify's release track list. Spotify release metadata determines which tracks are downloaded and merged.

### Produce one output file per episode

A requested range creates separate MP3 files, one for each episode, rather than combining multiple episodes into one file.

### Require evidence for release selection

The application must not silently choose among materially different plausible releases. Ambiguous candidates should be presented for user selection.

## Validation status

These are initial product and architecture decisions derived from the project requirements. Details involving spotDL behavior, Spotify search, and FFmpeg compatibility still require technical validation.
