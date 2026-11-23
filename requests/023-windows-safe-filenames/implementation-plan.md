# Implementation plan: Request 023

1. Trace every title-derived filesystem path in the import and merge workflows, including intermediate canonical track files, manifests where applicable, and the final merged output filename.
2. Introduce a single reusable filename sanitization helper for Windows-compatible names. Preserve readable titles while replacing or removing invalid characters, handling reserved device names (such as CON, NUL, AUX, COM1 and LPT1), trimming trailing dots and spaces, and applying a conservative length limit.
3. Ensure generated filenames remain unique within the destination directory. If sanitization produces collisions, add a deterministic disambiguating suffix rather than overwriting files.
4. Keep canonical titles and source mapping data unchanged. Store the actual safe filename/path in manifest fields that describe filesystem paths.
5. Apply the helper to all title-derived destination paths in the import and final merge workflow, without altering matching or verification rules.
6. Add unit tests covering question marks and other forbidden characters, reserved device names, trailing dots/spaces, excessive length, collision behaviour, and unchanged ordinary names.
7. Run the full test suite, Python compilation, and TKKGData contract smoke test. Do not perform a live Spotisaver download as part of verification.
