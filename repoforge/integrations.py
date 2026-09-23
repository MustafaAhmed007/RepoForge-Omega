from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IntegrationConfig:
    name: str
    enabled: bool = False
    endpoint: str | None = None


class IntegrationRegistry:
    """Vendor-neutral integration registry for MCP, browser, editor and plugin adapters."""

    def __init__(self) -> None:
        self._items: dict[str, IntegrationConfig] = {}

    def register(self, config: IntegrationConfig) -> None:
        self._items[config.name] = config

    def enabled(self) -> list[IntegrationConfig]:
        return [item for item in self._items.values() if item.enabled]

    def names(self) -> list[str]:
        return list(self._items)
