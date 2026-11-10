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
