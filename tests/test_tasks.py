from repoforge.tasks import Task, TaskGraph, TaskStatus


def test_dependency_graph_releases_tasks_in_order() -> None:
    graph = TaskGraph([Task("a", "A", "discover"), Task("b", "B", "test", ["a"])])
    assert [task.id for task in graph.ready()] == ["a"]
    graph.mark("a", TaskStatus.PASSED)
    assert [task.id for task in graph.ready()] == ["b"]
