# Repository instructions

## Project workflow

- Read `docs/knowledge/README.md` and all relevant Knowledge Base documents before changing the project.
- Read the active request and its implementation plan before working on a feature.
- A request defines the expected behavior and acceptance criteria. The implementation plan defines the technical approach.
- Do not implement a feature until the user has explicitly approved its implementation plan.
- Keep changes focused on the approved request.
- Add or update automated tests where practical and provide concrete manual test steps.
- Run the relevant tests and build or validation commands. Never claim checks passed if they were not run.
- Record implementation decisions and test results in the request notes.
- Update the Knowledge Base when a decision is reusable beyond one request.
- Use a dedicated branch for feature implementation. Do not merge into `main` without user approval after verification.

## Code quality

- Prefer simple, maintainable Python code and clear separation of responsibilities.
- Keep external command execution explicit and handle errors, missing dependencies, and interrupted downloads.
- Never silently select an ambiguous Spotify release or silently produce an incomplete output file.
- Do not commit credentials, tokens, personal data, or downloaded audio files.
- Keep generated downloads and temporary merge files out of version control.
