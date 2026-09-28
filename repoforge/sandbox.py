from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .security import assess_command


@dataclass(frozen=True, slots=True)
class SandboxResult:
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    workspace: str


class ExecutionSandbox:
    """Bounded workspace execution. It is not a kernel VM; destructive/network commands remain blocked."""

    def __init__(self, repo: Path, timeout_s: int = 120):
        self.repo = repo.resolve()
        self.timeout_s = timeout_s

    def run(self, command: list[str], env: dict[str, str] | None = None) -> SandboxResult:
        ok, reason = assess_command(command)
        if not ok:
            return SandboxResult("BLOCKED", None, "", reason or "", 0, str(self.repo))

        import time
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="repoforge-sandbox-") as temp:
            workspace = Path(temp)
            shutil.copytree(
                self.repo,
                workspace,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(
                    ".git", ".venv", "venv", "node_modules", ".repoforge",
                    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
                ),
            )
            child_env = os.environ.copy()
            if env:
                child_env.update(env)
            try:
                proc = subprocess.run(
                    command,
                    cwd=workspace,
                    env=child_env,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_s,
                    shell=False,
                )
                status = "PASS" if proc.returncode == 0 else "FAIL"
                return SandboxResult(
                    status,
                    proc.returncode,
                    proc.stdout[-12000:],
                    proc.stderr[-12000:],
                    int((time.perf_counter() - started) * 1000),
                    str(workspace),
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    "TIMEOUT", None, "", f"timeout after {self.timeout_s}s",
                    int((time.perf_counter() - started) * 1000), str(workspace),
                )


@dataclass(frozen=True, slots=True)
class ContainerSandboxPolicy:
    image: str
    network: bool = False
    memory: str = "2g"
    cpus: str = "2"

class DockerSandbox:
    """Stronger optional isolation when Docker is available."""

    def __init__(self, repo: Path, policy: ContainerSandboxPolicy, timeout_s: int = 120):
        self.repo = repo.resolve()
        self.policy = policy
        self.timeout_s = timeout_s

    def run(self, command: list[str]) -> SandboxResult:
        import time
        from .security import assess_command
        ok, reason = assess_command(command)
        if not ok:
            return SandboxResult("BLOCKED", None, "", reason or "", 0, str(self.repo))
        docker = ["docker", "run", "--rm", "-i", "--memory", self.policy.memory, "--cpus", self.policy.cpus]
        docker += ["--network", "none" if not self.policy.network else "bridge"]
        docker += ["-v", f"{self.repo}:/workspace", "-w", "/workspace", self.policy.image]
        docker += command
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                docker,
                text=True,
                capture_output=True,
                timeout=self.timeout_s,
                shell=False,
            )
            return SandboxResult(
                "PASS" if proc.returncode == 0 else "FAIL",
                proc.returncode,
                proc.stdout[-12000:],
                proc.stderr[-12000:],
                int((time.perf_counter() - started) * 1000),
                str(self.repo),
            )
        except FileNotFoundError:
            return SandboxResult("BLOCKED", None, "", "Docker executable not found.", 0, str(self.repo))
        except subprocess.TimeoutExpired:
            return SandboxResult("TIMEOUT", None, "", f"timeout after {self.timeout_s}s", int((time.perf_counter() - started) * 1000), str(self.repo))
