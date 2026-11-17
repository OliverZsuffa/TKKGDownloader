# Implementation plan: Request 021

## Scope

Fix the two confirmed Spotisaver issues without changing queue behavior, browser defaults, track matching, archive validation rules, or the download provider interface.

## 1. Make the Windows diagnostic log path package independent

- Change the Windows log root from `LOCALAPPDATA` to a stable user profile location that Microsoft Store Python does not redirect.
- Use `Path.home() / "TKKGDownloader" / "logs"`, resulting in `%USERPROFILE%\TKKGDownloader\logs`.
- Keep the existing macOS and Linux XDG state directory behavior unchanged.
- Continue creating the directory recursively and verifying that the log file exists.
- Log the resolved absolute path so diagnostics show the actual location.
- Update README and Knowledge Base documentation wherever the old Windows path is documented.
- Add tests proving Windows path selection ignores `LOCALAPPDATA` and uses the user profile, while non-Windows behavior remains unchanged.

## 2. Use the Chromium download file when CDP is active

- Inspect the existing CDP download event state and the exact point where the Playwright download event is received.
- When CDP is active and reports the correlated download as completed, do not call `download.save_as()`.
- Resolve the expected file in the configured Chromium download directory using the sanitized suggested filename.
- Wait for the file to appear and its size to remain stable across consecutive checks. Require a nonzero size and enforce a bounded timeout.
- If CDP reports completion but the expected file never appears, or remains empty or unstable until timeout, raise a clear diagnostic error. Do not silently switch to Playwright's temporary artifact after CDP claims completion.
- When CDP is unavailable, preserve the existing Playwright `download.save_as()` fallback.
- Keep the existing final file existence and nonzero size checks, then continue into the unchanged archive validation workflow.
- Ensure CDP detach still happens on success and failure.

## 3. Redesign terminal progress as an end-to-end pipeline view

The goal is to show what the downloader is doing throughout the complete episode workflow, not merely to polish the existing bars.

### 3.1 Diagnose and fix the duplicate ZIP progress output

- Trace every source that writes ZIP transfer progress, including the initial CDP event, subsequent CDP events, Playwright download callbacks, and explicit status messages.
- Establish from the code and tests why the supplied run printed a 0% line and then a separate 100% line instead of updating one progress bar.
- Ensure the ZIP transfer has exactly one progress display that is updated in place from its initial state through completion.
- Do not emit a second bar for the same transfer. If progress cannot be measured, show one clearly indeterminate state rather than fabricated intermediate percentages.
- Preserve byte counts and total size when known.

### 3.2 Correct archive preparation progress

- Trace how the archive preparation percentage is currently calculated and explain why it stopped at 90%.
- Determine whether the 90% is a hardcoded phase allocation, a weighted overall progress value, or an actual measured value.
- Do not present a stage allocation as if it were measured task progress.
- If archive creation exposes measurable progress, display it accurately and finish at 100%.
- If it does not expose measurable progress, use an indeterminate preparation indicator or clear stage messages, then show 100% only when archive creation has actually completed.
- Make the transition from preparation to ZIP transfer unambiguous.

### 3.3 Add progress visibility for the remaining processing stages

- Inspect the complete post-download pipeline and identify the real stages, including archive validation, extraction, track discovery or matching, audio merging, output writing, and cleanup where applicable.
- Add progress indicators for stages where meaningful progress can be measured, especially merging and other potentially long-running processing.
- For measurable work, show a single updating bar with current item count and percentage, such as merged tracks out of total tracks.
- For work without a measurable unit of progress, show an indeterminate activity indicator and a clear stage label. Do not invent percentages.
- Emit a clear completion message when each stage finishes.
- Keep the output compact and consistent, with no overlapping bars or progress updates that overwrite unrelated status messages.
- Avoid adding progress instrumentation that changes the underlying processing behavior.

### 3.4 Add total elapsed time

- Measure the full episode operation using a monotonic clock, starting when the episode workflow begins and ending on success or failure.
- Display elapsed time during the run in a stable location without creating a new line on every refresh.
- Always report the final total elapsed time, including on failure.
- Use a readable duration format and test short as well as multi-minute durations.
- If stage durations can be added without clutter, keep them supplementary. The total elapsed time is the required metric.

### 3.5 General presentation and tests

- Use the supplied episode 144 output as the baseline and verify the full sequence from browser startup through final merged output.
- Keep the display readable in standard Windows PowerShell.
- Use consistent bar width, alignment, spacing, units, and phase naming.
- Add deterministic tests for the single ZIP bar, archive preparation completion semantics, processing-stage progress, elapsed-time formatting and reporting, line replacement, and phase ordering.
- Do not introduce terminal-only dependencies or change download semantics solely for presentation.

## 4. Tests

Add focused tests for:
- CDP active, correlated download completed, file exists: use the Chromium file and never call `save_as()`.
- CDP active, file appears after a short delay: wait and accept once stable.
- CDP active, missing, empty, or persistently changing file: fail with an actionable timeout.
- CDP unavailable: call `save_as()` and retain existing behavior.
- CDP download event correlation and suggested filename handling remain correct.
- Windows log directory resolves under the user profile and does not use `LOCALAPPDATA`.
- Non-Windows log directory remains under XDG state or the existing home fallback.

Use deterministic mocks and temporary directories. Do not perform a live Spotisaver download in automated tests.

## 5. Documentation

- Update the README Windows diagnostic log location.
- Update the relevant Knowledge Base entry and request implementation record.
- Explain that CDP owns file persistence when available and Playwright owns it only in fallback mode.

## 6. Verification

- Run the complete unit test suite.
- Run Python compilation checks.
- Run the TKKGData contract smoke test.
- Inspect the final diff for unintended changes.
- Do not merge until the user explicitly approves after review.

## Acceptance criteria

- A successful CDP transfer no longer depends on Playwright's temporary artifact being available.
- A completed ZIP is not handed to archive validation until the file is present, nonempty, and stable.
- Playwright fallback remains functional when CDP is unavailable.
- On Windows, logs are directly accessible at `%USERPROFILE%\TKKGDownloader\logs`, including with Microsoft Store Python.
- Terminal output is visually consistent and readable across all download phases, with no stale progress characters, misleading transitions, or avoidable duplicate messages.
- All relevant tests and repository checks pass.
