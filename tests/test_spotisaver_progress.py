from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import re
from unittest.mock import patch

import tkkgdownloader.spotisaver as spotisaver_module

from tkkgdownloader.spotisaver import (
    _find_zip_download_button,
    _format_eta,
    _parse_track_progress,
    _render_progress_bar,
    _download_click,
    _ProgressReporter,
    _browser_launch_options,
    _format_duration,
)


class FakeButton:
    def __init__(self, label: str, *, visible: bool = True, enabled: bool = True, on_click=None):
        self.label = label
        self.visible = visible
        self.enabled = enabled
        self.on_click = on_click
        self.clicked = 0
        self.first = self

    def count(self):
        return 1

    def is_visible(self):
        return self.visible

    def is_enabled(self):
        return self.enabled

    def inner_text(self, timeout=None):
        return self.label

    def click(self):
        self.clicked += 1
        if self.on_click:
            self.on_click()


class ButtonCollection:
    def __init__(self, buttons):
        self.buttons = buttons
        self.first = buttons[0] if buttons else None

    def count(self):
        return len(self.buttons)

    def nth(self, index):
        return self.buttons[index]


class FakeModal:
    def __init__(self, buttons):
        self.buttons = buttons
        self.first = self

    def count(self):
        return 1

    def is_visible(self):
        return True

    def get_by_role(self, role, name):
        return ButtonCollection([
            button for button in self.buttons
            if role == "button" and name.fullmatch(button.label)
        ])

    def locator(self, selector):
        if selector == "button":
            return ButtonCollection(self.buttons)
        raise AssertionError(selector)


class FakePage:
    def __init__(self, snapshot, zip_button):
        self.snapshot = snapshot
        self.events = {}
        self.zip_button = zip_button
        self.modal = FakeModal([zip_button])
        self.closed = False

    def on(self, event, callback):
        self.events[event] = callback

    def evaluate(self, script):
        return self.snapshot

    def locator(self, selector):
        if selector == ".modal.show":
            return self.modal
        raise AssertionError(selector)

    def is_closed(self):
        return self.closed

    def wait_for_timeout(self, timeout):
        if self.zip_button.clicked and not getattr(self, "download_sent", False):
            self.download_sent = True
            self.events["download"](FakeDownload())


class FakeDownload:
    suggested_filename = "album.zip"

    def save_as(self, path):
        Path(path).write_bytes(b"verified archive")


