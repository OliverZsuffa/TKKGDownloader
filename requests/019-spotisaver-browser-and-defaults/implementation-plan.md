# Implementation plan: Request 019

## Status

Proposed. Waiting for Oliver's approval.

## 1. Inspect and preserve current behaviour

1. Review the current CLI parser, Spotisaver browser lifecycle, progress reporter, test fixtures, README, and Knowledge Base.
2. Identify every call path that launches Chromium and every call path that emits progress stage messages.
3. Keep existing provider selection, output naming, overwrite protection, diagnostic mode, and episode validation unchanged unless explicitly required by Request 019.

## 2. Fix the progress transition

1. Trace the phase transition in `_download_click()` where the first track progress is reported and the `Downloading...` stage is emitted.
2. Move the stage message before the first progress update for that phase, so it cannot terminate an already active progress line.
3. Keep `_ProgressReporter.stage()` semantics intact for other stages unless tests demonstrate a broader issue.
4. Add focused tests for the transition. Verify that the stage is emitted once before progress, subsequent progress updates overwrite the same line, and finalisation emits exactly one newline.
5. Preserve non-TTY output throttling and queue-wait behaviour.

## 3. Add browser runtime options

1. Extend the Spotisaver provider call with explicit browser visibility and audio settings.
2. Launch Chromium with `headless=True` by default and `headless=False` when `show_browser` is enabled.
3. Use Playwright's Chromium launch option `args=["--mute-audio"]` when browser audio should be muted.
4. Omit the mute argument only when the effective setting explicitly enables browser audio.
5. Keep the existing browser context download handling and guaranteed `browser.close()` cleanup.
6. Add mocked Playwright tests asserting the launch arguments for default, visible, and unmuted modes.

## 4. Introduce configuration loading

1. Add a small configuration module using Python's standard-library `tomllib`.
2. Resolve the default configuration path using the Windows roaming application data directory, with a documented XDG-style fallback on other platforms.
3. Parse only the supported settings: `default_provider`, `output_dir`, `show_browser`, and `mute_browser_audio`.
4. Validate types and allowed provider values. Resolve relative output paths consistently from the current working directory, matching today's `./output` behaviour.
5. Treat a missing file as an empty configuration. Treat malformed, unreadable, or invalid configuration as an actionable error rather than silently ignoring it.
6. Support `--config PATH` to load an alternate file.
7. Keep the configuration file user-owned and outside the repository. Do not automatically write machine-specific paths into Git.

## 5. Integrate configuration with the CLI

1. Change argparse defaults for configurable options to `None`, preserving whether the user explicitly supplied each option.
2. Resolve each effective setting in one place using command-line value, then config value, then built-in default.
3. Add `--show-browser` and `--unmute-browser` as explicit one-run overrides.
4. Pass the resolved browser options only to the Spotisaver provider.
5. Preserve `--diagnostic-dir` validation and the single-episode Spotisaver restriction.
6. Ensure explicit command-line options win even when the configuration file contains conflicting values.

## 6. Documentation

1. Update README usage examples for headless default operation and `--show-browser`.
2. Document browser audio muting and the `--unmute-browser` override.
3. Add the configuration file path and a complete TOML example.
4. Explain configuration precedence and how to use `--config`.
5. Update the project Knowledge Base and request index.

## 7. Verification

1. Run Python compilation.
2. Run focused tests for progress reporting, CLI resolution, configuration parsing, and Playwright launch arguments.
3. Run the complete unittest suite.
4. Run the TKKGData contract smoke test and all CI checks.
5. Inspect the final diff for accidental changes to download, queue, matching, merging, or output behaviour.
6. Do not claim a live Spotisaver download was tested unless one is actually performed.

## 8. Delivery

1. Implement on a dedicated feature branch after approval.
2. Commit the implementation and test results.
3. Open a pull request and inspect CI.
4. Report the PR and verification results.
5. Merge only after Oliver's explicit approval.

## Decisions retained

- Existing built-in defaults remain `yt-dlp` and `./output` unless Oliver chooses different values.
- Browser visibility defaults to hidden.
- Browser audio defaults to muted.
- Command-line arguments override configuration.
- No configuration file is required for existing users.
