from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProtocolEndpoint:
    name: str
    kind: str
    endpoint: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class ProtocolRegistry:
    """Protocol-neutral endpoint registry. Concrete MCP/editor/browser adapters plug in here."""

    def __init__(self) -> None:
        self._endpoints: dict[str, ProtocolEndpoint] = {}

    def register(self, endpoint: ProtocolEndpoint) -> None:
        self._endpoints[endpoint.name] = endpoint

    def get(self, name: str) -> ProtocolEndpoint:
        return self._endpoints[name]

    def list(self, kind: str | None = None) -> list[ProtocolEndpoint]:
        values = list(self._endpoints.values())
        return [x for x in values if kind is None or x.kind == kind]
