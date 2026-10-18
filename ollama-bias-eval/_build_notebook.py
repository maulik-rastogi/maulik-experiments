"""Rebuild the Jupyter notebook with valid JSON."""

from __future__ import annotations

import json
from pathlib import Path

CELLS: list[tuple[str, str]] = []


def md(src: str) -> None:
    CELLS.append(("markdown", src.strip() + "\n"))


def code(src: str) -> None:
    CELLS.append(("code", src.strip() + "\n"))


md(
    """# Fresno $70M multi-agent budget allocation

City of Fresno environmental-infrastructure deliberation. **$70 million** across Southwest, Central, and Northeast Fresno.

**Model:** five separate Ollama clones of **`qwen2.5:3b`** (one per agent), plus a clerk clone for the final package.

| Agent | Role | Ollama model |
| --- | --- | --- |
| Alex Navarro | Financial Officer | `fresno-qwen2.5-3b-finance` |
| Dr. Priya Menon | Sustainability Expert | `fresno-qwen2.5-3b-sustainability` |
| Rosa Delgado | Citizen, Southwest Fresno | `fresno-qwen2.5-3b-citizen_sw` |
| Marcus Lee | Citizen, Central Fresno | `fresno-qwen2.5-3b-citizen_c` |
| Helen Park | Citizen, Northeast Fresno | `fresno-qwen2.5-3b-citizen_ne` |

**Proposal data:** you supply the PDF(s). Extracted page text is the **only** project catalog the agents see (no built-in sample proposals).

Drop a combined PDF or 38 one-page PDFs into `proposals/`, or use the upload widget below.

After the run, **one JSON file** stores proposals, every agent output, the full transcript, and the final allocation."""
)

md(
    """## 0. Start Ollama (JupyterLab Terminal)

```bash
export OLLAMA_HOST=127.0.0.1:11466
export OLLAMA_MAX_LOADED_MODELS=6
export OLLAMA_NUM_PARALLEL=5
ollama serve
```

If Ollama is not installed: `curl -fsSL https://ollama.com/install.sh | sh`"""
)

md("## 1. Install Python deps")

code(
    """%pip install -q pandas numpy matplotlib seaborn networkx pydantic pyyaml tqdm json-repair pymupdf reportlab ipywidgets tabulate
print("Python deps ready. Ollama itself is a separate server (section 0).")"""
)

code(
    """from pathlib import Path
import os, sys, json, textwrap

ROOT = Path.cwd()
if not (ROOT / "fresno_mas").exists() and (ROOT.parent / "fresno_mas").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

print("ROOT", ROOT)

import pandas as pd
from IPython.display import display, Image, Markdown

from fresno_mas.config import ExperimentConfig
from fresno_mas.experiment import FresnoBudgetExperiment
from fresno_mas.pdf_ingest import save_notebook_uploads
from fresno_mas.viz import (
    allocation_table,
    plot_topology,
    plot_neighborhood_trajectory,
    plot_consensus,
    plot_elite_capture,
    plot_final_bars,
)
import matplotlib.pyplot as plt"""
)

md(
    """## 2. Experiment config

Single model family: **Qwen 2.5 3B**. Five independent clones, one per agent."""
)

code(
    """cfg = ExperimentConfig.from_yaml(ROOT / "config.yaml")

cfg.backend = "ollama"
cfg.ollama_host = "http://127.0.0.1:11466"
cfg.clone_per_agent = True
cfg.ollama_parallel = True
cfg.model_name = "qwen2.5:3b"
cfg.model_size = "3b"
cfg.n_rounds = 4
cfg.topology = "fully_connected"
cfg.speaker_order = "rotate"
cfg.max_model_len = 16384
cfg.temperature = 0.7
cfg.max_tokens = 2200
cfg.seed = 42
cfg.target_n_projects = 25
cfg.budget_usd = 70_000_000
cfg.use_sample_if_empty = False   # PDF only

exp = FresnoBudgetExperiment(cfg, root=ROOT)
print(cfg.model_name, cfg.backend)"""
)

md(
    """## 3. Add your proposal PDF(s)

This is the only project data the agents will read.

1. Copy a combined PDF **or** one PDF per proposal into `proposals/`, **or**
2. Use the upload widget, then run the next cell.

The run will not start until at least one `.pdf` is present."""
)

code(
    """import ipywidgets as widgets

uploader = widgets.FileUpload(
    accept=".pdf",
    multiple=True,
    description="Upload PDFs",
)
status = widgets.HTML("<i>Select your proposal PDF(s), then run the next cell.</i>")
display(uploader, status)"""
)

code(
    """prop_dir = ROOT / "proposals"
prop_dir.mkdir(exist_ok=True)

try:
    saved = save_notebook_uploads(uploader, prop_dir)
    if saved:
        print("Saved uploads:", [p.name for p in saved])
except Exception as e:
    print("Upload widget unused or failed:", e)

existing = list(prop_dir.glob("**/*.pdf"))
print(f"PDFs in {prop_dir}: {len(existing)}")
for p in existing:
    print(" -", p.name)
if not existing:
    raise FileNotFoundError(
        "No PDFs found. Put your proposal PDF(s) in proposals/ or use the upload widget, then re-run this cell."
    )"""
)

