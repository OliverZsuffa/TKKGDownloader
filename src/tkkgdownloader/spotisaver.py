"""Visible Playwright integration for Spotisaver's public album page."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import time
import traceback
from typing import Any
import unicodedata

from .audio_import import import_audio_files

SPOTISAVER_ALBUM_URL = "https://spotisaver.net/en/album/{album_id}/"


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def _log(message: str, started: float | None = None) -> None:
    """Print a timestamped, flushed diagnostic line."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    elapsed = f" +{time.monotonic() - started:.1f}s" if started is not None else ""
    print(f"[{timestamp}{elapsed}] {message}", flush=True)


def _log_selector_state(page: Any, selector: str) -> int:
    """Log the count and visible details for a selector, without failing discovery."""
    try:
        locator = page.locator(selector)
        count = locator.count()
    except Exception as exc:
        _log(f"Selector diagnostic failed for {selector!r}: {type(exc).__name__}: {exc}")
        return 0

    _log(f"Selector {selector!r}: {count} match(es)")
    for index in range(min(count, 5)):
        candidate = locator.nth(index)
        try:
            visible = candidate.is_visible()
        except Exception as exc:
            visible = f"error: {type(exc).__name__}: {exc}"
        try:
            label = candidate.inner_text(timeout=2_000).strip().replace("\n", " ")[:160]
        except Exception:
            label = ""
        attributes = {}
        for name in ("id", "class", "aria-label", "title", "onclick"):
            try:
                value = candidate.get_attribute(name)
            except Exception:
                value = None
            if value:
                attributes[name] = value[:180]
        _log(
            f"  match {index + 1}: visible={visible!r}, text={label!r}, "
            f"attributes={attributes!r}"
        )
    return count


def _read_download_modal(page: Any) -> dict[str, str]:
    """Read visible status text from Spotisaver's rendered download modal."""
    return page.evaluate(
        """() => {
            const read = (selector) => {
                const element = document.querySelector(selector);
                if (!element) return "";
                const style = window.getComputedStyle(element);
                if (style.display === "none" || style.visibility === "hidden") return "";
                return (element.innerText || element.textContent || "").trim();
            };
            const progress = document.querySelector("#downloadProgress");
            const progressText = progress
                ? [progress.getAttribute("aria-valuenow"), progress.style.width]
                    .filter(Boolean).join(" ")
                : "";
            const retryControls = Array.from(
                document.querySelectorAll(".modal.show button, .modal.show a")
            ).filter((element) => {
                const style = window.getComputedStyle(element);
                return style.display !== "none" && style.visibility !== "hidden";
            }).map((element) => ({
                text: (element.innerText || element.textContent || "").trim(),
                id: element.id || "",
                aria: element.getAttribute("aria-label") || ""
            }));
            return {
                status: read("#downloadStatusText"),
                log: read("#downloadMiniLog"),
                failed: read("#downloadFailedBadge"),
                progress: progressText,
                controls: JSON.stringify(retryControls)
            };
        }"""
    )


def _queue_retry_seconds(snapshot: dict[str, str]) -> int | None:
    """Extract a retry delay stated in the visible queue notice."""
    text = " ".join((snapshot.get("status", ""), snapshot.get("log", "")))
    if not re.search(r"all download slots are busy|slots are busy", text, re.I):
        return None
    match = re.search(
        r"try again in\s+(\d+)\s*(sec(?:ond)?s?|min(?:ute)?s?)",
        text,
        re.I,
    )
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 60 if match.group(2).lower().startswith("min") else amount


def _download_failure(snapshot: dict[str, str]) -> str | None:
    """Return an explicit failure reported by the modal, excluding queue notices."""
    failed_badge = snapshot.get("failed", "").strip()
    if failed_badge:
        return failed_badge
    text = " ".join((snapshot.get("status", ""), snapshot.get("log", "")))
    if re.search(
        r"download failed|failed to download|error downloading|"
        r"something went wrong|unable to download|could not download",
        text,
        re.I,
    ):
        return text[:500]
    return None


