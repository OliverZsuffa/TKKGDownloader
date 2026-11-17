# Request 019: Improve Spotisaver browser experience and downloader defaults

## Status

Implementation in progress

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
- Clear leftover characters from the previous terminal line whenever a shorter progress update replaces a longer one. This must prevent fragments such as `90%40 tracks 98%`.
- Print phase messages before the first progress update for that phase, or otherwise ensure that stage transitions do not finalise an active progress line unexpectedly.
- Correct ETA parsing and formatting so seconds-only estimates appear as `ETA 40s`, while estimates containing minutes appear as `ETA 2m 05s`. Never append duplicated unit suffixes.
- Inspect the actual Spotisaver DOM values for ETA components. Parse numeric values robustly and treat missing, malformed, or out-of-range values as unavailable rather than displaying corrupted text.
- Preserve concise output, colour handling, queue-wait display, non-interactive reporting, and final newline behaviour.
- Do not change download detection, queue handling, retry behaviour, or track progress calculations.

### 2. ZIP file transfer progress

- Add a separate progress display for the actual ZIP transfer from Spotisaver to the local computer, after the website reports that the archive is ready and the normal Download ZIP control is clicked.
- Use Chromium's supported DevTools download progress events through Playwright's CDP session, correlating the download event with the browser download already being awaited by the existing workflow.
- Display received bytes, total bytes, and percentage when Chromium supplies a valid non-zero total. Keep the display indeterminate when the total size is not yet known.
- Keep the website's track-processing progress and the browser's ZIP-transfer progress as distinct phases. Do not combine their percentages.
- If progress events are unavailable or unsupported, retain the existing wait-for-download-event behaviour and report that transfer progress is unavailable. Never invent or estimate a percentage from elapsed time.
- Continue saving and validating the archive through the existing Playwright download flow. The new progress display must not change download handling or validation.

### 3. Browser visibility

- Launch Spotisaver Chromium in headless mode by default.
- Add `--show-browser` to launch a normal visible browser window for a run.
- Keep browser visibility limited to the Spotisaver provider. The yt-dlp provider must not launch a browser.
- Ensure browser closure and exception cleanup work in both modes.
- Continue using normal Playwright page interactions and browser download events. Do not add stealth settings or bypass site restrictions.

### 4. Browser audio

- Mute Chromium audio by default so website sounds do not play during unattended background operation.
- Provide an explicit `--unmute-browser` override for the uncommon case where audible page output is useful.
- Apply the setting at browser launch and verify the correct Playwright launch option is used.
- Do not change operating-system audio settings or mute other applications.

### 5. User-level configuration

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

### 6. CLI behaviour and compatibility

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

- [ ] Interactive Spotisaver track progress uses one continuously updating line through phase transitions.
- [ ] Shorter progress updates clear stale characters left by longer previous updates.
- [ ] ETA formatting correctly handles seconds-only and minute-plus-second values, and malformed DOM values are safely ignored.
- [ ] Tests cover progress line clearing, phase transitions, ETA parsing, and ETA formatting.
- [ ] After the ZIP is ready, a distinct transfer progress display reports actual received and total bytes when Chromium exposes them.
- [ ] Transfer progress remains indeterminate when total size is unavailable and never fabricates a percentage.
- [ ] If CDP progress events are unavailable, the existing download event workflow still completes correctly.
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

## Decisions

- Retain the existing built-in defaults: `yt-dlp` and `./output`.
- Keep the configuration file optional and do not create it automatically.
- Browser visibility defaults to headless, and browser audio defaults to muted.
