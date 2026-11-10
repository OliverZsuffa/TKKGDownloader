from __future__ import annotations

import re
import unittest

from tkkgdownloader.spotisaver import _find_zip_download_button


class FakeControl:
    def __init__(self, label="Download ZIP", href="/en/download/test?direct=1", visible=True, disabled=False):
        self.label = label
        self.href = href
        self.visible = visible
        self.disabled = disabled
        self.first = self

    def count(self):
        return 1

    def nth(self, index):
        return self

    def is_visible(self):
        return self.visible

    def is_enabled(self):
        return not self.disabled

    def inner_text(self, timeout=None):
        return self.label

    def get_attribute(self, name):
        if name == "href":
            return self.href
        if name == "aria-disabled":
            return "true" if self.disabled else None
        return None


class FakeCollection:
    def __init__(self, items):
        self.items = items
        self.first = items[0] if items else FakeEmptyControl()

    def count(self):
        return len(self.items)

    def nth(self, index):
        return self.items[index]


class FakeEmptyControl:
    def is_visible(self):
        return False

    def is_enabled(self):
        return False


class FakeModal:
    def __init__(self, links=None, buttons=None, role_lookup=True):
        self.links = links or []
        self.buttons = buttons or []
        self.role_lookup = role_lookup
        self.first = self

    def count(self):
        return 1

    def is_visible(self):
        return True

    def get_by_role(self, role, name):
        if not self.role_lookup:
            raise RuntimeError("Role lookup unavailable")
        if role == "link":
            return FakeCollection(self.links)
        if role == "button":
            return FakeCollection(self.buttons)
        return FakeCollection([])

    def locator(self, selector):
        if selector == ".zip-ready-card a.zrc-cta":
            return FakeCollection(self.links)
        if selector == "button":
            return FakeCollection(self.buttons)
        raise AssertionError(f"Unexpected selector: {selector}")


class FakePage:
    def __init__(self, modal):
        self.modal = modal

    def locator(self, selector):
        if selector != ".modal.show":
            raise AssertionError(f"Unexpected selector: {selector}")
        return self.modal


class SpotisaverZipLinkTests(unittest.TestCase):
    def test_finds_ready_card_anchor_by_accessible_link_name(self):
        link = FakeControl(href="https://spotisaver.net/en/download/album_test?direct=1")
        result = _find_zip_download_button(FakePage(FakeModal(links=[link])))
        self.assertIs(result, link)
        self.assertIn("/en/download/", result.get_attribute("href"))

    def test_finds_ready_card_anchor_by_observed_css_fallback(self):
        link = FakeControl()
        result = _find_zip_download_button(
            FakePage(FakeModal(links=[link], role_lookup=False))
        )
        self.assertIs(result, link)

    def test_rejects_hidden_ready_card_anchor(self):
        link = FakeControl(visible=False)
        self.assertIsNone(_find_zip_download_button(FakePage(FakeModal(links=[link]))))

    def test_rejects_anchor_without_download_href(self):
        link = FakeControl(href="")
        self.assertIsNone(_find_zip_download_button(FakePage(FakeModal(links=[link]))))

    def test_rejects_aria_disabled_anchor(self):
        link = FakeControl(disabled=True)
        self.assertIsNone(_find_zip_download_button(FakePage(FakeModal(links=[link]))))

    def test_rejects_ambiguous_ready_card_links(self):
        links = [FakeControl(), FakeControl()]
        with self.assertRaisesRegex(RuntimeError, "2 matching Download ZIP links"):
            _find_zip_download_button(FakePage(FakeModal(links=links)))

    def test_keeps_compatibility_with_button_markup(self):
        button = FakeControl()
        result = _find_zip_download_button(FakePage(FakeModal(buttons=[button])))
        self.assertIs(result, button)


if __name__ == "__main__":
    unittest.main()
