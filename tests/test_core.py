from __future__ import annotations

import argparse
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tkkgdownloader.cli import parse_episode_spec
from tkkgdownloader.episodes import (
    DATASET_METADATA_URL,
    EPISODES_URL,
    Episode,
    fetch_catalog,
    get_episode,
    parse_catalog,
)
from tkkgdownloader.downloader import _run_with_progress
from tkkgdownloader.merger import ordered_tracks, track_number


def episode_record(number: int, title: str) -> dict:
    return {
        "number": number,
        "title": title,
        "physical_releases": [],
        "tracks": [],
        "cast": [],
        "credits": [],
        "ratings": [],
        "sources": [],
        "listening_links": [],
    }


class EpisodeParsingTests(unittest.TestCase):
    def test_single_number(self):
        self.assertEqual(parse_episode_spec("125"), [125])

    def test_range_is_inclusive(self):
        self.assertEqual(parse_episode_spec("1-3"), [1, 2, 3])

    def test_invalid_ranges(self):
        for value in ("0", "3-1", "1-", "a", "1-2-3", "1-501"):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_episode_spec(value)


class CatalogTests(unittest.TestCase):
    def test_parse_catalog(self):
        catalog = parse_catalog([
            episode_record(1, " Die Jagd nach den Millionendieben "),
            episode_record("2", "Der blinde Hellseher"),
        ])
        self.assertEqual(catalog[1], Episode(1, "Die Jagd nach den Millionendieben"))
        self.assertEqual(get_episode(catalog, 2).title, "Der blinde Hellseher")

    def test_missing_episode(self):
        with self.assertRaisesRegex(ValueError, "TKKGData"):
            get_episode({1: Episode(1, "Test")}, 2)

    def test_reject_duplicate_numbers(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_catalog([episode_record(1, "One"), episode_record(1, "Duplicate")])

    def test_reject_numbering_gaps(self):
        with self.assertRaisesRegex(ValueError, "gaps"):
            parse_catalog([episode_record(1, "One"), episode_record(3, "Three")])

    def test_reject_missing_ui_required_array(self):
        record = episode_record(1, "One")
        del record["listening_links"]
        with self.assertRaisesRegex(ValueError, "listening_links"):
            parse_catalog([record])

    def test_fetch_catalog_validates_metadata_before_returning_episodes(self):
        metadata = {"schema_version": "1.0.0", "episode_count": 1}
        payload = [episode_record(1, "One")]

        class FakeResponse:
            def __init__(self, value):
                self.value = json.dumps(value).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return self.value

        with patch(
            "tkkgdownloader.episodes.urllib.request.urlopen",
            side_effect=[FakeResponse(metadata), FakeResponse(payload)],
        ) as urlopen:
            catalog = fetch_catalog()
        self.assertEqual(catalog[1].title, "One")
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("TKKGData/main", DATASET_METADATA_URL)
        self.assertIn("TKKGData/main", EPISODES_URL)

    def test_fetch_catalog_rejects_unsupported_schema(self):
        metadata = {"schema_version": "2.0.0", "episode_count": 1}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(metadata).encode("utf-8")

        with patch("tkkgdownloader.episodes.urllib.request.urlopen", return_value=FakeResponse()):
            with self.assertRaisesRegex(ValueError, "Unsupported TKKGData schema"):
                fetch_catalog()

    def test_fetch_catalog_rejects_metadata_count_mismatch(self):
        metadata = {"schema_version": "1.0.0", "episode_count": 2}
        payload = [episode_record(1, "One")]

        class FakeResponse:
            def __init__(self, value):
                self.value = json.dumps(value).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return self.value

        with patch(
            "tkkgdownloader.episodes.urllib.request.urlopen",
            side_effect=[FakeResponse(metadata), FakeResponse(payload)],
        ):
            with self.assertRaisesRegex(ValueError, "reports 2"):
                fetch_catalog()


class ProgressRunnerTests(unittest.TestCase):
    @patch("tkkgdownloader.downloader.time.monotonic", side_effect=[0, 11, 12])
    @patch("tkkgdownloader.downloader.subprocess.Popen")
    def test_reports_heartbeat_and_completion(self, popen, monotonic):
        process = Mock()
        process.wait.side_effect = [
            subprocess.TimeoutExpired(["example"], 10),
            0,
        ]
        popen.return_value = process
        with patch("builtins.print") as output:
            result = _run_with_progress(
                ["example"], stage="Test stage", heartbeat_seconds=10
            )
        self.assertEqual(result, 0)
        self.assertGreaterEqual(output.call_count, 3)
        self.assertTrue(any("still running" in str(c.args[0]) for c in output.call_args_list))

    @patch("tkkgdownloader.downloader.time.monotonic", side_effect=[0, 2])
    @patch("tkkgdownloader.downloader.subprocess.Popen")
    def test_returns_nonzero_exit_code(self, popen, monotonic):
        process = Mock()
        process.wait.return_value = 2
        popen.return_value = process
        self.assertEqual(
            _run_with_progress(["example"], stage="Test stage"),
            2,
        )


class TrackOrderingTests(unittest.TestCase):
    def test_tracks_are_sorted_by_track_number(self):
        paths = [Path("03 - Ende.mp3"), Path("01 - Anfang.mp3"), Path("02 - Mitte.mp3")]
        self.assertEqual([p.name for p in ordered_tracks(paths)], [
            "01 - Anfang.mp3", "02 - Mitte.mp3", "03 - Ende.mp3"
        ])

    def test_invalid_track_number(self):
        with self.assertRaises(ValueError):
            track_number(Path("wrong-name.mp3"))

    def test_duplicate_track_number(self):
        with self.assertRaises(ValueError):
            ordered_tracks([Path("01 - A.mp3"), Path("01 - B.mp3")])


if __name__ == "__main__":
    unittest.main()
