"""
main.py
Fresno Infrastructure Budget Allocation — multi-agent emergent-bias study runner.

Runs one or all of the 5 experiments across one or all 3 topologies using
Ollama-served language models.  Tuned for NVIDIA L4 24GB.  No vLLM required.

Prerequisites (NVIDIA L4 24GB / JupyterLab):
  1. Install and start Ollama (flash-attn helps the L4 KV cache):
       curl -fsSL https://ollama.com/install.sh | sh
       export OLLAMA_FLASH_ATTENTION=1
       ollama serve &
  2. Pull the required models:
       ollama pull qwen3.5:4b
       ollama pull qwen3.5:9b      # needed for exp3–exp5
  3. Confirm the GPU:
       nvidia-smi
  4. Install Python deps:
       pip install -r requirements.txt

Usage
-----
  # Short live trial (1 round, Star, 4B, real Ollama):
  python3 main.py --trial

  # Overnight — all 5 experiments × 3 topologies:
  nohup python3 main.py > full_study.log 2>&1 &

  # Single experiment, all topologies:
  python3 main.py --experiment exp1_4b_no_judge

  # Single experiment + topology:
  python3 main.py --experiment exp1_4b_no_judge --topology star
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys

import config
from agents import build_agents
from logger import RunLogger, topo_file_label
from proposal_loader import load_proposals
from topologies import TOPOLOGY_REGISTRY
from transcript import TranscriptLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
_log = logging.getLogger("main")


# ===========================================================================
# CLI
# ===========================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description="Fresno Infrastructure Budget Allocation — Multi-Agent Bias Study",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--experiment",
        choices=list(config.EXPERIMENTS.keys()) + ["all"],
        default="all",
        help="Which experiment to run (default: all 5)",
    )
    p.add_argument(
        "--topology",
        choices=list(TOPOLOGY_REGISTRY.keys()) + ["all"],
        default="all",
        help="Which communication topology to use (default: all 3)",
    )
    p.add_argument(
        "--rounds",
        type=int,
        default=config.NEGOTIATION_ROUNDS,
        help=f"Number of negotiation rounds per run (default: {config.NEGOTIATION_ROUNDS})",
    )
    p.add_argument(
        "--pdf-path",
        default=None,
        help=(
            "Path to the 37-proposal PDF "
            f"(default: {config.PROPOSALS_PDF_PATH} or $PROPOSALS_PDF_PATH)"
        ),
    )
    p.add_argument(
        "--output-dir",
        default=config.OUTPUT_DIR,
        help=f"Directory for all output files (default: {config.OUTPUT_DIR})",
    )
    p.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip matplotlib figure generation (faster; traces and transcripts still saved)",
    )
    p.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Use offline placeholder fallback — run without a live Ollama server. "
            "Useful for testing pipeline wiring only; outputs are NOT real results."
        ),
    )
    p.add_argument(
        "--trial",
        action="store_true",
        help=(
            "Short live smoke test: exp1 (4B, no judge), Star, 1 round. "
            "Hits real Ollama. Overrides --experiment / --topology / --rounds."
        ),
    )
    p.add_argument(
        "--new-run",
        action="store_true",
        help=(
            "Write to a new numbered folder (exp3_9b_no_judge (1)) instead of "
            "reusing outputs/<experiment>/."
        ),
    )
    return p.parse_args()


def gpu_status_line() -> str:
    """Best-effort nvidia-smi one-liner so L4 VRAM is visible at start."""
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=8,
        ).strip().splitlines()[0]
        return out
    except Exception:
        return "nvidia-smi unavailable (is the L4 visible in this session?)"


def unique_experiment_dir(
    output_root: str, experiment: str, new_run: bool = False
) -> str:
    """
    One folder per experiment name. Reuses outputs/<experiment>/ so Star,
    Parallel, and Ring land together. Pass new_run=True for a numbered copy.
    """
    os.makedirs(output_root, exist_ok=True)
    candidate = os.path.join(output_root, experiment)
    if new_run:
        n = 1
        while os.path.exists(candidate):
            candidate = os.path.join(output_root, f"{experiment} ({n})")
            n += 1
    os.makedirs(candidate, exist_ok=True)
    return candidate


# ===========================================================================
# Single-run executor
# ===========================================================================

def run_one(
    experiment: str,
    topology: str,
    proposals,
    rounds: int,
    exp_dir: str,
    skip_plots: bool,
    offline: bool,
    transcript: "TranscriptLogger",
) -> dict:
    exp_cfg     = config.EXPERIMENTS[experiment]
    agent_model, judge_model = config.experiment_models(exp_cfg)
    use_judge   = exp_cfg["use_judge"]
    model_line  = (
        f"Agents: {agent_model}"
        + (f"  |  Judge: {judge_model}" if use_judge else "  |  Judge: OFF")
    )

    print(
        f"\n{'─' * 70}\n"
        f"  Topology   : {topology.upper()}\n"
        f"  {model_line}\n"
        f"  Rounds     : {rounds}\n"
        f"{'─' * 70}"
    )

    agents_list = build_agents(
        agent_model, judge_model=judge_model, allow_offline_fallback=offline
    )

    topo_cls = TOPOLOGY_REGISTRY[topology]
    run      = topo_cls(
        agents=agents_list,
        proposals=proposals,
        transcript=transcript,
        use_judge=use_judge,
    )
    try:
        messages, turn_metrics = run.run(rounds=rounds)
    except Exception as exc:
        _log.error("Run %s/%s failed: %s", experiment, topology, exc, exc_info=True)
        transcript.log_note(f"RUN FAILED ({topology}): {exc}")
        return {}

    judge_count  = sum(1 for tm in turn_metrics if tm.judge_triggered)
    mandate_viol = sum(1 for tm in turn_metrics if not tm.sw_mandate_met())
    final_gini   = turn_metrics[-1].gini_score if turn_metrics else float("nan")

    print(
        f"\n  Topology {topology.upper()} done:\n"
        f"    Turns: {len(messages)}  |  "
        f"Judge warnings: {judge_count}  |  "
        f"Mandate violations: {mandate_viol}  |  "
        f"Final Gini: {final_gini:.4f}"
    )

    return {"messages": messages, "turn_metrics": turn_metrics}


# ===========================================================================
# Main
# ===========================================================================

def main():
    args = parse_args()

    if args.trial:
        args.experiment = "exp1_4b_no_judge"
        args.topology = "star"
        args.rounds = 1
        print(
            "\n*** TRIAL MODE — 4B Star, 1 round, live Ollama. "
            "Not a full study run. ***\n"
        )

    # Apply CLI overrides to config
    config.NEGOTIATION_ROUNDS = args.rounds

    # Resolve PDF path
    pdf_path = args.pdf_path or config.PROPOSALS_PDF_PATH

    # ------------------------------------------------------------------
    # Print study header
    # ------------------------------------------------------------------
    print(
        f"\n{'=' * 78}\n"
        f"  Fresno Infrastructure Budget Allocation — Emergent Bias Study\n"
        f"  Target GPU:     {config.TARGET_GPU}\n"
        f"  Visible GPU:    {gpu_status_line()}\n"
        f"  Context / keep: {config.OLLAMA_NUM_CTX} tok  |  "
        f"keep_alive={config.OLLAMA_KEEP_ALIVE}  |  "
        f"timeout={config.REQUEST_TIMEOUT_S}s\n"
        f"  Total budget:   ${config.TOTAL_BUDGET_USD:,.0f}\n"
        f"  SW Fresno min:  ${config.SW_FRESNO_MIN_USD:,.0f}\n"
        f"  Rounds/run:     {config.NEGOTIATION_ROUNDS}\n"
        f"  Bias threshold: Gini > {config.GINI_INTERVENTION_THRESHOLD}\n"
        f"  Output dir:     {args.output_dir}\n"
        f"  PDF path:       {pdf_path}\n"
        f"{'=' * 78}"
    )

    # ------------------------------------------------------------------
    # Load proposals
    # ------------------------------------------------------------------
    catalog = config.PROPOSALS_JSON_PATH
    print(f"\nLoading proposals from: {catalog} (PDF only if catalog is missing)")
    proposals = load_proposals(pdf_path=pdf_path, json_path=catalog)
    sw_count = sum(1 for p in proposals if p.is_sw_fresno)
    using_synth = any(p.synthetic for p in proposals)

    print(f"  Loaded {len(proposals)} proposals")
    print(f"  → {sw_count} include Southwest Fresno as a project area")
    if using_synth:
        print(
            "\n  *** WARNING: One or more proposals are SYNTHETIC placeholders. ***\n"
            "  Place the real PDF at the path above (or set PROPOSALS_PDF_PATH).\n"
            "  Results from synthetic data must NOT be reported as real findings.\n"
        )

    # Sanity check: SW Fresno proposals must be fundable to ≥$37M
    sw_total_available = sum(p.tcc_request for p in proposals if p.is_sw_fresno)
    if sw_total_available < config.SW_FRESNO_MIN_USD:
        print(
            f"\n  *** CAUTION: Total TCC Request for SW Fresno proposals "
            f"(${sw_total_available:,.0f}) is less than the required minimum "
            f"${config.SW_FRESNO_MIN_USD:,.0f}. Agents will be unable to satisfy "
            f"the mandate from the available proposals alone. ***\n"
        )

    # ------------------------------------------------------------------
    # Determine experiment and topology sets
    # ------------------------------------------------------------------
    experiments = (
        list(config.EXPERIMENTS.keys())
        if args.experiment == "all"
        else [args.experiment]
    )
    topologies = (
        list(TOPOLOGY_REGISTRY.keys())
        if args.topology == "all"
        else [args.topology]
    )

    total_runs = len(experiments) * len(topologies)
    completed  = 0

    # ------------------------------------------------------------------
    # Execute runs — one folder per experiment, 20 files when all 3 finish
    # ------------------------------------------------------------------
    created_dirs: list = []
    for experiment in experiments:
        exp_cfg = config.EXPERIMENTS[experiment]
        exp_dir = unique_experiment_dir(
            args.output_dir, experiment, new_run=args.new_run
        )
        created_dirs.append(exp_dir)
        print(f"\n  Writing {experiment} → {exp_dir}")
        agent_model, judge_model = config.experiment_models(exp_cfg)
        use_judge = exp_cfg["use_judge"]
        model_note = (
            f"Agents: {agent_model}  |  "
            + (f"Judge: {judge_model}" if use_judge else "Judge: OFF")
        )

        all_metrics_for_exp: dict = {}
        run_results: dict = {}

        for topology in topologies:
            t_path = os.path.join(exp_dir, f"{topo_file_label(topology)}_transcript.txt")
            transcript = TranscriptLogger(t_path, echo_to_terminal=True)
            transcript.log_note(
                f"Experiment: {experiment}  |  {exp_cfg['description']}\n"
                f"{model_note}  |  "
                f"Topology: {topology}  |  Rounds: {args.rounds}"
            )
            transcript.log_topology_header(
                topology, experiment, model_note, args.rounds, use_judge
            )
            try:
                result = run_one(
                    experiment  = experiment,
                    topology    = topology,
                    proposals   = proposals,
                    rounds      = args.rounds,
                    exp_dir     = exp_dir,
                    skip_plots  = args.skip_plots,
                    offline     = args.offline,
                    transcript  = transcript,
                )
            finally:
                transcript.close()

            run_results[topology] = result
            if result.get("turn_metrics"):
                all_metrics_for_exp[topology] = result["turn_metrics"]
            else:
                print(
                    f"\n  *** {experiment}/{topology} produced no turns — "
                    f"Ollama likely failed. Later topologies still run. ***\n"
                )
                _log.error("%s/%s returned no turn metrics", experiment, topology)

            completed += 1
            print(f"\n  Transcript: {t_path}")
            print(f"\n  [{completed}/{total_runs} runs complete]")

        all_messages_for_exp: dict = {
            t: run_results[t].get("messages", [])
            for t in all_metrics_for_exp
        }
        if all_metrics_for_exp:
            pack = RunLogger(exp_dir)
            try:
                graph_path, summary_path = pack.write_experiment_pack(
                    experiment, all_metrics_for_exp, all_messages_for_exp,
                    model=agent_model, use_judge=use_judge, proposals=proposals,
                    judge_model=judge_model,
                )
                print(f"  Graph data: {graph_path}")
                print(f"  Summary:    {summary_path}")
            except Exception as exc:
                _log.warning("Experiment pack failed: %s", exc)
            if not args.skip_plots:
                for pp in pack.save_experiment_plots(experiment, all_metrics_for_exp):
                    print(f"  Plot:       {pp}")

    print(
        f"\n{'=' * 78}\n"
        f"  All {completed} run(s) complete.\n"
        f"  Each experiment folder (when all 3 topologies finish):\n"
        f"    3 transcripts, 5 graphs, summary.md, graph_data.json\n"
    )
    for path in created_dirs:
        print(f"    {path}/")
    print(f"{'=' * 78}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
        sys.exit(130)
