from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tkkgdownloader.audio_diagnostics import _duration_flags
from tkkgdownloader.merger import merge_tracks


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg tools are unavailable")
class SafeMergeIntegrationTests(unittest.TestCase):
    def _make_track(self, path: Path, sample_rate: int, frequency: int = 440) -> None:
        result = subprocess.run([
            FFMPEG, "-hide_banner", "-v", "error", "-y",
            "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration=1.5",
            "-ar", str(sample_rate), "-ac", "1",
            "-c:a", "libmp3lame", "-b:a", "192k", str(path),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(path.is_file())

    def test_mixed_sample_rates_select_pcm_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "01 - first.mp3"
            second = root / "02 - second.mp3"
            self._make_track(first, 44100)
            self._make_track(second, 48000, 660)
            output = root / "merged.mp3"
            details: dict = {}

            merge_tracks([first, second], output, ffmpeg=FFMPEG, ffprobe=FFPROBE,
                         diagnostics=details)

            self.assertTrue(output.is_file())
            self.assertEqual(details["selected_method"], "pcm_24bit_then_mp3_320k")
            self.assertTrue(details["attempts"][0]["skipped"])
            self.assertEqual(details["attempts"][0]["reason"],
                             "source_audio_formats_are_incompatible")
            self.assertEqual(details["attempts"][1]["sample_rate"], 48000)
            self.assertLessEqual(
                abs(details["attempts"][1]["duration_difference_seconds"]),
                details["attempts"][1]["duration_tolerance_seconds"],
            )

    def test_compatible_sources_keep_stream_copy_when_duration_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "01 - first.mp3"
            second = root / "02 - second.mp3"
            self._make_track(first, 44100)
            self._make_track(second, 44100, 660)
            output = root / "merged.mp3"
            details: dict = {}

            merge_tracks([first, second], output, ffmpeg=FFMPEG, ffprobe=FFPROBE,
                         diagnostics=details)

            self.assertTrue(output.is_file())
            self.assertEqual(details["selected_method"], "stream_copy")
            self.assertTrue(details["attempts"][0]["decode_valid"])
            self.assertLessEqual(
                abs(details["attempts"][0]["duration_difference_seconds"]),
                details["attempts"][0]["duration_tolerance_seconds"],
            )

    def test_stream_copy_duration_mismatch_falls_back_to_pcm(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "01 - first.mp3"
            second = root / "02 - second.mp3"
            self._make_track(first, 44100)
            self._make_track(second, 44100, 660)
            wrong = root / "wrong.mp3"
            self._make_track(wrong, 44100)
            long_result = subprocess.run([
                FFMPEG, "-hide_banner", "-v", "error", "-y",
                "-f", "lavfi", "-i", "sine=frequency=330:duration=12",
                "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame",
                "-b:a", "192k", str(wrong),
            ], capture_output=True, text=True)
            self.assertEqual(long_result.returncode, 0, long_result.stderr)

            output = root / "merged.mp3"
            details: dict = {}

            def write_wrong_stream_copy(tracks, concat_file, temporary_output, ffmpeg):
                shutil.copyfile(wrong, temporary_output)
                return {"command": ["synthetic"], "returncode": 0, "stdout": "", "stderr": ""}

            with patch("tkkgdownloader.merger._run_stream_copy",
                       side_effect=write_wrong_stream_copy):
                merge_tracks([first, second], output, ffmpeg=FFMPEG, ffprobe=FFPROBE,
                             diagnostics=details)

            self.assertEqual(details["attempts"][0]["rejected_reason"], "duration_mismatch")
            self.assertEqual(details["selected_method"], "pcm_24bit_then_mp3_320k")
            self.assertTrue(output.is_file())


class IntroDurationRuleTests(unittest.TestCase):
    def test_long_intro_is_not_compared_with_regular_segments(self):
        self.assertEqual(_duration_flags(1, 127.896, 87.5), [])

    def test_unusually_long_intro_is_still_flagged(self):
        self.assertEqual(_duration_flags(1, 400, 87.5), ["intro_duration_outlier"])

    def test_regular_segment_outlier_is_flagged(self):
        self.assertEqual(_duration_flags(12, 130, 87.5), ["duration_outlier"])


if __name__ == "__main__":
    unittest.main()
