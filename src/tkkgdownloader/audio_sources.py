"""Validate verified Spotify and YouTube Music track mappings from TKKGData."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse


SPOTIFY_ID = re.compile(r"^[A-Za-z0-9]{22}$")
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _required_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"Verified audio metadata has an invalid {field}.")
    return value


def validate_audio_release(audio_release: Any) -> dict[str, Any]:
    """Return a normalized download plan or reject incomplete/unverified metadata."""
    if not isinstance(audio_release, dict):
        raise ValueError("No verified audio release is available in TKKGData for this episode.")
    verification = audio_release.get("verification")
    spotify = audio_release.get("spotify")
    youtube_music = audio_release.get("youtube_music")
    if not isinstance(verification, dict) or verification.get("status") != "verified":
        raise ValueError("TKKGData does not mark this audio release as verified.")
    if not isinstance(spotify, dict) or not isinstance(youtube_music, dict):
        raise ValueError("TKKGData audio release is missing Spotify or YouTube Music metadata.")

    album_id = spotify.get("album_id")
    album_url = spotify.get("url")
    if not isinstance(album_id, str) or not SPOTIFY_ID.fullmatch(album_id):
        raise ValueError("TKKGData audio release has an invalid Spotify album ID.")
    if album_url != f"https://open.spotify.com/album/{album_id}":
        raise ValueError("TKKGData Spotify album URL does not match its album ID.")
    if not isinstance(spotify.get("title"), str) or not spotify["title"].strip():
        raise ValueError("TKKGData audio release has no Spotify album title.")

    tracks = youtube_music.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("TKKGData audio release has no verified individual YouTube Music track links.")
    expected_count = _required_int(spotify.get("track_count"), "Spotify track_count")
    ytm_count = _required_int(youtube_music.get("track_count"), "YouTube Music track_count")
    matched_count = _required_int(verification.get("matched_track_count"), "matched_track_count")
    if expected_count != len(tracks) or ytm_count != len(tracks) or matched_count != len(tracks):
        raise ValueError("Spotify, YouTube Music, and verified matched track counts do not agree.")

    normalized_tracks: list[dict[str, Any]] = []
    for index, track in enumerate(tracks, start=1):
        if not isinstance(track, dict):
            raise ValueError(f"TKKGData audio track {index} is malformed.")
        track_number = _required_int(track.get("track_number"), f"track {index} number")
        if track_number != index:
            raise ValueError("TKKGData audio track numbering is not contiguous and ordered.")

        spotify_track_id = track.get("spotify_track_id")
        spotify_track_url = track.get("spotify_track_url")
        if not isinstance(spotify_track_id, str) or not SPOTIFY_ID.fullmatch(spotify_track_id):
            raise ValueError(f"TKKGData Spotify track {index} has an invalid ID.")
        if spotify_track_url != f"https://open.spotify.com/track/{spotify_track_id}":
            raise ValueError(f"TKKGData Spotify track {index} URL does not match its ID.")

        video_id = track.get("video_id")
        ytm_url = track.get("url")
        if not isinstance(video_id, str) or not YOUTUBE_ID.fullmatch(video_id):
            raise ValueError(f"TKKGData YouTube Music track {index} has an invalid video ID.")
        parsed_ytm = urlparse(str(ytm_url or ""))
        query_video_id = parse_qs(parsed_ytm.query).get("v", [None])[0]
        if parsed_ytm.scheme != "https" or parsed_ytm.netloc != "music.youtube.com" or parsed_ytm.path != "/watch" or query_video_id != video_id:
            raise ValueError(f"TKKGData YouTube Music track {index} URL does not match its video ID.")

        normalized_tracks.append({
            "track_number": track_number,
            "spotify_track_url": spotify_track_url,
            "youtube_music_url": ytm_url,
            "spotify_title": track.get("spotify_title") or track.get("title") or f"Track {track_number}",
        })

    playlist = youtube_music.get("playlist")
    playlist_url = None
    if playlist is not None:
        if not isinstance(playlist, dict):
            raise ValueError("TKKGData YouTube Music playlist metadata is malformed.")
        playlist_id = playlist.get("playlist_id")
        playlist_url = playlist.get("url")
        parsed_playlist = urlparse(str(playlist_url or ""))
        query_playlist_id = parse_qs(parsed_playlist.query).get("list", [None])[0]
        if (
            not isinstance(playlist_id, str)
            or not re.fullmatch(r"(OLAK5uy_[A-Za-z0-9_-]+|PL[A-Za-z0-9_-]+)", playlist_id)
            or parsed_playlist.scheme != "https"
            or parsed_playlist.netloc != "music.youtube.com"
            or parsed_playlist.path != "/playlist"
            or query_playlist_id != playlist_id
        ):
            raise ValueError("TKKGData YouTube Music playlist URL does not match its playlist ID.")
        if playlist.get("track_count") != expected_count:
            raise ValueError("TKKGData YouTube Music playlist track count does not match Spotify.")
        # spotDL 4.5.2 pairs OLAK YouTube Music albums with Spotify albums.
        # A PL YouTube playlist would require a Spotify playlist, not this album.
        if not playlist_id.startswith("OLAK5uy_"):
            playlist_url = None

    return {
        "spotify_album_url": album_url,
        "spotify_album_title": spotify["title"],
        "youtube_music_playlist_url": playlist_url,
        "tracks": normalized_tracks,
        "track_count": expected_count,
    }

