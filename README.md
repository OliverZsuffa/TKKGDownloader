# TKKGDownloader

A Windows friendly command line tool that creates one MP3 file per TKKG audio drama episode.

## Requirements

- Python 3.11 or newer
- spotDL
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
    python tkkg.py 1

You can also use the installed command:

    tkkg 1

## Usage

Download one episode:

    python tkkg.py 1

Download an inclusive range:

    python tkkg.py 1-10

Accept the selected release without a confirmation prompt:

    python tkkg.py 1 --yes

Choose another output folder:

    python tkkg.py 1 --output-dir "D:\\Music\\TKKG"

Replace an existing output:

    python tkkg.py 1 --overwrite

Get help:

    python tkkg.py --help

## What it does

The current implementation retrieves episode metadata from TKKGTracker, resolves Spotify metadata with spotDL, downloads matching YouTube audio, validates track order, and merges the tracks with FFmpeg.

The target architecture is to retrieve episode and verified Spotify and YouTube Music source mappings from [TKKGData](https://github.com/OliverZsuffa/TKKGData). TKKGData will own scraping, source discovery, verification, and the shared dataset. TKKGDownloader will remain responsible for downloading and merging audio.

This migration is proposed in [Request 004](requests/004-tkkgdata-consumer/request.md) and has not yet been implemented. Until the migration is approved and verified, the current implementation and data source remain in effect.

spotDL does not download audio directly from Spotify. It uses Spotify metadata to identify tracks and finds matching audio on YouTube. Make sure you have the rights and permissions required for any audio you download.

## Output

For example:

    output/TKKG 001 - Die Jagd nach den Millionendieben.mp3

Existing files are skipped by default. Use --overwrite to replace them.

## Tests

Run the automated tests:

    py -m unittest discover -s tests -v

## Project workflow

See [Requests](requests/README.md) and the [Knowledge Base](docs/knowledge/README.md).
