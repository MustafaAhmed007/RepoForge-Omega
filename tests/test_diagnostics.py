from pathlib import Path
from repoforge.diagnostics import DiagnosticEngine

def test_missing_tests_is_reported(tmp_path: Path):
    (tmp_path/'main.py').write_text('print(1)\n',encoding='utf-8')
    _, findings=DiagnosticEngine(tmp_path).run()
    assert any(x.code=='NO_TESTS' for x in findings)
