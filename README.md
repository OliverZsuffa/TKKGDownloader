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

Use Spotisaver for one episode. Chromium runs in the background by default:

    py tkkg.py 150 --provider spotisaver

Show the browser window when troubleshooting:

    py tkkg.py 150 --provider spotisaver --show-browser

Browser audio is muted by default. Use --unmute-browser only when audible page output is useful.

Run the quality-first diagnostic workflow in a new, empty directory:

    py tkkg.py 150 --provider spotisaver --diagnostic-dir "D:\TKKG\episode-150-diagnostics"

Diagnostic mode preserves the original Spotisaver archive, extracted source files, and validated numbered tracks. It fully decodes every source, records FFprobe metadata and silence indicators, compares the legacy stream-copy merger with a PCM master encoded once at 320 kbit/s, extracts and verifies embedded cover artwork and ID3 metadata, and creates a lossless review file for every track transition. It writes JSON and readable reports under the diagnostic directory. The two MP3 candidates are diagnostic outputs only. It does not replace or create the normal final episode file. The diagnostic directory must be new or empty. Existing files are never overwritten. Keep the workspace until the source and boundary review is complete. This workflow runs locally and is intentionally not part of GitHub Actions.

Download an inclusive range with the default provider:

    py tkkg.py 1-10

Choose another output folder:

    py tkkg.py 1 --output-dir "D:\\Music\\TKKG"

Replace an existing output:

    py tkkg.py 1 --overwrite

Get help:

    py tkkg.py --help

Normal Spotisaver downloads now reuse the diagnostic artwork and metadata implementation. They extract the first valid embedded JPEG or PNG in canonical track order, preserve its original bytes, write the episode title, verified album title, and consistent source tags, then read back and verify the result. The merged candidate is fully decoded and probed after metadata finalization and only then moved into the final output path. If no source cover exists, this is reported clearly and no replacement image is invented. Queue waiting uses one cumulative in-place line in interactive terminals, and ETA supports both seconds-only and minutes-plus-seconds displays.

Spotisaver mode accepts exactly one episode per invocation. Run it separately for each episode. It launches Chromium headlessly and muted by default. Use --show-browser to display the browser or --unmute-browser to enable its audio. It polls for the actual `#downloadAllBtn` control immediately after the page body appears. It checks every second for up to 120 seconds and clicks the visible, enabled `Download entire playlist` button as soon as it is ready, without scrolling or waiting for all track titles to appear in the page text. If the button never appears, it records page and control diagnostics in the run log. Only then may it use the intermediate `Download Playlist` scroll control and poll briefly again.

The normal terminal output shows the browser opening, queue state, track download progress, archive preparation, one ZIP transfer progress bar, archive extraction, metadata reading, track matching, source integrity checks, copying verified tracks, audio merging, metadata finalization, and final audio verification. Progress is measured in track or archive-member counts where possible. FFmpeg progress is read from its machine-readable progress output and converted to a percentage using the probed source duration. Stages without measurable progress are reported as activity messages rather than fabricated percentages. Interactive terminals update the active progress line in place. Redirected output avoids printing repeated ZIP transfer bars and reports the final transfer state once. The total elapsed time is shown alongside progress and reported when the episode completes or stops. Completed progress is green, remaining progress is grey, informational messages are cyan, queue waits are yellow, and errors are red. Colour is disabled when the terminal does not support it, output is redirected, or `NO_COLOR` is set. Messages remain understandable without colour.

Detailed browser diagnostics, selector information, modal snapshots, retry decisions, download events, temporary paths, and tracebacks are written to a unique timestamped log for each run. On Windows, logs are stored under `%USERPROFILE%\TKKGDownloader\logs`. This avoids Microsoft Store Python redirecting writes into its private package directory. On other platforms they are stored under `~/.local/state/tkkgdownloader/logs`, or the directory configured by `XDG_STATE_HOME`. If Spotisaver explicitly reports that all download slots are busy, the provider waits for the configured queue retry interval (25 seconds by default), checks that the rejection is still active, closes the visible modal, confirms that it has closed, verifies the download button is available, and clicks it again. After five consecutive retries have themselves been explicitly rejected (configurable), it reloads the complete album page, verifies the expected album URL, waits for the real download button, and submits a fresh request. The retry counter resets after a successful reload. It repeats only after another explicit queue rejection. If the queue notice disappears without positive processing evidence, the provider treats the state as unconfirmed and keeps monitoring without claiming that a slot was acquired. It reports slot acquisition only after actual non-zero track progress, an explicit processing or slot-acquired status, or ZIP creation begins. The initial "Downloading playlist..." status is provisional for five seconds to allow a delayed queue rejection to appear. If it remains visible without rejection for the full confirmation window, it counts as acceptance. A zero-percent progress bar alone is not sufficient. Generic errors and slow processing do not trigger retries. The browser download listener remains active through queue retries, processing, ZIP creation, and the final ZIP click. After the browser download event confirms that the transfer started, the provider waits for the matching Chromium DevTools download to complete. The transfer has a 120-second inactivity timeout that resets whenever received bytes increase, not a 30-second total deadline. Explicit cancellation fails immediately, and diagnostics include received and expected bytes. After completion, the downloaded file gets a separate 30-second window to become non-empty and stable. The provider then safely extracts the archive and validates every track against TKKGData before automatic merging. ETA is informational only. Ctrl+C cancels cleanly. It does not use private endpoints, hidden APIs, stealth browser settings, or access-control workarounds. If the website changes its interface or presents a restriction, the run stops.

