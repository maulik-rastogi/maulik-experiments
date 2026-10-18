from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .agents import default_agents
from .bias import evaluate
from .config import ExperimentConfig
from .discussion import DiscussionEngine, ExperimentResult
from .llm import create_backend
from .pdf_ingest import collect_pdf_files, load_proposals, render_page_pngs
from .proposals import Proposal
from .record import build_record


class FresnoBudgetExperiment:
    """
    End-to-end runner for the Fresno $70M multi-agent allocation environment.

    Typical Jupyter use:
        exp = FresnoBudgetExperiment.from_yaml("config.yaml")
        exp.load()          # requires PDFs in proposals/
        result = exp.run()  # five qwen2.5:3b clones; writes one record JSON
    """

    def __init__(self, cfg: ExperimentConfig, root: Path | None = None):
        self.cfg = cfg.resolve(root)
        self.root = Path(self.cfg.extra["root"])
        self.backend = None
        self.proposals: list[Proposal] = []
        self.pages: list[dict] = []
        self.agents = default_agents()
        self.page_images: list[Path] = []
        self.record_path: Path | None = None

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml", **overrides) -> "FresnoBudgetExperiment":
        root = Path(path).resolve().parent if Path(path).is_file() else Path.cwd()
        cfg = ExperimentConfig.from_yaml(path, **overrides) if Path(path).is_file() else ExperimentConfig(**overrides)
        return cls(cfg, root=root)

    def start_llm(self):
        if self.backend is None:
            self.backend = create_backend(self.cfg, agents=self.agents)
        return self.backend

    def load(self, source: str | Path | None = None, structure_with_llm: bool = False):
        src = Path(source) if source else self.root / self.cfg.proposals_dir
        json_path = None
        if self.cfg.proposals_json:
            cand = self.root / self.cfg.proposals_json
            json_path = cand if cand.is_file() else None
        if structure_with_llm:
            self.start_llm()
        self.proposals, self.pages = load_proposals(
            source=src if src.exists() else None,
            json_path=json_path,
            use_sample_if_empty=self.cfg.use_sample_if_empty,
            llm_backend=self.backend,
            structure_with_llm=structure_with_llm,
        )
        if self.pages:
            img_dir = self.root / self.cfg.output_dir / "proposal_pages"
            self.page_images = render_page_pngs(self.pages, img_dir)
        pdfs = collect_pdf_files(src) if src.exists() else []
        print(f"Loaded {len(self.proposals)} proposals from {len(pdfs) or len(self.pages)} PDF source(s).")
        return self.proposals

    def run(self) -> ExperimentResult:
        self.start_llm()
        kind = type(self.backend).__name__
        print(f"LLM in use: {kind}  ollama={self.cfg.ollama_host}  model={self.cfg.model_name}")
        if kind != "OllamaAgentPool":
            raise RuntimeError(
                f"Refusing to run: got {kind}, not OllamaAgentPool. "
                "Start `ollama serve` on the host in config.yaml."
            )
        if not self.proposals:
            self.load()
        if not self.proposals:
            raise RuntimeError("No proposals loaded. Drop your PDF into proposals/ first.")
        print("Catalog (from PDF) first titles:")
        for p in self.proposals[:5]:
            print(f"  {p.id}: {p.title[:80]}")
        return self._execute()

    def _record_path(self) -> Path:
        out_dir = self.root / self.cfg.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.cfg.record_file:
            p = Path(self.cfg.record_file)
            return p if p.is_absolute() else self.root / p
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return out_dir / f"fresno_deliberation_{stamp}.json"

    def _execute(self) -> ExperimentResult:
        engine = DiscussionEngine(self.cfg, self.backend, self.proposals, self.agents)
        result = engine.run()
        self.record_path = self.save_record(result)
        print(f"Saved one record file → {self.record_path}")
        return result

    def save_record(self, result: ExperimentResult, path: str | Path | None = None) -> Path:
        dest = Path(path) if path else self._record_path()
        dest.parent.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(
            {
                str(p.source_pdf)
                for p in self.proposals
                if p.source_pdf
            }
            | {str(pg.get("source_pdf") or "") for pg in self.pages if pg.get("source_pdf")}
        )
        pdfs = [p for p in pdfs if p]
        record = build_record(
            result,
            proposals=self.proposals,
            agents=self.agents,
            source_pdfs=pdfs,
            page_texts=self.pages,
            record_path=str(dest),
        )
        dest.write_text(json.dumps(record, indent=2, ensure_ascii=False))
        return dest

    def evaluate(self, result: ExperimentResult) -> dict:
        return evaluate(result, self.proposals)
