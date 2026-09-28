from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .permissions import PermissionPolicy


class BrowserAdapter(Protocol):
    def open(self, url: str) -> None: ...
    def snapshot(self) -> str: ...
    def close(self) -> None: ...


@dataclass(slots=True)
class BrowserSession:
    policy: PermissionPolicy

    def open(self, url: str, adapter: BrowserAdapter) -> None:
        self.policy.authorize_browser()
        adapter.open(url)

    def snapshot(self, adapter: BrowserAdapter) -> str:
        self.policy.authorize_browser()
        return adapter.snapshot()

    def close(self, adapter: BrowserAdapter) -> None:
        adapter.close()


from urllib.parse import urlparse

@dataclass(frozen=True, slots=True)
class BrowserCheck:
    url: str
    title: str
    status: int
    ok: bool
    error: str | None = None

class BrowserVerifier:
    def verify(self, url: str, timeout_ms: int = 15000) -> BrowserCheck:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return BrowserCheck(url, "", 0, False, "Only absolute HTTP(S) URLs are allowed.")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return BrowserCheck(url, "", 0, False, "Playwright is not installed.")
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                title = page.title()
                status = response.status if response else 0
                browser.close()
                return BrowserCheck(url, title, status, 200 <= status < 400)
        except Exception as exc:
            return BrowserCheck(url, "", 0, False, str(exc))
