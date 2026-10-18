"""Five independent Ollama models (one per agent), same architecture, separate names."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .agents import Agent, default_agents
from .config import ExperimentConfig
from .llm import LLMBackend


def _slug(model: str) -> str:
    return model.replace(":", "-").replace("/", "-").replace(" ", "").lower()


def clone_name(base_model: str, agent_id: str) -> str:
    """Distinct Ollama model name for one agent. Same weights, own identity."""
    return f"fresno-{_slug(base_model)}-{agent_id}"


class OllamaHTTP:
    def __init__(self, host: str, timeout: int = 600):
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, payload: dict | None = None, stream: bool = False) -> Any:
        url = f"{self.host}{path}"
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.host} ({exc}). "
                "Start it with `ollama serve` (or in JupyterLab: Terminal → ollama serve)."
            ) from exc
        if stream:
            return resp
        with resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}

    def tags(self) -> set[str]:
        data = self._request("/api/tags")
        names = set()
        for m in data.get("models") or []:
            name = m.get("name") or ""
            names.add(name)
            if ":" in name:
                names.add(name.split(":")[0])
                names.add(name.rsplit(":", 1)[0])
        return names

    def has_model(self, name: str) -> bool:
        installed = self.tags()
        return name in installed or f"{name}:latest" in installed

    def pull(self, name: str) -> None:
        if self.has_model(name):
            print(f"[ollama] already present: {name}")
            return
        print(f"[ollama] pulling {name} …")
        url = f"{self.host}/api/pull"
        payload = json.dumps({"name": name, "stream": True}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=None) as resp:
            last = ""
            for line in resp:
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line.decode())
                except json.JSONDecodeError:
                    continue
                status = ev.get("status") or ev.get("error") or ""
                if status and status != last:
                    print(f"  {status}")
                    last = status
                if ev.get("error"):
                    raise RuntimeError(f"ollama pull failed for {name}: {ev['error']}")
        print(f"[ollama] pulled {name}")

    def copy(self, source: str, destination: str) -> None:
        if self.has_model(destination):
            print(f"[ollama] clone exists: {destination}")
            return
        print(f"[ollama] copy {source} → {destination}")
        self._request("/api/copy", {"source": source, "destination": destination})

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        options: dict[str, Any],
        keep_alive: str = "30m",
    ) -> str:
        data = self._request(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "keep_alive": keep_alive,
                "options": options,
            },
        )
        msg = data.get("message") or {}
        content = (msg.get("content") or "").strip()
        if not content:
            err = data.get("error") or data
            raise RuntimeError(
                f"Ollama returned empty text for model {model}. "
                f"Is `ollama serve` running and is {model} pulled? Raw: {err!r}"
            )
        return content


class OllamaAgentClient:
    """One Ollama model instance dedicated to a single agent."""

    def __init__(self, http: OllamaHTTP, model: str, agent_id: str, cfg: ExperimentConfig):
        self.http = http
        self.model = model
        self.agent_id = agent_id
        self.cfg = cfg

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        seed = (self.cfg.seed + (zlib.adler32(self.agent_id.encode()) % 10_000)) % (2**31)
        options = {
            "temperature": self.cfg.temperature if temperature is None else temperature,
            "top_p": self.cfg.top_p,
            "num_predict": max_tokens or self.cfg.max_tokens,
            "num_ctx": min(self.cfg.max_model_len, 32768),
            "seed": seed,
        }
        print(f"  [{self.agent_id}] → {self.model}")
        return self.http.chat(
            self.model,
            messages,
            options=options,
            keep_alive=self.cfg.ollama_keep_alive,
        )


class OllamaAgentPool(LLMBackend):
    """Five separate Ollama models (plus a clerk clone), typically the same family."""

    def __init__(self, cfg: ExperimentConfig, agents: list[Agent]):
        self.cfg = cfg
        self.model_name = cfg.model_name
        self.http = OllamaHTTP(cfg.ollama_host)
        self.clients: dict[str, OllamaAgentClient] = {}
        self.agent_models: dict[str, str] = {}
        self.proposals = None
        self._provision(agents)

    def _provision(self, agents: list[Agent]) -> None:
        base = self.cfg.model_name
        print(f"[ollama] provisioning {len(agents)} agent models from {base}")
        self.http.pull(base)
        ids = [a.id for a in agents] + ["clerk"]
        for aid in ids:
            tag = clone_name(base, aid) if self.cfg.clone_per_agent else base
            if self.cfg.clone_per_agent:
                self.http.copy(base, tag)
            self.agent_models[aid] = tag
            self.clients[aid] = OllamaAgentClient(self.http, tag, aid, self.cfg)
        for agent in agents:
            agent.model_name = self.agent_models[agent.id]
        print("[ollama] agent models:")
        for aid, tag in self.agent_models.items():
            print(f"    {aid:16s}  {tag}")

    def chat_batch(
        self,
        conversations: list[list[dict[str, str]]],
        *,
        json_mode: bool = False,
        max_tokens: int | None = None,
        temperature: float | None = None,
        agent_ids: list[str] | None = None,
    ) -> list[str]:
        # Never force Ollama JSON mode: agents must emit a spoken statement plus JSON.
        del json_mode
        if not agent_ids:
            agent_ids = list(self.clients)[: len(conversations)]
        if len(agent_ids) != len(conversations):
            raise ValueError("agent_ids must match conversations")

        def _one(aid: str, msgs: list[dict[str, str]]) -> tuple[str, str]:
            client = self.clients.get(aid) or self.clients["clerk"]
            return aid, client.chat(msgs, max_tokens=max_tokens, temperature=temperature)

        if self.cfg.ollama_parallel and len(conversations) > 1:
            out: dict[str, str] = {}
            with ThreadPoolExecutor(max_workers=len(conversations)) as pool:
                futs = [pool.submit(_one, aid, msgs) for aid, msgs in zip(agent_ids, conversations)]
                for fut in as_completed(futs):
                    aid, text = fut.result()
                    out[aid] = text
            return [out[aid] for aid in agent_ids]

        return [_one(aid, msgs)[1] for aid, msgs in zip(agent_ids, conversations)]

    def chat_one(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        aid = kwargs.pop("agent_id", "clerk")
        client = self.clients.get(aid) or self.clients["clerk"]
        return client.chat(
            messages,
            max_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature"),
        )


def create_ollama_pool(cfg: ExperimentConfig, agents: list[Agent] | None = None) -> OllamaAgentPool:
    return OllamaAgentPool(cfg, agents or default_agents())
