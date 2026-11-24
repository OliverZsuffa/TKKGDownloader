import unittest

from tkkgdownloader.audio_sources import validate_audio_release


def spotify_release(count=2):
    album_id = "0ZqyFeMXxCyIJvYptGlnn1"
    tracks = []
    for number in range(1, count + 1):
        track_id = f"{number:022d}"
        tracks.append({
            "track_number": number,
            "track_id": track_id,
            "url": f"https://open.spotify.com/track/{track_id}",
            "title": f"Spotify Teil {number:02d}",
        })
    return {
        "album": {
            "album_id": album_id,
            "url": f"https://open.spotify.com/album/{album_id}",
            "title": "Spotify episode album",
            "track_count": count,
            "source_query": "reviewed episode album",
        },
        "tracks": tracks,
        "track_count": count,
    }


def youtube_release(count=2, with_playlist=True):
    playlist = None
    if with_playlist:
        playlist_id = "OLAK5uy_mQRbJNANh1H4CKbmM5ez5LSW1HJFvE3QI"
        playlist = {
            "playlist_id": playlist_id,
            "url": f"https://music.youtube.com/playlist?list={playlist_id}",
            "title": "YouTube episode playlist",
            "track_count": count,
        }
    tracks = []
    for number in range(1, count + 1):
        video_id = f"videoid{number:04d}"
        tracks.append({
            "track_number": number,
            "video_id": video_id,
            "url": f"https://music.youtube.com/watch?v={video_id}",
            "title": f"YouTube Teil {number:02d}",
            "artists": ["TKKG"],
        })
    return {
        "album": {
            "browse_id": "MPREb_Example",
            "url": "https://music.youtube.com/browse/MPREb_Example",
            "title": "YouTube episode album",
            "track_count": count,
        },
        "playlist": playlist,
        "tracks": tracks,
        "track_count": count,
    }


def make_audio_release(spotify_count=2, youtube_count=2, with_playlist=True):
    return {
        "schema_version": 2,
        "spotify": spotify_release(spotify_count),
        "youtube_music": youtube_release(youtube_count, with_playlist),
        "verification": {
            "status": "verified" if spotify_count == youtube_count else "partial",
            "verified_at": "2026-11-24T12:00:00Z",
            "method": "independent_provider_tracklist_validation",
            "spotify": {"status": "verified", "verified_track_count": spotify_count},
            "youtube_music": {
                "status": "verified",
                "verified_track_count": youtube_count,
                "playlist_status": "verified" if with_playlist else "unavailable",
                "playlist_error": None,
            },
        },
    }


