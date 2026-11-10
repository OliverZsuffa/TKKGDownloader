from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from mutagen.id3 import APIC, ID3, TPE1, TPE2, TCON
from tkkgdownloader.audio_diagnostics import (
    _extract_artwork,
    _image_dimensions,
    _write_metadata,
    run_episode_diagnostics,
)


class ArtworkTests(unittest.TestCase):
    def test_png_dimensions_are_read_without_reencoding(self):
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + (640).to_bytes(4, "big") + (480).to_bytes(4, "big")
        self.assertEqual(_image_dimensions(png, "image/png"), (640, 480))

    def test_artwork_on_later_track_is_extracted_and_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "01 - first.mp3"
            second = root / "02 - second.mp3"
            first.write_bytes(b"")
            second.write_bytes(b"")
            png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + (64).to_bytes(4, "big") + (64).to_bytes(4, "big")
            tags = ID3()
            tags.add(APIC(encoding=3, mime="image/png", type=3, desc="Cover", data=png))
            tags.save(second)
            result = _extract_artwork([first, second], root / "artwork")
            self.assertTrue(result["artwork_found"])
            self.assertEqual(result["selected"]["source_track"], second.name)
            self.assertEqual(Path(result["selected"]["path"]).read_bytes(), png)
            self.assertEqual(result["selected"]["width"], 64)

    def test_distinct_cover_variants_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracks = []
            for number, marker in ((1, b"a"), (2, b"b")):
                path = root / f"{number:02d} - part.mp3"
                path.write_bytes(b"")
                tags = ID3()
                tags.add(APIC(encoding=3, mime="image/png", type=3, desc="Cover", data=(
                    b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + marker * 8
                )))
                tags.save(path)
                tracks.append(path)
            result = _extract_artwork(tracks, root / "artwork")
            self.assertEqual(len(result["pictures"]), 2)
            self.assertTrue((root / "artwork" / "cover-source-track-01.png").exists())
            self.assertTrue((root / "artwork" / "cover-source-track-02.png").exists())

    def test_no_artwork_is_reported_without_substitution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            track = root / "01 - part.mp3"
            track.write_bytes(b"not an mp3")
            result = _extract_artwork([track], root / "artwork")
            self.assertFalse(result["artwork_found"])
            self.assertIsNone(result["selected"])


class MetadataTests(unittest.TestCase):
    def test_episode_metadata_and_consistent_source_tags_are_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracks = []
            for number in (1, 2):
                path = root / f"{number:02d} - part.mp3"
                path.write_bytes(b"audio")
                tags = ID3()
                tags.add(TPE1(encoding=3, text="TKKG"))
                tags.add(TPE2(encoding=3, text="Europa"))
                tags.add(TCON(encoding=3, text="Hörspiel"))
                tags.save(path)
                tracks.append(path)
            output = root / "candidate.mp3"
            output.write_bytes(b"audio")
            episode = SimpleNamespace(number=150, title="Test episode")
            result = _write_metadata(
                output, episode, {"spotify_album_title": "Test album"}, tracks,
                {"selected": None},
            )
            self.assertTrue(result["verified"])
            self.assertEqual(result["readback"]["title"], "TKKG 150: Test episode")
            self.assertEqual(result["readback"]["album"], "Test album")
            self.assertEqual(result["readback"]["artist"], "TKKG")
            self.assertEqual(result["readback"]["album_artist"], "Europa")
            self.assertEqual(result["readback"]["track"], "1/1")
            self.assertEqual(result["readback"]["artwork_count"], 0)

    def test_missing_optional_source_tags_are_not_invented(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "01 - part.mp3"
            source.write_bytes(b"audio")
            output = root / "candidate.mp3"
            output.write_bytes(b"audio")
            result = _write_metadata(
                output, SimpleNamespace(number=1, title="Episode"),
                {"spotify_album_title": "Album"}, [source], {"selected": None},
            )
            self.assertNotIn("artist", result["fields"])
            self.assertNotIn("genre", result["fields"])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg tools are unavailable")
class DiagnosticIntegrationTests(unittest.TestCase):
    def test_full_pipeline_builds_two_validated_candidates_and_boundary_review(self):
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracks_dir = root / "source" / "tracks"
            tracks_dir.mkdir(parents=True)
            tracks = []
            for number, frequency in ((1, 440), (2, 660)):
                path = tracks_dir / f"{number:02d} - part {number}.mp3"
                result = subprocess.run([
                    ffmpeg, "-hide_banner", "-v", "error", "-y",
                    "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration=1.5",
                    "-c:a", "libmp3lame", "-b:a", "192k", str(path),
                ], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                tracks.append(path)
            episode = SimpleNamespace(number=150, title="Diagnostic test")
            report = run_episode_diagnostics(
                episode, {"track_count": 2, "spotify_album_title": "Test album"},
                tracks, root / "workspace", ffmpeg=ffmpeg, ffprobe=ffprobe,
            )
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["track_count"], 2)
            self.assertTrue(Path(data["outputs"]["stream_copy"]).is_file())
            self.assertTrue(Path(data["outputs"]["pcm_mp3"]).is_file())
            self.assertTrue(Path(data["outputs"]["pcm_master"]).is_file())
            self.assertTrue(Path(data["outputs"]["boundary_review"]).is_file())
            self.assertEqual(len(data["boundaries"]), 1)
            self.assertTrue(data["pcm_320k_mp3"]["metadata"]["verified"])
            self.assertEqual(len(tracks), 2)
            self.assertTrue(all(path.is_file() for path in tracks))


if __name__ == "__main__":
    unittest.main()
