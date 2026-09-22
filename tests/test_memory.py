from pathlib import Path
from repoforge.memory import MemoryStore

def test_memory_round_trip(tmp_path:Path):
    store=MemoryStore(tmp_path/'events.jsonl')
    store.append('verification','pass','tests','all tests passed')
    events=store.recent()
    assert len(events)==1 and events[0].outcome=='pass'
