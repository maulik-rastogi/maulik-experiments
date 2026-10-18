# Fresno $70M Multi-Agent Budget Allocation

Five Ollama clones of **`qwen2.5:3b`** (financial officer, sustainability expert, three neighborhood citizens) deliberate on a **$70M** Fresno environmental-infrastructure budget.

**You provide the proposal PDF(s).** Extracted text is the only project catalog the agents see.

Each run writes **one JSON file** with proposals, every agent output, the transcript, and the final allocation.

Each agent must produce a spoken **statement** (several sentences) plus JSON. The record's `llm.llm_class` must be `OllamaAgentPool` and `llm.is_real_model` true. Start `ollama serve` before running.

## Add your PDFs

Put files in `proposals/`:

- one combined PDF (one page per proposal is ideal), or
- many one-page PDFs

The notebook also has an upload widget. The run **will not** fall back to a built-in catalog.

## Run on JupyterLab

Terminal 1:

```bash
export OLLAMA_HOST=127.0.0.1:11466
export OLLAMA_MAX_LOADED_MODELS=6
export OLLAMA_NUM_PARALLEL=5
ollama serve
```

Then `pip install -r requirements.txt`, open `Fresno_MAS_Budget_Allocation.ipynb`, and run all cells.

Or:

```bash
python run_experiment.py --pdf proposals/your_file.pdf
```

Optional fixed record path:

```bash
python run_experiment.py --pdf proposals/ --record outputs/my_run.json
```

## Output

One file per run, e.g. `outputs/fresno_deliberation_20260819_170501.json`:

- `source` — which PDFs were used
- `proposals` / `pdf_page_texts` — extracted catalog
- `agents` — roles and model names
- `transcript` / `rounds` — every agent’s spoken statement, reasoning, and allocation each round
- `final_allocation` — the clerk’s spoken statement plus one $70M package
- `majority_merge_allocation` — vote/average of the last round (comparison)

## Five models

`ollama pull qwen2.5:3b` then copies to:

- `fresno-qwen2.5-3b-finance`
- `fresno-qwen2.5-3b-sustainability`
- `fresno-qwen2.5-3b-citizen_sw`
- `fresno-qwen2.5-3b-citizen_c`
- `fresno-qwen2.5-3b-citizen_ne`
- `fresno-qwen2.5-3b-clerk` (final package only)