class AudioSourceTests(unittest.TestCase):
    def test_youtube_plan_uses_its_own_verified_tracklist(self):
        plan = validate_audio_release(make_audio_release(), provider="yt-dlp")
        self.assertEqual(plan["provider"], "yt-dlp")
        self.assertEqual(plan["track_count"], 2)
        self.assertEqual(plan["tracks"][0]["title"], "YouTube Teil 01")
        self.assertEqual(
            plan["tracks"][0]["youtube_music_url"],
            "https://music.youtube.com/watch?v=videoid0001",
        )

    def test_spotify_plan_uses_its_own_verified_tracklist(self):
        plan = validate_audio_release(make_audio_release(), provider="spotisaver")
        self.assertEqual(plan["provider"], "spotisaver")
        self.assertEqual(plan["track_count"], 2)
        self.assertEqual(plan["tracks"][0]["spotify_title"], "Spotify Teil 01")
        self.assertEqual(
            plan["tracks"][0]["spotify_track_url"],
            "https://open.spotify.com/track/0000000000000000000001",
        )

    def test_unequal_provider_counts_are_valid_and_independent(self):
        release = make_audio_release(spotify_count=2, youtube_count=3)
        spotify = validate_audio_release(release, provider="spotisaver")
        youtube = validate_audio_release(release, provider="yt-dlp")
        self.assertEqual(spotify["track_count"], 2)
        self.assertEqual(youtube["track_count"], 3)
        self.assertEqual([t["track_number"] for t in youtube["tracks"]], [1, 2, 3])

    def test_playlist_is_optional_when_individual_tracks_are_verified(self):
        plan = validate_audio_release(
            make_audio_release(with_playlist=False), provider="yt-dlp"
        )
        self.assertIsNone(plan["youtube_music_playlist_url"])
        self.assertEqual(len(plan["tracks"]), 2)

    def test_generic_youtube_playlist_is_retained_as_metadata(self):
        release = make_audio_release()
        playlist_id = "PL12345678901234567890"
        release["youtube_music"]["playlist"]["playlist_id"] = playlist_id
        release["youtube_music"]["playlist"]["url"] = (
            f"https://music.youtube.com/playlist?list={playlist_id}"
        )
        plan = validate_audio_release(release, provider="yt-dlp")
        self.assertEqual(plan["youtube_music_playlist_url"],
                         f"https://music.youtube.com/playlist?list={playlist_id}")

    def test_overall_partial_status_does_not_reject_verified_selected_provider(self):
        release = make_audio_release()
        release["verification"]["status"] = "partial"
        self.assertEqual(
            validate_audio_release(release, provider="yt-dlp")["track_count"], 2
        )

    def test_missing_other_provider_does_not_block_selected_provider(self):
        release = make_audio_release()
        release["spotify"] = None
        release["verification"]["spotify"] = {
            "status": "pending", "verified_track_count": 0,
        }
        self.assertEqual(
            validate_audio_release(release, provider="yt-dlp")["track_count"], 2
        )
        with self.assertRaisesRegex(ValueError, "no Spotify release"):
            validate_audio_release(release, provider="spotisaver")

    def test_spotify_remains_usable_when_youtube_music_is_missing(self):
        release = make_audio_release()
        release["youtube_music"] = None
        release["verification"]["youtube_music"] = {
            "status": "pending", "verified_track_count": 0,
        }
        self.assertEqual(
            validate_audio_release(release, provider="spotisaver")["track_count"], 2
        )
        with self.assertRaisesRegex(ValueError, "no YouTube Music release"):
            validate_audio_release(release, provider="yt-dlp")

    def test_spotify_duplicate_track_ids_are_rejected(self):
        release = make_audio_release()
        release["spotify"]["tracks"][1]["track_id"] = release["spotify"]["tracks"][0]["track_id"]
        release["spotify"]["tracks"][1]["url"] = release["spotify"]["tracks"][0]["url"]
        with self.assertRaisesRegex(ValueError, "duplicates a previous track ID"):
            validate_audio_release(release, provider="spotisaver")

    def test_spotify_disc_positions_must_be_strictly_ordered(self):
        release = make_audio_release(spotify_count=3, youtube_count=2)
        release["spotify"]["tracks"][2]["track_number"] = 1
        with self.assertRaisesRegex(ValueError, "duplicates or are out of order"):
            validate_audio_release(release, provider="spotisaver")

    def test_spotify_declared_count_must_match_its_own_tracklist(self):
        release = make_audio_release()
        release["spotify"]["track_count"] = 3
        with self.assertRaisesRegex(ValueError, "Spotify declared track counts"):
            validate_audio_release(release, provider="spotisaver")

    def test_duplicate_youtube_video_ids_are_rejected(self):
        release = make_audio_release()
        release["youtube_music"]["tracks"][1]["video_id"] = release["youtube_music"]["tracks"][0]["video_id"]
        release["youtube_music"]["tracks"][1]["url"] = release["youtube_music"]["tracks"][0]["url"]
        with self.assertRaisesRegex(ValueError, "duplicates a previous video ID"):
            validate_audio_release(release, provider="yt-dlp")

    def test_unverified_selected_provider_is_rejected(self):
        release = make_audio_release()
        release["verification"]["youtube_music"]["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "does not independently mark"):
            validate_audio_release(release, provider="yt-dlp")

    def test_selected_provider_verified_count_must_match_its_list(self):
        release = make_audio_release()
        release["verification"]["youtube_music"]["verified_track_count"] = 1
        with self.assertRaisesRegex(ValueError, "verified tracks"):
            validate_audio_release(release, provider="yt-dlp")

    def test_wrong_audio_release_version_is_rejected(self):
        release = make_audio_release()
        release["schema_version"] = 1
        with self.assertRaisesRegex(ValueError, "schema version"):
            validate_audio_release(release, provider="yt-dlp")

    def test_spotify_track_id_must_match_url(self):
        release = make_audio_release()
        release["spotify"]["tracks"][0]["track_id"] = "x" * 22
        with self.assertRaisesRegex(ValueError, "Spotify track 1 URL"):
            validate_audio_release(release, provider="spotisaver")

    def test_youtube_video_id_must_match_url(self):
        release = make_audio_release()
        release["youtube_music"]["tracks"][0]["video_id"] = "x" * 11
        with self.assertRaisesRegex(ValueError, "YouTube Music track 1 URL"):
            validate_audio_release(release, provider="yt-dlp")

    def test_youtube_track_order_must_be_contiguous(self):
        release = make_audio_release()
        release["youtube_music"]["tracks"][1]["track_number"] = 3
        with self.assertRaisesRegex(ValueError, "not contiguous"):
            validate_audio_release(release, provider="yt-dlp")

    def test_playlist_count_must_match_its_own_tracklist(self):
        release = make_audio_release()
        release["youtube_music"]["playlist"]["track_count"] = 1
        with self.assertRaisesRegex(ValueError, "playlist count"):
            validate_audio_release(release, provider="yt-dlp")

    def test_spotify_multi_disc_track_numbers_are_preserved_with_flattened_order(self):
        release = make_audio_release(spotify_count=3, youtube_count=2)
        release["spotify"]["tracks"][2]["disc_number"] = 2
        release["spotify"]["tracks"][2]["track_number"] = 1
        plan = validate_audio_release(release, provider="spotisaver")
        self.assertEqual([t["track_number"] for t in plan["tracks"]], [1, 2, 3])
        self.assertEqual(plan["tracks"][2]["source_track_number"], 1)
        self.assertEqual(plan["tracks"][2]["disc_number"], 2)


if __name__ == "__main__":
    unittest.main()
