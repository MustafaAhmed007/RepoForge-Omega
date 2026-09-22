from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .fingerprint import detect
from .models import VerificationReport


@dataclass(slots=True)
class DeploymentPlan:
    target: str
    commands: list[list[str]]
    prerequisites: list[str]
    executable: bool


def plan(repo: Path, verification: VerificationReport | None = None) -> DeploymentPlan:
    fp = detect(repo)
    if verification is not None and verification.release_status.value != "VERIFIED":
        return DeploymentPlan("blocked", [], ["verification must be VERIFIED"], False)
    if (repo / "Dockerfile").exists():
        return DeploymentPlan("docker", [["docker", "build", "."]], ["Docker installed"], True)
    if "vercel.json" in fp.deployment_targets or (repo / "next.config.js").exists():
        return DeploymentPlan("vercel", [["npx", "vercel", "build"]], ["Vercel CLI installed", "deployment credentials configured"], True)
    if (repo / "netlify.toml").exists():
        return DeploymentPlan("netlify", [["netlify", "build"]], ["Netlify CLI installed", "deployment credentials configured"], True)
    if "Python" in fp.languages:
        return DeploymentPlan("python", [], ["choose a runtime/host and configure credentials"], False)
    return DeploymentPlan("unknown", [], ["no supported deployment adapter detected"], False)
