#!/usr/bin/env python3
"""CLI entry point. On JupyterLab you will usually use the notebook instead."""

from __future__ import annotations

import argparse
from pathlib import Path

from fresno_mas.config import ExperimentConfig
from fresno_mas.experiment import FresnoBudgetExperiment
from fresno_mas.viz import allocation_table


def main() -> None:
    p = argparse.ArgumentParser(description="Fresno $70M multi-agent budget deliberation")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--topology", default=None)
    p.add_argument("--rounds", type=int, default=None)
    p.add_argument("--backend", default=None, help=argparse.SUPPRESS)
    p.add_argument("--host", default=None, help="Ollama host, default http://127.0.0.1:11466")
    p.add_argument("--pdf", "--proposals", dest="proposals", default=None,
                   help="PDF file or folder of proposal PDFs (required unless already in proposals/)")
    p.add_argument("--record", default=None, help="Path for the single output JSON record")
    args = p.parse_args()

    overrides = {
        "topology": args.topology,
        "n_rounds": args.rounds,
        "model_name": "qwen2.5:3b",
        "model_size": "3b",
        "ollama_host": args.host,
        "record_file": args.record,
    }
    cfg_path = Path(args.config)
    if cfg_path.is_file():
        exp = FresnoBudgetExperiment.from_yaml(cfg_path, **overrides)
    else:
        exp = FresnoBudgetExperiment(
            ExperimentConfig(**{k: v for k, v in overrides.items() if v is not None})
        )

    exp.load(source=args.proposals)
    print(f"Loaded {len(exp.proposals)} proposals")
    result = exp.run()
    table = allocation_table(result.final, exp.proposals)
    print("\nFINAL PACKAGE")
    print(table.to_string(index=False))
    print(f"\nTotal: ${result.final.total:,.0f}  |  projects: {len(result.final.funded_ids())}")
    print(f"Record file: {exp.record_path}")
    bias = exp.evaluate(result)
    print("\n" + bias["summary"]["bias_readout"])


if __name__ == "__main__":
    main()
