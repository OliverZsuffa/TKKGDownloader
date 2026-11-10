from __future__ import annotations

import contextlib
import io
import os
import tempfile
import time
import warnings
from unittest.mock import patch
import unittest
import zipfile
from pathlib import Path

from tkkgdownloader.audio_import import import_audio_files
from tkkgdownloader.cli import build_parser
from tkkgdownloader.spotisaver import (
    _download_click,
    _ProgressReporter,
    _render_progress_bar,
    _create_diagnostic_logger,
    _download_failure,
    _queue_retry_seconds,
    _find_album_download,
    _find_playlist_navigation,
    _log_selector_state,
    _wait_for_album_download,
)


def tracks():
    return [
        {"track_number": 1, "spotify_title": "TKKG 150 Teil 01"},
        {"track_number": 2, "spotify_title": "TKKG 150 Teil 02"},
    ]


class SpotisaverImportTests(unittest.TestCase):
    def test_imports_zip_and_orders_by_tkkgdata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "album.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("Album/TKKG 150 Teil 02.mp3", b"second")
                zipped.writestr("Album/TKKG 150 Teil 01.mp3", b"first")
                zipped.writestr("Album/cover.jpg", b"image")
            result = import_audio_files([archive], tracks(), root / "work")
            self.assertEqual([path.name for path in result], [
                "01 - TKKG 150 Teil 01.mp3",
                "02 - TKKG 150 Teil 02.mp3",
            ])
            self.assertEqual(result[0].read_bytes(), b"first")
            self.assertEqual(result[1].read_bytes(), b"second")

    def test_rejects_missing_track(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "album.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("TKKG 150 Teil 01.mp3", b"first")
                zipped.writestr("TKKG 150 Teil 03.mp3", b"third")
            with self.assertRaisesRegex(RuntimeError, "uniquely match"):
                import_audio_files([archive], tracks(), root / "work")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("../escape.mp3", b"bad")
            with self.assertRaisesRegex(RuntimeError, "Unsafe path"):
                import_audio_files([archive], tracks(), root / "work")

    def test_rejects_corrupt_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "bad.zip"
            archive.write_bytes(b"not a zip")
            with self.assertRaisesRegex(RuntimeError, "corrupt ZIP"):
                import_audio_files([archive], tracks(), root / "work")

    def test_rejects_empty_track(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "album.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("TKKG 150 Teil 01.mp3", b"")
                zipped.writestr("TKKG 150 Teil 02.mp3", b"second")
            with self.assertRaisesRegex(RuntimeError, "empty"):
                import_audio_files([archive], tracks(), root / "work")


class FakeLocator:
    def __init__(self, label='', visible=True):
        self.label = label
        self.visible = visible
        self.enabled = True
        self.first = self

    def count(self):
        return 1 if self.label or self.visible else 0

    def is_visible(self):
        return self.visible

    def is_enabled(self):
        return self.enabled

    def inner_text(self, timeout=None):
        return self.label

    def nth(self, index):
        return self

class FakePage:
    def __init__(self, direct=None, navigation=None):
        self.direct = direct or FakeLocator('', visible=False)
        self.navigation = navigation or FakeLocator('', visible=False)

    def locator(self, selector):
        if selector == '#downloadAllBtn':
            return self.direct
        if selector == 'button.btn-playlist-download':
            return self.navigation
        raise AssertionError(f'Unexpected selector: {selector}')

    def get_by_role(self, role, name):
        return FakeLocator('', visible=False)

    def wait_for_timeout(self, timeout):
        self.waited = getattr(self, 'waited', 0) + timeout
        time.sleep(timeout / 1000)

class SpotisaverDownloadControlTests(unittest.TestCase):
    def test_prefers_visible_entire_playlist_button(self):
        button = FakeLocator('Download entire playlist')
        self.assertIs(_find_album_download(FakePage(direct=button)), button)

    def test_does_not_select_hidden_playlist_button(self):
        button = FakeLocator('Download entire playlist', visible=False)
        self.assertIsNone(_find_album_download(FakePage(direct=button)))

    def test_rejects_disabled_download_button(self):
        button = FakeLocator('Download entire playlist')
        button.enabled = False
        self.assertIsNone(_find_album_download(FakePage(direct=button)))

    def test_polls_until_direct_button_becomes_visible(self):
        class AppearingLocator(FakeLocator):
            def __init__(self):
                super().__init__('Download entire playlist', visible=False)
                self.checks = 0

            def is_visible(self):
                self.checks += 1
                self.visible = self.checks >= 3
                return self.visible

        button = AppearingLocator()
        page = FakePage(direct=button)
        result = _wait_for_album_download(page, timeout_ms=50, poll_interval_ms=1)
        self.assertIs(result, button)
        self.assertEqual(page.waited, 2)

    def test_times_out_without_clicking_or_selecting_scroll_control(self):
        page = FakePage(direct=FakeLocator('Download entire playlist', visible=False))
        result = _wait_for_album_download(page, timeout_ms=2, poll_interval_ms=1)
        self.assertIsNone(result)
        self.assertEqual(page.waited, 2)

    def test_finds_scroll_control_only_as_fallback(self):
        button = FakeLocator('Download Playlist')
        self.assertIs(_find_playlist_navigation(FakePage(navigation=button)), button)

    def test_rejects_unrelated_navigation_button(self):
        button = FakeLocator('Play playlist')
        self.assertIsNone(_find_playlist_navigation(FakePage(navigation=button)))

class SpotisaverCliTests(unittest.TestCase):
    def test_provider_is_opt_in(self):
        args = build_parser().parse_args(["150"])
        self.assertEqual(args.provider, "yt-dlp")

    def test_spotisaver_provider_can_be_selected(self):
        args = build_parser().parse_args(["150", "--provider", "spotisaver"])
        self.assertEqual(args.provider, "spotisaver")


class SpotisaverDiagnosticsTests(unittest.TestCase):
    def test_selector_diagnostic_reports_visibility_and_attributes(self):
        class DiagnosticLocator:
            first = None

            def __init__(self):
                self.first = self

            def count(self):
                return 1

            def nth(self, index):
                return self

            def is_visible(self):
                return True

            def inner_text(self, timeout=None):
                return "Download entire playlist"

            def get_attribute(self, name):
                return {
                    "id": "downloadAllBtn",
                    "class": "btn-success",
                    "title": "Download all",
                }.get(name)

        class DiagnosticPage:
            def locator(self, selector):
                self.selector = selector
                return DiagnosticLocator()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            count = _log_selector_state(DiagnosticPage(), "#downloadAllBtn")
        self.assertEqual(count, 1)
        self.assertEqual(output.getvalue(), "")

    def test_module_compiles_without_invalid_escape_warnings(self):
        module_path = Path(__file__).parents[1] / "src" / "tkkgdownloader" / "spotisaver.py"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            compile(module_path.read_text(encoding="utf-8"), str(module_path), "exec")
        syntax_warnings = [item for item in caught if issubclass(item.category, SyntaxWarning)]
        self.assertEqual(syntax_warnings, [])

    def test_download_click_registers_listener_before_click_and_saves(self):
        class FakeDownload:
            suggested_filename = "album.zip"

            def save_as(self, path):
                Path(path).write_bytes(b"archive")

        class DownloadPage:
            def __init__(self):
                self.events = {}
                self.closed = False
                self.waited = 0
                self.snapshot = {
                    "status": "Downloading playlist...",
                    "log": "",
                    "failed": "",
                    "progress": "0 100%",
                    "controls": "[]",
                }

            def on(self, event, callback):
                self.events[event] = callback

            def evaluate(self, script):
                return self.snapshot

            def is_closed(self):
                return self.closed

            def wait_for_timeout(self, timeout):
                self.waited += timeout
                self.events["download"](FakeDownload())

        class ClickLocator:
            def __init__(self, page):
                self.page = page
                self.clicked = 0

            def click(self):
                self.clicked += 1
                self.assert_listener_registered = "download" in self.page.events

        with tempfile.TemporaryDirectory() as temp:
            page = DownloadPage()
            locator = ClickLocator(page)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = _download_click(page, locator, Path(temp))
            self.assertEqual(locator.clicked, 1)
            self.assertTrue(locator.assert_listener_registered)
            self.assertEqual(result.name, "album.zip")
            self.assertEqual(result.read_bytes(), b"archive")
            self.assertIn("Starting download...", output.getvalue())
            self.assertIn("Waiting for queue...", output.getvalue())
            self.assertNotIn("Browser download event received", output.getvalue())
            self.assertNotIn("album.zip", output.getvalue())
            self.assertNotIn("Saved file size", output.getvalue())

    def test_download_click_waits_through_queue_notice_without_second_click(self):
        class FakeDownload:
            suggested_filename = "album.zip"

            def save_as(self, path):
                Path(path).write_bytes(b"archive")

        class DownloadPage:
            def __init__(self):
                self.events = {}
                self.closed = False
                self.waited = 0
                self.snapshots = [
                    {
                        "status": "Downloading playlist...",
                        "log": "Sorry, all download slots are busy right now. Please try again in 25 sec.",
                        "failed": "",
                        "progress": "0 100%",
                        "controls": "[]",
                    },
                    {
                        "status": "Downloading playlist...",
                        "log": "",
                        "failed": "",
                        "progress": "50 100%",
                        "controls": "[]",
                    },
                ]

            def on(self, event, callback):
                self.events[event] = callback

            def evaluate(self, script):
                return self.snapshots[min(self.waited, len(self.snapshots) - 1)]

            def is_closed(self):
                return self.closed

            def wait_for_timeout(self, timeout):
                self.waited += 1
                if self.waited == 3:
                    self.events["download"](FakeDownload())

        class ClickLocator:
            def __init__(self):
                self.clicked = 0

            def click(self):
                self.clicked += 1

        with tempfile.TemporaryDirectory() as temp:
            page = DownloadPage()
            locator = ClickLocator()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = _download_click(page, locator, Path(temp))
            self.assertEqual(locator.clicked, 1)
            self.assertEqual(page.waited, 3)
            self.assertEqual(result.name, "album.zip")
            self.assertIn("Queue busy. Retrying in 30 seconds.", output.getvalue())
            self.assertIn("Downloading...", output.getvalue())
            self.assertNotIn("rejected attempt", output.getvalue())
            self.assertNotIn("Website retry instruction", output.getvalue())
            self.assertNotIn("queue notice cleared", output.getvalue())

    def test_queue_retry_delay_parser(self):
        snapshot = {
            "status": "Downloading playlist...",
            "log": "Sorry, all download slots are busy. Please try again in 25 sec.",
        }
        self.assertEqual(_queue_retry_seconds(snapshot), 25)
        snapshot["log"] = "All download slots are busy. Please try again in 2 minutes."
        self.assertEqual(_queue_retry_seconds(snapshot), 120)

    def test_queue_notice_is_not_treated_as_final_failure(self):
        snapshot = {
            "status": "Downloading playlist...",
            "log": "Sorry, all download slots are busy. Please try again in 25 sec.",
            "failed": "",
        }
        self.assertIsNone(_download_failure(snapshot))

    def test_explicit_modal_failure_is_reported(self):
        snapshot = {
            "status": "Download failed",
            "log": "Unable to download playlist",
            "failed": "",
        }
        self.assertIn("Download failed", _download_failure(snapshot))

    def test_page_closure_before_event_fails_with_last_status(self):
        class ClosedPage:
            def __init__(self):
                self.callback = None

            def on(self, event, callback):
                self.callback = callback

            def is_closed(self):
                return True

        class ClickLocator:
            def click(self):
                pass

        with self.assertRaisesRegex(RuntimeError, "page closed before a browser download event"):
            _download_click(ClosedPage(), ClickLocator(), Path("."))

    def test_keyboard_interrupt_propagates_without_retry(self):
        class InterruptPage:
            def on(self, event, callback):
                self.callback = callback

            def evaluate(self, script):
                return {"status": "Downloading playlist...", "log": "", "failed": "", "progress": "", "controls": ""}

            def is_closed(self):
                return False

            def wait_for_timeout(self, timeout):
                raise KeyboardInterrupt

        class ClickLocator:
            def __init__(self):
                self.clicked = 0

            def click(self):
                self.clicked += 1

        locator = ClickLocator()
        with self.assertRaises(KeyboardInterrupt):
            _download_click(InterruptPage(), locator, Path("."))
        self.assertEqual(locator.clicked, 1)


    def test_queue_rejection_closes_modal_waits_and_reclicks_once(self):
        class Clock:
            now = 0.0

            def monotonic(self):
                return self.now

        clock = Clock()

        class FakeDownload:
            suggested_filename = "album.zip"

            def save_as(self, path):
                Path(path).write_bytes(b"archive")

        class ModalLocator:
            def __init__(self, page):
                self.page = page
                self.first = self

            def count(self):
                return 1

            def is_visible(self):
                return self.page.modal_open

        class CloseButton:
            def __init__(self, page):
                self.page = page
                self.first = self

            def count(self):
                return 1 if self.page.modal_open else 0

            def is_visible(self):
                return self.page.modal_open

            def click(self):
                self.page.close_clicks += 1
                self.page.modal_open = False

        class AlbumButton:
            def __init__(self, page):
                self.page = page
                self.first = self

            def count(self):
                return 1

            def is_visible(self):
                return not self.page.modal_open

            def is_enabled(self):
                return True

            def inner_text(self, timeout=None):
                return "Download entire playlist"

            def click(self):
                self.page.album_clicks += 1
                if self.page.album_clicks == 2:
                    self.page.modal_open = True

        class RetryPage:
            def __init__(self):
                self.events = {}
                self.modal_open = True
                self.album_clicks = 0
                self.close_clicks = 0

            def on(self, event, callback):
                self.events[event] = callback

            def locator(self, selector):
                if selector == '.modal.show button[aria-label="Close"]':
                    return CloseButton(self)
                if selector == ".modal.show":
                    return ModalLocator(self)
                if selector == "#downloadAllBtn":
                    return AlbumButton(self)
                raise AssertionError(f"Unexpected selector: {selector}")

            def evaluate(self, script):
                if self.album_clicks == 1:
                    return {
                        "status": "Downloading playlist...",
                        "log": "Sorry, all download slots are busy right now. Please try again in 25 sec.",
                        "failed": "",
                        "progress": "0 100%",
                        "controls": '[{"aria":"Close"}]',
                    }
                return {
                    "status": "Downloading playlist...",
                    "log": "",
                    "failed": "",
                    "progress": "100 100%",
                    "controls": "[]",
                }

            def is_closed(self):
                return False

            def wait_for_timeout(self, timeout):
                clock.now += timeout / 1000
                if self.album_clicks >= 2 and clock.now >= 31:
                    self.events["download"](FakeDownload())

        page = RetryPage()
        first_button = AlbumButton(page)
        with tempfile.TemporaryDirectory() as temp:
            output = io.StringIO()
            with patch("tkkgdownloader.spotisaver.time.monotonic", clock.monotonic):
                with contextlib.redirect_stdout(output):
                    result = _download_click(
                        page,
                        first_button,
                        Path(temp),
                        queue_retry_wait_ms=30_000,
                    )
        self.assertEqual(page.album_clicks, 2)
        self.assertEqual(page.close_clicks, 1)
        self.assertEqual(result.name, "album.zip")
        self.assertIn("Queue busy. Retrying in 30 seconds.", output.getvalue())
        self.assertIn("Downloading...", output.getvalue())
        self.assertNotIn("Submitting Spotisaver download attempt", output.getvalue())
        self.assertNotIn("Browser download event received", output.getvalue())

    def test_generic_stall_does_not_trigger_retry(self):
        class FakeDownload:
            suggested_filename = "album.zip"

            def save_as(self, path):
                Path(path).write_bytes(b"archive")

        class Page:
            def __init__(self):
                self.events = {}
                self.waits = 0
                self.clicked = 0

            def on(self, event, callback):
                self.events[event] = callback

            def evaluate(self, script):
                return {
                    "status": "Downloading playlist...",
                    "log": "",
                    "failed": "",
                    "progress": "0 100%",
                    "controls": "[]",
                }

            def is_closed(self):
                return False

            def wait_for_timeout(self, timeout):
                self.waits += 1
                if self.waits == 2:
                    self.events["download"](FakeDownload())

        class Button:
            def __init__(self, page):
                self.page = page

            def click(self):
                self.page.clicked += 1

        page = Page()
        with tempfile.TemporaryDirectory() as temp:
            result = _download_click(page, Button(page), Path(temp), queue_retry_wait_ms=0)
        self.assertEqual(page.clicked, 1)
        self.assertEqual(result.name, "album.zip")


class SpotisaverConsoleTests(unittest.TestCase):

    def test_diagnostic_logs_are_unique_and_persist_outside_work_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "state")}):
                first, first_path = _create_diagnostic_logger(148)
                second, second_path = _create_diagnostic_logger(148)
            try:
                self.assertNotEqual(first_path, second_path)
                self.assertTrue(first_path.parent.is_dir())
                self.assertIn("148", first_path.name)
                first.info("diagnostic test")
                for handler in list(first.handlers):
                    handler.flush()
                    handler.close()
                    first.removeHandler(handler)
                self.assertIn("diagnostic test", first_path.read_text(encoding="utf-8"))
            finally:
                for logger in (first, second):
                    for handler in list(logger.handlers):
                        handler.close()
                        logger.removeHandler(handler)

    def test_progress_line_uses_track_count_and_eta(self):
        snapshot = {
            "status": "Downloaded 8 of 40 tracks",
            "progress": "20%",
            "eta_minutes": "5",
            "eta_seconds": "20",
        }
        line = _render_progress_bar(snapshot)
        self.assertIn("8/40 tracks", line)
        self.assertIn("20%", line)
        self.assertIn("ETA 5m 20s", line)

    def test_progress_fallback_does_not_mislabel_percentage_as_track_count(self):
        snapshot = {
            "status": "Downloading playlist",
            "progress": "20%",
            "eta_minutes": "",
            "eta_seconds": "",
        }
        line = _render_progress_bar(snapshot)
        self.assertIn("20%", line)
        self.assertNotIn("20/100 tracks", line)
        self.assertNotIn("ETA", line)

    def test_missing_eta_is_not_retained(self):
        first = {"status": "Downloaded 8 of 40 tracks", "progress": "20%", "eta_minutes": "5", "eta_seconds": "20"}
        second = {"status": "Downloaded 9 of 40 tracks", "progress": "22%", "eta_minutes": "", "eta_seconds": ""}
        self.assertIn("ETA 5m 20s", _render_progress_bar(first))
        self.assertNotIn("ETA", _render_progress_bar(second))

    def test_no_color_environment_disables_ansi(self):
        class TTY(io.StringIO):
            def isatty(self):
                return True

        stream = TTY()
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            with contextlib.redirect_stdout(stream):
                reporter = _ProgressReporter()
                reporter.stage("Queue busy.", "warning")
        self.assertEqual(stream.getvalue(), "Queue busy.\n")

    def test_noninteractive_output_disables_ansi(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            reporter = _ProgressReporter()
            reporter.stage("Browser opened.", "success")
        self.assertEqual(stream.getvalue(), "Browser opened.\n")

    def test_interactive_stage_uses_semantic_colour(self):
        class TTY(io.StringIO):
            def isatty(self):
                return True

        stream = TTY()
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=False):
            with patch.dict(os.environ, {"NO_COLOR": ""}):
                with contextlib.redirect_stdout(stream):
                    reporter = _ProgressReporter()
                    reporter.stage("Queue busy.", "warning")
        self.assertIn("\033[33m", stream.getvalue())
        self.assertIn("Queue busy.", stream.getvalue())
        self.assertIn("\033[0m", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
