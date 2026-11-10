# Requests

Requests define what the project should do. Implementation plans define how an approved request should be implemented.

## Workflow

1. Create a numbered request folder for each substantial feature.
2. Write expected behaviour, scope, constraints, and acceptance criteria in request.md.
3. Record the proposed technical approach and verification strategy in implementation-plan.md.
4. Put request-specific questions in questions.md when needed and supporting material in attachments/.
5. Wait for explicit user approval before implementation.
6. Implement on a dedicated branch, test, and record results in notes.md.
7. Merge into main only after verification and Oliver's explicit approval.

## Request index

- [013: Diagnose and produce a high-quality episode 150 merge](013-episode-150-audio-quality-diagnostics/request.md) — preserve Spotisaver sources, inspect all 40 tracks, compare stream-copy and decoded PCM merging, and review all 39 boundaries.

- [012: Complete Spotisaver ZIP download and improve progress output](012-spotisaver-zip-button-and-progress/request.md) — read the ETA and track progress, then click the final visible Download ZIP control to trigger the actual browser download.

- [011: Retry Spotisaver after a queue rejection](011-spotisaver-queue-retry/request.md) — wait 30 seconds after an explicit queue rejection, close the modal, and submit the album request again.
- [010: Wait for Spotisaver's queued browser download](010-spotisaver-wait-for-download-event/request.md) — monitor queue notices and modal progress until the browser signals the download, without a fixed timeout or repeated clicks.
- [009: Poll Spotisaver for the album download button](009-spotisaver-button-first-readiness/request.md) — poll the real download button every second, click immediately when ready, and preserve strict archive validation.
- [008: Spotisaver diagnostic logging](008-spotisaver-diagnostic-logging/request.md) — add timestamped stage, selector, click, download-event, and file-save diagnostics.
- [007: Spotisaver action button workflow](007-spotisaver-action-buttons/request.md) — prioritise the actual full-playlist download button and use the scroll control only as a fallback.
- [006: Spotisaver browser provider](006-spotisaver-import-workflow/request.md) — download one requested album through the visible website interface, validate its tracks, and merge it locally.
- [005: Fix verified YouTube Music downloads](005-fix-youtube-music-download/request.md) — use exact verified TKKGData track IDs.
- [004: Make TKKGDownloader a TKKGData consumer](004-tkkgdata-consumer/request.md) — consume shared episode and verified audio release data.
- [003: Album count and progress](003-album-count-and-progress/implementation-plan.md)
- [001: Episode downloader](001-episode-downloader/request.md)

## Naming

Use NNN-short-description for request folders, for example 001-episode-downloader.

Copy TEMPLATE.md when creating a new request.
