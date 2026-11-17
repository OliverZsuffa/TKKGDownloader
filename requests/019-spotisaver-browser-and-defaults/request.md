# Request 019: Improve Spotisaver browser experience and downloader defaults

## Status

Proposed

## Objective

Make normal Spotisaver downloads quieter and less intrusive, fix the duplicate progress bar display, and allow frequently used downloader settings to be configured once instead of supplied on every invocation.

## User experience

The normal Spotisaver workflow runs Chromium in the background with audio muted. The user can opt into a visible browser for troubleshooting with `--show-browser`.

The downloader reads defaults from a user-level configuration file. Command-line arguments always take precedence, so one-off overrides remain straightforward.

Examples:

```powershell
# Use configured defaults
py tkkg.py 150

# Show the Spotisaver browser for this run
py tkkg.py 150 --show-browser

# Override the configured provider or output folder for one run
py tkkg.py 150 --provider yt-dlp --output-dir "D:\\Music\\TKKG"
```

## Functional requirements

### 1. Progress display

- Fix the transition into the Spotisaver track-download phase so the progress bar remains a single in-place line in interactive terminals.
- Print the `Downloading...` stage before the first progress bar update, or otherwise ensure that the stage transition does not finalise an already active progress line.
- Preserve the existing concise output, colour handling, queue-wait display, non-interactive reporting, and final newline behaviour.
- Do not change download detection, queue handling, retry behaviour, or progress calculations.

### 2. Browser visibility

- Launch Spotisaver Chromium in headless mode by default.
- Add `--show-browser` to launch a normal visible browser window for a run.
- Keep browser visibility limited to the Spotisaver provider. The yt-dlp provider must not launch a browser.
- Ensure browser closure and exception cleanup work in both modes.
- Continue using normal Playwright page interactions and browser download events. Do not add stealth settings or bypass site restrictions.

### 3. Browser audio

- Mute Chromium audio by default so website sounds do not play during unattended background operation.
- Provide an explicit `--unmute-browser` override for the uncommon case where audible page output is useful.
- Apply the setting at browser launch and verify the correct Playwright launch option is used.
- Do not change operating-system audio settings or mute other applications.

### 4. User-level configuration

- Add a user-level TOML configuration file, separate from the repository and downloaded audio.
- On Windows, use `%APPDATA%\\TKKGDownloader\\config.toml`. Provide a documented platform-appropriate fallback for other operating systems.
- Support at least these settings:
  - `default_provider`
  - `output_dir`
  - `show_browser`
  - `mute_browser_audio`
- Use the precedence order: explicit command-line argument, configuration file, built-in default.
- Keep the existing built-in defaults unless Oliver specifies different initial values: provider `yt-dlp`, output directory `./output`, browser hidden, browser audio muted.
- Allow an optional `--config PATH` argument to select a different configuration file.
- Validate configuration values and report a clear error for invalid provider names, invalid types, malformed TOML, or unreadable configuration files.
- Missing configuration files must be normal and must not produce warnings.
- Do not store credentials, cookies, or browser session data in the configuration file.
- Document the file location, supported keys, example contents, and precedence in the README.

### 5. CLI behaviour and compatibility

- Preserve existing explicit flags such as `--provider`, `--output-dir`, `--overwrite`, and `--diagnostic-dir`.
- Make parser defaults distinguish between an omitted option and an explicitly supplied option, so configuration values are not accidentally overwritten by argparse defaults.
- Keep existing episode range validation and the Spotisaver single-episode restriction.
- Preserve current output paths and provider behaviour when no configuration file exists and no new flags are supplied.

## Constraints

- TKKGData remains the sole source of truth for episode and track metadata.
- Spotisaver downloads remain user-initiated and limited to one episode per invocation.
- No private endpoints, hidden APIs, stealth plugins, CAPTCHA bypass, login bypass, access-control workarounds, or anti-automation evasion.
- No changes to audio matching, validation, merging, metadata, or overwrite safeguards.
- Configuration is local to the user and must not be committed with personal paths.

## Out of scope

- A graphical settings interface.
- Automatic configuration migration from undocumented locations.
- Changing the default provider from yt-dlp without Oliver's explicit preference.
- Muting the entire operating system or other applications.
- Keeping the browser open after a run.

## Acceptance criteria

- [ ] Interactive Spotisaver progress uses one continuously updating progress line through the transition into track downloading.
- [ ] Progress output tests cover the stage transition and confirm that the old progress line is not left behind.
- [ ] Spotisaver launches headless by default.
- [ ] `--show-browser` launches visible Chromium.
- [ ] Browser audio is muted by default.
- [ ] `--unmute-browser` enables browser audio for that run.
- [ ] User-level TOML settings are loaded correctly.
- [ ] CLI arguments override configuration values.
- [ ] Configuration values override built-in defaults.
- [ ] Missing configuration is handled silently.
- [ ] Invalid configuration produces a clear actionable error.
- [ ] Existing CLI behaviour and episode validation remain compatible.
- [ ] Unit tests cover configuration loading, precedence, validation, browser launch options, and progress output.
- [ ] README documents the new browser options and configuration file.
- [ ] Python compilation and the complete automated test suite pass.
- [ ] The TKKGData contract smoke test and all existing CI checks pass.

## Open questions

- Confirm the initial configured default provider and output directory. The proposal retains the current defaults, `yt-dlp` and `./output`, until Oliver chooses otherwise.
- Confirm whether the configuration file should be created automatically with commented example settings, or simply documented for manual creation.
