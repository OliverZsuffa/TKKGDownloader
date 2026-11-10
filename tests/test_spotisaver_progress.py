from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import re

from tkkgdownloader.spotisaver import (
    _find_zip_download_button,
    _format_eta,
    _parse_track_progress,
    _render_progress_bar,
    _download_click,
    _ProgressReporter,
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
            self.assertNotIn("Clicking the verified Download ZIP button", output.getvalue())
            self.assertNotIn("Browser download event received", output.getvalue())


if __name__ == "__main__":
    unittest.main()
