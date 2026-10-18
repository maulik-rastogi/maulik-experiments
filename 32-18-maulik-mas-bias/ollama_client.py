"""
ollama_client.py
Thin, robust wrapper around Ollama chat completions.

Tries the `ollama` Python library first (preferred); falls back to a direct
HTTP POST to /api/chat if the library is not installed. Both code paths use
the same retry-with-backoff logic and honour the same config constants.

Usage:
    client = OllamaClient(model="qwen3:4b")
    text = client.chat(system_prompt="...", user_prompt="...")

Ollama must be running before any call:
    ollama serve        # in a terminal, or managed by the system
    ollama pull qwen3:4b
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import config

logger = logging.getLogger("ollama_client")


class OllamaClient:
    """
    Wrapper around Ollama chat completions with retry / backoff.

    allow_offline_fallback: if True, exhausting all retries returns a clearly
    flagged placeholder string instead of raising — useful for dev/test without
    a live Ollama server.  Set False (default) for real runs so a dead call
    fails loudly rather than injecting fake allocations into results.
    """

    def __init__(
        self,
        model: str,
        base_url: str = None,
        max_retries: int = None,
        allow_offline_fallback: bool = False,
    ):
        self.model = model
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.max_retries = max_retries or config.MAX_RETRIES
        self.allow_offline_fallback = allow_offline_fallback
        self._use_library = self._check_library()
        self._http = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        json_mode: bool = False,
    ) -> str:
        """
        Send a system + user message pair and return the model's reply.
        Retries up to max_retries times with linear backoff.
        json_mode=True asks Ollama for a JSON object (allocation turns).
        """
        temperature = config.GENERATION_TEMPERATURE if temperature is None else temperature
        max_tokens = max_tokens or config.GENERATION_MAX_TOKENS

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                if self._use_library:
                    return self._chat_library(
                        system_prompt, user_prompt, temperature, max_tokens, json_mode
                    )
                return self._chat_http(
                    system_prompt, user_prompt, temperature, max_tokens, json_mode
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                wait = config.RETRY_BACKOFF_S * attempt
                logger.warning(
                    "Ollama call failed for model '%s' (attempt %d/%d): %s. "
                    "Retrying in %.1fs...",
                    self.model, attempt, self.max_retries, exc, wait,
                )
                time.sleep(wait)

        if self.allow_offline_fallback:
            logger.error(
                "Ollama call to model '%s' failed %d times. "
                "allow_offline_fallback=True — returning placeholder. "
                "DO NOT use these turns in reported results.",
                self.model, self.max_retries,
            )
            return self._offline_fallback()

        raise RuntimeError(
            f"Ollama call to model '{self.model}' at {self.base_url} failed "
            f"{self.max_retries} times (last error: {last_exc}). "
            f"Is Ollama running?  Try:  ollama serve  &&  ollama pull {self.model}"
        )

    def warm(self) -> None:
        """Load this tag into VRAM and pin it for OLLAMA_KEEP_ALIVE."""
        try:
            if self._use_library:
                import ollama
                kwargs = dict(
                    model=self.model,
                    messages=[{"role": "user", "content": "ready"}],
                    think=False,
                    keep_alive=config.OLLAMA_KEEP_ALIVE,
                    options=self._gen_options(0, 1),
                )
                try:
                    ollama.chat(**kwargs)
                except TypeError:
                    kwargs.pop("think", None)
                    kwargs.pop("keep_alive", None)
                    ollama.chat(**kwargs)
            else:
                self._http_session().post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ready"}],
                        "stream": False,
                        "think": False,
                        "keep_alive": config.OLLAMA_KEEP_ALIVE,
                        "options": self._gen_options(0, 1),
                    },
                    timeout=config.REQUEST_TIMEOUT_S,
                ).raise_for_status()
            logger.info("Warmed and pinned model '%s' (%s)", self.model, config.OLLAMA_KEEP_ALIVE)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Warmup skipped for '%s': %s", self.model, exc)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _http_session(self):
        if self._http is None:
            import requests
            self._http = requests.Session()
        return self._http

    @staticmethod
    def _gen_options(temperature: float, max_tokens: int) -> dict:
        return {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": config.OLLAMA_NUM_CTX,
            "num_batch": config.OLLAMA_NUM_BATCH,
        }

    def _check_library(self) -> bool:
        """Return True if the `ollama` Python package is importable."""
        try:
            import ollama  # noqa: F401
            logger.debug("ollama Python library found; using it for calls.")
            return True
        except ImportError:
            logger.info(
                "ollama Python library not installed; falling back to requests HTTP. "
                "Install with:  pip install ollama"
            )
            return False

    def _chat_library(
        self, system: str, user: str, temperature: float, max_tokens: int,
        json_mode: bool = False,
    ) -> str:
        import ollama
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            think=False,
            keep_alive=config.OLLAMA_KEEP_ALIVE,
            options=self._gen_options(temperature, max_tokens),
        )
        if json_mode:
            kwargs["format"] = "json"
        try:
            client = ollama.Client(host=self.base_url, timeout=config.REQUEST_TIMEOUT_S)
        except TypeError:
            client = ollama.Client(host=self.base_url)
        try:
            response = client.chat(**kwargs)
        except TypeError:
            kwargs.pop("think", None)
            kwargs.pop("keep_alive", None)
            response = client.chat(**kwargs)
        return response["message"]["content"]

    def _chat_http(
        self, system: str, user: str, temperature: float, max_tokens: int,
        json_mode: bool = False,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "think": False,
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "options": self._gen_options(temperature, max_tokens),
        }
        if json_mode:
            payload["format"] = "json"
        resp = self._http_session().post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=config.REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    @staticmethod
    def _offline_fallback() -> str:
        return (
            "[OLLAMA_UNAVAILABLE_FALLBACK] No live model response — Ollama server "
            "was unreachable. Allocation unchanged from prior turn. "
            '{"reasoning": "offline fallback, no live model output", '
            '"funded_projects": []}'
        )