code(
    """proposals = exp.load(source=prop_dir, structure_with_llm=False)
print(f"Loaded {len(proposals)} proposals from your PDF(s); "
      f"combined listed cost ${sum(p.cost_usd for p in proposals):,.0f}")

df_cat = pd.DataFrame(
    [
        {
            "id": p.id,
            "title": p.title,
            "neighborhood": p.neighborhood,
            "category": p.category,
            "cost_usd": p.cost_usd,
            "source": Path(p.source_pdf).name if p.source_pdf else "",
            "page": p.source_page,
        }
        for p in proposals
    ]
)
display(df_cat)"""
)

md("Rendered pages (for you). Agents see the **extracted text**, not these images:")

code(
    """if exp.page_images:
    display(Markdown(f"Showing first 4 of {len(exp.page_images)} rendered pages."))
    for img in exp.page_images[:4]:
        display(Markdown(f"**{img.name}**"))
        display(Image(filename=str(img), width=720))
else:
    display(Markdown("_No PDF pages were ingested._"))"""
)

md(
    """## 4. Agents and topology

Role briefs only. Project facts come from your PDF."""
)

code(
    """for a in exp.agents:
    display(Markdown(
        f"**{a.name}** — _{a.title}_  \\n"
        + textwrap.shorten(a.instructions.replace(chr(10), " "), width=360)
    ))

fig, ax = plt.subplots(figsize=(7, 5))
plot_topology(exp.agents, cfg.topology, ax=ax)
plt.show()"""
)

md(
    """## 5. Run (Qwen 3B, five agents)

Writes **one** JSON record: PDF-extracted proposals, every agent output, the transcript, and the final allocation."""
)

code(
    """result = exp.run()
print("Record file:", exp.record_path)
print("LLM class:", result.config.get("llm_class"), "backend:", result.config.get("backend"))
if result.config.get("llm_class") != "OllamaAgentPool":
    raise RuntimeError("This was not an Ollama Qwen run. Start `ollama serve` and set cfg.backend='ollama'.")
print("Final total $", f"{result.final.total:,.0f}",
      "projects", len(result.final.funded_ids()),
      "under budget", result.final.total <= cfg.budget_usd)
print("Agent models:", {a.id: a.model_name for a in exp.agents})
print("Catalog IDs:", [p.id for p in exp.proposals][:20], "...")"""
)

md("## 6. Final package")

code(
    """final_tbl = allocation_table(result.final, exp.proposals)
display(Markdown(
    f"### Final allocation — **${result.final.total:,.0f}** "
    f"across **{len(final_tbl)}** projects (budget ${cfg.budget_usd:,.0f})"
))
display(final_tbl)

display(Markdown("### Last-round statements"))
last = result.rounds[-1]
for msg in last.messages:
    display(Markdown(f"**{msg['agent_name']}** ({msg['agent_id']})"))
    print((msg.get("statement") or msg.get("discussion") or "")[:1200])
    print("—")

display(Markdown(f"Full record (proposals + transcript + allocations) is in `{exp.record_path}`"))"""
)

md(
    """## 7. Emergent bias

Need-weighted fair share of the $70M: **Southwest 50% / Central 30% / Northeast 20%**. These metrics are computed from the run; they are not extra proposal data."""
)

code(
    """bias = exp.evaluate(result)
out_dir = ROOT / "outputs"
out_dir.mkdir(exist_ok=True)

print(bias["summary"]["bias_readout"])
print("final neighborhood $", {k: round(v) for k, v in bias["summary"]["final_neighborhood_usd"].items()})

display(Markdown("**Per-agent neighborhood dollars by round**"))
display(bias["per_agent_rounds"])
display(Markdown("**Preference drift vs each agent’s own opening**"))
display(bias["preference_drift"])
display(Markdown("**Consensus tightness**"))
display(bias["consensus"])
display(Markdown("**Citizen alignment with the Financial Officer**"))
display(bias["elite_capture"])

plot_neighborhood_trajectory(bias, out_dir / "neighborhood_trajectory.png")
plot_consensus(bias, out_dir / "consensus.png")
plot_elite_capture(bias, out_dir / "elite_capture.png")
plot_final_bars(result, exp.proposals, out_dir / "final_vs_fair.png")
plt.show()
print("Primary archive is the one JSON record:", exp.record_path)"""
)

md(
    """## Notes

- Put your PDF(s) in `proposals/` (one file with all pages, or one page per file). That extract is the only catalog.
- Five agents = five `qwen2.5:3b` Ollama names.
- One output file per run: `outputs/fresno_deliberation_<timestamp>.json` (proposals, transcript, agent outputs, final allocation).
- Set `cfg.record_file = "outputs/my_run.json"` if you want a fixed path."""
)


def main() -> None:
    nb_cells = []
    for kind, src in CELLS:
        cell = {"cell_type": kind, "metadata": {}, "source": src.splitlines(keepends=True)}
        if kind == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        nb_cells.append(cell)
    nb = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "accelerator": "GPU",
        },
        "cells": nb_cells,
    }
    dest = Path("Fresno_MAS_Budget_Allocation.ipynb")
    dest.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    json.loads(dest.read_text())
    print(f"wrote {dest} ({len(nb_cells)} cells)")


if __name__ == "__main__":
    main()
