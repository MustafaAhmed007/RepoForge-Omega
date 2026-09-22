from pathlib import Path
from repoforge.fingerprint import detect

def test_detects_python_project(tmp_path:Path):
    (tmp_path/"pyproject.toml").write_text("[project]\nname='demo'\n",encoding="utf-8")
    (tmp_path/"main.py").write_text("print('ok')\n",encoding="utf-8")
    fp=detect(tmp_path)
    assert "Python" in fp.languages
    assert "main.py" in fp.entry_points
