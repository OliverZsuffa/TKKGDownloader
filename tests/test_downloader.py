import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tkkgdownloader.downloader import download_episode, download_episode_spotisaver
from tkkgdownloader.episodes import Episode


def audio_release(track_count=2, with_playlist=True):
    spotify_album_id = "0ZqyFeMXxCyIJvYptGlnn1"
    playlist = None
    if with_playlist:
        playlist_id = "OLAK5uy_mQRbJNANh1H4CKbmM5ez5LSW1HJFvE3QI"
        playlist = {
            "playlist_id": playlist_id,
            "url": f"https://music.youtube.com/playlist?list={playlist_id}",
            "title": "150/Heiße Nächte im Dezember",
            "track_count": track_count,
        }
    tracks = []
    for number in range(1, track_count + 1):
        spotify_id = f"{number:022d}"
        video_id = f"videoid{number:04d}"
        tracks.append({
            "track_number": number,
            "spotify_title": f"Teil {number:02d}",
            "spotify_track_id": spotify_id,
            "spotify_track_url": f"https://open.spotify.com/track/{spotify_id}",
            "video_id": video_id,
            "url": f"https://music.youtube.com/watch?v={video_id}",
            "title": f"Teil {number:02d}",
        })
    return {
        "spotify": {
            "album_id": spotify_album_id,
            "url": f"https://open.spotify.com/album/{spotify_album_id}",
            "title": "150/Heiße Nächte im Dezember",
            "track_count": track_count,
        },
        "youtube_music": {
            "playlist": playlist,
            "tracks": tracks,
            "track_count": track_count,
        },
        "verification": {"status": "verified", "matched_track_count": track_count},
    }


