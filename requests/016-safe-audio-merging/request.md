# R16: Safe audio merging and introductory track diagnostics

## Problem

Episode 150 contains source MP3 files with different sample rates. The legacy FFmpeg concat stream-copy operation completed successfully but produced a file 162.6 seconds longer than the sum of the source durations. A 24-bit PCM merge encoded once at 320 kbit/s produced a duration within approximately 1.5 seconds of the source sum.

The first segment is also longer than the remaining segments because TKKG releases commonly place an introduction and sometimes a disclaimer in track 1. It should not be judged against the ordinary segment duration threshold.

## Expected behaviour

1. The normal production merger probes every source before selecting a merge strategy.
2. Stream copy is used only when all source codec, sample rate, channel count, and channel layout values agree.
3. A stream-copy output must pass full decode validation and a duration comparison against the sum of source durations.
4. If formats differ or stream copy fails validation, decode each source to 24-bit PCM at a common sample rate and channel count, concatenate the PCM segments, and encode once at 320 kbit/s.
5. The PCM-derived MP3 must also pass full decode and duration validation before replacing the final output.
6. Never leave a partial or unvalidated output at the final destination.
7. Keep the legacy stream-copy path available only for diagnostic comparison, not as the production default.
8. Calculate the ordinary segment duration median from tracks 2 onward. Give track 1 a separate introductory segment threshold.

## Acceptance criteria

- Mixed 44.1 kHz and 48 kHz source fixtures select PCM merging.
- Compatible source fixtures can retain stream copy when the output duration is valid.
- A stream-copy output with a large duration discrepancy is rejected and replaced by the PCM result.
- Both final strategies require successful full decoding and duration validation.
- Track 1 at approximately 128 seconds is not flagged against the ordinary segment median.
- Implausibly short or excessively long track 1 remains reviewable.
- Existing manifest integrity validation still happens before any FFmpeg processing.
- README and Knowledge Base document the production behaviour and diagnostic policy.
