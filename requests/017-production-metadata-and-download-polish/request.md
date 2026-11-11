# Request 017: Production metadata and download output polish

## Problem

The diagnostic workflow extracts source cover artwork and writes verified ID3 metadata, but the normal Spotisaver download workflow only merges audio. As a result, normal downloads can lack the artwork and metadata present in diagnostic candidates.

The Spotisaver modal can also display ETA as seconds only, while the current parser expects both minute and second fields. Queue retries are technically correct but repeated queue messages make long waits unnecessarily noisy.

## Expected behaviour

- Normal Spotisaver downloads embed the original available source cover and consistent source metadata into the final MP3.
- The final MP3 is verified after metadata writing and is published only after all checks pass.
- Missing source artwork is reported clearly without inventing a replacement.
- ETA works for seconds-only and minutes-plus-seconds displays.
- Queue waiting uses one cumulative in-place line in interactive terminals and does not print repeated retry messages.
- Console output shows concise processing stages while detailed diagnostics remain in the persistent log.

## Constraints

- Preserve the R16 merger and its validation rules.
- Preserve the existing queue retry state machine, retry interval, and cancellation behaviour.
- Do not use private endpoints or browser workarounds.
- Do not overwrite an existing valid final file unless the replacement has passed validation.
- Keep the default yt-dlp provider behaviour unchanged.
- Tests must not require network access or real retry delays.

## Acceptance criteria

A normal Spotisaver download with embedded source artwork produces a final MP3 with the original cover bytes and verified ID3 metadata. The audio fully decodes after metadata finalization. Failed finalization does not replace an existing output. Seconds-only ETA is displayed correctly. Queue waiting remains one cumulative status line regardless of retry count.
