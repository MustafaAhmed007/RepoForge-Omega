from repoforge.providers import DisabledProvider, provider_from_environment


def test_provider_is_disabled_without_credentials(monkeypatch):
    monkeypatch.delenv("REPOFORGE_PROVIDER", raising=False)
    monkeypatch.delenv("REPOFORGE_API_KEY", raising=False)
    assert isinstance(provider_from_environment(), DisabledProvider)
