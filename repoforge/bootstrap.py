from __future__ import annotations
from pathlib import Path

DEFAULT_CONFIG='''[repoforge]\nversion = 1\nmode = "evidence-first"\ntimeout_seconds = 120\nrepair_mode = "plan-only"\n'''

def bootstrap(repo:Path)->Path:
    target=repo/'.repoforge'
    target.mkdir(exist_ok=True)
    config=target/'config.toml'
    if not config.exists(): config.write_text(DEFAULT_CONFIG,encoding='utf-8')
    return target
