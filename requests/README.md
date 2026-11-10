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
- [005: Fix verified YouTube Music downloads](005-fix-youtube-music-download/request.md) — replace the failing spotDL YouTube extraction path with a reliable method using exact verified TKKGData track IDs.
- [004: Make TKKGDownloader a TKKGData consumer](004-tkkgdata-consumer/request.md) — consume shared episode and verified audio release data rather than resolving metadata independently.
- [003: Album count and progress](003-album-count-and-progress/implementation-plan.md)
- [001: Episode downloader](001-episode-downloader/request.md)

## Naming
Use NNN-short-description for request folders, for example 001-episode-downloader.

Copy TEMPLATE.md when creating a new request.