## User configuration

The optional TOML configuration file is stored outside the repository. On Windows the default path is %APPDATA%/TKKGDownloader/config.toml. On Linux and macOS it is $XDG_CONFIG_HOME/tkkgdownloader/config.toml, falling back to ~/.config/tkkgdownloader/config.toml.

Example:

    default_provider = "yt-dlp"
    output_dir = "./output"
    show_browser = false
    mute_browser_audio = true
    queue_retry_interval_seconds = 25
    queue_reload_after_retries = 5

Supported keys are default_provider (yt-dlp or spotisaver), output_dir (a path), show_browser (boolean), mute_browser_audio (boolean), queue_retry_interval_seconds (positive integer), and queue_reload_after_retries (positive integer). The queue retry interval controls how long the provider waits after an explicit queue rejection. The reload threshold counts consecutive retries that were themselves explicitly rejected. After the threshold, the full album page is reloaded and the retry counter resets. Unconfirmed states and generic errors do not trigger retries or reloads. The file is optional and is not created automatically. A missing file is ignored. Malformed TOML, unknown keys, invalid types, and unsupported provider names produce an actionable error.

Settings are resolved in this order: explicit command-line arguments, the configuration file, then built-in defaults. The built-in defaults are yt-dlp, ./output, a hidden browser, and muted browser audio. Use --config PATH to select another configuration file. --provider and --output-dir override their configured values for one run. --show-browser displays Chromium for one run, and --unmute-browser enables browser audio for one run.

## Data ownership

[TKKGData](https://github.com/OliverZsuffa/TKKGData) is the single source of truth for episode metadata, verified Spotify releases, YouTube Music playlist URLs, individual song URLs, and source verification.

TKKGDownloader fetches the published TKKGData episode array and dataset metadata. It does not read the TKKGTracker catalogue, scrape sources, search for Spotify albums, discover YouTube matches, or write metadata back to TKKGData.

## Download and output

The default provider invokes yt-dlp once per exact verified YouTube Music track URL, extracts MP3 audio at 192 kbit/s, validates every expected file, then automatically merges the tracks with FFmpeg. The merger probes every source first. It uses stream copy only when codec, sample rate, channel count, and channel layout agree and the completed file passes a full decode and duration check. Otherwise it decodes each track to 24-bit PCM at a common sample rate and channel count, concatenates the PCM segments, and encodes one 320 kbit/s MP3. The final output must decode successfully and remain within a track-count-adjusted duration tolerance of the summed source durations. No merge confirmation is required.

The Spotisaver provider uses Playwright to operate the public album page in Chromium. It saves the normal browser download, safely extracts ZIP files, and identifies every MP3 using layered deterministic evidence. It first checks exact normalized filenames, including recognised provider wrappers such as `TKKG - ... (SPOTISAVER)`, then exact embedded ID3 titles, then a matching embedded album and track number together. Verified alternate titles may be supplied through an `alternate_titles` list on a track record when the upstream data contract supports it. Track number alone is never sufficient. Partial and fuzzy matches are never used for automatic assignment. Ambiguous files are rejected. It rejects missing, duplicate, ambiguous, empty, unexpected, non-contiguous, or byte-identical source tracks before merging. Embedded ID3 title and track-number disagreements are recorded as warnings and never override TKKGData. A SHA-256 manifest records the exact source-to-canonical mapping and the evidence used for each match and verifies copied files again immediately before merging. In normal mode the manifest stays in memory. In diagnostic mode it is preserved as reports/track-manifest.json and incorporated into the R13 source inspection report. The FFmpeg merger runs automatically only after the complete tracklist passes validation.

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
