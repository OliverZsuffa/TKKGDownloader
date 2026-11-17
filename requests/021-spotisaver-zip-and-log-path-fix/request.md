# Request 021: Fix Spotisaver ZIP persistence and diagnostic log location

## Problem 1: ZIP download fails after Chromium reports completion

During an episode 144 download, Spotisaver completed the ZIP transfer through Chromium DevTools Protocol. The terminal showed the full 150.2 MB transfer reaching 100%, but the workflow then failed in Playwright's `download.save_as()` with ENOENT because Playwright's temporary artifact had already disappeared.

The current implementation configures Chromium's download path through CDP and also unconditionally asks Playwright to copy its temporary download artifact. These two persistence paths conflict in this environment.

## Problem 2: Diagnostic logs are inaccessible with Microsoft Store Python

The diagnostic logger currently writes Windows logs below `%LOCALAPPDATA%\TKKGDownloader\logs`. The installed Microsoft Store Python redirects that path into its package's `LocalCache\Local` directory. Python can see the files, but ordinary PowerShell and CMD cannot.

The logger should use a stable, user accessible Windows location that is not redirected by the Store Python package.

## Expected outcome

1. A completed CDP download is taken from Chromium's configured download directory, waited for until it exists and has a stable nonzero size, and then passed to archive validation.
2. Playwright `download.save_as()` remains the fallback only when CDP download handling is unavailable.
3. Diagnostic logs on Windows are written to a stable user profile directory visible to ordinary Windows applications.
4. Existing non-Windows log location behavior remains unchanged.
5. ZIP transfer is represented by one progress bar, not separate initial and final bars.
6. Archive preparation reaches an explicit 100% completion state when the website confirms the ZIP is ready, rather than remaining at 90%.
7. Progress is visible for extraction, track metadata reading, matching, integrity checks, copying, merging, and final verification wherever reliable measurements exist.
8. A total elapsed timer covers the full episode workflow and is reported on success or failure.
9. Tests cover both ZIP persistence paths, progress rendering and callbacks, elapsed time formatting, and Windows log path selection.
