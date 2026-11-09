import unittest

from tkkgdownloader.audio_sources import (
    build_individual_track_queries,
    build_playlist_query,
    validate_audio_release,
)


def make_audio_release(with_playlist=True):
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
            "artists": ["TKKG"],
            "match_score": 140,
            "match_evidence": ["exact_normalised_title", "episode_album"],
        })
    return {
        "spotify": {
            "album_id": spotify_album_id,
            "url": f"https://open.spotify.com/album/{spotify_album_id}",
            "title": "150/Heiße Nächte im Dezember",
            "track_count": 2,
        },
        "youtube_music": {
            "playlist": playlist,
            "tracks": tracks,
            "track_count": 2,
        },
        "verification": {
            "status": "verified",
            "matched_track_count": 2,
        },
    }


class AudioSourceTests(unittest.TestCase):
    def test_verified_release_produces_playlist_and_individual_queries(self):
        plan = validate_audio_release(make_audio_release())
        self.assertEqual(plan["track_count"], 2)
        self.assertIn("music.youtube.com/playlist", build_playlist_query(plan))
        queries = build_individual_track_queries(plan)
        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[0]["track_number"], 1)
        self.assertIn("music.youtube.com/watch?v=videoid0001|https://open.spotify.com/track/", queries[0]["query"])

    def test_missing_playlist_keeps_individual_track_fallback(self):
        plan = validate_audio_release(make_audio_release(with_playlist=False))
        self.assertIsNone(build_playlist_query(plan))
        self.assertEqual(len(build_individual_track_queries(plan)), 2)

    def test_generic_youtube_playlist_uses_individual_pairs_with_spotify_album(self):
        release = make_audio_release()
        playlist_id = "PL12345678901234567890"
        release["youtube_music"]["playlist"]["playlist_id"] = playlist_id
        release["youtube_music"]["playlist"]["url"] = f"https://music.youtube.com/playlist?list={playlist_id}"
        plan = validate_audio_release(release)
        self.assertIsNone(build_playlist_query(plan))
        self.assertEqual(len(build_individual_track_queries(plan)), 2)

    def test_unverified_release_is_rejected(self):
        release = make_audio_release()
        release["verification"]["status"] = "candidate"
        with self.assertRaisesRegex(ValueError, "does not mark"):
            validate_audio_release(release)

    def test_count_mismatch_is_rejected(self):
        release = make_audio_release()
        release["youtube_music"]["track_count"] = 1
        with self.assertRaisesRegex(ValueError, "counts do not agree"):
            validate_audio_release(release)

    def test_spotify_track_id_must_match_url(self):
        release = make_audio_release()
        release["youtube_music"]["tracks"][0]["spotify_track_id"] = "x" * 22
        with self.assertRaisesRegex(ValueError, "Spotify track 1 URL"):
            validate_audio_release(release)

    def test_youtube_video_id_must_match_url(self):
        release = make_audio_release()
        release["youtube_music"]["tracks"][0]["video_id"] = "x" * 11
        with self.assertRaisesRegex(ValueError, "YouTube Music track 1 URL"):
            validate_audio_release(release)

    def test_track_order_must_be_contiguous(self):
        release = make_audio_release()
        release["youtube_music"]["tracks"][1]["track_number"] = 3
        with self.assertRaisesRegex(ValueError, "not contiguous"):
            validate_audio_release(release)

    def test_playlist_count_must_match(self):
        release = make_audio_release()
        release["youtube_music"]["playlist"]["track_count"] = 1
        with self.assertRaisesRegex(ValueError, "playlist track count"):
            validate_audio_release(release)


if __name__ == "__main__":
    unittest.main()
