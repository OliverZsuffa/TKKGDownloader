from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from tkkgdownloader.audio_import import import_audio_files
from tkkgdownloader.cli import build_parser
from tkkgdownloader.spotisaver import (
    _album_title,
    _download_click,
    _find_album_download,
    _find_playlist_navigation,
    _log_selector_state,
    _wait_for_album_data,
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


class SpotisaverPageWaitTests(unittest.TestCase):
    def test_album_title_removes_episode_prefix(self):
        self.assertEqual(
            _album_title("150/Heiße Nächte im Dezember"),
            "Heiße Nächte im Dezember",
        )

    def test_waits_for_album_and_all_track_titles(self):
        class FakePage:
            def __init__(self):
                self.call = None

            def wait_for_function(self, expression, *, arg, timeout):
                self.call = (expression, arg, timeout)

        page = FakePage()
        plan = {
            "spotify_album_title": "150/Heiße Nächte im Dezember",
            "tracks": [
                {"track_number": 1, "spotify_title": "TKKG 150 Teil 01"},
                {"track_number": 2, "spotify_title": "TKKG 150 Teil 02"},
            ],
        }
        _wait_for_album_data(page, plan)
        self.assertIsNotNone(page.call)
        self.assertEqual(page.call[1][0], "heienachteimdezember")
        self.assertEqual(page.call[1][1], ["tkkg150teil01", "tkkg150teil02"])
        self.assertEqual(page.call[2], 120_000)


class FakeLocator:
    def __init__(self, label='', visible=True):
        self.label = label
        self.visible = visible
        self.first = self

    def count(self):
        return 1 if self.label or self.visible else 0

    def is_visible(self):
        return self.visible

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

class SpotisaverDownloadControlTests(unittest.TestCase):
    def test_prefers_visible_entire_playlist_button(self):
        button = FakeLocator('Download entire playlist')
        self.assertIs(_find_album_download(FakePage(direct=button)), button)

    def test_does_not_select_hidden_playlist_button(self):
        button = FakeLocator('Download entire playlist', visible=False)
        self.assertIsNone(_find_album_download(FakePage(direct=button)))

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


if __name__ == "__main__":
    unittest.main()


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
        self.assertIn("visible=True", output.getvalue())
        self.assertIn("downloadAllBtn", output.getvalue())
        self.assertIn("Download entire playlist", output.getvalue())

    def test_download_click_reports_and_saves_download(self):
        class FakeDownload:
            suggested_filename = "album.zip"

            def save_as(self, path):
                Path(path).write_bytes(b"archive")

        class DownloadContext:
            value = FakeDownload()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class DownloadPage:
            def expect_download(self, timeout):
                self.timeout = timeout
                return DownloadContext()

        class ClickLocator:
            clicked = False

            def click(self):
                self.clicked = True

        with tempfile.TemporaryDirectory() as temp:
            locator = ClickLocator()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = _download_click(DownloadPage(), locator, Path(temp), 5_000)
            self.assertTrue(locator.clicked)
            self.assertEqual(result.name, "album.zip")
            self.assertEqual(result.read_bytes(), b"archive")
            self.assertIn("Issuing Playwright click", output.getvalue())
            self.assertIn("Browser download event received", output.getvalue())
            self.assertIn("Saved file size: 7 bytes", output.getvalue())
