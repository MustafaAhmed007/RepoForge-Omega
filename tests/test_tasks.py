from repoforge.tasks import Task, TaskGraph, TaskStatus


def test_dependency_graph_releases_tasks_in_order() -> None:
    graph = TaskGraph([Task("a", "A", "discover"), Task("b", "B", "test", ["a"])])
    assert [task.id for task in graph.ready()] == ["a"]
    graph.mark("a", TaskStatus.PASSED)
    assert [task.id for task in graph.ready()] == ["b"]


def test_skipped_dependency_can_release_downstream_task() -> None:
    graph = TaskGraph([Task("a", "A", "repair"), Task("b", "B", "verify", ["a"])])
    graph.mark("a", TaskStatus.SKIPPED, ["no mutation required"])
    assert [task.id for task in graph.ready()] == ["b"]


def test_unknown_dependency_is_rejected() -> None:
    try:
        TaskGraph([Task("b", "B", "test", ["missing"])])
    except ValueError as exc:
        assert "Unknown task dependencies" in str(exc)
    else:
        raise AssertionError("expected missing dependency to fail")
