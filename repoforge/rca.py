from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from .evidence import EvidenceBundle, EvidenceItem
from .models import VerificationReport


@dataclass(frozen=True, slots=True)
class Hypothesis:
    statement: str
    evidence: list[str]
    confidence: float
    category: str


@dataclass(slots=True)
class RootCauseAnalysis:
    run_id: str
    failure: str
    hypotheses: list[Hypothesis] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    reproduction: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def primary(self) -> Hypothesis | None:
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda h: h.confidence)


class RootCauseAnalysisEngine:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()

    def analyze(
        self, verification: VerificationReport, evidence: EvidenceBundle
    ) -> RootCauseAnalysis:
        failures = [
            c for c in verification.checks if c.status.value in {"FAIL", "BLOCKED"}
        ]
        if not failures:
            return RootCauseAnalysis(evidence.run_id, "No failing deterministic checks.")

        check = failures[0]
        output = (check.stdout + "\n" + check.stderr).strip()
        affected = re.findall(r"(?m)([A-Za-z0-9_./\\-]+\.py):\d+", output)
        hypotheses: list[Hypothesis] = []

        if "ModuleNotFoundError" in output or "ImportError" in output:
            hypotheses.append(
                Hypothesis(
                    "The target runtime is missing a dependency.",
                    ["import/module error"],
                    0.95,
                    "environment",
                )
            )

        if re.search(r"AssertionError|assert .*? == .*", output, re.I):
            hypotheses.append(
                Hypothesis(
                    "Implementation behavior differs from an explicit test contract.",
                    ["assertion failure"],
                    0.8,
                    "behavior",
                )
            )

        node = re.search(
            r"([A-Za-z0-9_./\\-]+\.py::[A-Za-z0-9_]+)", output
        )
        if node:
            test_ref = node.group(1)
            test_path = test_ref.split("::")[0]
            test_symbol = test_ref.split("::")[-1]
            affected.append(test_path)

            for path in self._trace_test_to_production(test_path, test_symbol):
                affected.append(path)
                hypotheses.append(
                    Hypothesis(
                        f"Failing test '{test_symbol}' calls production code in '{path}'.",
                        [test_ref, path],
                        0.85,
                        "localization",
                    )
                )

            for path in self._find_symbol(test_symbol):
                affected.append(path)
                hypotheses.append(
                    Hypothesis(
                        f"Implementation associated with '{test_symbol}' is a candidate root-cause location.",
                        [test_ref, path],
                        0.7,
                        "localization",
                    )
                )

        evidence.add(EvidenceItem("failure", check.name, output[-12000:]))
        for path in sorted(set(affected))[:20]:
            file_path = (self.repo / path).resolve()
            if file_path.is_file() and self.repo in file_path.parents:
                evidence.add(
                    EvidenceItem(
                        "source",
                        path,
                        file_path.read_text(
                            encoding="utf-8", errors="replace"
                        )[:50000],
                        0.8,
                    )
                )

        confidence = 0.0
        for hypothesis in hypotheses:
            confidence = max(confidence, hypothesis.confidence)

        return RootCauseAnalysis(
            evidence.run_id,
            f"{check.name} failed",
            hypotheses,
            sorted(set(affected)),
            [check.name],
            confidence=confidence,
        )

    def _trace_test_to_production(
        self, test_path: str, test_symbol: str
    ) -> list[str]:
        path = (self.repo / test_path).resolve()
        if not path.is_file() or self.repo not in path.parents:
            return []

        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8", errors="replace")
            )
        except (OSError, SyntaxError):
            return []

        test_node = next(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == test_symbol
            ),
            None,
        )
        if test_node is None:
            return []

        imports = self._import_map(tree)
        candidates: list[str] = []

        for node in ast.walk(test_node):
            if not isinstance(node, ast.Call):
                continue
            name = self._call_name(node)
            if not name:
                continue
            module, symbol = imports.get(name, (None, name))
            if module is None:
                continue
            source = self._module_path(module)
            if source is None:
                continue
            candidates.append(source)
            definition = self._find_definition(source, symbol)
            if definition is not None:
                candidates.extend(
                    self._trace_definition_calls(source, definition)
                )

        return list(dict.fromkeys(candidates))[:10]

    def _import_map(
        self, tree: ast.Module
    ) -> dict[str, tuple[str | None, str]]:
        imports: dict[str, tuple[str | None, str]] = {}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    imports[local] = (alias.name, "")
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    imports[local] = (node.module, alias.name)
        return imports

    def _call_name(self, node: ast.Call) -> str | None:
        target = node.func
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            return f"{target.value.id}.{target.attr}"
        return None

    def _module_path(self, module: str) -> str | None:
        relative = Path(*module.split("."))
        candidates = [self.repo / f"{relative}.py", self.repo / relative / "__init__.py"]
        for candidate in candidates:
            if candidate.is_file() and self.repo in candidate.resolve().parents:
                return str(candidate.relative_to(self.repo)).replace("\\", "/")
        return None

    def _find_definition(self, path: str, symbol: str) -> ast.AST | None:
        if not symbol:
            return None
        file_path = self.repo / path
        try:
            tree = ast.parse(
                file_path.read_text(encoding="utf-8", errors="replace")
            )
        except (OSError, SyntaxError):
            return None
        return next(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == symbol
            ),
            None,
        )

    def _trace_definition_calls(
        self, path: str, definition: ast.AST
    ) -> list[str]:
        if not isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return []
        file_path = self.repo / path
        try:
            tree = ast.parse(
                file_path.read_text(encoding="utf-8", errors="replace")
            )
        except (OSError, SyntaxError):
            return []

        imports = self._import_map(tree)
        out: list[str] = []
        for node in ast.walk(definition):
            if not isinstance(node, ast.Call):
                continue
            name = self._call_name(node)
            if not name or name not in imports:
                continue
            module, symbol = imports[name]
            if module is None:
                continue
            source = self._module_path(module)
            if source is not None:
                out.append(source)
        return list(dict.fromkeys(out))[:10]

    def _find_symbol(self, symbol: str) -> list[str]:
        out: list[str] = []
        for path in self.repo.rglob("*.py"):
            if any(
                part in {".git", ".venv", "venv", ".repoforge", "__pycache__"}
                for part in path.parts
            ):
                continue
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8", errors="replace")
                )
            except (OSError, SyntaxError):
                continue
            if any(
                isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                and node.name == symbol
                for node in ast.walk(tree)
            ):
                out.append(
                    str(path.relative_to(self.repo)).replace("\\", "/")
                )
        return out[:10]
