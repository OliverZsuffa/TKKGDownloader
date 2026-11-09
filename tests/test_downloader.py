import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tkkgdownloader.downloader import download_episode
from tkkgdownloader.episodes import Episode


def audio_release(with_playlist=True):
    spotify_album_id = "0ZqyFeMXxCyIJvYptGlnn1"
    playlist = None
    if with_playlist:
        playlist_id = "OLAK5uy_mQRbJNANh1H4CKbmM5ez5LSW1HJFvE3QI"
        playlist = {
            "playlist_id": playlist_id,
            "url": f"https://music.youtube.com/playlist?list={playlist_id}",
            "title": "150/Heiße Nächte im Dezember",
            "track_count": 2,
        }
    tracks = []
    for number in (1, 2):
        spotify_id = f"000000000000000000000{number}"
        video_id = f"videoid000{number}"
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
            "track_count": 2,
        },
        "youtube_music": {"playlist": playlist, "tracks": tracks, "track_count": 2},
        "verification": {"status": "verified", "matched_track_count": 2},
    }


class DownloaderSourceTests(unittest.TestCase):
    def _fake_successful_download(self, commands):
        def run(command, *, stage, cwd=None, heartbeat_seconds=10):
            commands.append(command)
            number = len(commands) if "verified track" in stage else None
            if number is None:
                numbers = (1, 2)
            else:
                numbers = (number,)
            album_dir = cwd / "150 - Heiße Nächte im Dezember"
            album_dir.mkdir(parents=True, exist_ok=True)
            for track_number in numbers:
                (album_dir / f"{track_number:02d} - Teil {track_number:02d}.mp3").write_bytes(b"audio")
            return 0
        return run

    def test_playlist_pair_is_preferred_and_merged(self):
        episode = Episode(150, "Heiße Nächte im Dezember", audio_release())
        commands = []
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch("tkkgdownloader.downloader._command", side_effect=[["spotdl"], "ffmpeg"]), \
             patch("tkkgdownloader.downloader._run_with_progress", side_effect=self._fake_successful_download(commands)), \
             patch("tkkgdownloader.downloader.merge_tracks") as merge:
            result = download_episode(episode, Path(temp_dir), assume_yes=True)
        self.assertTrue(result.name.startswith("TKKG 150"))
        self.assertEqual(len(commands), 1)
        self.assertIn("music.youtube.com/playlist", commands[0][2])
        self.assertIn("open.spotify.com/album", commands[0][2])
        self.assertEqual(len(merge.call_args.args[0]), 2)

    def test_playlist_failure_falls_back_to_exact_individual_pairs(self):
        episode = Episode(150, "Heiße Nächte im Dezember", audio_release())
        commands = []
        def run(command, *, stage, cwd=None, heartbeat_seconds=10):
            commands.append(command)
            if "playlist" in stage:
                return 1
            track_number = int(stage.split("track ")[1].split("/")[0])
            album_dir = cwd / "150 - Heiße Nächte im Dezember"
            album_dir.mkdir(parents=True, exist_ok=True)
            (album_dir / f"{track_number:02d} - Teil {track_number:02d}.mp3").write_bytes(b"audio")
            return 0
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch("tkkgdownloader.downloader._command", side_effect=[["spotdl"], "ffmpeg"]), \
             patch("tkkgdownloader.downloader._run_with_progress", side_effect=run), \
             patch("tkkgdownloader.downloader.merge_tracks") as merge:
            result = download_episode(episode, Path(temp_dir), assume_yes=True)
        self.assertTrue(result.name.startswith("TKKG 150"))
        self.assertEqual(len(commands), 3)
        self.assertIn("music.youtube.com/watch?v=videoid0001|https://open.spotify.com/track/", commands[1][2])
        self.assertEqual(len(merge.call_args.args[0]), 2)

    def test_missing_verified_mapping_fails_clearly(self):
        episode = Episode(150, "Heiße Nächte im Dezember")
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "No usable verified audio source"):
                download_episode(episode, Path(temp_dir), assume_yes=True)


if __name__ == "__main__":
    unittest.main()
