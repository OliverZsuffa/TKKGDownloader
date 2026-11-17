# Implementation plan: Request 019

## Status

Implemented. All CI checks passed on the final branch head.

## 1. Inspect and preserve current behaviour

1. Review the current CLI parser, Spotisaver browser lifecycle, progress reporter, test fixtures, README, and Knowledge Base.
2. Identify every call path that launches Chromium and every call path that emits progress stage messages.
3. Keep existing provider selection, output naming, overwrite protection, diagnostic mode, and episode validation unchanged unless explicitly required by Request 019.

## 2. Fix the progress transition

1. Trace the phase transition in `_download_click()` where the first track progress is reported and the `Downloading...` stage is emitted. The current loop updates the progress reporter before it emits the phase message, which can freeze the first line.
2. Emit each phase message before the first progress update for that phase, so it cannot terminate an active progress line.
3. Fix in-place terminal rendering so shorter lines erase the remainder of the previous line. Prefer a portable strategy that works in supported Windows terminals and does not count ANSI colour escape sequences as visible characters.
4. Inspect the raw ETA fields returned by `_read_download_modal()` and the current live page structure. Normalize numeric text before formatting. Handle seconds-only values as `40s` and minute-plus-second values as `2m 05s`; reject malformed values cleanly.
5. Keep `_ProgressReporter.stage()` semantics intact for other stages unless tests demonstrate a broader issue.
6. Add focused tests for stage ordering, line clearing, exact output for shorter replacement lines, ETA DOM value variants, malformed values, and final newline behaviour.
7. Preserve non-TTY output throttling and queue-wait behaviour.

## 3. Add ZIP transfer progress

1. Confirm the Chromium DevTools Protocol events available in the Playwright version used by the project. Use a CDP session attached to the page or browser context and enable download progress events without replacing Playwright's existing accepted-download handling.
2. Listen for `Browser.downloadWillBegin` and `Browser.downloadProgress`. Correlate the event GUID with the ZIP download initiated by the verified Download ZIP control. Ignore unrelated downloads.
3. Render a separate transfer progress line using `receivedBytes` and `totalBytes`. Show bytes and percentage only when the total is positive. Until then, show an indeterminate transfer state rather than a fabricated percentage.
4. Treat the CDP `completed` event and Playwright's download event as complementary signals. Continue to call the existing `save_as()` and validate the saved archive exactly as before.
5. If the protocol event cannot be enabled or the browser does not report a total, log the limitation and fall back to the current wait-for-download-event behaviour without failing the download.
6. Add mocked tests for progress updates, unknown total size, completion, unrelated download GUIDs, and unavailable CDP support.

## 4. Add browser runtime options

1. Extend the Spotisaver provider call with explicit browser visibility and audio settings.
2. Launch Chromium with `headless=True` by default and `headless=False` when `show_browser` is enabled.
3. Use Playwright's Chromium launch option `args=["--mute-audio"]` when browser audio should be muted.
4. Omit the mute argument only when the effective setting explicitly enables browser audio.
5. Keep the existing browser context download handling and guaranteed `browser.close()` cleanup.
6. Add mocked Playwright tests asserting the launch arguments for default, visible, and unmuted modes.

## 5. Introduce configuration loading

1. Add a small configuration module using Python's standard-library `tomllib`.
2. Resolve the default configuration path using the Windows roaming application data directory, with a documented XDG-style fallback on other platforms.
3. Parse only the supported settings: `default_provider`, `output_dir`, `show_browser`, and `mute_browser_audio`.
4. Validate types and allowed provider values. Resolve relative output paths consistently from the current working directory, matching today's `./output` behaviour.
5. Treat a missing file as an empty configuration. Treat malformed, unreadable, or invalid configuration as an actionable error rather than silently ignoring it.
6. Support `--config PATH` to load an alternate file.
7. Keep the configuration file user-owned and outside the repository. Do not automatically write machine-specific paths into Git.

## 6. Integrate configuration with the CLI

1. Change argparse defaults for configurable options to `None`, preserving whether the user explicitly supplied each option.
2. Resolve each effective setting in one place using command-line value, then config value, then built-in default.
3. Add `--show-browser` and `--unmute-browser` as explicit one-run overrides.
4. Pass the resolved browser options only to the Spotisaver provider.
5. Preserve `--diagnostic-dir` validation and the single-episode Spotisaver restriction.
6. Ensure explicit command-line options win even when the configuration file contains conflicting values.

## 7. Documentation

1. Update README usage examples for headless default operation and `--show-browser`.
2. Document browser audio muting and the `--unmute-browser` override.
3. Add the configuration file path and a complete TOML example.
4. Explain configuration precedence and how to use `--config`.
5. Update the project Knowledge Base and request index.

## 8. Verification

1. Run Python compilation.
2. Run focused tests for progress reporting, CLI resolution, configuration parsing, and Playwright launch arguments.
3. Run the complete unittest suite.
4. Run the TKKGData contract smoke test and all CI checks.
5. Inspect the final diff for accidental changes to download, queue, matching, merging, or output behaviour. The existing Playwright save flow and archive validation remain intact.
6. No live Spotisaver download was performed for this implementation.

## 9. Delivery

1. Implement on a dedicated feature branch after approval.
2. Commit the implementation and test results.
3. Open a pull request and inspect CI.
4. Report the PR and verification results.
5. Merge only after Oliver's explicit approval.

## Decisions retained

- Existing built-in defaults remain `yt-dlp` and `./output`.
- Browser visibility defaults to headless.
- Browser audio defaults to muted.
- Command-line arguments override configuration.
- The configuration file is optional and is not created automatically.
