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

The Spotisaver track progress and final ZIP transfer are separate phases. ZIP transfer percentage is displayed only when Chromium reports a positive total byte count through its DevTools download progress events. If those events are unavailable, the normal Playwright download event and archive validation continue without a fabricated percentage.
