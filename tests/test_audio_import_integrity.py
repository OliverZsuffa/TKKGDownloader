from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

from mutagen.id3 import ID3, TIT2, TRCK

from tkkgdownloader.audio_import import (
    import_audio_files,
    serializable_manifest,
    validate_track_manifest,
)
from tkkgdownloader.merger import merge_tracks


def make_archive(root: Path, names_and_data: list[tuple[str, bytes]]) -> Path:
    archive = root / "album.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        for name, data in names_and_data:
            zipped.writestr(name, data)
    return archive


def expected(*titles: str) -> list[dict]:
    return [
        {"track_number": index, "spotify_title": title}
        for index, title in enumerate(titles, start=1)
    ]


class TrackIdentityTests(unittest.TestCase):
    def test_exact_matching_distinguishes_part_1_from_part_10(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [
                ("Album/TKKG Teil 10.mp3", b"ten"),
                ("Album/TKKG Teil 1.mp3", b"one"),
            ])
            result = import_audio_files(
                [archive], expected("TKKG Teil 1", "TKKG Teil 10"), root / "work"
            )
            self.assertEqual(result[0].read_bytes(), b"one")
            self.assertEqual(result[1].read_bytes(), b"ten")

    def test_matching_accepts_case_punctuation_and_unicode_normalization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Album/TKKG_Épisode 01!.mp3", b"audio")])
            result = import_audio_files(
                [archive], expected("tkkg épisode-01"), root / "work"
            )
            self.assertEqual(result[0].read_bytes(), b"audio")

    def test_matching_accepts_only_correct_numeric_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Album/01 - TKKG Teil 01.mp3", b"audio")])
            result = import_audio_files(
                [archive], expected("TKKG Teil 01"), root / "work"
            )
            self.assertEqual(result[0].read_bytes(), b"audio")

    def test_rejects_wrong_numeric_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Album/02 - TKKG Teil 01.mp3", b"audio")])
            with self.assertRaisesRegex(RuntimeError, "uniquely match"):
                import_audio_files([archive], expected("TKKG Teil 01"), root / "work")

    def test_rejects_colliding_canonical_titles(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Teil 1.mp3", b"one"), ("Teil-1.mp3", b"two")])
            with self.assertRaisesRegex(RuntimeError, "colliding normalised titles"):
                import_audio_files(
                    [archive], expected("Teil 1", "Teil-1"), root / "work"
                )

    def test_rejects_non_contiguous_track_numbers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Teil 1.mp3", b"one"), ("Teil 3.mp3", b"three")])
            tracks = [
                {"track_number": 1, "spotify_title": "Teil 1"},
                {"track_number": 3, "spotify_title": "Teil 3"},
            ]
            with self.assertRaisesRegex(RuntimeError, "contiguous one-based"):
                import_audio_files([archive], tracks, root / "work")

    def test_rejects_duplicate_source_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [
                ("Teil 1.mp3", b"identical audio"),
                ("Teil 2.mp3", b"identical audio"),
            ])
            with self.assertRaisesRegex(RuntimeError, "byte-identical"):
                import_audio_files(
                    [archive], expected("Teil 1", "Teil 2"), root / "work"
                )

    def test_manifest_records_mapping_hashes_and_is_portable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [
                ("Album/Teil 02.mp3", b"second"),
                ("Album/Teil 01.mp3", b"first"),
            ])
            manifest: dict = {}
            result = import_audio_files(
                [archive],
                expected("Teil 01", "Teil 02"),
                root / "work",
                manifest_out=manifest,
                episode_number=150,
                episode_title="Example episode",
                album_title="Example album",
            )
            self.assertEqual(manifest["status"], "warnings")
            self.assertEqual(manifest["episode"]["number"], 150)
            self.assertEqual([item["track_number"] for item in manifest["tracks"]], [1, 2])
            self.assertTrue(all(len(item["source_sha256"]) == 64 for item in manifest["tracks"]))
            self.assertTrue(all(
                item["source_sha256"] == item["canonical_sha256"]
                for item in manifest["tracks"]
            ))
            portable = serializable_manifest(manifest)
            self.assertNotIn("_workspace_root", portable)
            self.assertEqual(validate_track_manifest(result, manifest), result)

    def test_embedded_metadata_disagreement_is_a_warning_not_reassignment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tagged = root / "tagged.mp3"
            tagged.write_bytes(b"audio")
            tags = ID3()
            tags.add(TIT2(encoding=3, text="Incorrect embedded title"))
            tags.add(TRCK(encoding=3, text="7/12"))
            tags.save(tagged)
            archive = make_archive(root, [("Canonical.mp3", tagged.read_bytes())])
            manifest: dict = {}
            import_audio_files(
                [archive], expected("Canonical"), root / "work",
                manifest_out=manifest,
            )
            self.assertEqual(manifest["tracks"][0]["embedded_metadata"]["track_number"], "7/12")
            self.assertTrue(any("differs from canonical number" in item
                                for item in manifest["tracks"][0]["warnings"]))
            self.assertEqual(manifest["status"], "warnings")

    def test_manifest_rejects_modified_file_before_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Teil 1.mp3", b"original")])
            manifest: dict = {}
            result = import_audio_files(
                [archive], expected("Teil 1"), root / "work", manifest_out=manifest
            )
            result[0].write_bytes(b"modified")
            with self.assertRaisesRegex(RuntimeError, "integrity check failed"):
                validate_track_manifest(result, manifest)

    def test_merger_rejects_tampered_manifest_input_before_ffmpeg(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [("Teil 1.mp3", b"original")])
            manifest: dict = {}
            result = import_audio_files(
                [archive], expected("Teil 1"), root / "work", manifest_out=manifest
            )
            result[0].write_bytes(b"tampered")
            with patch("tkkgdownloader.merger.subprocess.run") as run:
                with self.assertRaisesRegex(RuntimeError, "integrity check failed"):
                    merge_tracks(result, root / "output.mp3", manifest=manifest)
                run.assert_not_called()

    def test_manifest_rejects_wrong_order_before_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = make_archive(root, [
                ("Teil 1.mp3", b"first"),
                ("Teil 2.mp3", b"second"),
            ])
            manifest: dict = {}
            result = import_audio_files(
                [archive], expected("Teil 1", "Teil 2"), root / "work",
                manifest_out=manifest,
            )
            with self.assertRaisesRegex(RuntimeError, "manifest-defined track order"):
                validate_track_manifest(list(reversed(result)), manifest)


if __name__ == "__main__":
    unittest.main()
