from repoforge.evidence import EvidenceBundle, EvidenceItem
def test_evidence_is_redacted_and_digested():
    b=EvidenceBundle("run")
    b.add(EvidenceItem("log","x","api_key=SUPERSECRET"))
    assert "SUPERSECRET" not in b.items[0].content
    assert b.digest()
