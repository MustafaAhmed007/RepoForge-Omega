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

    def choose(self, task: str) -> tuple[ModelProvider, RouteDecision]:
        available = [p for p in self.providers if getattr(p, "name", "disabled") != "disabled"]
        if not available:
            raise RuntimeError(f"No model provider available for task: {task}")
        ordered = sorted(
            available,
            key=lambda p: self.policy.preferred.index(p.name)
            if p.name in self.policy.preferred else len(self.policy.preferred),
        )
        chosen = ordered[: self.policy.max_candidates][0]
        return chosen, RouteDecision(chosen.name, f"selected for {task}", [p.name for p in ordered])