def _download_click(
    page: Any,
    locator: Any,
    target: Path,
    *,
    queue_retry_wait_ms: int = 30_000,
) -> Path:
    """Submit a visible download request and retry only explicit queue rejections."""
    started = time.monotonic()
    download_events: list[Any] = []
    last_snapshot: dict[str, str] | None = None
    last_heartbeat = started
    queue_started: float | None = None
    attempt = 1
    _log(f"Preparing browser download; target directory: {target}")
    page.on("download", lambda download: download_events.append(download))
    _log("Registered browser download listener before clicking.")
    _log(f"Issuing Spotisaver download attempt {attempt}.")
    try:
        locator.click()
    except Exception as exc:
        _log(f"CLICK FAILED: {type(exc).__name__}: {exc}", started)
        raise

    _log(
        "Click call returned successfully. Monitoring Spotisaver's queue and waiting "
        "without a fixed download-event timeout.",
        started,
    )
    while not download_events:
        if page.is_closed():
            raise RuntimeError(
                "Spotisaver page closed before a browser download event arrived. "
                f"Last modal state: {(last_snapshot or {})!r}"
            )

        try:
            snapshot = _read_download_modal(page)
        except Exception as exc:
            if page.is_closed():
                raise RuntimeError(
                    "Spotisaver page closed while waiting for the download event."
                ) from exc
            _log(f"Could not read download modal yet: {type(exc).__name__}: {exc}", started)
            snapshot = {}

        queue_text = " ".join((snapshot.get("status", ""), snapshot.get("log", "")))
        queue_busy = bool(re.search(r"all download slots are busy|slots are busy", queue_text, re.I))
        now = time.monotonic()

        if queue_busy:
            if queue_started is None:
                queue_started = now
                stated_delay = _queue_retry_seconds(snapshot)
                delay_text = f" Website retry instruction: {stated_delay}s." if stated_delay else ""
                _log(
                    f"Spotisaver rejected attempt {attempt}: all download slots are busy."
                    f"{delay_text} Will close the queue modal and retry after "
                    f"{queue_retry_wait_ms / 1000:.0f}s if the rejection remains active.",
                    started,
                )
            elif now - queue_started >= queue_retry_wait_ms / 1000:
                # Re-read immediately before acting. The queue may have cleared
                # between the previous poll and the retry deadline.
                snapshot = _read_download_modal(page)
                queue_text = " ".join((snapshot.get("status", ""), snapshot.get("log", "")))
                queue_busy = bool(re.search(r"all download slots are busy|slots are busy", queue_text, re.I))
                if queue_busy and not download_events:
                    _log(
                        f"Queue rejection is still active after {queue_retry_wait_ms / 1000:.0f}s. "
                        "Closing the visible modal before retrying.",
                        started,
                    )
                    close_button = page.locator('.modal.show button[aria-label="Close"]')
                    if not close_button.count() or not close_button.first.is_visible():
                        raise RuntimeError(
                            "Spotisaver queue retry is required, but the visible modal Close "
                            f"button was not found. Last modal state: {snapshot!r}"
                        )
                    close_button.first.click()
                    _log("Clicked the modal Close button. Waiting for the modal to disappear.", started)

                    modal = page.locator(".modal.show")
                    modal_deadline = time.monotonic() + 10
                    while modal.count() and modal.first.is_visible():
                        if page.is_closed():
                            raise RuntimeError("Spotisaver page closed while closing the queue modal.")
                        if time.monotonic() >= modal_deadline:
                            raise RuntimeError(
                                "Spotisaver queue modal did not close after clicking Close. "
                                f"Last modal state: {snapshot!r}"
                            )
                        page.wait_for_timeout(250)

                    _log("Confirmed that the queue modal is closed.", started)
                    album_button = _find_album_download(page)
                    button_deadline = time.monotonic() + 10
                    while album_button is None and time.monotonic() < button_deadline:
                        if page.is_closed():
                            raise RuntimeError("Spotisaver page closed before the album button could be retried.")
                        page.wait_for_timeout(500)
                        album_button = _find_album_download(page)
                    if album_button is None:
                        _log_selector_state(page, "#downloadAllBtn")
                        raise RuntimeError(
                            "Spotisaver queue modal closed, but the verified "
                            "'Download entire playlist' button did not become available."
                        )

                    attempt += 1
                    _log(f"Submitting Spotisaver download attempt {attempt}.", started)
                    album_button.click()
                    _log(
                        f"Attempt {attempt} click returned. Monitoring for another queue "
                        "rejection or the browser download event.",
                        started,
                    )
                    queue_started = None
                    last_snapshot = None
                    last_heartbeat = time.monotonic()
                    continue
            # If the queue notice clears before the retry deadline, the normal
            # processing path below takes over and no retry is issued.
        elif queue_started is not None:
            _log(
                f"Spotisaver queue notice cleared during attempt {attempt}. "
                "Continuing to monitor processing without another click.",
                started,
            )
            queue_started = None

        if snapshot and snapshot != last_snapshot:
            status = snapshot.get("status", "")
            log_text = snapshot.get("log", "")
            if not queue_busy and (status or log_text):
                _log(
                    f"Spotisaver modal status: {status[:240]!r}; "
                    f"message: {log_text[:360]!r}",
                    started,
                )
            if snapshot.get("progress"):
                _log(f"Spotisaver progress indicator: {snapshot['progress']!r}", started)
            if snapshot.get("controls"):
                _log(f"Visible modal controls: {snapshot['controls'][:500]}", started)
            last_snapshot = snapshot

        failure = _download_failure(snapshot)
        if failure:
            raise RuntimeError(f"Spotisaver reported a download failure: {failure}")

        now = time.monotonic()
        if now - last_heartbeat >= 15:
            status = snapshot.get("status", "") if snapshot else ""
            summary = f" Current status: {status[:160]!r}." if status else ""
            _log(
                f"Still waiting for Spotisaver's browser download event "
                f"({now - started:.0f}s elapsed).{summary}",
                started,
            )
            last_heartbeat = now
        page.wait_for_timeout(1_000)

    _log(f"Browser download event received during attempt {attempt}.", started)
    download = download_events[0]
    suggested = Path(download.suggested_filename).name
    destination = target / suggested
    _log(f"Website suggested filename: {suggested!r}")
    _log(f"Saving browser download to: {destination}")
    try:
        download.save_as(str(destination))
    except Exception as exc:
        _log(f"SAVE FAILED for {destination}: {type(exc).__name__}: {exc}", started)
        raise
    if not destination.is_file():
        raise RuntimeError(f"Browser download did not create the expected file: {destination}")
    size = destination.stat().st_size
    _log(f"Saved file size: {size} bytes; elapsed download workflow: {time.monotonic() - started:.1f}s.")
    if size == 0:
        raise RuntimeError(f"Spotisaver produced an empty download: {suggested}")
    _log(f"Download validated successfully: {destination}", started)
    return destination

