# Technical Decisions

## 001. Use TKKGData as the only metadata source

Episode identity and verified provider mappings are fetched from TKKGData. Validate the dataset metadata schema version, episode count, required record arrays, unique episode numbers, and contiguous numbering before using it.

Do not query TKKGTracker or keep an independent authoritative episode catalogue.

## 002. Do not perform source discovery in the downloader

TKKGData owns scraping, Spotify resolution, YouTube Music matching, source verification, provenance, and publication. The downloader only consumes verified identifiers and URLs. It must never use text search as a fallback or write corrections back to TKKGData.

## 003. Download exact verified YouTube video URLs directly

The default provider uses yt-dlp directly with each individual YouTube Music video URL and the exact video ID validated from TKKGData. Do not ask spotDL to resolve the playlist or individual song URLs. The previous spotDL 4.5.2 path attempted downloads with a YouTube URL containing a missing video ID.

## 004. Validate track integrity from the shared mapping

The Spotify track count, YouTube Music track count, matched count, and actual list length must agree. Track numbers must be contiguous and ordered. Validate each provider ID against its corresponding URL.

After downloading, require every expected MP3 file to exist and be non-empty. Never create a combined file from an incomplete or ambiguous download.

## 005. Preserve the command line contract

Keep commands such as py tkkg.py 150 and py tkkg.py 1-10. Preserve range handling, output naming, overwrite protection, per episode failure reporting, FFmpeg merging, and temporary file cleanup.

## 006. Keep downloads local

Downloaded audio and temporary files stay outside version control. The downloader never uploads audio or user data to TKKGData.

## 007. Spotisaver is an explicit one-episode browser provider

Spotisaver is selected explicitly with --provider spotisaver. Playwright launches visible Chromium and uses the public album page and normal rendered download controls. Immediately after the page body becomes visible, the provider polls the actual `#downloadAllBtn` control every second for up to 120 seconds. It accepts only a visible, enabled button labelled `Download entire playlist` and clicks it directly without scrolling or waiting for the complete tracklist to appear in page text.

If the real button does not appear during the polling window, the provider logs selector diagnostics, page title, a bounded body text preview, and visible controls. Only after that timeout may it click `button.btn-playlist-download`, which is an intermediate scroll control, and poll for the real action for a further 15 seconds. If the album action remains unavailable, the provider may use normal visible individual-track controls sequentially.

The canonical Spotify album ID from TKKGData is the album page identity anchor. Regardless of the browser readiness path, imported audio is validated against every canonical track. Require the exact expected MP3 count, unique filename-to-title matches, non-empty files, safe ZIP paths, and no unexpected audio files. No merge occurs unless all tracks match.

Detailed browser diagnostics are written to a persistent, timestamped per-run log outside the temporary download workspace. Selector checks record counts, visibility, text, and identifying attributes. The provider registers a browser download listener before clicking a normal website control. It monitors the rendered download modal, including #downloadStatusText, #downloadMiniLog, #downloadFailedBadge, visible progress, and visible modal controls. Queue notices and stated retry delays are logged as queue states, not final failures. If the explicit all-slots-busy notice remains active for 30 seconds, the provider rechecks it, closes the visible modal, confirms that the modal is closed, verifies the original download control is visible and enabled, and clicks that control again. The listener remains active across attempts. This repeats only for another explicit queue rejection. If the queue notice clears into processing, no retry is issued. Generic errors and a merely slow download never trigger retries. The provider waits for the browser download event without a fixed timeout while the page remains open. Ctrl+C propagates cleanly, while unexpected page closure and explicit site failure produce concise console errors with the diagnostic log location. Suggested filename, save destination, file size, and save errors remain in the log.

Do not use private endpoints, stealth plugins, CAPTCHA bypasses, login bypasses, access-control workarounds, or unattended catalogue downloads. Stop when the site presents a restriction or its interface cannot be verified. Spotisaver's permission and limits are separate from technical implementation and must be respected.

## 008. Treat Spotisaver playlist processing and ZIP download as separate stages

The website may finish processing every playlist track and create a ZIP archive without triggering a browser download. The provider must then locate and click the visible, enabled `Download ZIP` control in the active modal. Keep the browser download listener registered from before the initial album request through queue retries, processing, archive creation, and the final ZIP-button click. Only the subsequent browser download event confirms that the archive is being transferred. Save and validate the archive before reporting success. The modal ETA and track counter are informational progress signals. ETA must never trigger retries, impose a timeout, or prove completion. Show concise progress summaries by default while retaining detailed diagnostics for state transitions and failures.

