"""Ollama-only. All agents are Qwen 2.5 3B via Ollama."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .agents import Agent
from .config import ExperimentConfig

OLLAMA_QWEN = "qwen2.5:3b"


class LLMBackend(ABC):
    model_name: str

    @abstractmethod
    def chat_batch(
        self,
        conversations: list[list[dict[str, str]]],
        *,
        json_mode: bool = False,
        max_tokens: int | None = None,
        temperature: float | None = None,
        agent_ids: list[str] | None = None,
    ) -> list[str]:
        raise NotImplementedError

    def chat_one(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        kwargs.pop("agent_id", None)
        return self.chat_batch([messages], **kwargs)[0]


def create_backend(cfg: ExperimentConfig, agents: list[Agent] | None = None) -> LLMBackend:
    cfg.backend = "ollama"
    cfg.model_name = OLLAMA_QWEN
    cfg.model_size = "3b"
    from .ollama_backend import create_ollama_pool

    print(f"[LLM] Ollama Qwen @ {cfg.ollama_host}  model={cfg.model_name}")
    return create_ollama_pool(cfg, agents)