def _find_album_download(page: Any) -> Any | None:
    """Find Spotisaver's actual full-playlist button, never the scroll control."""
    direct = page.locator("#downloadAllBtn")
    if not direct.count():
        return None
    candidate = direct.first
    if not candidate.is_visible() or not candidate.is_enabled():
        return None
    label = candidate.inner_text(timeout=3_000).strip()
    if re.search(r"download\s+entire\s+playlist", label, re.I):
        return candidate
    return None


def _wait_for_album_download(
    page: Any,
    *,
    timeout_ms: int = 120_000,
    poll_interval_ms: int = 1_000,
) -> Any | None:
    """Poll for the real album download button until it is ready or time expires."""
    started = time.monotonic()
    next_status = 10.0
    _log(
        f"Polling for visible, enabled #downloadAllBtn every "
        f"{poll_interval_ms / 1000:.1f}s (timeout {timeout_ms / 1000:.0f}s)..."
    )
    while True:
        candidate = _find_album_download(page)
        if candidate is not None:
            elapsed = time.monotonic() - started
            _log(f"Album download button is ready after {elapsed:.1f}s.")
            return candidate

        elapsed = time.monotonic() - started
        remaining_ms = timeout_ms - int(elapsed * 1000)
        if remaining_ms <= 0:
            _log(f"Album download button did not become ready within {timeout_ms / 1000:.0f}s.")
            return None

        if elapsed >= next_status:
            _log(f"Still waiting for #downloadAllBtn ({elapsed:.0f}s elapsed).")
            next_status += 10.0

        page.wait_for_timeout(min(poll_interval_ms, remaining_ms))


