from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class DependencyGraph:
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add(self, source: str, target: str) -> None:
        self.edges.setdefault(source, set()).add(target)

    def dependencies_of(self, source: str) -> list[str]:
        return sorted(self.edges.get(source, set()))


def build_python_graph(repo: Path) -> DependencyGraph:
    g = DependencyGraph()
    for p in repo.rglob("*.py"):
        if any(x in {".git", ".venv", "venv", ".repoforge", "__pycache__"} for x in p.parts):
            continue
        rel = str(p.relative_to(repo)).replace("\\", "/")
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    g.add(rel, imported.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                g.add(rel, node.module)
    return g
