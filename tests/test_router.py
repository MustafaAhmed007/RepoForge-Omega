from dataclasses import dataclass

import pytest

from repoforge.router import ModelRouter, RoutePolicy


@dataclass
class FakeProvider:
    name: str
    kind: str
    model: str = "test"


def test_router_respects_local_only_policy() -> None:
    local = FakeProvider("local", "local")
    remote = FakeProvider("remote", "remote")
    chosen, decision = ModelRouter(
        [remote, local],
        RoutePolicy(allow_remote=False, allow_local=True),
    ).choose("repair")
    assert chosen.name == "local"
    assert decision.candidates == ["local"]


def test_router_fails_when_policy_excludes_all_providers() -> None:
    with pytest.raises(RuntimeError):
        ModelRouter(
            [FakeProvider("remote", "remote")],
            RoutePolicy(allow_remote=False, allow_local=False),
        ).choose("repair")
