# TKKGDownloader

A Windows friendly command line tool that creates one MP3 file per TKKG audio drama episode.

## Requirements

- Python 3.11 or newer
- [spotDL](https://spotdl.readthedocs.io/en/latest/)
- FFmpeg 4.2 or newer, available on PATH
- Deno is recommended by spotDL for some YouTube downloads

Install spotDL:

```powershell
py -m pip install --upgrade spotdl
```

Check that both external tools are available:

```powershell
spotdl --version
ffmpeg -version
```

If FFmpeg is not installed, follow the [spotDL installation guide](https://spotdl.readthedocs.io/en/latest/installation/).

## Run from a repository checkout

Open PowerShell in the project folder:

```powershell
py -m pip install -e .
python tkkg.py 1
```

You can also use the installed command:

```powershell
tkkg 1
```

## Usage

Download one episode:

```powershell
python tkkg.py 1
```

Download an inclusive range:

```powershell
python tkkg.py 1-10
```

Accept the release selected by spotDL without a confirmation prompt:

```powershell
python tkkg.py 1 --yes
```

Choose another output folder:

```powershell
python tkkg.py 1 --output-dir "D:\\Music\\TKKG"
```

Replace an existing output:

```powershell
python tkkg.py 1 --overwrite
```

Get help:

```powershell
python tkkg.py --help
```

## What it does

1. Downloads the current episode catalog from [TKKGTracker](https://github.com/OliverZsuffa/TKKGtracker).
2. Gets the official episode title for the requested episode number.
3. Builds an album search query containing the episode number and title.
4. Passes the query to spotDL, which resolves Spotify metadata and searches YouTube for matching audio.
5. Saves the selected album tracks as MP3 files in a temporary directory.
6. Shows the selected release and ordered track list for confirmation.
7. Uses FFmpeg to merge the tracks into one MP3.
8. Writes the finished file to `output/` by default.

**Important:** spotDL does not download audio directly from Spotify. It uses Spotify metadata to identify tracks and finds matching audio on YouTube. Make sure you have the rights and permissions required for any audio you download.

The TKKGTracker `tracks` field is deliberately not used for track selection. It contains chapter information and does not reliably match Spotify's release track divisions.

## Output

For example:

`output/TKKG 001 - Die Jagd nach den Millionendieben.mp3`

Existing files are skipped by default. Use `--overwrite` to replace them.

## Tests

Run the automated tests:

```powershell
py -m unittest discover -s tests -v
```

## Project workflow

See [Requests](requests/README.md) and the [Knowledge Base](docs/knowledge/README.md).
