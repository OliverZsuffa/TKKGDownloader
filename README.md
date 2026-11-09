# TKKGDownloader

A command line tool for creating one MP3 file per TKKG audio drama episode, suitable for offline listening.

## Planned usage

```powershell
python tkkg.py 1
python tkkg.py 1-10
python tkkg.py 125
```

The tool will retrieve the official episode title from the TKKGTracker dataset, search Spotify using the episode number and title, identify the corresponding Spotify release and its tracks, download the tracks with spotDL, and merge them into one MP3 with FFmpeg.

The TKKGTracker `tracks` field is not a source for Spotify track selection. It describes chapter information and must not be treated as Spotify's track listing.

## Project status

The initial feature is documented in [Request 001](requests/001-episode-downloader/request.md). No downloader implementation has been approved or started yet.

## Requirements

The planned application uses Python, spotDL, and FFmpeg. Exact versions and installation instructions will be documented once the implementation approach has been validated.

## Project workflow

See [Requests](requests/README.md) and the [Knowledge Base](docs/knowledge/README.md).
