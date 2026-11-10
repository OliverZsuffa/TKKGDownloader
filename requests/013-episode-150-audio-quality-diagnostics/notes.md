# Request 013 implementation notes

## Status

PR #20 was squash merged into main as 118163169a30ddaf560980f3e35f2a2ecb18cd4d. Automated verification passed. The real episode 150 Spotisaver download and review remain pending local execution.

## Implemented

- Added the opt-in `--diagnostic-dir` mode for one Spotisaver episode.
- Retained the original downloaded ZIP, raw extracted MP3 files, canonical numbered tracks, and Spotisaver diagnostic log path in a persistent workspace.
- Added FFprobe inspection and complete FFmpeg decoding for every source track.
- Recorded codec, duration, size, bitrate, sample rate, channels, stream data, decode diagnostics, silence detection, RMS, peak level, and outlier flags.
- Preserved the existing default merge behaviour and added optional reporting of the baseline stream-copy or 192 kbit/s fallback command.
- Generated a lossless 24-bit PCM master and a separate 320 kbit/s MP3 encoded once from that master.
- Fully decoded and probed both MP3 candidates and the PCM master.
- Extracted embedded artwork from the source parts, preserved distinct cover variants, embedded the selected source cover in the PCM-derived MP3, and verified it by reading the ID3 tag back.
- Wrote episode title, verified album title, consistent source artist metadata where available, and track 1/1. Every populated field is read back and checked.
- Generated all transition excerpts, a combined lossless boundary review, a boundary index, and JSON and text reports.
- Added failure reporting that retains source evidence and does not create candidates if a source fails probing or full decoding.
- Documented the command in README.

## Verification

- GitHub Actions run 42862758005 passed.
- Python compilation passed.
- TKKGData contract smoke test passed.
- All 86 unit tests passed.
- CI installs FFmpeg and runs the synthetic audio integration tests, including the two-candidate merge, metadata read-back, boundary metrics, and corrupt-source failure path.
- CI does not contact Spotisaver or download real episode audio.

## Local execution still required

Run on Oliver's Windows machine with a new empty diagnostic directory:

```powershell
py tkkg.py 150 --provider spotisaver --diagnostic-dir "D:\TKKG\episode-150-diagnostics"
```

The real download, the 40 source files, the artwork actually present in those files, the full episode comparison, and listening to all 39 boundaries have not yet been verified. Do not delete the diagnostic workspace or replace the existing episode MP3 until the results have been reviewed.
