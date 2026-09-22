from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(slots=True)
class ModelRequest:
    system: str
    prompt: str
    context: str=''

@dataclass(slots=True)
class ModelResponse:
    text: str
    provider: str
    model: str

class ModelProvider(Protocol):
    name: str
    model: str
    def complete(self, request: ModelRequest) -> ModelResponse: ...

class DisabledProvider:
    name='disabled'
    model='none'
    def complete(self, request:ModelRequest)->ModelResponse:
        raise RuntimeError('No model provider configured; deterministic verification remains available.')