The playlist processing state and final ZIP transfer are separate. Read the modal track counter, percentage, and ETA to render a pip-style in-place terminal progress bar, with concise periodic output in non-interactive terminals. ETA is informational only. When the modal reports `ZIP archive created.`, locate the unique visible, enabled `Download ZIP` button by accessible name or exact rendered text scoped to the active modal, then click it exactly once. Keep the browser download listener registered from before the first album click through queue retries and the final ZIP click. Only the subsequent browser download event, a saved non-empty archive, strict track validation, and successful merge can establish completion. If the ZIP button cannot be identified, stop and report the active modal's visible controls rather than guessing a selector.

## Verification status

Automated tests cover the data contract, CLI selection, safe ZIP import, filename matching, and downloader behaviour. Real Spotisaver download, FFmpeg merge, and playback remain separate end to end checks and must not be reported as passed until tested locally.


## 009. Keep Spotisaver terminal output concise and semantic

Normal console output shows only meaningful stage transitions, a single progress line, and the final MP3 path. Browser and DOM diagnostics, raw modal text, selector details, temporary paths, and tracebacks belong in a persistent per-run log outside the temporary download workspace. The log filename includes the episode number and a timestamp. Create it before launching Chromium and close it on success, failure, or cancellation.

Use cyan for informational stages and ETA, yellow for queue waits and retries, green for successful stages and completed progress, red for errors, and grey for remaining progress. Colour is supplementary and must not carry meaning by itself. Disable ANSI colour for non-interactive output, terminals marked as dumb, and when NO_COLOR is set. In interactive terminals update one progress line in place. In non-interactive output, emit concise progress no more often than the existing 15-second heartbeat. Show the track count only when the site actually supplies it, and clear missing or invalid ETA values rather than retaining stale estimates. Never derive an ETA from elapsed time.


## 010. Keep quality diagnostics opt-in and preserve all source evidence

The normal downloader and its default merge behaviour remain unchanged. The optional `--diagnostic-dir` mode is available only with the Spotisaver provider and one episode per invocation. It requires a new or empty directory and never replaces the normal final episode MP3.

Keep the original Spotisaver ZIP, extracted raw files, canonical numbered tracks, and the path to the persistent browser diagnostic log. Inspect every source with FFprobe, a full FFmpeg decode, silence detection, RMS and peak analysis. A failed source probe or decode stops candidate generation but still produces a failure report and preserves all downloaded evidence.

Generate two independent MP3 candidates. Candidate A uses the existing merger and records whether stream copy or its existing 192 kbit/s fallback was selected. Candidate B decodes each source to 24-bit PCM, concatenates the tracks in canonical order, retains the lossless WAV master, and encodes once at 320 kbit/s. Use the common source sample rate and channel count when all tracks agree. Otherwise preserve the highest source sample rate and channel count to avoid downsampling or downmixing. Fully decode and probe the candidates and PCM master.

Inspect embedded ID3 attached pictures across the source parts. Preserve distinct cover images and their source details. Embed the selected source image in the PCM-derived MP3. Populate metadata from TKKGData and consistent source tags only, then read back and verify every populated ID3 field and the artwork. Never invent missing values.

Create a lossless review excerpt around every track boundary and record its timestamp, silence, RMS, and peak metrics. Reports must distinguish source validation failures from candidate validation results. Keep all intermediate files until the user has reviewed the recording. The real episode workflow runs locally because it involves a long browser download and media processing. CI runs synthetic fixtures only.

## 011. Require deterministic Spotisaver track identity and a verified import manifest

Spotisaver sources must map to canonical TKKGData tracks through deterministic evidence. Exact normalized filename titles are preferred, including explicitly recognised provider wrappers. Exact embedded ID3 title is a fallback. Embedded album identity together with a valid track number is a further fallback when the album exactly matches the verified TKKGData album title. Track number alone is never sufficient. Exact verified alternate titles may be accepted only when explicitly supplied by trusted upstream metadata. Partial and fuzzy matching are prohibited. A leading numeric filename prefix is accepted only when it equals the expected canonical track number. Canonical track numbers must be positive, unique, contiguous, and one-based. Ambiguous, missing, extra, empty, or byte-identical source tracks are rejected before merging.

