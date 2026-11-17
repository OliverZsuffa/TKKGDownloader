"""User-level TOML configuration and validation."""

from __future__ import annotations

import os
from pathlib import Path
import tomllib
from typing import Any


class ConfigurationError(ValueError):
    """Raised when the user configuration cannot be read or validated."""


_ALLOWED_KEYS = {
    "default_provider",
    "output_dir",
    "show_browser",
    "mute_browser_audio",
}


def default_config_path() -> Path:
    """Return the platform-appropriate per-user configuration path."""
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return root / "TKKGDownloader" / "config.toml"
    root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return root / "tkkgdownloader" / "config.toml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load optional TOML settings, rejecting malformed or unsupported values."""
    config_path = Path(path).expanduser() if path is not None else default_config_path()
    try:
        with config_path.open("rb") as stream:
            values = tomllib.load(stream)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Invalid TOML in {config_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Could not read configuration file {config_path}: {exc}") from exc

    unknown = sorted(set(values) - _ALLOWED_KEYS)
    if unknown:
        raise ConfigurationError(
            f"Unknown configuration key(s) in {config_path}: {', '.join(unknown)}. "
            f"Supported keys: {', '.join(sorted(_ALLOWED_KEYS))}."
        )

    provider = values.get("default_provider")
    if provider is not None and (not isinstance(provider, str) or provider not in {"yt-dlp", "spotisaver"}):
        raise ConfigurationError("default_provider must be either 'yt-dlp' or 'spotisaver'.")

    output_dir = values.get("output_dir")
    if output_dir is not None and (not isinstance(output_dir, str) or not output_dir.strip()):
        raise ConfigurationError("output_dir must be a non-empty string.")

    for key in ("show_browser", "mute_browser_audio"):
        if key in values and type(values[key]) is not bool:
            raise ConfigurationError(f"{key} must be true or false.")

    return values
