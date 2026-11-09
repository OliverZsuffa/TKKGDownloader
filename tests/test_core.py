import argparse
import unittest
from pathlib import Path

from tkkgdownloader.cli import parse_episode_spec
from tkkgdownloader.episodes import Episode, get_episode, parse_catalog
from tkkgdownloader.merger import ordered_tracks, track_number
from tkkgdownloader.spotify import build_album_query


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


class SpotifyQueryTests(unittest.TestCase):
    def test_query_contains_zero_padded_number_and_title(self):
        query = build_album_query(Episode(1, "Die Jagd nach den Millionendieben"))
        self.assertEqual(query, "album:TKKG 001 Die Jagd nach den Millionendieben")


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
