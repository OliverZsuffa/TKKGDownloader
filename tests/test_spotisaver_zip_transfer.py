from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tkkgdownloader.spotisaver import (
    _wait_for_cdp_download_completion,
    _wait_for_download_file,
)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class FakePage:
    def __init__(self, clock, on_wait=None):
        self.clock = clock
        self.on_wait = on_wait
        self.waits = 0

    def wait_for_timeout(self, milliseconds):
        self.waits += 1
        self.clock.now += milliseconds / 1000
        if self.on_wait:
            self.on_wait(self.waits)


class SpotisaverZipTransferTests(unittest.TestCase):
    def _state(self, clock):
        return {
            "state": "inProgress",
            "received_bytes": 0,
            "total_bytes": 1000,
            "last_progress_at": clock.monotonic(),
        }

    def test_transfer_longer_than_30_seconds_succeeds_when_bytes_keep_arriving(self):
        clock = FakeClock()
        state = self._state(clock)

        def progress(wait_number):
            if wait_number in (40, 80, 120, 160, 200):
                state["received_bytes"] += 100
                state["last_progress_at"] = clock.monotonic()
            if wait_number == 240:
                state["received_bytes"] = 1000
                state["state"] = "completed"

        page = FakePage(clock, progress)
        with patch("tkkgdownloader.spotisaver.time.monotonic", clock.monotonic):
            _wait_for_cdp_download_completion(page, state)
        self.assertGreater(clock.now, 30)
        self.assertEqual(state["state"], "completed")

    def test_intermittent_progress_resets_inactivity_timer(self):
        clock = FakeClock()
        state = self._state(clock)

        def progress(wait_number):
            if wait_number in (300, 600, 900):
                state["received_bytes"] += 100
                state["last_progress_at"] = clock.monotonic()
            if wait_number == 901:
                state["state"] = "completed"

        page = FakePage(clock, progress)
        with patch("tkkgdownloader.spotisaver.time.monotonic", clock.monotonic):
            _wait_for_cdp_download_completion(page, state, inactivity_timeout_seconds=120)
        self.assertGreater(clock.now, 120)
        self.assertEqual(state["received_bytes"], 300)

    def test_no_progress_times_out_with_received_and_expected_bytes(self):
        clock = FakeClock()
        state = self._state(clock)
        state["received_bytes"] = 497
        state["last_progress_at"] = 0
        page = FakePage(clock)
        with patch("tkkgdownloader.spotisaver.time.monotonic", clock.monotonic):
            with self.assertRaisesRegex(RuntimeError, "497 B of 1000 B"):
                _wait_for_cdp_download_completion(
                    page, state, inactivity_timeout_seconds=2, heartbeat_interval_seconds=10
                )
        self.assertGreaterEqual(clock.now, 2)

    def test_explicit_cancellation_fails_immediately(self):
        clock = FakeClock()
        state = self._state(clock)
        state.update({"state": "canceled", "received_bytes": 350})
        page = FakePage(clock)
        with patch("tkkgdownloader.spotisaver.time.monotonic", clock.monotonic):
            with self.assertRaisesRegex(RuntimeError, "canceled.*350 B of 1000 B"):
                _wait_for_cdp_download_completion(page, state)
        self.assertEqual(page.waits, 0)

    def test_file_verification_has_its_own_timeout_after_transfer_completion(self):
        clock = FakeClock()
        page = FakePage(clock)
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "album.zip"

            def create_file(wait_number):
                if wait_number == 2:
                    destination.write_bytes(b"archive")

            page.on_wait = create_file
            with patch("tkkgdownloader.spotisaver.time.monotonic", clock.monotonic):
                _wait_for_download_file(page, destination, timeout_seconds=5)
            self.assertEqual(destination.read_bytes(), b"archive")
            self.assertEqual(page.waits, 4)


if __name__ == "__main__":
    unittest.main()
