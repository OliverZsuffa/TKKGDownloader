import argparse
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from tkkgdownloader.cli import parse_episode_spec
from tkkgdownloader.episodes import Episode, get_episode, parse_catalog
from tkkgdownloader.merger import ordered_tracks, track_number
from tkkgdownloader.spotify import (
    build_first_track_query,
    resolve_album_metadata,
    validate_album_metadata,
)
from tkkgdownloader.downloader import _run_with_progress


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
            {"number": 1, "title": " Die Jagd nach den Millionendieben "},
            {"number": "2", "title": "Der blinde Hellseher"},
            {"number": "invalid", "title": "Ignored"},
        ])
        self.assertEqual(catalog[1], Episode(1, "Die Jagd nach den Millionendieben"))
        self.assertEqual(get_episode(catalog, 2).title, "Der blinde Hellseher")

    def test_missing_episode(self):
        with self.assertRaises(ValueError):
            get_episode({1: Episode(1, "Test")}, 2)


class SpotifyResolutionTests(unittest.TestCase):
    def setUp(self):
        self.episode = Episode(150, "Heiße Nächte im Dezember")
        self.track = {
            "name": "150 - Heiße Nächte im Dezember - Teil 01",
            "artists": ["TKKG"],
            "artist": "TKKG",
            "album_name": "150/Heiße Nächte im Dezember",
            "album_id": "0ZqyFeMXxCyIJvYptGlnn1",
            "tracks_count": 25,
        }

    def test_query_targets_first_chapter(self):
        self.assertEqual(
            build_first_track_query(self.episode),
            "TKKG 150 Heiße Nächte im Dezember Teil 01",
        )

    def test_resolve_album_from_first_track_ignores_inconsistent_spotify_count(self):
        album = resolve_album_metadata([self.track], self.episode)
        self.assertEqual(album["album_id"], "0ZqyFeMXxCyIJvYptGlnn1")
        self.assertEqual(
            album["album_url"],
            "https://open.spotify.com/album/0ZqyFeMXxCyIJvYptGlnn1",
        )
        self.assertNotIn("tracks_count", album)

    def test_reject_empty_or_multiple_results(self):
        for payload in ([], [self.track, self.track]):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                resolve_album_metadata(payload, self.episode)

    def test_reject_wrong_artist(self):
        track = {**self.track, "artists": ["Someone Else"], "artist": "Someone Else"}
        with self.assertRaisesRegex(ValueError, "artist named TKKG"):
            resolve_album_metadata([track], self.episode)

    def test_reject_wrong_episode_or_part(self):
        for name in (
            "151 - Heiße Nächte im Dezember - Teil 01",
            "150 - Heiße Nächte im Dezember - Teil 02",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                resolve_album_metadata([{**self.track, "name": name}], self.episode)

    def test_reject_missing_album_id(self):
        track = {key: value for key, value in self.track.items() if key != "album_id"}
        with self.assertRaisesRegex(ValueError, "album ID"):
            resolve_album_metadata([track], self.episode)

    def test_album_count_is_derived_from_all_returned_songs(self):
        album = resolve_album_metadata([self.track], self.episode)
        records = [
            {"album_id": album["album_id"], "track_number": n}
            for n in range(1, 41)
        ]
        self.assertEqual(validate_album_metadata(records, album), 40)

    def test_album_metadata_must_be_a_complete_track_sequence(self):
        album = resolve_album_metadata([self.track], self.episode)
        complete = [
            {"album_id": album["album_id"], "track_number": n}
            for n in range(1, 5)
        ]
        self.assertEqual(validate_album_metadata(complete, album), 4)
        with self.assertRaisesRegex(ValueError, "complete track sequence"):
            validate_album_metadata(complete[:2] + complete[3:], album)

    def test_wrong_album_and_duplicate_track_numbers_rejected(self):
        album = resolve_album_metadata([self.track], self.episode)
        with self.assertRaisesRegex(ValueError, "different album"):
            validate_album_metadata(
                [
                    {"album_id": album["album_id"], "track_number": 1},
                    {"album_id": "another-album", "track_number": 2},
                ],
                album,
            )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_album_metadata(
                [
                    {"album_id": album["album_id"], "track_number": 1},
                    {"album_id": album["album_id"], "track_number": 1},
                ],
                album,
            )


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