def _log_page_snapshot(page: Any) -> None:
    """Capture useful page context when the expected download control never appears."""
    try:
        _log(f"Page title: {page.title()!r}")
    except Exception as exc:
        _log(f"Could not read page title: {type(exc).__name__}: {exc}")
    try:
        body = page.locator("body").inner_text(timeout=3_000)
        preview = re.sub(r"\s+", " ", body).strip()[:1_200]
        _log(f"Page text preview: {preview!r}")
    except Exception as exc:
        _log(f"Could not read page text: {type(exc).__name__}: {exc}")


def _find_playlist_navigation(page: Any) -> Any | None:
    """Find the intermediate button that only scrolls to the action area."""
    locator = page.locator("button.btn-playlist-download")
    if not locator.count():
        return None
    candidate = locator.first
    if not candidate.is_visible():
        return None
    label = candidate.inner_text(timeout=3_000).strip()
    return candidate if re.search(r"download\s+playlist", label, re.I) else None


def _log_visible_download_controls(page: Any) -> None:
    """Print a compact diagnostic list of visible buttons and links."""
    controls = page.locator("button:visible, a:visible").evaluate_all(
        r"""elements => elements.slice(0, 30).map(element => ({
            tag: element.tagName.toLowerCase(),
            text: (element.innerText || element.textContent || "").trim().replace(/\s+/g, " ").slice(0, 100),
            id: element.id || "",
            title: element.getAttribute("title") || "",
            aria: element.getAttribute("aria-label") || "",
            className: typeof element.className === "string" ? element.className : "",
            href: element.getAttribute("href") || "",
            download: element.getAttribute("download") || ""
        }))"""
    )
    if not controls:
        _log("No visible buttons or links were found.")
        return
    _log(f"Visible page controls (showing {len(controls)} maximum 30):")
    for item in controls:
        details = ", ".join(f"{key}={value!r}" for key, value in item.items() if value)
        _log(f"  <{item['tag']}> {details}")


def _find_track_download(page: Any, title: str) -> Any | None:
    text_locator = page.get_by_text(title, exact=True).first
    if not text_locator.count():
        text_locator = page.get_by_text(title, exact=False).first
    if not text_locator.count():
        return None
    current = text_locator
    for _ in range(6):
        buttons = current.get_by_role("button", name=re.compile(r"download", re.I))
        for index in range(buttons.count()):
            candidate = buttons.nth(index)
            if candidate.is_visible():
                return candidate
        current = current.locator("xpath=..")
    return None


