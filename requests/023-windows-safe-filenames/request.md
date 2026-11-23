# Request 023: Windows safe output filenames

## Problem
Spotisaver episode 134 downloaded and validated all 40 source tracks and completed the ZIP transfer. Import failed when copying a verified track because the canonical Spotify title contained a question mark, which Windows does not permit in a filename. The current import path constructs destination filenames directly from track titles.

## Expected behaviour
- Keep canonical episode and track titles unchanged in metadata, matching, diagnostics, and manifests.
- Generate portable output filenames that are safe on Windows, without losing meaningful title information unnecessarily.
- Handle Windows reserved characters, reserved device names, trailing spaces or periods, and overly long filenames.
- Avoid collisions when sanitization causes two titles to produce the same filename.
- Do not weaken track identity validation or integrity checks.
- Ensure the final merged episode filename is also safe.

## Scope
Address source-track destination filenames and final episode output naming where title-based filenames are constructed. Keep this focused on filesystem naming, not changes to download acquisition or audio processing.

## Acceptance criteria
- Episode 134 and its track titles can be imported on Windows.
- Filename sanitization is deterministic and tested.
- Sanitized filename collisions are handled explicitly and safely.
- Canonical titles remain intact in manifests and metadata.
- Existing behaviour on valid filenames remains unchanged where possible.
- Tests cover invalid characters, reserved Windows names, trailing dots/spaces, long names, collision handling, and normal titles.
- All existing tests pass.
