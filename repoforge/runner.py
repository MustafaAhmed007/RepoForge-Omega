from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .models import CheckResult, GateStatus
from .security import assess_command


def run_check(
    name: str,
    command: list[str],
    cwd: Path,
    timeout_s: int = 120,
    allow_side_effects: bool = False,
    required: bool = True,
) -> CheckResult:
    ok, reason = assess_command(command, allow_side_effects)
    if not ok:
        return CheckResult(
            name,
            GateStatus.BLOCKED,
            None,
            0,
            command=command,
            reason=reason,
            required=required,
        )
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            shell=False,
        )
        return CheckResult(
            name,
            GateStatus.PASS if proc.returncode == 0 else GateStatus.FAIL,
            proc.returncode,
            int((time.perf_counter() - started) * 1000),
            proc.stdout[-12000:],
            proc.stderr[-12000:],
            command,
            required=required,
        )
    except FileNotFoundError as e:
        return CheckResult(
            name,
            GateStatus.BLOCKED,
            None,
            int((time.perf_counter() - started) * 1000),
            command=command,
            reason=f"executable not found: {e.filename}",
            required=required,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name,
            GateStatus.FAIL,
            None,
            int((time.perf_counter() - started) * 1000),
            command=command,
            reason=f"timeout after {timeout_s}s",
            required=required,
        )