def download_from_spotisaver(plan: dict, destination: Path, *, timeout_ms: int = 120_000) -> list[Path]:
    """Download one album through the normal visible website interface."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run py -m pip install -e . and "
            "py -m playwright install chromium."
        ) from exc

    workflow_started = time.monotonic()
    stage = "initialization"
    destination.mkdir(parents=True, exist_ok=True)
    album_id = plan["spotify_album_url"].rsplit("/", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9]{22}", album_id):
        raise RuntimeError("The Spotify album ID from TKKGData is invalid.")
    url = SPOTISAVER_ALBUM_URL.format(album_id=album_id)
    _log(f"Workflow started for {plan.get('spotify_album_title', 'unknown album')!r}.", workflow_started)
    _log(f"Destination directory: {destination}", workflow_started)
    _log(f"Launching visible Chromium for {url}", workflow_started)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            _log("Visible Chromium launched successfully.", workflow_started)
            page = browser.new_page(accept_downloads=True)
            try:
                stage = "page navigation"
                _log("Navigating to album page (wait_until=domcontentloaded)...", workflow_started)
                response = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                status = getattr(response, "status", None)
                _log(f"Navigation completed; HTTP status={status!r}.", workflow_started)
                stage = "document visibility"
                page.locator("body").wait_for(state="visible", timeout=30_000)
                _log("Document body is visible.", workflow_started)

                stage = "album download button polling"
                _log_selector_state(page, "#downloadAllBtn")
                album_download = _wait_for_album_download(
                    page,
                    timeout_ms=timeout_ms,
                    poll_interval_ms=1_000,
                )

                if album_download is None:
                    stage = "download control diagnostics"
                    _log(
                        "The full-playlist button did not appear during polling. "
                        "Capturing page state before trying the site's scroll control.",
                        workflow_started,
                    )
                    _log_selector_state(page, "#downloadAllBtn")
                    _log_selector_state(page, "#downloadAllBtnLabel")
                    _log_page_snapshot(page)
                    _log_visible_download_controls(page)

                    navigation = _find_playlist_navigation(page)
                    if navigation is not None:
                        nav_label = navigation.inner_text(timeout=3_000).strip()
                        _log(
                            f"Clicking intermediate navigation control {nav_label!r}; "
                            "this is only used after the normal polling period expires.",
                            workflow_started,
                        )
                        navigation.click()
                        _log("Intermediate navigation click returned; polling for the actual button for 15s.", workflow_started)
                        album_download = _wait_for_album_download(
                            page,
                            timeout_ms=15_000,
                            poll_interval_ms=1_000,
                        )
                    else:
                        _log("No usable intermediate navigation control was found.", workflow_started)

                if album_download is not None:
                    _log(
                        "The verified #downloadAllBtn control is ready. "
                        "Clicking directly without scrolling.",
                        workflow_started,
                    )

                if album_download is not None:
                    label = album_download.inner_text(timeout=3_000).strip()
                    _log(f"Selected album download control: {label!r}.", workflow_started)
                    stage = "album download click and browser event"
                    result = _download_click(page, album_download, destination)
                    _log(f"Album download workflow completed: {result.name}", workflow_started)
                    return [result]

                stage = "download control diagnostics"
                _log(
                    "No verified album download button was found. Collecting visible control "
                    "inventory before individual track fallback.",
                    workflow_started,
                )
                _log_visible_download_controls(page)
                _log("Starting sequential individual-track fallback.", workflow_started)
                files: list[Path] = []
                for index, track in enumerate(plan["tracks"], start=1):
                    number = track["track_number"]
                    title = track["spotify_title"]
                    stage = f"track {number} control discovery"
                    _log(f"Track fallback {index}/{len(plan['tracks'])}: locating {title!r}.", workflow_started)
                    button = _find_track_download(page, title)
                    if button is None:
                        raise RuntimeError(
                            f"Could not locate the normal Download control for track "
                            f"{number}/{plan['track_count']} ({title})."
                        )
                    _log(f"Found visible Download control for track {number}: {title!r}.", workflow_started)
                    stage = f"track {number} download"
                    files.append(_download_click(page, button, destination))
                    _log(f"Track {number}/{len(plan['tracks'])} saved: {files[-1].name}", workflow_started)
                _log(f"All {len(files)} individual track downloads completed.", workflow_started)
                return files
            finally:
                _log("Closing visible Chromium browser.", workflow_started)
                browser.close()
    except PlaywrightTimeoutError as exc:
        _log(
            f"FAILED during {stage}: Playwright timeout after "
            f"{time.monotonic() - workflow_started:.1f}s: {exc}",
            workflow_started,
        )
        traceback.print_exc()
        raise RuntimeError(
            f"Spotisaver timed out during {stage} after "
            f"{time.monotonic() - workflow_started:.1f}s: {exc}"
        ) from exc
    except RuntimeError as exc:
        _log(f"FAILED during {stage}: {type(exc).__name__}: {exc}", workflow_started)
        traceback.print_exc()
        raise
    except Exception as exc:
        message = str(exc)
        _log(
            f"FAILED during {stage}: {type(exc).__name__}: {message}",
            workflow_started,
        )
        traceback.print_exc()
        if any(term in message.lower() for term in ("captcha", "rate limit", "too many requests", "access denied")):
            raise RuntimeError(
                f"Spotisaver displayed an access or rate restriction during {stage}: {message}. "
                "The downloader stopped without attempting to bypass it."
            ) from exc
        raise RuntimeError(f"Spotisaver browser workflow failed during {stage}: {message}") from exc


def download_and_import(plan: dict, work_dir: Path) -> list[Path]:
    downloads = work_dir / "spotisaver-downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    files = download_from_spotisaver(plan, downloads)
    return import_audio_files(files, plan["tracks"], work_dir / "validated-tracks")