Build the complete one-to-one mapping before creating numbered copies. Record the source filename and relative path, canonical track number and title, matching rule, file size, SHA-256 checksums, and available embedded ID3 title, artist, album, track number, and disc number in a versioned manifest. Embedded metadata is corroborating evidence only. Missing or conflicting tags are warnings and never override TKKGData or cause automatic reordering.

Verify that each canonical copy has the same SHA-256 as its source. Immediately before every Spotisaver merge candidate, verify that the supplied paths exactly match the manifest order and that every file still has its recorded checksum. In R13 diagnostic mode preserve the portable manifest as `reports/track-manifest.json` and include mapping evidence in the source inspection reports. In normal mode keep the manifest in memory only.

Checksums establish byte identity and traceability, not semantic audio correctness or the editorial correctness of TKKGData's sequence. Audio diagnostics and human listening remain necessary for those questions. Do not automatically reorder or repair audio based on tags, durations, fingerprints, or heuristics.



## 012. Use layered deterministic evidence for Spotisaver source identity

Resolve each source in this order: exact normalized filename title, exact normalized filename after removing known provider wrappers, exact embedded ID3 title, then exact embedded album identity together with the expected track number. The current known Spotisaver wrapper is a leading `TKKG - ` and trailing ` (SPOTISAVER)`. Do not strip arbitrary words or provider labels.

Track records may expose an `alternate_titles` list. Treat each alias as an exact title key and apply the same collision checks as the canonical title. Do not invent aliases or infer them from fuzzy similarity.

The album and track metadata fallback requires both an exact normalized album match against the verified album title and a valid embedded track number. Track number alone is insufficient. If metadata is absent, malformed, contradictory, or does not establish a unique one-to-one mapping, reject the import.

Record the matching method, evidence type, and matched title key in the manifest. Keep fuzzy similarity strictly diagnostic only. It may be used to explain likely candidates in a future interactive review workflow, but never to assign a source automatically.

At logger startup, create the persistent diagnostic file, write and flush an initialization record, and verify that the file exists before starting the browser. If this fails, report the actual filesystem error and do not claim that a log exists.


## 013. Validate source formats and output duration before selecting a merge

The normal merger uses an automatic quality-first strategy. Probe every source track and record codec, sample rate, channel count, channel layout, and duration. Stream copy is eligible only when all source audio formats are identical. A stream-copy candidate must pass a full decode and its duration must be within the configured tolerance of the summed source durations. If source formats differ, stream copy fails, decoding fails, or the duration check fails, discard the candidate and merge through 24-bit PCM segments at a common sample rate and channel count, followed by one 320 kbit/s MP3 encode. The PCM-derived output must also pass a full decode and duration validation before it replaces the requested output. Never leave a partial or unvalidated file at the final destination.

The duration tolerance is max(3 seconds, 0.1 seconds per source track), allowing normal MP3 frame padding and encoder delay while rejecting substantial timestamp drift. Preserve the old stream-copy and 192 kbit/s fallback path only as an explicitly selected legacy strategy for diagnostics. It is not the production default.

Diagnostic duration outlier analysis treats track 1 separately because TKKG episode releases commonly include an introduction and disclaimer in the first segment. The median for ordinary segments is calculated from tracks 2 onward. Track 1 is flagged only when it is implausibly short or exceeds the dedicated intro threshold. This is a review heuristic, not evidence that audio is defective.

Checksums and successful decoding establish file identity and technical readability, not semantic correctness or audible continuity. Boundary review and human listening remain necessary.


## 014. Finalize production MP3 metadata before publication

Normal Spotisaver downloads and diagnostic candidates share one metadata implementation. Extract the first valid embedded JPEG or PNG in canonical track order, preserve the source image bytes, write episode and verified album metadata, and include optional source tags only when consistent across all tracks. Read back and verify every written field and the embedded cover bytes. Missing source artwork is reported without substituting generated artwork. Merge and finalize into a temporary candidate in the destination filesystem, probe and fully decode it after metadata writing, and only then atomically replace the destination. A failed replacement must leave an existing final file untouched. Queue waiting is presented as one cumulative line, and ETA parsing supports seconds-only as well as minutes-and-seconds formats.
