"""Validate provider-specific audio release plans from TKKGData schema v2."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

SPOTIFY_ID = re.compile(r"^[A-Za-z0-9]{22}$")
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID = re.compile(r"^(OLAK5uy_[A-Za-z0-9_-]+|PL[A-Za-z0-9_-]+)$")


def _required_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"Verified audio metadata has an invalid {field}.")
    return value


def _provider_verification(audio_release: dict[str, Any], provider: str, count: int) -> None:
    verification = audio_release.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("TKKGData audio release has no verification metadata.")
    if verification.get("status") not in ("verified", "partial", "unverified"):
        raise ValueError("TKKGData audio release has an invalid combined verification status.")
    if not isinstance(verification.get("method"), str) or not verification["method"].strip():
        raise ValueError("TKKGData audio release has no verification method.")
    if audio_release.get("schema_version") != 2:
        raise ValueError(
            f"Unsupported TKKGData audio release schema version: "
            f"{audio_release.get('schema_version')!r}; expected 2."
        )
    provider_verification = verification.get(provider)
    if not isinstance(provider_verification, dict):
        raise ValueError(f"TKKGData has no {provider} verification record.")
    if provider_verification.get("status") != "verified":
        raise ValueError(
            f"TKKGData does not independently mark {provider} as verified "
            f"(status: {provider_verification.get('status')!r})."
        )
    verified_count = provider_verification.get("verified_track_count")
    if isinstance(verified_count, bool) or verified_count != count:
        raise ValueError(
            f"TKKGData {provider} verification reports {verified_count!r} verified tracks, "
            f"but its provider tracklist contains {count}."
        )


def _validate_track_order(tracks: Any, provider_label: str) -> list[dict[str, Any]]:
    if not isinstance(tracks, list) or not tracks:
        raise ValueError(f"TKKGData has no {provider_label} individual tracklist.")
    result: list[dict[str, Any]] = []
    for index, track in enumerate(tracks, start=1):
        if not isinstance(track, dict):
            raise ValueError(f"TKKGData {provider_label} track {index} is malformed.")
        number = _required_int(track.get("track_number"), f"{provider_label} track {index} number")
        if number != index:
            raise ValueError(
                f"TKKGData {provider_label} track numbering is not contiguous and ordered "
                f"at position {index} (found {number})."
            )
        result.append(track)
    return result


def _validate_spotify(audio_release: dict[str, Any]) -> dict[str, Any]:
    spotify = audio_release.get("spotify")
    if not isinstance(spotify, dict):
        raise ValueError("TKKGData has no Spotify release metadata.")
    album = spotify.get("album")
    if not isinstance(album, dict):
        raise ValueError("TKKGData Spotify release has no album metadata.")

    album_id = album.get("album_id")
    album_url = album.get("url")
    if not isinstance(album_id, str) or not SPOTIFY_ID.fullmatch(album_id):
        raise ValueError("TKKGData Spotify release has an invalid album ID.")
    if album_url != f"https://open.spotify.com/album/{album_id}":
        raise ValueError("TKKGData Spotify album URL does not match its album ID.")
    album_title = album.get("title")
    if not isinstance(album_title, str) or not album_title.strip():
        raise ValueError("TKKGData Spotify release has no album title.")
    source_query = album.get("source_query")
    if not isinstance(source_query, str) or not source_query.strip():
        raise ValueError("TKKGData Spotify release has no source query provenance.")

    raw_tracks = spotify.get("tracks")
    if not isinstance(raw_tracks, list) or not raw_tracks:
        raise ValueError("TKKGData has no Spotify individual tracklist.")
    tracks = []
    previous_position: tuple[int, int] | None = None
    for index, track in enumerate(raw_tracks, start=1):
        if not isinstance(track, dict):
            raise ValueError(f"TKKGData Spotify track {index} is malformed.")
        source_number = _required_int(track.get("track_number"), f"Spotify track {index} number")
        disc_number = track.get("disc_number", 1)
        if isinstance(disc_number, bool) or not isinstance(disc_number, int) or disc_number < 1:
            raise ValueError(f"TKKGData Spotify track {index} has an invalid disc number.")
        position = (disc_number, source_number)
        if previous_position is not None and position <= previous_position:
            raise ValueError("TKKGData Spotify album positions contain duplicates or are out of order.")
        previous_position = position
        tracks.append(track)
    count = _required_int(spotify.get("track_count"), "Spotify track_count")
    album_count = _required_int(album.get("track_count"), "Spotify album track_count")
    if count != len(tracks) or album_count != len(tracks):
        raise ValueError(
            "TKKGData Spotify declared track counts do not match its own ordered tracklist."
        )

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, track in enumerate(tracks, start=1):
        track_id = track.get("track_id")
        track_url = track.get("url")
        title = track.get("title")
        if not isinstance(track_id, str) or not SPOTIFY_ID.fullmatch(track_id):
            raise ValueError(f"TKKGData Spotify track {index} has an invalid track ID.")
        if track_url != f"https://open.spotify.com/track/{track_id}":
            raise ValueError(f"TKKGData Spotify track {index} URL does not match its ID.")
        if track_id in seen_ids:
            raise ValueError(f"TKKGData Spotify track {index} duplicates a previous track ID.")
        seen_ids.add(track_id)
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"TKKGData Spotify track {index} has no title.")

        disc_number = track.get("disc_number", 1)
        source_number = track["track_number"]
        normalized.append({
            "track_number": index,
            "source_track_number": source_number,
            "disc_number": disc_number,
            "spotify_track_id": track_id,
            "spotify_track_url": track_url,
            "spotify_title": title.strip(),
            "alternate_titles": [],
        })

    _provider_verification(audio_release, "spotify", len(normalized))
    return {
        "provider": "spotisaver",
        "album_title": album_title.strip(),
        "spotify_album_title": album_title.strip(),
        "spotify_album_url": album_url,
        "spotify_album_id": album_id,
        "tracks": normalized,
        "track_count": len(normalized),
    }


def _validate_youtube_music(audio_release: dict[str, Any]) -> dict[str, Any]:
    youtube = audio_release.get("youtube_music")
    if not isinstance(youtube, dict):
        raise ValueError("TKKGData has no YouTube Music release metadata.")

    tracks = _validate_track_order(youtube.get("tracks"), "YouTube Music")
    count = _required_int(youtube.get("track_count"), "YouTube Music track_count")
    if count != len(tracks):
        raise ValueError(
            "TKKGData YouTube Music declared track count does not match its own ordered tracklist."
        )

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, track in enumerate(tracks, start=1):
        video_id = track.get("video_id")
        url = track.get("url")
        title = track.get("title")
        if not isinstance(video_id, str) or not YOUTUBE_ID.fullmatch(video_id):
            raise ValueError(f"TKKGData YouTube Music track {index} has an invalid video ID.")
        parsed = urlparse(str(url or ""))
        query_id = parse_qs(parsed.query).get("v", [None])[0]
        if (
            parsed.scheme != "https" or parsed.netloc != "music.youtube.com"
            or parsed.path != "/watch" or query_id != video_id
        ):
            raise ValueError(f"TKKGData YouTube Music track {index} URL does not match its video ID.")
        if video_id in seen_ids:
            raise ValueError(f"TKKGData YouTube Music track {index} duplicates a previous video ID.")
        seen_ids.add(video_id)
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"TKKGData YouTube Music track {index} has no title.")
        artists = track.get("artists")
        if not isinstance(artists, list) or not all(
            isinstance(artist, str) for artist in artists
        ):
            raise ValueError(f"TKKGData YouTube Music track {index} has invalid artist metadata.")
        normalized.append({
            "track_number": index,
            "video_id": video_id,
            "youtube_music_url": url,
            "title": title.strip(),
        })

    _provider_verification(audio_release, "youtube_music", len(normalized))

    album = youtube.get("album")
    album_title = None
    if album is not None:
        if not isinstance(album, dict):
            raise ValueError("TKKGData YouTube Music album metadata is malformed.")
        browse_id = album.get("browse_id")
        album_url = album.get("url")
        parsed_album = urlparse(str(album_url or ""))
        path_id = parsed_album.path.rstrip("/").split("/")[-1]
        if (
            not isinstance(browse_id, str) or not browse_id.strip()
            or parsed_album.scheme != "https"
            or parsed_album.netloc != "music.youtube.com"
            or parsed_album.path != f"/browse/{browse_id}"
            or path_id != browse_id
        ):
            raise ValueError("TKKGData YouTube Music album URL does not match its browse ID.")
        album_count = _required_int(album.get("track_count"), "YouTube Music album track_count")
        if album_count != len(normalized):
            raise ValueError("TKKGData YouTube Music album count does not match its own tracklist.")
        album_title = album.get("title")
        if not isinstance(album_title, str) or not album_title.strip():
            raise ValueError("TKKGData YouTube Music album has no title.")
        album_title = album_title.strip()

    playlist = youtube.get("playlist")
    playlist_url = None
    if playlist is not None:
        if not isinstance(playlist, dict):
            raise ValueError("TKKGData YouTube Music playlist metadata is malformed.")
        playlist_id = playlist.get("playlist_id")
        playlist_url = playlist.get("url")
        parsed_playlist = urlparse(str(playlist_url or ""))
        query_id = parse_qs(parsed_playlist.query).get("list", [None])[0]
        if (
            not isinstance(playlist_id, str) or not PLAYLIST_ID.fullmatch(playlist_id)
            or parsed_playlist.scheme != "https"
            or parsed_playlist.netloc != "music.youtube.com"
            or parsed_playlist.path != "/playlist"
            or query_id != playlist_id
        ):
            raise ValueError("TKKGData YouTube Music playlist URL does not match its playlist ID.")
        playlist_title = playlist.get("title")
        if not isinstance(playlist_title, str) or not playlist_title.strip():
            raise ValueError("TKKGData YouTube Music playlist has no title.")
        playlist_count = _required_int(playlist.get("track_count"), "YouTube Music playlist track_count")
        if playlist_count != len(normalized):
            raise ValueError("TKKGData YouTube Music playlist count does not match its own tracklist.")

    verification = audio_release["verification"]["youtube_music"]
    playlist_status = verification.get("playlist_status")
    if playlist_status == "verified" and playlist is None:
        raise ValueError("TKKGData marks the YouTube Music playlist verified but supplies no playlist.")
    if playlist_status == "unavailable":
        playlist_url = None
    elif playlist_status not in (None, "verified"):
        raise ValueError(f"TKKGData has an unsupported YouTube Music playlist status: {playlist_status!r}.")

    return {
        "provider": "yt-dlp",
        "album_title": album_title,
        "youtube_music_album_title": album_title,
        "youtube_music_album_url": album.get("url") if isinstance(album, dict) else None,
        "youtube_music_playlist_url": playlist_url,
        "tracks": normalized,
        "track_count": len(normalized),
    }


def validate_audio_release(audio_release: Any, provider: str = "yt-dlp") -> dict[str, Any]:
    """Build a strictly validated plan for exactly one selected provider.

    Spotify and YouTube Music are validated independently. No cross-provider
    track count, title, numbering, or positional correspondence is assumed.
    """
    if not isinstance(audio_release, dict):
        raise ValueError("No audio release metadata is available in TKKGData for this episode.")
    if provider in ("yt-dlp", "youtube_music"):
        return _validate_youtube_music(audio_release)
    if provider in ("spotisaver", "spotify"):
        return _validate_spotify(audio_release)
    raise ValueError(f"Unsupported audio provider: {provider!r}.")
