# Implementation plan: Request 006

## Status

Approved by Oliver on 2026-11-10. Implementation committed to feature/spotisaver-import. CI and a real Windows browser download remain to be verified.

## Implemented

1. Added Playwright as a project dependency.
2. Added an isolated Spotisaver provider using visible Chromium and the public album URL derived from the validated Spotify album ID.
3. Added visible album title and full track title verification before download.
4. Added normal browser download event handling for an album ZIP or sequential individual track controls.
5. Added safe ZIP extraction, rejecting traversal paths and symlinks.
6. Added exact filename matching against canonical TKKGData track titles, with one non-empty MP3 required per expected track.
7. Added --provider spotisaver to the CLI and restricted this provider to one episode per invocation.
8. Reused the existing confirmation, FFmpeg merge, output naming, and overwrite safeguards.
9. Added synthetic ZIP and CLI tests.
10. Updated README and Knowledge Base documentation.

## Files changed

- src/tkkgdownloader/spotisaver.py
- src/tkkgdownloader/audio_import.py
- src/tkkgdownloader/downloader.py
- src/tkkgdownloader/cli.py
- tests/test_spotisaver.py
- pyproject.toml
- README.md
- docs/knowledge/project-overview.md
- docs/knowledge/technical-decisions.md
- docs/knowledge/tkkgdata-integration.md
- docs/knowledge/README.md
- requests/README.md

## Verification plan

1. Run Python compilation and the complete unittest suite in CI.
2. Confirm the existing TKKGData live contract smoke test remains green.
3. Install Playwright Chromium on Windows with py -m playwright install chromium.
4. Run py tkkg.py 150 --provider spotisaver.
5. Verify the visible album and tracklist check, downloaded filenames, exact 40-track mapping, merged MP3 playback, and total duration.
6. Do not report the live website flow as passed until Oliver confirms the Windows test.

## Safeguards

- Exactly one episode per Spotisaver invocation.
- No unattended catalogue crawling, concurrent downloads, or automated retry loops.
- Use normal visible website controls only.
- No private endpoints, hidden APIs, stealth browser settings, CAPTCHA bypass, login bypass, access-control workarounds, or anti-automation evasion.
- Stop when the site displays a restriction or its interface cannot be verified.
- Keep downloaded audio and temporary files out of version control.
