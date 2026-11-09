"""Build spotDL queries for TKKG releases."""

from .episodes import Episode


def build_album_query(episode: Episode) -> str:
    """Return a Spotify album search query containing number and official title."""
    return f"album:TKKG {episode.number:03d} {episode.title}"
