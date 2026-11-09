# TKKGDownloader

A Windows friendly command line tool that creates one MP3 file per TKKG audio drama episode.

## Requirements

- Python 3.11 or newer
- spotDL 4.5.2 or a compatible version
- FFmpeg 4.2 or newer, available on PATH
- Deno is recommended by spotDL for some YouTube downloads

Install spotDL:

    py -m pip install --upgrade spotdl

Check that both external tools are available:

    spotdl --version
    ffmpeg -version

## Run from a repository checkout

Open PowerShell in the project folder:

    py -m pip install -e .
    python tkkg.py 150

You can also use the installed command:

    tkkg 150

## Usage

Download one episode:

    python tkkg.py 1

Download an inclusive range:

    python tkkg.py 1-10

Skip the merge confirmation after verified source selection:

    python tkkg.py 150 --yes

Choose another output folder:

    python tkkg.py 1 --output-dir "D:\\Music\\TKKG"

Replace an existing output:

    python tkkg.py 1 --overwrite

Get help:

    python tkkg.py --help

## Data ownership

[TKKGData](https://github.com/OliverZsuffa/TKKGData) is the single source of truth for episode metadata, verified Spotify releases, YouTube Music playlist URLs, individual song URLs, and source verification.

TKKGDownloader fetches the published TKKGData episode array and its dataset metadata. It does not read the TKKGTracker catalogue, scrape sources, search for Spotify albums, discover YouTube matches, or write metadata back to TKKGData.

The dataset contains a verified Spotify album URL and, where available, a verified YouTube Music playlist URL. It also stores exact Spotify track URLs paired with individual YouTube Music song URLs. The downloader prefers the verified playlist and Spotify album pairing. If that path fails or the playlist is unavailable, it falls back to the exact individual track pairs. It never falls back to unverified text search.

If an episode has no complete verified audio mapping, the downloader stops with an actionable error. Audio discovery and correction belong in TKKGData.

## Download and output

The downloader uses spotDL to retrieve the exact source pairings, validates the downloaded track count and contiguous order against TKKGData, then merges the tracks with FFmpeg.

For example:

    output/TKKG 150 - Heiße Nächte im Dezember.mp3

Existing files are skipped by default. Use --overwrite to replace them. Episode range processing reports failures per episode and continues with the remaining requested episodes.

spotDL uses Spotify metadata and downloads audio from the explicitly paired YouTube source. Make sure you have the rights and permissions required for any audio you download.

## Tests

Run the automated tests:

    py -m unittest discover -s tests -v

The tests mock network and subprocess calls. They do not download real audio.

## Project workflow

See [Requests](requests/README.md), the [Knowledge Base](docs/knowledge/README.md), and [Request 004](requests/004-tkkgdata-consumer/request.md).
