# Requests

Requests define what the project should do. Implementation plans define how an approved request should be implemented.

## Workflow

1. Create a numbered request folder for each substantial feature.
2. Write the expected behavior, scope, constraints, and acceptance criteria in `request.md`.
3. Record the proposed technical approach and verification strategy in `implementation-plan.md`.
4. Put request-specific questions in `questions.md` when needed and supporting material in `attachments/`.
5. Wait for explicit user approval before implementation.
6. Implement on a dedicated branch, test, and record results in `notes.md`.
7. Merge into `main` only after verification and explicit user approval.

## Naming

Use `NNN-short-description` for request folders, for example `001-episode-downloader`.

Copy [TEMPLATE.md](TEMPLATE.md) when creating a new request.
