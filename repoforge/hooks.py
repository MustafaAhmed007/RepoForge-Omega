from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


HOOKS = (
    "session_start",
    "before_task",
    "after_task",
    "before_change",
    "after_change",
    "before_verify",
    "after_verify",
    "session_end",
)


@dataclass(slots=True)
class HookEvent:
    name: str
    payload: dict[str, object]


HookHandler = Callable[[HookEvent], None]


class HookBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[HookHandler]] = defaultdict(list)

    def register(self, name: str, handler: HookHandler) -> None:
        if name not in HOOKS:
            raise ValueError(f"Unsupported hook: {name}")
        self._handlers[name].append(handler)

    def emit(self, name: str, **payload: object) -> None:
        if name not in HOOKS:
            raise ValueError(f"Unsupported hook: {name}")
        event = HookEvent(name, payload)
        for handler in self._handlers[name]:
            handler(event)
