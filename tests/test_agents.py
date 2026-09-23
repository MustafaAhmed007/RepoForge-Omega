from repoforge.agents import AgentRuntime, AgentRole, AgentSpec


def test_default_agents_cover_roles() -> None:
    runtime = AgentRuntime()
    runtime.register_defaults()
    assert {spec.role for spec in runtime.specs()} == set(AgentRole)


def test_unhandled_agent_is_planned() -> None:
    runtime = AgentRuntime()
    runtime.register(AgentSpec("review", AgentRole.REVIEW))
    assert runtime.run("review", {}).status == "PLANNED"
