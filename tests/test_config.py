from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tkkgdownloader.config import ConfigurationError, default_config_path, load_config


class ConfigurationTests(unittest.TestCase):
    def test_missing_config_is_silent_and_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(load_config(Path(temp) / "missing.toml"), {})

    def test_loads_supported_values(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.toml"
            path.write_text(
                'default_provider = "spotisaver"\n'
                'output_dir = "D:/Music/TKKG"\n'
                'show_browser = true\n'
                'mute_browser_audio = false\n',
                encoding="utf-8",
            )
            self.assertEqual(load_config(path), {
                "default_provider": "spotisaver",
                "output_dir": "D:/Music/TKKG",
                "show_browser": True,
                "mute_browser_audio": False,
            })

    def test_rejects_malformed_toml(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.toml"
            path.write_text('default_provider = "spotisaver"\ninvalid', encoding="utf-8")
            with self.assertRaisesRegex(ConfigurationError, "Invalid TOML"):
                load_config(path)

    def test_rejects_invalid_values_and_unknown_keys(self):
        cases = (
            ('default_provider = "other"\n', "default_provider"),
            ('show_browser = "yes"\n', "show_browser"),
            ('output_dir = 42\n', "output_dir"),
            ('unknown_setting = true\n', "Unknown configuration key"),
        )
        for content, message in cases:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "config.toml"
                path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ConfigurationError, message):
                    load_config(path)

    def test_windows_config_path(self):
        with patch("tkkgdownloader.config.os.name", "nt"), patch.dict(
            os.environ, {"APPDATA": "C:/Users/Oliver/AppData/Roaming"}
        ):
            self.assertEqual(
                default_config_path(),
                Path("C:/Users/Oliver/AppData/Roaming/TKKGDownloader/config.toml"),
            )

    def test_xdg_config_path(self):
        with patch("tkkgdownloader.config.os.name", "posix"), patch.dict(
            os.environ, {"XDG_CONFIG_HOME": "/tmp/config"}
        ):
            self.assertEqual(default_config_path(), Path("/tmp/config/tkkgdownloader/config.toml"))


if __name__ == "__main__":
    unittest.main()
