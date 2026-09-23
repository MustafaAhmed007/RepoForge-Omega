from __future__ import annotations

from dataclasses import dataclass, field

from .providers import ModelProvider


@dataclass(slots=True)
class RoutePolicy:
    preferred: list[str] = field(default_factory=list)
    allow_remote: bool = True
    allow_local: bool = True
    max_candidates: int = 3


@dataclass(slots=True)
class RouteDecision:
    provider: str
    reason: str
    candidates: list[str]


class ModelRouter:
    """Selects an available reasoning adapter; never decides release status."""

    def __init__(self, providers: list[ModelProvider], policy: RoutePolicy | None = None) -> None:
        self.providers = providers
        self.policy = policy or RoutePolicy()

    def _allowed(self, provider: ModelProvider) -> bool:
        kind = str(getattr(provider, "kind", "remote")).lower()
        if kind == "local":
            return self.policy.allow_local
        return self.policy.allow_remote

    def choose(self, task: str) -> tuple[ModelProvider, RouteDecision]:
        available = [
            provider for provider in self.providers
            if getattr(provider, "name", "disabled") != "disabled" and self._allowed(provider)
        ]
        if not available:
            raise RuntimeError(f"No model provider available for task: {task}")
        ordered = sorted(
            available,
            key=lambda provider: self.policy.preferred.index(provider.name)
            if provider.name in self.policy.preferred else len(self.policy.preferred),
        )
        candidates = [provider.name for provider in ordered[: self.policy.max_candidates]]
        chosen = ordered[0]
        return chosen, RouteDecision(
            chosen.name,
            f"selected for {task}",
            candidates,
        )
