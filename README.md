# TKKGDownloader

A Windows friendly command line tool that creates one MP3 file per TKKG audio drama episode.

## Requirements

- Python 3.11 or newer
- FFmpeg available on PATH
- Chromium for the optional Spotisaver browser provider

Install the project:

    py -m pip install -e .

Install the Playwright browser once:

    py -m playwright install chromium

Check FFmpeg:

    ffmpeg -version

## Usage

Download through the existing verified YouTube Music provider:

    py tkkg.py 150

Use Spotisaver through a visible Chromium browser for one episode:

    py tkkg.py 150 --provider spotisaver

Download an inclusive range with the default provider:

    py tkkg.py 1-10

Skip the merge confirmation after all tracks have passed validation:

    py tkkg.py 150 --provider spotisaver --yes

Choose another output folder:

    py tkkg.py 1 --output-dir "D:\\Music\\TKKG"

Replace an existing output:

    py tkkg.py 1 --overwrite

Get help:

    py tkkg.py --help

Spotisaver mode accepts exactly one episode per invocation. Run it separately for each episode. It opens a visible browser and checks the album and tracklist against TKKGData. It first clicks the visible `Download entire playlist` button directly. Only if that button is not visible does it click the intermediate `Download Playlist` navigation control to reveal the action area. If no verified album action is available, it logs visible controls before considering individual track downloads. It does not use private endpoints, hidden APIs, stealth browser settings, or access-control workarounds. If the website changes its interface or presents a restriction, the run stops.

## Data ownership

[TKKGData](https://github.com/OliverZsuffa/TKKGData) is the single source of truth for episode metadata, verified Spotify releases, YouTube Music playlist URLs, individual song URLs, and source verification.

TKKGDownloader fetches the published TKKGData episode array and dataset metadata. It does not read the TKKGTracker catalogue, scrape sources, search for Spotify albums, discover YouTube matches, or write metadata back to TKKGData.

## Download and output

The default provider invokes yt-dlp once per exact verified YouTube Music track URL, extracts MP3 audio at 192 kbit/s, validates every expected file, then merges the tracks with FFmpeg.

The Spotisaver provider uses Playwright to operate the public album page in visible Chromium. It saves the normal browser download, safely extracts ZIP files, matches every MP3 filename against the canonical track titles from TKKGData, and rejects missing, duplicate, ambiguous, empty, or unexpected tracks. The existing FFmpeg merger runs only after the complete tracklist passes validation.

Example output:

    output/TKKG 150 - Heiße Nächte im Dezember.mp3

Existing files are skipped by default. Use --overwrite to replace them. The default provider retains episode range processing and per-episode error reporting.

Make sure you have the rights and permissions required for any audio you download. Spotisaver permission and usage limits are separate from the downloader's technical checks.

## Tests

Run the automated tests:

    py -m unittest discover -s tests -v

Tests use mocked browser and download behaviour or synthetic ZIP fixtures. They do not download real recordings.

## Project workflow

See [Requests](requests/README.md), the [Knowledge Base](docs/knowledge/README.md), and [Request 006](requests/006-spotisaver-import-workflow/request.md).