class SpotisaverProgressTests(unittest.TestCase):
    def test_parses_track_count_and_percentage(self):
        self.assertEqual(
            _parse_track_progress({"status": "Downloaded 30 of 40", "progress": "75 75%"}),
            (30, 40, 75),
        )

    def test_falls_back_to_progress_percentage(self):
        self.assertEqual(
            _parse_track_progress({"status": "Creating ZIP archive", "progress": "98 98%"}),
            (98, 100, 98),
        )

    def test_rejects_invalid_track_count(self):
        self.assertIsNone(_parse_track_progress({"status": "Downloaded 41 of 40", "progress": ""}))

    def test_formats_eta_and_rejects_invalid_values(self):
        self.assertEqual(_format_eta({"eta_minutes": "1", "eta_seconds": "32"}), "1m 32s")
        self.assertEqual(_format_eta({"eta_minutes": "0", "eta_seconds": "8"}), "8s")
        self.assertEqual(_format_eta({"eta_minutes": "", "eta_seconds": "42"}), "42s")
        self.assertEqual(_format_eta({"eta_minutes": "2m", "eta_seconds": "05s"}), "2m 05s")
        self.assertEqual(_format_eta({"eta": "Estimated time: 42s"}), "42s")
        self.assertEqual(_format_eta({"eta": "Estimated time: 1m 05s"}), "1m 05s")
        self.assertIsNone(_format_eta({"eta_minutes": "1", "eta_seconds": "75"}))
        self.assertIsNone(_format_eta({"eta_minutes": "", "eta_seconds": ""}))

    def test_renders_pip_style_progress_line(self):
        line = _render_progress_bar({
            "status": "Downloaded 30 of 40",
            "progress": "75 75%",
            "eta_minutes": "1",
            "eta_seconds": "32",
        })
        self.assertIn("30/40 tracks", line)
        self.assertIn("75%", line)
        self.assertIn("ETA 1m 32s", line)
        self.assertIn("█", line)
        self.assertIn("░", line)

    def test_queue_wait_is_printed_once_in_noninteractive_output(self):
        reporter = _ProgressReporter()
        reporter.interactive = False
        output = io.StringIO()
        with patch("tkkgdownloader.spotisaver.time.monotonic", side_effect=[100.0, 100.0, 102.0]):
            with contextlib.redirect_stdout(output):
                reporter.start_queue_wait()
                reporter.finish_queue_wait()
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^Waiting for download slot\.\.\. \d+m \d{2}s elapsed$")

    def test_queue_wait_uses_one_carriage_return_line_interactively(self):
        reporter = _ProgressReporter()
        reporter.interactive = True
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            reporter.start_queue_wait()
            reporter.update_queue_wait()
            reporter.finish_queue_wait()
        self.assertEqual(output.getvalue().count("\r"), 1)
        self.assertEqual(output.getvalue().count("\n"), 1)

    def test_elapsed_duration_formatting(self):
        self.assertEqual(_format_duration(0), "0s")
        self.assertEqual(_format_duration(63), "1m 03s")
        self.assertEqual(_format_duration(3661), "1h 01m 01s")

    def test_browser_launch_defaults_to_headless_and_muted(self):
        self.assertEqual(_browser_launch_options(), {
            "headless": True,
            "args": ["--mute-audio"],
        })

    def test_browser_launch_overrides_are_independent(self):
        self.assertEqual(_browser_launch_options(show_browser=True), {
            "headless": False,
            "args": ["--mute-audio"],
        })
        self.assertEqual(_browser_launch_options(mute_browser_audio=False), {
            "headless": True,
        })

    def test_transfer_progress_formats_known_and_unknown_totals(self):
        reporter = _ProgressReporter()
        reporter.interactive = False
        reporter.last_report = 0
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            reporter.update_transfer(12_400_000, 25_800_000)
            reporter.last_report = 0
            reporter.update_transfer(12_400_000, None)
        self.assertEqual(output.getvalue(), "")
        with contextlib.redirect_stdout(output):
            reporter.finish_transfer(25_800_000, 25_800_000)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("100%", lines[0])
        self.assertIn("24.6 MB / 24.6 MB", lines[0])

    def test_interactive_progress_clears_longer_previous_line(self):
        class TTY(io.StringIO):
            def isatty(self):
                return True
        output = TTY()
        with contextlib.redirect_stdout(output):
            reporter = _ProgressReporter()
            reporter.update({"status": "Downloaded 40 of 40 tracks", "progress": "100%"}, 0)
            reporter.update({"status": "Downloaded 1 of 40 tracks", "progress": "3%"}, 0)
        self.assertGreaterEqual(output.getvalue().count("\r"), 2)

    def test_track_phase_message_precedes_its_first_progress_update(self):
        class Reporter:
            def __init__(self):
                self.queue_wait_started = None
                self.events = []
            def stage(self, message, tone="info"):
                self.events.append(("stage", message))
            def start_queue_wait(self):
                self.queue_wait_started = 0
            def update_queue_wait(self):
                pass
            def finish_queue_wait(self):
                self.queue_wait_started = None
                return 0
            def update(self, snapshot, started):
                self.events.append(("update", snapshot.get("status", "")))
            def update_task(self, label, current, total):
                self.events.append(("task", label, current, total))
            def finish_transfer(self, received, total):
                pass
            def finish(self):
                pass
            def update_transfer(self, received, total):
                pass

        class Page(FakePage):
            def __init__(self, snapshot, zip_button):
                super().__init__(snapshot, zip_button)
                self.polls = 0
            def evaluate(self, script):
                return self.snapshot
            def wait_for_timeout(self, timeout):
                self.polls += 1
                if self.polls == 1:
                    self.snapshot = {
                        "status": "ZIP archive created.",
                        "log": "",
                        "failed": "",
                        "progress": "100 100%",
                        "eta": "",
                        "eta_template": "",
                        "eta_minutes": "",
                        "eta_seconds": "",
                        "controls": '[{"text":"Download ZIP"}]',
                    }
                elif self.zip_button.clicked and not getattr(self, "download_sent", False):
                    self.download_sent = True
                    self.events["download"](FakeDownload())

        reporter = Reporter()
        zip_button = FakeButton("Download ZIP")
        page = Page({
            "status": "Downloaded 1 of 40 tracks",
            "log": "",
            "failed": "",
            "progress": "2 2%",
            "eta": "",
            "eta_template": "",
            "eta_minutes": "",
            "eta_seconds": "",
            "controls": "[]",
        }, zip_button)

        class AlbumButton:
            def click(self):
                pass

        with tempfile.TemporaryDirectory() as temp, patch.object(
            spotisaver_module, "_ACTIVE_PROGRESS_REPORTER", reporter
        ):
            _download_click(page, AlbumButton(), Path(temp))

        stage_index = reporter.events.index(("stage", "Downloading..."))
        first_progress_index = next(
            index for index, event in enumerate(reporter.events)
            if event[0] == "update" and event[1] == "Downloaded 1 of 40 tracks"
        )
        self.assertLess(stage_index, first_progress_index)

    def test_cdp_progress_tracks_only_the_zip_download_guid(self):
        class Reporter:
            def __init__(self):
                self.queue_wait_started = None
                self.transfer_updates = []
            def stage(self, message, tone="info"):
                pass
            def start_queue_wait(self):
                self.queue_wait_started = 0
            def update_queue_wait(self):
                pass
            def finish_queue_wait(self):
                self.queue_wait_started = None
                return 0
            def update(self, snapshot, started):
                pass
            def finish(self):
                pass
            def update_transfer(self, received, total):
                self.transfer_updates.append((received, total))
            def finish_transfer(self, received, total):
                self.completed_transfer = (received, total)
            def update_task(self, label, current, total):
                pass

        class CDP:
            def __init__(self, page):
                self.page = page
                self.handlers = {}
                self.commands = []
                self.detached = False
            def send(self, method, params=None):
                self.commands.append((method, params))
                if method == "Browser.setDownloadBehavior":
                    self.download_path = Path(params["downloadPath"])
                if method == "Target.getTargets":
                    return {"targetInfos": [{
                        "type": "page",
                        "url": self.page.url,
                        "browserContextId": "spotisaver-context",
                    }]}
                return {}
            def on(self, event, callback):
                self.handlers[event] = callback
            def emit(self, event, payload):
                self.handlers[event](payload)
            def detach(self):
                self.detached = True

        class Download:
            suggested_filename = "album.zip"
            def save_as(self, path):
                raise AssertionError("Playwright save_as must not be used when CDP owns the download")

        class Page(FakePage):
            def __init__(self, snapshot, zip_button):
                super().__init__(snapshot, zip_button)
                self.url = "https://spotisaver.net/en/album/example/"
                self.cdp = CDP(self)
                self.context = type("Context", (), {})()
                self.context.browser = type(
                    "Browser", (), {"new_browser_cdp_session": lambda browser: self.cdp}
                )()
            def wait_for_timeout(self, timeout):
                if self.zip_button.clicked and not getattr(self, "download_sent", False):
                    self.download_sent = True
                    self.cdp.download_path.joinpath("album.zip").write_bytes(b"archive")
                    self.events["download"](Download())

        reporter = Reporter()
        zip_button = FakeButton("Download ZIP")
        def emit_download_events():
            page.cdp.emit("Browser.downloadWillBegin", {
                "guid": "zip-guid",
                "url": "https://cdn.example/album.zip",
                "suggestedFilename": "album.zip",
            })
            page.cdp.emit("Browser.downloadProgress", {
                "guid": "unrelated-guid",
                "receivedBytes": 1000,
                "totalBytes": 1000,
                "state": "completed",
            })
            page.cdp.emit("Browser.downloadProgress", {
                "guid": "zip-guid",
                "receivedBytes": 500,
                "totalBytes": 1000,
                "state": "inProgress",
            })
            page.cdp.emit("Browser.downloadProgress", {
                "guid": "zip-guid",
                "receivedBytes": 1000,
                "totalBytes": 1000,
                "state": "completed",
            })
        zip_button.on_click = emit_download_events
        page = Page({
            "status": "ZIP archive created.",
            "log": "",
            "failed": "",
            "progress": "100 100%",
            "eta": "",
            "eta_template": "",
            "eta_minutes": "",
            "eta_seconds": "",
            "controls": '[{"text":"Download ZIP"}]',
        }, zip_button)
        class AlbumButton:
            def click(self):
                pass

        with tempfile.TemporaryDirectory() as temp, patch.object(
            spotisaver_module, "_ACTIVE_PROGRESS_REPORTER", reporter
        ):
            result = _download_click(page, AlbumButton(), Path(temp))

        self.assertEqual(result.name, "album.zip")
        self.assertEqual(reporter.transfer_updates, [(500, 1000)])
        self.assertEqual(reporter.completed_transfer, (1000, 1000))
        behavior = next(
            params for method, params in page.cdp.commands
            if method == "Browser.setDownloadBehavior"
        )
        self.assertEqual(behavior["browserContextId"], "spotisaver-context")
        self.assertTrue(page.cdp.detached)

    def test_finds_unique_visible_enabled_zip_button(self):
        button = FakeButton("Download ZIP")
        self.assertIs(_find_zip_download_button(FakePage({}, button)), button)

    def test_rejects_hidden_or_disabled_zip_button(self):
        hidden = FakeButton("Download ZIP", visible=False)
        disabled = FakeButton("Download ZIP", enabled=False)
        self.assertIsNone(_find_zip_download_button(FakePage({}, hidden)))
        self.assertIsNone(_find_zip_download_button(FakePage({}, disabled)))

    def test_clicks_zip_button_once_after_archive_ready_and_waits_for_event(self):
        with tempfile.TemporaryDirectory() as temp:
            zip_button = FakeButton("Download ZIP")
            page = FakePage({
                "status": "ZIP archive created.",
                "log": "",
                "failed": "",
                "progress": "100 100%",
                "eta": "",
                "eta_template": "",
                "eta_minutes": "",
                "eta_seconds": "",
                "controls": '[{"text":"Download ZIP"}]',
            }, zip_button)

            class AlbumButton:
                clicked = 0

                def click(self):
                    self.clicked += 1
                    self.listener_was_registered = "download" in page.events

            album_button = AlbumButton()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = _download_click(page, album_button, Path(temp))

            self.assertEqual(album_button.clicked, 1)
            self.assertTrue(album_button.listener_was_registered)
            self.assertEqual(zip_button.clicked, 1)
            self.assertEqual(result.name, "album.zip")
            self.assertEqual(result.read_bytes(), b"verified archive")
            self.assertIn("Archive ready. Downloading...", output.getvalue())
            self.assertIn("ZIP transfer progress unavailable", output.getvalue())
            self.assertNotIn("Clicking the verified Download ZIP button", output.getvalue())
            self.assertNotIn("Browser download event received", output.getvalue())


if __name__ == "__main__":
    unittest.main()
