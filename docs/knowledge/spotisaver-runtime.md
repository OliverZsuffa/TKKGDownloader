Spotisaver runtime configuration
==================================

Spotisaver uses Playwright Chromium through the public album page. The browser runs headlessly and muted by default. The --show-browser option displays the window for troubleshooting, while --unmute-browser enables page audio for a single run.

The optional user-level TOML file is stored at:

* Windows: %APPDATA%/TKKGDownloader/config.toml
* Linux and macOS: $XDG_CONFIG_HOME/tkkgdownloader/config.toml, falling back to ~/.config/tkkgdownloader/config.toml

Supported settings:

    default_provider = "yt-dlp"
    output_dir = "./output"
    show_browser = false
    mute_browser_audio = true

The file is not created automatically. Missing configuration is normal. Invalid TOML, unknown keys, and invalid values are reported instead of silently ignored. Explicit CLI arguments take precedence over the file, which takes precedence over built-in defaults.

The Spotisaver track progress and ZIP transfer are separate phases. ZIP transfer uses one progress display. In interactive terminals it updates in place; redirected output emits the final transfer state once rather than printing a separate line for every event. ZIP transfer percentage is displayed only when Chromium reports a positive total byte count through its DevTools download progress events. When CDP reports completion, Chromium's downloaded file is used directly and checked for a non-zero, stable size. Playwright's save_as path remains the fallback when CDP download events are unavailable.

Archive preparation uses the website's reported progress while the archive is being created. When the website reports that the ZIP has been created, the preparation stage is explicitly completed at 100%. This avoids leaving the stage at 90% after the website has finished.

After download, progress is also shown for archive extraction, reading embedded track metadata, matching tracks against TKKGData, checking source integrity, and copying verified tracks. Audio merging uses FFmpeg's machine-readable progress output and the summed source duration to calculate a measured percentage. PCM conversion, concatenation, and MP3 encoding expose their own progress when that merge strategy is needed. Final metadata and full audio verification are reported as separate stages. Stages without a reliable measurable unit remain status messages instead of displaying invented percentages.

A monotonic timer measures the complete Spotisaver episode operation. Elapsed time appears alongside active progress and the final total is reported on success or failure.
