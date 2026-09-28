from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class ModelRequest:
    system: str
    prompt: str
    context: str = ""


@dataclass(slots=True)
class ModelResponse:
    text: str
    provider: str
    model: str


class ModelProvider(Protocol):
    name: str
    model: str
    kind: str
    def complete(self, request: ModelRequest) -> ModelResponse: ...


class DisabledProvider:
    name = "disabled"
    model = "none"
    kind = "none"
    def complete(self, request: ModelRequest) -> ModelResponse:
        raise RuntimeError("No model provider configured.")


class OpenAICompatibleProvider:
    kind = "remote"

    def __init__(self, endpoint: str, api_key: str, model: str, name: str, timeout: int = 90):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = name
        self.timeout = timeout

    def complete(self, request: ModelRequest) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt + "\n" + request.context},
            ],
        }
        req = urllib.request.Request(
            f"{self.endpoint}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return ModelResponse(
            str(data["choices"][0]["message"]["content"]),
            self.name,
            self.model,
        )


def provider_for_role(role: str) -> ModelProvider:
    prefix = "REPOFORGE_REVIEW_" if role == "review" else "REPOFORGE_REPAIR_"
    enabled = os.getenv(prefix + "PROVIDER", os.getenv("REPOFORGE_PROVIDER", "none")).lower()
    key = os.getenv(prefix + "API_KEY", os.getenv("REPOFORGE_API_KEY", ""))
    if enabled not in {"openai", "compatible"} or not key:
        return DisabledProvider()
    return OpenAICompatibleProvider(
        os.getenv(prefix + "ENDPOINT", os.getenv("REPOFORGE_ENDPOINT", "https://api.openai.com/v1")),
        key,
        os.getenv(prefix + "MODEL", os.getenv("REPOFORGE_MODEL", "gpt-5")),
        "openai-compatible-" + role,
    )


def provider_from_environment() -> ModelProvider:
    return provider_for_role("repair")
