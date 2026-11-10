# R16 implementation plan

## 1. Production merger

Extend `merge_tracks()` with an automatic strategy, retaining an explicit legacy strategy for the R13 comparison. Probe every source with FFprobe and collect codec, sample rate, channels, channel layout, and duration.

Only attempt stream copy when all source format tuples are identical. Probe and fully decode the candidate. Compare its duration with the sum of source durations using a tolerance of max(3 seconds, 0.1 seconds per source track).

If the sources are incompatible or the candidate fails either validation, discard the temporary output and create 24-bit PCM segments at the highest source sample rate and channel count required by the input set. Concatenate the PCM segments and encode once at 320 kbit/s. Probe and fully decode the final candidate, enforce the same duration tolerance, and atomically replace the destination only after validation.

## 2. Diagnostic comparison

Keep R13's legacy stream-copy candidate so the report continues to show the original behaviour. It must be explicitly selected and must not be confused with the production automatic strategy.

## 3. Track duration diagnostics

Calculate the ordinary duration median using tracks 2 onward. Apply the existing outlier threshold to those tracks. Apply a separate threshold to track 1 so an ordinary longer introduction is not flagged, while implausibly short or excessively long introductory audio remains reviewable.

## 4. Tests

Add FFmpeg integration tests for mixed sample rates, compatible sample rates, and a synthetic stream-copy output with a deliberately incorrect duration. Add unit tests for the introductory track duration rule. Retain the existing manifest integrity tests.

## 5. Documentation

Update README, technical decisions, request index, and this request's implementation notes.

## 6. Verification

Run Python compilation and the complete unittest suite in GitHub Actions. Do not claim real episode playback or semantic boundary correctness from synthetic tests. After CI passes, rerun the existing episode 150 processing locally against the already downloaded archive, without redownloading it.
