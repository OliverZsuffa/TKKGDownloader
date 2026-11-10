# Request 005 implementation notes

## 2026-11-10

Oliver approved the implementation plan.

### Changes made

- Replaced spotDL playlist download and spotDL individual fallback with direct yt-dlp downloads.
- Each track is downloaded from the exact YouTube Music watch URL validated from its TKKGData video ID.
- Spotify track titles and track numbers from TKKGData determine deterministic output filenames and order.
- yt-dlp extracts MP3 audio at 192 kbit/s.
- Added yt-dlp as a project dependency. If the executable is not on PATH, the downloader invokes the installed Python module.
- The playlist URL is retained for provenance and displayed as such, but is no longer passed to a download provider.
- The downloader stops on the first failed track and identifies its track number.
- A successful yt-dlp exit code is not sufficient. The expected MP3 file must exist and be non-empty.
- The full dynamic track count and contiguous order are validated before the existing FFmpeg merge.
- Temporary files remain isolated in a TemporaryDirectory and are removed after success or failure.
- Updated unit tests, CI smoke test, README, and Knowledge Base to reflect the direct download path.

### Automated coverage added or updated

- Exact verified URLs are passed to yt-dlp without playlist resolution or text search.
- Track count is dynamic.
- Playlist metadata is not required for downloading.
- Failed track stops the process and prevents merging.
- Missing output file prevents merging.
- Missing verified mapping is rejected.
- Existing source ID, URL, count, and ordering validation remains covered.

### Not yet verified

- No real YouTube audio was downloaded in this implementation environment.
- No real Windows run or FFmpeg playback check has been performed.
- CI results will be recorded after the pull request workflow completes.

### CI

- GitHub Actions run 42780852150 passed on commit c889f2c553b543c226293c65119c9802c00187fa. This run covered the direct yt-dlp implementation, test updates, and live TKKGData contract smoke test.
- Subsequent changes to the Knowledge Base are documentation only. A fresh run is being triggered for the final branch head.
