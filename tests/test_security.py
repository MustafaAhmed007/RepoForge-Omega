from repoforge.security import assess_command

def test_blocks_destructive_command():
    ok,reason=assess_command(["rm","-rf","/"])
    assert not ok and reason

def test_allows_safe_test_command():
    ok,reason=assess_command(["python","-m","pytest"])
    assert ok and reason is None
