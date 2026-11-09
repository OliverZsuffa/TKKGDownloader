# Request 001: Download TKKG episodes as MP3

## Status

Awaiting implementation plan approval.

## Objective

Create a Python command line tool that takes one TKKG episode number or an episode range and produces one complete MP3 file for each requested episode.

## Intended usage

```powershell
python tkkg.py 1
python tkkg.py 1-10
python tkkg.py 125
```

## Functional requirements

1. Accept a single episode number or an inclusive range.
2. Retrieve the latest episode metadata from the public TKKGTracker repository.
3. Resolve the official episode number and title from the dataset.
4. Search Spotify using the episode number and official title together.
5. Identify the Spotify release belonging to the requested episode and determine all of its audio tracks in the correct order.
6. Do not use the TKKGTracker `tracks` array to determine Spotify tracks. That array represents chapter information and does not correspond reliably to Spotify's track divisions.
7. Use spotDL to retrieve the selected tracks.
8. Use FFmpeg to combine the tracks into one MP3 per episode.
9. Verify that all expected tracks were downloaded and that the merged output exists and is non-empty.
10. Use a predictable output filename containing the zero-padded episode number and official title.
11. For ranges, process each episode independently and report successes and failures clearly.
12. Avoid overwriting an existing finished file without an explicit overwrite option or clear user confirmation.

## Expected output

Example:

`output/TKKG 001 - Die Jagd nach den Millionendieben.mp3`

## User experience and error handling

- Explain invalid episode numbers and malformed ranges clearly.
- Handle unavailable episode metadata, no Spotify match, ambiguous releases, missing dependencies, download failures, and merge failures.
- Do not silently choose between materially different Spotify releases when the match is ambiguous.
- Preserve enough diagnostic information to understand which episode or track failed.
- Keep temporary files separate from final output and clean them up safely.

## Constraints

- Target environment: Windows, with PowerShell examples.
- Python is the application language.
- spotDL is already installed in the user's environment.
- FFmpeg is required for merging.
- Spotify search must use the official episode number and title, not the TKKGTracker chapter list.
- The tool should use publicly available episode metadata and should not require hardcoded episode titles.

## Out of scope for the first version

- A graphical user interface.
- A music library manager.
- Automatic tagging or artwork beyond what is needed for a useful output file.
- Downloading arbitrary non-TKKG content.

## Acceptance criteria

- [ ] A single episode number produces one correctly named MP3.
- [ ] An inclusive episode range processes every requested episode independently.
- [ ] The episode title is resolved from the current TKKGTracker dataset.
- [ ] Spotify track selection is based on the Spotify release, not the dataset's `tracks` field.
- [ ] Track order is preserved when merging.
- [ ] Ambiguous Spotify matches are surfaced rather than silently guessed.
- [ ] Missing or failed tracks cannot result in a misleadingly successful final file.
- [ ] Existing output files are protected from accidental overwrite.
- [ ] Automated tests cover argument parsing, metadata lookup, match selection, ordering, and failure handling.
- [ ] Setup and usage instructions are documented.

## Open questions

- What Spotify search and result selection method is most reliable and maintainable with spotDL?
- Can spotDL download a selected album or a curated list of Spotify track URLs in a way that reliably preserves the required order?
- What exact verification is needed to distinguish a complete episode from an unrelated or partial release?
