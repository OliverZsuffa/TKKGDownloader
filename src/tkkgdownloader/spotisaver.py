"""Visible Playwright integration for Spotisaver's public album page."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import unicodedata

from .audio_import import import_audio_files

SPOTISAVER_ALBUM_URL = "https://spotisaver.net/en/album/{album_id}/"


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def _album_title(title: str) -> str:
    return title.split("/", 1)[-1].strip() if "/" in title else title.strip()



def _wait_for_album_data(page: Any, plan: dict, timeout_ms: int = 120_000) -> None:
    """Wait for Spotisaver's client-side album lookup and tracklist to finish."""
    album = _normalize(_album_title(plan["spotify_album_title"]))
    track_titles = [
        _normalize(track["spotify_title"])
        for track in plan["tracks"]
        if len(_normalize(track["spotify_title"])) >= 5
    ]
    if len(album) < 5 or not track_titles:
        raise RuntimeError("TKKGData does not contain enough album identity data to verify Spotisaver.")

    print(
        "Waiting for Spotisaver to load the album metadata and complete tracklist "
        f"(up to {timeout_ms // 1000} seconds)...",
        flush=True,
    )
    page.wait_for_function(
        """([expectedAlbum, expectedTracks]) => {
            const body = document.body?.innerText || "";
            const normalize = value => value
                .normalize("NFKD")
                .replace(/[\\u0300-\\u036f]/g, "")
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "");
            const content = normalize(body);
            return content.includes(expectedAlbum) &&
                expectedTracks.every(title => content.includes(title));
        }""",
        arg=[album, track_titles],
        timeout=timeout_ms,
    )
    print("Spotisaver album metadata and all expected track titles are loaded.", flush=True)

def _verify_album_page(page: Any, plan: dict) -> None:
    body = page.locator("body").inner_text(timeout=15_000)
    normalized_body = _normalize(body)
    expected_album = _normalize(_album_title(plan["spotify_album_title"]))
    if len(expected_album) < 5 or expected_album not in normalized_body:
        raise RuntimeError(
            "Spotisaver page does not visibly identify the expected album "
            f"{plan['spotify_album_title']!r}. No download was started."
        )
    missing = []
    for track in plan["tracks"]:
        title = _normalize(track["spotify_title"])
        if len(title) >= 5 and title not in normalized_body:
            missing.append(track["track_number"])
    if missing:
        preview = ", ".join(str(number) for number in missing[:8])
        raise RuntimeError(
            "Spotisaver's visible tracklist does not match TKKGData. "
            f"Track titles not found: {preview}. No download was started."
        )


def _download_click(page: Any, locator: Any, target: Path, timeout_ms: int) -> Path:
    with page.expect_download(timeout=timeout_ms) as download_info:
        locator.click()
    download = download_info.value
    suggested = Path(download.suggested_filename).name
    destination = target / suggested
    download.save_as(str(destination))
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"Spotisaver produced an empty download: {suggested}")
    return destination


def _find_album_download(page: Any) -> Any | None:
    patterns = re.compile(r"(download\s*(all|album|zip)|album\s*download|download\s*as\s*zip)", re.I)
    for role in ("button", "link"):
        locator = page.get_by_role(role, name=patterns)
        if locator.count():
            return locator.first
    return None


def _find_track_download(page: Any, title: str) -> Any | None:
    text_locator = page.get_by_text(title, exact=True).first
    if not text_locator.count():
        text_locator = page.get_by_text(title, exact=False).first
    if not text_locator.count():
        return None
    current = text_locator
    for _ in range(6):
        buttons = current.get_by_role("button", name=re.compile(r"download", re.I))
        if buttons.count() == 1:
            return buttons.first
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

    destination.mkdir(parents=True, exist_ok=True)
    album_id = plan["spotify_album_url"].rsplit("/", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9]{22}", album_id):
        raise RuntimeError("The Spotify album ID from TKKGData is invalid.")
    url = SPOTISAVER_ALBUM_URL.format(album_id=album_id)
    print(f"Opening Spotisaver album in visible Chromium: {url}", flush=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page(accept_downloads=True)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.locator("body").wait_for(state="visible", timeout=30_000)
                _wait_for_album_data(page, plan, timeout_ms=120_000)
                _verify_album_page(page, plan)
                album_download = _find_album_download(page)
                if album_download is not None:
                    print("Starting the website's album download...", flush=True)
                    return [_download_click(page, album_download, destination, timeout_ms)]

                print(
                    "No album ZIP control was found. Downloading the visible track controls "
                    "one at a time.",
                    flush=True,
                )
                files: list[Path] = []
                for track in plan["tracks"]:
                    number = track["track_number"]
                    button = _find_track_download(page, track["spotify_title"])
                    if button is None:
                        raise RuntimeError(
                            f"Could not locate the normal Download control for track "
                            f"{number}/{plan['track_count']} ({track['spotify_title']})."
                        )
                    print(f"Downloading track {number}/{plan['track_count']}...", flush=True)
                    files.append(_download_click(page, button, destination, timeout_ms))
                return files
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(
                    "Spotisaver did not finish loading the expected album data or complete "
                    "the download within the timeout. The browser was left without further "
                    "interaction. Check the site and try again."
                ) from exc
            finally:
                browser.close()
    except RuntimeError:
        raise
    except Exception as exc:
        message = str(exc)
        if any(term in message.lower() for term in ("captcha", "rate limit", "too many requests", "access denied")):
            raise RuntimeError(
                f"Spotisaver displayed an access or rate restriction: {message}. "
                "The downloader stopped without attempting to bypass it."
            ) from exc
        raise RuntimeError(f"Spotisaver browser workflow failed: {message}") from exc


def download_and_import(plan: dict, work_dir: Path) -> list[Path]:
    downloads = work_dir / "spotisaver-downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    files = download_from_spotisaver(plan, downloads)
    return import_audio_files(files, plan["tracks"], work_dir / "validated-tracks")
