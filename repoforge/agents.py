from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable


class AgentRole(str, Enum):
    DISCOVER = "discover"
    DIAGNOSE = "diagnose"
    PLAN = "plan"
    REPAIR = "repair"
    TEST = "test"
    REVIEW = "review"
    SECURITY = "security"
    RELEASE = "release"


@dataclass(slots=True)
class AgentSpec:
    name: str
    role: AgentRole
    capabilities: set[str] = field(default_factory=set)
    max_iterations: int = 1
    requires_approval: bool = True


@dataclass(slots=True)
class AgentResult:
    agent: str
    status: str
    evidence: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    error: str | None = None


AgentHandler = Callable[[AgentSpec, dict[str, object]], AgentResult]


class AgentRuntime:
    """Small, deterministic agent runtime; providers are execution adapters, not authorities."""

    def __init__(self, handler: AgentHandler | None = None) -> None:
        self._agents: dict[str, AgentSpec] = {}
        self._handler = handler

    def register(self, spec: AgentSpec) -> None:
        self._agents[spec.name] = spec

    def register_defaults(self) -> None:
        for role in AgentRole:
            self.register(AgentSpec(f"{role.value}-agent", role, {role.value}))

    def specs(self) -> list[AgentSpec]:
        return list(self._agents.values())

    def run(self, name: str, context: dict[str, object]) -> AgentResult:
        if name not in self._agents:
            raise KeyError(f"Unknown agent: {name}")
        spec = self._agents[name]
        if self._handler is None:
            return AgentResult(spec.name, "PLANNED", ["No execution handler configured"])
        return self._handler(spec, context)

    def run_many(self, names: Iterable[str], context: dict[str, object]) -> list[AgentResult]:
        return [self.run(name, context) for name in names]
