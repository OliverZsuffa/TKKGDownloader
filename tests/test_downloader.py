import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tkkgdownloader.downloader import download_episode, download_episode_spotisaver
from tkkgdownloader.episodes import Episode


def audio_release(track_count=2, with_playlist=True, spotify_track_count=None):
    spotify_track_count = track_count if spotify_track_count is None else spotify_track_count
    spotify_album_id = "0ZqyFeMXxCyIJvYptGlnn1"
    playlist = None
    if with_playlist:
        playlist_id = "OLAK5uy_mQRbJNANh1H4CKbmM5ez5LSW1HJFvE3QI"
        playlist = {
            "playlist_id": playlist_id,
            "url": f"https://music.youtube.com/playlist?list={playlist_id}",
            "title": "YouTube episode playlist",
            "track_count": track_count,
        }
    spotify_tracks = []
    for number in range(1, spotify_track_count + 1):
        track_id = f"{number:022d}"
        spotify_tracks.append({
            "track_number": number,
            "track_id": track_id,
            "url": f"https://open.spotify.com/track/{track_id}",
            "title": f"Teil {number:02d}",
        })
    youtube_tracks = []
    for number in range(1, track_count + 1):
        video_id = f"videoid{number:04d}"
        youtube_tracks.append({
            "track_number": number,
            "video_id": video_id,
            "url": f"https://music.youtube.com/watch?v={video_id}",
            "title": f"Teil {number:02d}",
            "artists": ["TKKG"],
        })
    return {
        "schema_version": 2,
        "spotify": {
            "album": {
                "album_id": spotify_album_id,
                "url": f"https://open.spotify.com/album/{spotify_album_id}",
                "title": "Spotify episode album",
                "track_count": spotify_track_count,
                "source_query": "reviewed episode album",
            },
            "tracks": spotify_tracks,
            "track_count": spotify_track_count,
        },
        "youtube_music": {
            "album": {
                "browse_id": "MPREb_Example",
                "url": "https://music.youtube.com/browse/MPREb_Example",
                "title": "YouTube episode album",
                "track_count": track_count,
            },
            "playlist": playlist,
            "tracks": youtube_tracks,
            "track_count": track_count,
        },
        "verification": {
            "status": "verified" if spotify_track_count == track_count else "partial",
            "verified_at": "2026-11-24T12:00:00Z",
            "method": "independent_provider_tracklist_validation",
            "spotify": {"status": "verified", "verified_track_count": spotify_track_count},
            "youtube_music": {
                "status": "verified",
                "verified_track_count": track_count,
                "playlist_status": "verified" if with_playlist else "unavailable",
                "playlist_error": None,
            },
        },
    }
