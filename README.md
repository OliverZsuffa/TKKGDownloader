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

Choose another output folder:

    py tkkg.py 1 --output-dir "D:\\Music\\TKKG"

Replace an existing output:

    py tkkg.py 1 --overwrite

Get help:

    py tkkg.py --help

Spotisaver mode accepts exactly one episode per invocation. Run it separately for each episode. It opens a visible browser and polls for the actual `#downloadAllBtn` control immediately after the page body appears. It checks every second for up to 120 seconds and clicks the visible, enabled `Download entire playlist` button as soon as it is ready, without scrolling or waiting for all track titles to appear in the page text. If the button never appears, it logs page and control diagnostics. Only then may it use the intermediate `Download Playlist` scroll control and poll briefly again. While Spotisaver processes the playlist, the terminal shows a pip-style progress bar with completed tracks, percentage, and ETA when available. The bar updates in place in interactive terminals and falls back to concise periodic lines elsewhere. Once the modal reports `ZIP archive created.`, the provider finds the visible, enabled `Download ZIP` link inside that modal and clicks it exactly once. The browser download listener is registered before the initial album request and remains active through queue retries, processing, ZIP creation, and the final ZIP click. The provider waits for the actual browser download event without a fixed timeout, saves the archive, safely extracts it, and validates every track against TKKGData before merging. ETA is informational only. If Spotisaver explicitly reports that all download slots are busy, the provider waits 30 seconds, checks that the rejection is still active, closes the visible modal, confirms that it has closed, verifies the download button is available, and clicks it again. It repeats only after another explicit queue rejection. If the queue notice clears into processing, it does not retry. Generic errors and slow processing do not trigger retries. Timestamped diagnostics retain meaningful state transitions, selector decisions, retry decisions, browser download events, suggested filename, save destination, file size, and elapsed time. Ctrl+C cancels cleanly, and page closure or an explicit site failure is reported. If the final ZIP button cannot be uniquely identified, the run stops with modal and visible-control diagnostics. It does not use private endpoints, hidden APIs, stealth browser settings, or access-control workarounds. If the website changes its interface or presents a restriction, the run stops.

## Data ownership

[TKKGData](https://github.com/OliverZsuffa/TKKGData) is the single source of truth for episode metadata, verified Spotify releases, YouTube Music playlist URLs, individual song URLs, and source verification.

TKKGDownloader fetches the published TKKGData episode array and dataset metadata. It does not read the TKKGTracker catalogue, scrape sources, search for Spotify albums, discover YouTube matches, or write metadata back to TKKGData.

## Download and output

The default provider invokes yt-dlp once per exact verified YouTube Music track URL, extracts MP3 audio at 192 kbit/s, validates every expected file, then automatically merges the tracks with FFmpeg. No merge confirmation is required.

The Spotisaver provider uses Playwright to operate the public album page in visible Chromium. It saves the normal browser download, safely extracts ZIP files, matches every MP3 filename against the canonical track titles from TKKGData, and rejects missing, duplicate, ambiguous, empty, or unexpected tracks. The FFmpeg merger runs automatically only after the complete tracklist passes validation.

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
