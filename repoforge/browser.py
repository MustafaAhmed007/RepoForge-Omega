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
