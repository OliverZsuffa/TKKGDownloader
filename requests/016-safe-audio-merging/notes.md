# R16 implementation notes

Implementation is on branch `r16-safe-audio-merging`.

Changes:
- Production `merge_tracks()` now probes source audio formats and durations.
- Stream copy is attempted only for identical audio format tuples.
- Stream copy output must pass full decode and duration validation.
- Incompatible or invalid stream-copy candidates fall back to 24-bit PCM concatenation and one 320 kbit/s MP3 encode.
- PCM output is also fully decoded and duration checked before replacing the destination.
- The old stream-copy and 192 kbit/s fallback remains available through an explicit legacy strategy for diagnostic comparison.
- Track 1 duration is assessed separately from ordinary segments.
- Added integration tests for mixed formats, compatible formats, and incorrect stream-copy duration, plus intro duration rule tests.
- Updated README and technical decision 013.

Verification status: GitHub Actions has not yet been checked. Real episode 150 processing and playback remain pending.
