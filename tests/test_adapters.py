from pathlib import Path
from repoforge.adapters import PythonAdapter, discover_checks
def test_python_adapter_discovers_pytest(tmp_path: Path):
    (tmp_path/"pyproject.toml").write_text("[project]\nname='x'\n",encoding="utf-8")
    (tmp_path/"main.py").write_text("print(1)\n",encoding="utf-8")
    (tmp_path/"tests").mkdir()
    assert any(x.name=="python-tests" for x in PythonAdapter().checks(tmp_path))
    assert any(x.name=="python-tests" for x in discover_checks(tmp_path))
