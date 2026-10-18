from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

BUDGET_USD = 70_000_000

NEIGHBORHOODS = {
    "southwest": {
        "id": "southwest",
        "name": "Southwest Fresno",
        "short": "SW",
        "need_weight": 0.50,
        "calenviroscreen_percentile": 92,
        "tree_canopy_pct": 6.5,
        "median_income": 34200,
        "heat_index": 0.91,
        "notes": "Historically redlined; high PM2.5 and heat; lowest canopy.",
    },
    "central": {
        "id": "central",
        "name": "Central Fresno",
        "short": "C",
        "need_weight": 0.30,
        "calenviroscreen_percentile": 74,
        "tree_canopy_pct": 11.0,
        "median_income": 41800,
        "heat_index": 0.78,
        "notes": "Downtown, Chinatown, Tower District; mixed income; infill heat.",
    },
    "northeast": {
        "id": "northeast",
        "name": "Northeast Fresno",
        "short": "NE",
        "need_weight": 0.20,
        "calenviroscreen_percentile": 38,
        "tree_canopy_pct": 22.4,
        "median_income": 78600,
        "heat_index": 0.49,
        "notes": "Woodward Park / Copper River; more existing green infrastructure.",
    },
}

TopologyName = Literal[
    "fully_connected",
    "star",
    "ring",
    "hierarchical",
    "neighborhood_clusters",
]
BackendName = Literal["ollama"]
SpeakerOrder = Literal["rotate", "fixed", "random"]


@dataclass
class ExperimentConfig:
    budget_usd: int = BUDGET_USD
    n_rounds: int = 4
    topology: TopologyName = "fully_connected"
    speaker_order: SpeakerOrder = "rotate"

    model_name: str = "qwen2.5:3b"
    model_size: str = "3b"
    backend: BackendName = "ollama"
    ollama_host: str = "http://127.0.0.1:11466"
    clone_per_agent: bool = True
    ollama_keep_alive: str = "30m"
    ollama_parallel: bool = True
    trial_3b_models: list[str] = field(default_factory=lambda: ["qwen2.5:3b"])
    trial_7b_models: list[str] = field(default_factory=list)
    max_model_len: int = 16384
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2200
    seed: int = 42

    proposals_dir: str = "proposals"
    proposals_json: str = ""
    output_dir: str = "outputs"
    record_file: str = ""
    use_sample_if_empty: bool = False
    target_n_projects: int | None = 25

    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def root(self) -> Path:
        return Path(self.extra.get("root", ".")).resolve()

    @classmethod
    def from_yaml(cls, path: str | Path, **overrides: Any) -> "ExperimentConfig":
        raw = yaml.safe_load(Path(path).read_text()) or {}
        raw.update({k: v for k, v in overrides.items() if v is not None})
        raw["backend"] = "ollama"
        raw["model_name"] = raw.get("model_name") or "qwen2.5:3b"
        if raw.get("model_name") != "qwen2.5:3b":
            raw["model_name"] = "qwen2.5:3b"
        raw["model_size"] = "3b"
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in raw.items() if k not in known}
        cfg = cls(**{k: v for k, v in raw.items() if k in known})
        cfg.extra.update(extra)
        return cfg

    def resolve(self, root: Path | None = None) -> "ExperimentConfig":
        root = (root or Path.cwd()).resolve()
        self.extra["root"] = str(root)
        return self
