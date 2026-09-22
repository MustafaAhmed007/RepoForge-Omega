from __future__ import annotations
import shlex

_BLOCKED = (" rm -rf /", " rm -rf ~", " format c:", " shutdown ", " reboot ")
_NETWORK_SIDE_EFFECTS = ("git push", "git reset --hard", "curl ", "wget ", "invoke-webrequest")

def normalize_command(command: list[str]) -> str:
    return " ".join(shlex.quote(x) for x in command).lower()

def assess_command(command: list[str], allow_side_effects: bool = False) -> tuple[bool, str | None]:
    text = " " + normalize_command(command) + " "
    for fragment in _BLOCKED:
        if fragment in text:
            return False, f"blocked destructive command pattern: {fragment.strip()}"
    if not allow_side_effects:
        for fragment in _NETWORK_SIDE_EFFECTS:
            if fragment in text:
                return False, f"side-effect/network command requires explicit approval: {fragment.strip()}"
    return True, None