class DownloaderSourceTests(unittest.TestCase):
    def _fake_download(self, commands, *, fail_at=None, omit_at=None):
        def run(command, *, stage, cwd=None, heartbeat_seconds=10):
            commands.append(command)
            output_template = Path(command[command.index("--output") + 1])
            output_path = Path(str(output_template).replace("%(ext)s", "mp3"))
            track_number = int(output_path.name.split(" - ", 1)[0])
            if track_number == fail_at:
                return 1
            if track_number != omit_at:
                output_path.write_bytes(b"mock audio")
            return 0
        return run

    def _patches(self, commands, *, fail_at=None, omit_at=None):
        return (
            patch("tkkgdownloader.downloader._command", return_value=["yt-dlp"]),
            patch("tkkgdownloader.downloader.shutil.which", return_value="ffmpeg"),
            patch(
                "tkkgdownloader.downloader._run_with_progress",
                side_effect=self._fake_download(commands, fail_at=fail_at, omit_at=omit_at),
            ),
        )

    def test_downloads_each_exact_verified_video_url_and_merges(self):
        release = audio_release(track_count=3)
        episode = Episode(150, "Heiße Nächte im Dezember", release)
        commands = []
        patches = self._patches(commands)
        with tempfile.TemporaryDirectory() as temp_dir, patches[0], patches[1], patches[2], \
             patch("tkkgdownloader.downloader.merge_tracks") as merge, \
             patch("builtins.input", side_effect=AssertionError("Merge must not ask for confirmation")):
            result = download_episode(episode, Path(temp_dir))

        self.assertTrue(result.name.startswith("TKKG 150"))
        self.assertEqual(len(commands), 3)
        self.assertEqual(len(merge.call_args.args[0]), 3)
        for index, command in enumerate(commands, start=1):
            self.assertIn("--no-playlist", command)
            self.assertIn("--extract-audio", command)
            self.assertIn(f"https://music.youtube.com/watch?v=videoid{index:04d}", command)
            self.assertNotIn("spotdl", command[0].lower())
            self.assertNotIn("https://music.youtube.com/playlist", " ".join(command))

    def test_download_does_not_depend_on_playlist_metadata(self):
        episode = Episode(150, "Heiße Nächte im Dezember", audio_release(with_playlist=False))
        commands = []
        patches = self._patches(commands)
        with tempfile.TemporaryDirectory() as temp_dir, patches[0], patches[1], patches[2], \
             patch("tkkgdownloader.downloader.merge_tracks") as merge:
            download_episode(episode, Path(temp_dir))
        self.assertEqual(len(commands), 2)
        self.assertEqual(len(merge.call_args.args[0]), 2)

    def test_failed_track_stops_download_and_prevents_merge(self):
        episode = Episode(150, "Heiße Nächte im Dezember", audio_release())
        commands = []
        patches = self._patches(commands, fail_at=2)
        with tempfile.TemporaryDirectory() as temp_dir, patches[0], patches[1], patches[2], \
             patch("tkkgdownloader.downloader.merge_tracks") as merge:
            with self.assertRaisesRegex(RuntimeError, "verified track 2/2"):
                download_episode(episode, Path(temp_dir))
        self.assertEqual(len(commands), 2)
        merge.assert_not_called()

    def test_success_without_expected_mp3_fails_before_merge(self):
        episode = Episode(150, "Heiße Nächte im Dezember", audio_release())
        commands = []
        patches = self._patches(commands, omit_at=1)
        with tempfile.TemporaryDirectory() as temp_dir, patches[0], patches[1], patches[2], \
             patch("tkkgdownloader.downloader.merge_tracks") as merge:
            with self.assertRaisesRegex(RuntimeError, "did not produce the expected MP3"):
                download_episode(episode, Path(temp_dir))
        merge.assert_not_called()


    def test_spotisaver_download_merges_and_finalizes_metadata_automatically(self):
        episode = Episode(149, "Tims gefährlichster Gegner", audio_release())
        def create_candidate(tracks, output, **kwargs):
            output.write_bytes(b"mock merged audio")
        completed = type("Completed", (), {"returncode": 0, "stdout": "1.0", "stderr": ""})()
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch("tkkgdownloader.downloader.shutil.which", side_effect=["ffmpeg", "ffprobe"]), \
             patch(
                 "tkkgdownloader.downloader.download_and_import",
                 return_value=[Path("01 - Teil 01.mp3"), Path("02 - Teil 02.mp3")],
             ), \
             patch("tkkgdownloader.downloader.merge_tracks", side_effect=create_candidate) as merge, \
             patch("tkkgdownloader.downloader.finalize_metadata", return_value={
                 "verified": True, "artwork_embedded": True,
             }) as finalize, \
             patch("tkkgdownloader.downloader.subprocess.run", return_value=completed), \
             patch("builtins.input", side_effect=AssertionError("Merge must not ask for confirmation")):
            result = download_episode_spotisaver(episode, Path(temp_dir))
            self.assertTrue(result.is_file())
            self.assertEqual(len(merge.call_args.args[0]), 2)
            finalize.assert_called_once()

        self.assertTrue(result.name.startswith("TKKG 149"))

    def test_metadata_failure_preserves_existing_output(self):
        episode = Episode(149, "Tims gefährlichster Gegner", audio_release())
        def create_candidate(tracks, output, **kwargs):
            output.write_bytes(b"new candidate audio")
        completed = type("Completed", (), {"returncode": 0, "stdout": "1.0", "stderr": ""})()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            final_path = output_dir / "TKKG 149 - Tims gefährlichster Gegner.mp3"
            final_path.write_bytes(b"existing valid output")
            with patch("tkkgdownloader.downloader.shutil.which", side_effect=["ffmpeg", "ffprobe"]), \
                 patch(
                     "tkkgdownloader.downloader.download_and_import",
                     return_value=[Path("01 - Teil 01.mp3"), Path("02 - Teil 02.mp3")],
                 ), \
                 patch("tkkgdownloader.downloader.merge_tracks", side_effect=create_candidate), \
                 patch(
                     "tkkgdownloader.downloader.finalize_metadata",
                     side_effect=RuntimeError("metadata verification failed"),
                 ), \
                 patch("tkkgdownloader.downloader.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(RuntimeError, "metadata verification failed"):
                    download_episode_spotisaver(episode, output_dir, overwrite=True)
            self.assertEqual(final_path.read_bytes(), b"existing valid output")
            self.assertEqual(list(output_dir.glob("*.partial.mp3")), [])

    def test_missing_verified_mapping_fails_clearly(self):
        episode = Episode(150, "Heiße Nächte im Dezember")
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "No usable verified audio source"):
                download_episode(episode, Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
