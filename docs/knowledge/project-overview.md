# Project Overview

## Purpose

TKKGDownloader is a Windows friendly Python command line tool that downloads a TKKG audio drama episode and merges its parts into one MP3 file.

## Responsibility boundary

TKKGData is the canonical source for episode metadata and verified provider mappings:
- Repository: https://github.com/OliverZsuffa/TKKGData
- Episode dataset: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/episodes.json
- Dataset metadata: https://raw.githubusercontent.com/OliverZsuffa/TKKGData/main/data/dataset-metadata.json

TKKGDownloader is a read only consumer. It does not scrape sources, search Spotify or YouTube Music, maintain a second catalogue, or write metadata back to TKKGData.

## Download workflow

1. Fetch and validate the TKKGData dataset and schema version.
2. Resolve the requested episode number and official title.
3. Validate its verified Spotify album, YouTube Music playlist, and ordered individual track pairings.
4. Prefer the YouTube Music playlist paired with the Spotify album.
5. If playlist download fails or no playlist is available, use the exact individual YouTube Music song and Spotify track URL pairs.
6. Validate the downloaded track count, numbering, and album folder.
7. Ask for confirmation unless `--yes` was supplied.
8. Merge the episode parts into one MP3 with FFmpeg.

The dataset's `tracks` array describes episode chapter segmentation. It is not the provider album track list. Download completeness comes from the verified `audio_release` mapping.

## Intended environment

- Windows and PowerShell
- Python 3.11 or later
- spotDL 4.5.2
- FFmpeg

Install the project with `py -m pip install -e .`. FFmpeg must also be installed and available on PATH.
