import argparse
import unittest
from pathlib import Path

from tkkgdownloader.cli import parse_episode_spec
from tkkgdownloader.episodes import Episode, get_episode, parse_catalog
from tkkgdownloader.merger import ordered_tracks, track_number
from tkkgdownloader.spotify import (
    build_first_track_query,
    resolve_album_metadata,
    validate_album_metadata,
)


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
            "tracks_count": 3,
        }

    def test_query_targets_first_chapter(self):
        self.assertEqual(
            build_first_track_query(self.episode),
            "TKKG 150 Heiße Nächte im Dezember Teil 01",
        )

    def test_resolve_album_from_first_track(self):
        album = resolve_album_metadata([self.track], self.episode)
        self.assertEqual(album["album_id"], "0ZqyFeMXxCyIJvYptGlnn1")
        self.assertEqual(
            album["album_url"],
            "https://open.spotify.com/album/0ZqyFeMXxCyIJvYptGlnn1",
        )
        self.assertEqual(album["tracks_count"], 3)

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

    def test_validate_album_track_count_and_album_identity(self):
        album = resolve_album_metadata([self.track], self.episode)
        records = [
            {"album_id": album["album_id"], "track_number": n}
            for n in (3, 1, 2)
        ]
        self.assertEqual(validate_album_metadata(records, album), 3)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            validate_album_metadata(records[:2], album)
        with self.assertRaisesRegex(ValueError, "different album"):
            validate_album_metadata(
                [*records[:2], {"album_id": "another-album", "track_number": 3}],
                album,
            )

    def test_duplicate_album_track_numbers_rejected(self):
        album = resolve_album_metadata([self.track], self.episode)
        records = [
            {"album_id": album["album_id"], "track_number": n}
            for n in (1, 1, 3)
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_album_metadata(records, album)

    def test_list_length_is_not_used_as_track_count(self):
        track = {**self.track, "list_length": 40}
        album = resolve_album_metadata([track], self.episode)
        self.assertEqual(album["tracks_count"], 3)


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
