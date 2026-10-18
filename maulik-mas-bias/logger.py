"""
logger.py
Per-experiment output pack (when all 3 topologies finish):

  Star_transcript.txt / Parallel_transcript.txt / Ring_transcript.txt
  5 graphs (all topologies on each figure)
  summary.md
  graph_data.json
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")   # headless-safe — no display required
import matplotlib.pyplot as plt
import numpy as np

import config
from metrics import TurnMetrics, final_round_consensus

_log = logging.getLogger("logger")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# Plot style constants
_TOPO_COLOR  = {"star": "#d95f02", "parallel": "#1b9e77", "ring": "#7570b3"}
_TOPO_MARKER = {"star": "o",       "parallel": "s",        "ring": "^"}
_TOPO_LABEL  = {"star": "Star",    "parallel": "Parallel", "ring": "Ring"}
_NBHD_COLOR  = {
    "Southwest Fresno": "#e41a1c",
    "Chinatown":        "#ff7f00",
    "Downtown Fresno":  "#4daf4a",
    "Shared":           "#377eb8",
}


# ===========================================================================
# RunLogger — the main interface called from main.py
# ===========================================================================

def topo_file_label(topology: str) -> str:
    return _TOPO_LABEL.get(topology, topology.capitalize())


class RunLogger:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _prefix(self, topology: str) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        return os.path.join(self.output_dir, topo_file_label(topology))

    def save_plots(
        self,
        experiment: str,
        topology: str,
        turn_metrics: List[TurnMetrics],
        messages: Optional[List] = None,
    ) -> List[str]:
        """Kept for callers; experiment-level plots are save_experiment_plots."""
        return []

    def save_experiment_plots(
        self,
        experiment: str,
        all_metrics: Dict[str, List[TurnMetrics]],
    ) -> List[str]:
        """Five figures for the experiment — topologies share each graph."""
        if not all_metrics:
            return []
        out = self.output_dir
        jobs = [
            ("Gini", _plot_cross_topology_gini,
             os.path.join(out, "gini_trajectory.png")),
            ("Neighbourhood by round", _plot_cross_topology_nbhd_rounds,
             os.path.join(out, "neighborhood_allocations.png")),
            ("SW mandate", _plot_cross_topology_sw,
             os.path.join(out, "sw_mandate.png")),
            ("Budget", _plot_cross_topology_budget,
             os.path.join(out, "budget_utilisation.png")),
            ("Final allocation", _plot_cross_topology_nbhd,
             os.path.join(out, "final_allocation.png")),
        ]
        saved: List[str] = []
        for label, fn, path in jobs:
            try:
                p = fn(all_metrics, experiment, path)
                if p:
                    saved.append(p)
            except Exception as exc:
                _log.warning("%s plot failed: %s", label, exc)
        return saved

    def write_experiment_pack(
        self,
        experiment: str,
        all_metrics: Dict[str, List[TurnMetrics]],
        all_messages: Dict[str, List],
        model: str,
        use_judge: bool,
        proposals=None,
        judge_model: str = None,
    ) -> tuple:
        graph_path = os.path.join(self.output_dir, "graph_data.json")
        summary_path = os.path.join(self.output_dir, "summary.md")
        payload = _graph_data_payload(
            experiment, all_metrics, all_messages, model, use_judge,
            proposals=proposals, judge_model=judge_model,
        )
        with open(graph_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        with open(summary_path, "w", encoding="utf-8") as fh:
            fh.write(_summary_markdown(experiment, payload, all_metrics, all_messages))
        _log.info("Saved: %s", graph_path)
        _log.info("Saved: %s", summary_path)
        return graph_path, summary_path

    # ------------------------------------------------------------------
    # Cross-topology plots (called after all topologies for one experiment)
    # ------------------------------------------------------------------

# ===========================================================================
# graph_data.json + summary.md
# ===========================================================================

def _round_list(metrics: List[TurnMetrics]) -> List[int]:
    return sorted(set(tm.round_number for tm in metrics))


def _plotted_series(metrics: List[TurnMetrics]) -> dict:
    rounds = _round_list(metrics)
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))
    last_r = rounds[-1] if rounds else 0
    last_m = [tm for tm in metrics if tm.round_number == last_r]
    nbhds = config.ALLOCATION_BUCKETS

    gini_by_agent = {}
    sw_by_agent = {}
    budget_by_agent = {}
    for speaker in speakers:
        s_m = sorted([tm for tm in metrics if tm.speaker == speaker], key=lambda t: t.round_number)
        gini_by_agent[speaker] = [round(t.gini_score, 4) for t in s_m]
        sw_by_agent[speaker] = [round(t.sw_fresno_shortfall_usd) for t in s_m]
        budget_by_agent[speaker] = [round(t.total_allocated_usd) for t in s_m]

    nbhd_avg = {}
    for r in rounds:
        r_m = [tm for tm in metrics if tm.round_number == r]
        nbhd_avg[str(r)] = {
            n: round(float(np.mean([tm.neighborhood_totals.get(n, 0.0) for tm in r_m])))
            for n in nbhds
        }

    return {
        "gini_trajectory": {
            "rounds": rounds,
            "avg_gini": [round(v, 4) for v in _rounds_and_avg_gini(metrics)[1]],
            "per_agent": gini_by_agent,
        },
        "neighborhood_allocations": {
            "rounds": rounds,
            "avg_usd_by_round": nbhd_avg,
        },
        "sw_mandate": {
            "rounds": rounds,
            "shortfall_usd_per_agent": sw_by_agent,
        },
        "budget_utilisation": {
            "rounds": rounds,
            "total_usd_per_agent": budget_by_agent,
            "cap_usd": config.TOTAL_BUDGET_USD,
            "floor_usd": config.MIN_BUDGET_USD,
        },
        "final_allocation": {
            "round": last_r,
            "per_agent": {
                tm.speaker: {n: round(tm.neighborhood_totals.get(n, 0.0)) for n in nbhds}
                for tm in last_m
            },
        },
    }


def _unplotted_series(metrics: List[TurnMetrics], messages: List) -> dict:
    rounds = _round_list(metrics)
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))
    from collections import Counter
    freq: Counter = Counter()
    for msg in messages or []:
        for pid in getattr(msg, "funded_projects", {}) or {}:
            freq[int(pid)] += 1

    judge_by_round = {
        str(r): sum(1 for tm in metrics if tm.round_number == r and tm.judge_triggered)
        for r in rounds
    }
    fiscal_by_round = {}
    for r in rounds:
        counts: Dict[str, int] = {}
        for tm in metrics:
            if tm.round_number != r:
                continue
            for flag in getattr(tm, "fiscal_flags", []) or []:
                counts[flag] = counts.get(flag, 0) + 1
        fiscal_by_round[str(r)] = counts

    share_ratio = {}
    for r in rounds:
        r_m = [tm for tm in metrics if tm.round_number == r]
        sw = float(np.mean([
            tm.neighborhood_totals.get("Southwest Fresno", 0.0)
            + tm.neighborhood_totals.get("Shared", 0.0)
            for tm in r_m
        ]))
        dt = float(np.mean([tm.neighborhood_totals.get("Downtown Fresno", 0.0) for tm in r_m]))
        share_ratio[str(r)] = {
            "avg_sw_plus_shared_usd": round(sw),
            "avg_downtown_usd": round(dt),
            "downtown_over_sw": round(dt / sw, 4) if sw else None,
        }

    unique_projects = {}
    for speaker in speakers:
        unique_projects[speaker] = {}
        for r in rounds:
            ids = set()
            for msg in messages or []:
                if msg.speaker == speaker and msg.round_number == r:
                    ids.update(int(p) for p in (msg.funded_projects or {}))
            unique_projects[speaker][str(r)] = sorted(ids)

    return {
        "project_frequency": {
            "note": "Not drawn. Counts of (agent, round) slates that include each ID.",
            "counts": {str(k): v for k, v in sorted(freq.items(), key=lambda kv: -kv[1])},
        },
        "judge_warnings_by_round": {
            "note": "Not drawn. Judge BIAS DETECTED counts per round.",
            "counts": judge_by_round,
        },
        "fiscal_flags_by_round": {
            "note": "Not drawn. overfunding / underfunding / southwest_underfunding counts.",
            "counts": fiscal_by_round,
        },
        "downtown_vs_sw_share": {
            "note": "Not drawn. Mean Downtown $ vs SW+Shared $ by round.",
            "by_round": share_ratio,
        },
        "unique_projects_per_agent": {
            "note": "Not drawn. Proposal IDs each agent funded each round.",
            "by_agent": unique_projects,
        },
    }


def _graph_data_payload(
    experiment: str,
    all_metrics: Dict[str, List[TurnMetrics]],
    all_messages: Dict[str, List],
    model: str,
    use_judge: bool,
    proposals=None,
    judge_model: str = None,
) -> dict:
    exp_cfg = config.EXPERIMENTS[experiment]
    plotted = {}
    unplotted = {}
    turns = {}
    consensus = {}
    for topo, metrics in all_metrics.items():
        label = topo_file_label(topo)
        plotted[label] = _plotted_series(metrics)
        unplotted[label] = _unplotted_series(metrics, all_messages.get(topo, []))
        turns[label] = [tm.to_dict() for tm in metrics]
        if proposals is not None:
            consensus[label] = final_round_consensus(
                all_messages.get(topo, []), proposals
            )
    return {
        "experiment": experiment,
        "description": exp_cfg["description"],
        "model": model,
        "agent_model": model,
        "judge_model": judge_model,
        "use_judge": use_judge,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "final_round_consensus": {
            "note": (
                "Per topology, final-round only: for each catalog project, "
                "sum the six panelists' funded TCC amounts and divide by 6. "
                "An agent who did not fund it contributes $0."
            ),
            "topologies": consensus,
        },
        "plotted": {
            "note": (
                "Series behind the five PNGs per topology: gini_trajectory, "
                "neighborhood_allocations, sw_mandate, budget_utilisation, "
                "final_allocation."
            ),
            "topologies": plotted,
        },
        "unplotted": {
            "note": (
                "Raw series for five graphs that are not created: "
                "project_frequency, judge_warnings_by_round, "
                "fiscal_flags_by_round, downtown_vs_sw_share, "
                "unique_projects_per_agent."
            ),
            "topologies": unplotted,
        },
        "turns": turns,
    }


def _summary_markdown(
    experiment: str,
    payload: dict,
    all_metrics: Dict[str, List[TurnMetrics]],
    all_messages: Dict[str, List],
) -> str:
    lines = [
        f"# {experiment}",
        "",
        payload.get("description", ""),
        "",
        f"Agents: `{payload.get('model')}`  |  Judge: "
        f"{('`' + str(payload.get('judge_model')) + '`') if payload.get('use_judge') else 'OFF'}",
        "",
        "## Trends",
        "",
    ]
    for topo, metrics in all_metrics.items():
        label = topo_file_label(topo)
        if not metrics:
            continue
        rounds = _round_list(metrics)
        first_g = float(np.mean([tm.gini_score for tm in metrics if tm.round_number == rounds[0]]))
        last_g = float(np.mean([tm.gini_score for tm in metrics if tm.round_number == rounds[-1]]))
        direction = "fell" if last_g < first_g - 0.01 else ("rose" if last_g > first_g + 0.01 else "held")
        mandate_miss = sum(1 for tm in metrics if not tm.sw_mandate_met())
        budget_miss = sum(1 for tm in metrics if not tm.budget_ok())
        judges = sum(1 for tm in metrics if tm.judge_triggered)
        lines += [
            f"### {label}",
            f"- Average Gini {direction}: {first_g:.3f} (round {rounds[0]}) → {last_g:.3f} (round {rounds[-1]})",
            f"- Mandate misses: {mandate_miss}/{len(metrics)} turns",
            f"- Budget band misses ($60–66.5M): {budget_miss}/{len(metrics)} turns",
            f"- Judge warnings stored: {judges}",
            "",
        ]

    cons = (payload.get("final_round_consensus") or {}).get("topologies") or {}
    if cons:
        lines += ["## Final-round consensus", ""]
        lines.append(
            "Final round only. For each catalog project: add the six "
            "panelists' TCC amounts and divide by 6. Unfunded = $0."
        )
        lines.append("")
        for label, block in cons.items():
            rnd = block.get("round", "?")
            n = block.get("n_agents", 0)
            rows = [r for r in (block.get("projects") or []) if r.get("average_usd", 0) > 0]
            lines.append(f"### {label} (round {rnd}, {n} panelists)")
            if not rows:
                lines.append("- No funded projects.")
            else:
                for r in rows[:15]:
                    lines.append(
                        f"- #{r['id']} {r['title']} — {r['n_agents_funding']}/{r['n_agents']} "
                        f"agents, avg ${r['average_usd']:,.0f} (TCC ${r['tcc_request']:,.0f})"
                    )
                extra = len(rows) - 15
                if extra > 0:
                    lines.append(f"- … {extra} more with avg $ > 0 (see graph_data.json)")
            lines.append("")

    lines += ["## Outliers", ""]
    all_tm = [(topo, tm) for topo, ms in all_metrics.items() for tm in ms]
    if all_tm:
        hi = max(all_tm, key=lambda x: x[1].gini_score)
        lo_sw = max(all_tm, key=lambda x: x[1].sw_fresno_shortfall_usd)
        hi_over = max(all_tm, key=lambda x: x[1].budget_overrun_usd)
        lines += [
            f"- Highest Gini: **{hi[1].gini_score:.3f}** — {hi[1].speaker} "
            f"({topo_file_label(hi[0])}, round {hi[1].round_number})",
            f"- Largest SW shortfall: **${lo_sw[1].sw_fresno_shortfall_usd:,.0f}** — "
            f"{lo_sw[1].speaker} ({topo_file_label(lo_sw[0])}, round {lo_sw[1].round_number})",
            f"- Largest budget overrun: **${hi_over[1].budget_overrun_usd:,.0f}** — "
            f"{hi_over[1].speaker} ({topo_file_label(hi_over[0])}, round {hi_over[1].round_number})",
        ]

    from collections import Counter
    freq: Counter = Counter()
    for messages in all_messages.values():
        for msg in messages or []:
            for pid in getattr(msg, "funded_projects", {}) or {}:
                freq[int(pid)] += 1
    if freq:
        top = freq.most_common(5)
        lines += ["", "- Most-funded proposal IDs (all topologies): " +
                  ", ".join(f"#{pid} ({n})" for pid, n in top)]

    lines += ["", "## Notable turns", ""]
    notables = []
    for topo, messages in all_messages.items():
        for msg in messages or []:
            text = (msg.reasoning or "").strip()
            if not text:
                continue
            notables.append((topo, msg, text))
    flagged = []
    for topo, tm in all_tm:
        if tm.judge_triggered or tm.gini_score > 0.6 or tm.sw_fresno_shortfall_usd > 20_000_000:
            flagged.append((topo, tm))
    flagged.sort(key=lambda x: (-x[1].gini_score, -x[1].sw_fresno_shortfall_usd))
    for topo, tm in flagged[:8]:
        snippet = ""
        for msg in all_messages.get(topo, []) or []:
            if msg.speaker == tm.speaker and msg.round_number == tm.round_number:
                snippet = (msg.reasoning or "").replace("\n", " ")[:280]
                break
        lines.append(
            f"- **{tm.speaker}** / {topo_file_label(topo)} / R{tm.round_number}: "
            f"Gini {tm.gini_score:.3f}, SW short ${tm.sw_fresno_shortfall_usd:,.0f}"
            f"{'; judge flagged' if tm.judge_triggered else ''}."
        )
        if snippet:
            lines.append(f"  > {snippet}")
    if len(flagged) == 0:
        lines.append("- No high-Gini, large-SW-miss, or judge-flagged turns.")

    lines += ["", "---", "Data for the five drawn graphs and five reserved series: `graph_data.json`.", ""]
    return "\n".join(lines) + "\n"


# ===========================================================================
# Plot helpers
# ===========================================================================

def _rounds_and_avg_gini(metrics: List[TurnMetrics]):
    """Returns (round_list, avg_gini_per_round)."""
    rounds = sorted(set(tm.round_number for tm in metrics))
    avgs = [
        float(np.mean([tm.gini_score for tm in metrics if tm.round_number == r]))
        for r in rounds
    ]
    return rounds, avgs


def _plot_gini_trajectory(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """Gini over rounds: group average + individual per-agent lines."""
    rounds, avgs = _rounds_and_avg_gini(metrics)
    color  = _TOPO_COLOR.get(topology, "#4c72b0")
    marker = _TOPO_MARKER.get(topology, "o")

    fig, ax = plt.subplots(figsize=(9, 5))

    # Per-agent thin lines
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))
    agent_colors = plt.cm.Set2(np.linspace(0, 1, len(speakers)))
    for i, speaker in enumerate(speakers):
        s_m = sorted([tm for tm in metrics if tm.speaker == speaker],
                     key=lambda t: t.round_number)
        ax.plot([t.round_number for t in s_m], [t.gini_score for t in s_m],
                color=agent_colors[i], linewidth=1.0, alpha=0.45, linestyle="--")

    # Bold average line
    ax.plot(rounds, avgs, color=color, marker=marker,
            markersize=8, linewidth=2.5, label="Avg Gini per round", zorder=4)

    # Judge warning markers
    warned = sorted(set(tm.round_number for tm in metrics if tm.judge_triggered))
    for wr in warned:
        if wr in rounds:
            idx = rounds.index(wr)
            ax.scatter([wr], [avgs[idx]], s=220, facecolors="none",
                       edgecolors="red", linewidths=2.5, zorder=5,
                       label="Judge warning fired" if wr == warned[0] else "")

    ax.axhline(
        config.GINI_INTERVENTION_THRESHOLD, color="red", linestyle="--",
        linewidth=1.4, alpha=0.8,
        label=f"Judge threshold ({config.GINI_INTERVENTION_THRESHOLD})",
    )
    ax.axhspan(0, config.GINI_INTERVENTION_THRESHOLD, alpha=0.04, color="green",
               label="Equitable zone")

    ax.set_xlabel("Negotiation Round", fontsize=11)
    ax.set_ylabel("Gini Coefficient\n(0 = equal; 1 = maximally unequal)", fontsize=10)
    ax.set_title(
        f"Gini Coefficient Trajectory — Emergent Socioeconomic Bias\n"
        f"{experiment}  /  {topology.capitalize()}",
        fontsize=12,
    )
    ax.set_xticks(rounds)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_neighbourhood_bars(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    rounds = sorted(set(tm.round_number for tm in metrics))
    nbhds  = config.ALLOCATION_BUCKETS

    # Average allocation per neighbourhood per round (in $M)
    round_avgs: Dict[int, Dict[str, float]] = {}
    for r in rounds:
        r_metrics = [tm for tm in metrics if tm.round_number == r]
        round_avgs[r] = {
            n: float(np.mean([tm.neighborhood_totals.get(n, 0.0) for tm in r_metrics])) / 1e6
            for n in nbhds
        }

    x     = np.arange(len(rounds))
    width = 0.2
    fig, ax = plt.subplots(figsize=(10, 5))

    for i, nbhd in enumerate(nbhds):
        vals = [round_avgs[r][nbhd] for r in rounds]
        ax.bar(
            x + (i - (len(nbhds) - 1) / 2) * width, vals, width,
            label=nbhd,
            color=_NBHD_COLOR.get(nbhd, f"C{i}"),
            alpha=0.85, edgecolor="black", linewidth=0.6,
        )

    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Avg Allocation per Panelist ($M)")
    ax.set_title(
        f"Neighbourhood + Shared by Round (multi-area $ in Shared only)\n"
        f"{experiment}  /  {topology.capitalize()}"
    )
    ax.set_xticks(x)
    ax.set_xticklabels([f"Rd {r}" for r in rounds])
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_sw_mandate(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """
    Per-agent SW Fresno shortfall across rounds.
    Positive value = under-funded; zero/negative = mandate met.
    """
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))  # stable order
    colors   = plt.cm.tab10(np.linspace(0, 1, len(speakers)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, speaker in enumerate(speakers):
        s_metrics = sorted(
            [tm for tm in metrics if tm.speaker == speaker],
            key=lambda t: t.round_number,
        )
        r_rounds = [tm.round_number for tm in s_metrics]
        r_vals   = [tm.sw_fresno_shortfall_usd / 1e6 for tm in s_metrics]
        ax.plot(r_rounds, r_vals, marker="o", markersize=5,
                label=speaker, color=colors[i], linewidth=1.6, alpha=0.85)

    ax.axhline(0, color="green", linestyle="--", linewidth=1.8, alpha=0.8,
               label="Mandate threshold ($37M met)")
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("SW Fresno Shortfall ($M)\n(positive = under-funded)")
    ax.set_title(
        f"SW Fresno Mandate Compliance per Agent\n"
        f"{experiment}  /  {topology.capitalize()}"
    )
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_budget_utilisation(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """Per-agent total allocation over rounds vs. the $66.5M target."""
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))
    colors   = plt.cm.tab10(np.linspace(0, 1, len(speakers)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, speaker in enumerate(speakers):
        s_m = sorted([tm for tm in metrics if tm.speaker == speaker],
                     key=lambda t: t.round_number)
        ax.plot(
            [t.round_number for t in s_m],
            [t.total_allocated_usd / 1e6 for t in s_m],
            marker="o", markersize=5, linewidth=1.8,
            label=speaker, color=colors[i], alpha=0.85,
        )

    ax.axhline(config.TOTAL_BUDGET_USD / 1e6, color="navy", linestyle="-",
               linewidth=1.8, alpha=0.7,
               label=f"Target (${config.TOTAL_BUDGET_USD/1e6:.1f}M)")
    ax.axhline(60, color="orange", linestyle=":", linewidth=1.5, alpha=0.7,
               label="Minimum acceptable ($60M)")
    ax.set_xlabel("Negotiation Round", fontsize=11)
    ax.set_ylabel("Total Allocated ($M)", fontsize=10)
    ax.set_title(
        f"Budget Utilisation per Agent\n{experiment}  /  {topology.capitalize()}",
        fontsize=12,
    )
    ax.legend(fontsize=7, loc="lower right", ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_final_allocation_bar(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """
    Final-round stacked bar per agent showing neighbourhood breakdown.
    Illustrates which agents skewed toward which neighbourhoods.
    """
    rounds  = sorted(set(tm.round_number for tm in metrics))
    last_r  = rounds[-1]
    last_m  = [tm for tm in metrics if tm.round_number == last_r]
    speakers = [tm.speaker for tm in last_m]
    nbhds    = config.ALLOCATION_BUCKETS

    fig, ax = plt.subplots(figsize=(11, 5))
    bottoms = np.zeros(len(speakers))

    for nbhd in nbhds:
        vals = np.array([
            tm.neighborhood_totals.get(nbhd, 0.0) / 1e6
            for tm in last_m
        ])
        ax.bar(speakers, vals, bottom=bottoms,
               label=nbhd, color=_NBHD_COLOR.get(nbhd, "gray"),
               alpha=0.85, edgecolor="black", linewidth=0.5)
        bottoms += vals

    ax.axhline(config.TOTAL_BUDGET_USD / 1e6, color="navy", linestyle="-",
               linewidth=1.5, alpha=0.6,
               label=f"Total budget (${config.TOTAL_BUDGET_USD/1e6:.1f}M)")

    ax.set_xlabel("Agent", fontsize=11)
    ax.set_ylabel("Allocated ($M)", fontsize=10)
    ax.set_title(
        f"Final-Round Allocation by Agent (exclusive neighborhoods + Shared)\n"
        f"{experiment}  /  {topology.capitalize()}",
        fontsize=12,
    )
    plt.xticks(rotation=25, ha="right", fontsize=9)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_project_frequency(
    messages: list,
    experiment: str,
    topology: str,
    path: str,
    top_n: int = 20,
) -> str:
    """
    Frequency chart: which proposals were funded most often across all agents
    and rounds.  Bars are coloured by neighbourhood tag.
    """
    from collections import Counter
    from proposal_loader import Proposal  # local import to avoid circular deps

    # Count how many (agent, round) combos funded each project
    counter: Counter = Counter()
    for msg in messages:
        for pid in msg.funded_projects:
            counter[pid] += 1

    if not counter:
        return ""

    most_common = counter.most_common(top_n)
    pids   = [str(pid) for pid, _ in most_common]
    counts = [cnt for _, cnt in most_common]

    fig, ax = plt.subplots(figsize=(12, 5))
    bar_colors = ["#e41a1c"] * len(pids)   # default red (SW Fresno colour)
    ax.barh(pids, counts, color=bar_colors, alpha=0.8, edgecolor="black",
            linewidth=0.5)

    ax.set_xlabel("Number of agent-round allocations", fontsize=11)
    ax.set_ylabel("Proposal ID", fontsize=10)
    ax.set_title(
        f"Top {top_n} Most-Funded Proposals (all agents, all rounds)\n"
        f"{experiment}  /  {topology.capitalize()}",
        fontsize=12,
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_gini(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    fig, ax = plt.subplots(figsize=(9, 5.5))

    for topo_name, metrics in all_metrics.items():
        if not metrics:
            continue
        rounds, avgs = _rounds_and_avg_gini(metrics)
        ax.plot(
            rounds, avgs,
            label=_TOPO_LABEL.get(topo_name, topo_name.capitalize()),
            color=_TOPO_COLOR.get(topo_name, "#888"),
            marker=_TOPO_MARKER.get(topo_name, "o"),
            markersize=7, linewidth=2.2, alpha=0.9,
        )

    ax.axhline(
        config.GINI_INTERVENTION_THRESHOLD, color="red",
        linestyle="--", linewidth=1.3, alpha=0.7,
        label=f"Judge threshold ({config.GINI_INTERVENTION_THRESHOLD})",
    )
    ax.set_xlabel("Negotiation Round", fontsize=11)
    ax.set_ylabel("Average Gini (neighbourhood inequality)", fontsize=10)
    ax.set_title(
        f"Gini Trajectory — All Topologies\n"
        f"{experiment}  (emergent socioeconomic bias study)",
        fontsize=12,
    )
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _mean_by_round(metrics: List[TurnMetrics], attr: str) -> tuple:
    rounds = sorted(set(tm.round_number for tm in metrics))
    avgs = [
        float(np.mean([getattr(tm, attr) for tm in metrics if tm.round_number == r]))
        for r in rounds
    ]
    return rounds, avgs


def _plot_cross_topology_nbhd_rounds(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    topos = [t for t, m in all_metrics.items() if m]
    if not topos:
        return ""
    nbhds = config.ALLOCATION_BUCKETS
    fig, axes = plt.subplots(1, len(topos), figsize=(4.2 * len(topos), 4.8), sharey=True)
    if len(topos) == 1:
        axes = [axes]
    for ax, topo in zip(axes, topos):
        metrics = all_metrics[topo]
        rounds = sorted(set(tm.round_number for tm in metrics))
        x = np.arange(len(rounds))
        width = 0.2
        for i, nbhd in enumerate(nbhds):
            vals = [
                float(np.mean([
                    tm.neighborhood_totals.get(nbhd, 0.0) for tm in metrics
                    if tm.round_number == r
                ])) / 1e6
                for r in rounds
            ]
            ax.bar(
                x + (i - (len(nbhds) - 1) / 2) * width, vals, width,
                label=nbhd if ax is axes[0] else None,
                color=_NBHD_COLOR.get(nbhd, f"C{i}"),
                alpha=0.85, edgecolor="black", linewidth=0.5,
            )
        ax.set_title(_TOPO_LABEL.get(topo, topo))
        ax.set_xticks(x)
        ax.set_xticklabels([f"R{r}" for r in rounds])
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Avg allocation ($M)")
    fig.suptitle(f"Neighbourhood + Shared by Round\n{experiment}", fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_sw(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for topo, metrics in all_metrics.items():
        if not metrics:
            continue
        rounds, avgs = _mean_by_round(metrics, "sw_fresno_shortfall_usd")
        ax.plot(
            rounds, [v / 1e6 for v in avgs],
            label=_TOPO_LABEL.get(topo, topo),
            color=_TOPO_COLOR.get(topo, "#888"),
            marker=_TOPO_MARKER.get(topo, "o"),
            markersize=7, linewidth=2.2,
        )
    ax.axhline(0, color="green", linestyle="--", linewidth=1.6,
               label="Mandate met ($37M)")
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Avg SW shortfall ($M)\n(positive = under-funded)")
    ax.set_title(f"SW Fresno Mandate — All Topologies\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_budget(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for topo, metrics in all_metrics.items():
        if not metrics:
            continue
        rounds, avgs = _mean_by_round(metrics, "total_allocated_usd")
        ax.plot(
            rounds, [v / 1e6 for v in avgs],
            label=_TOPO_LABEL.get(topo, topo),
            color=_TOPO_COLOR.get(topo, "#888"),
            marker=_TOPO_MARKER.get(topo, "o"),
            markersize=7, linewidth=2.2,
        )
    ax.axhline(config.TOTAL_BUDGET_USD / 1e6, color="navy", linestyle="-",
               linewidth=1.5, label=f"Cap (${config.TOTAL_BUDGET_USD/1e6:.1f}M)")
    ax.axhline(config.MIN_BUDGET_USD / 1e6, color="orange", linestyle=":",
               linewidth=1.5, label=f"Floor (${config.MIN_BUDGET_USD/1e6:.1f}M)")
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Avg total allocated ($M)")
    ax.set_title(f"Budget Utilisation — All Topologies\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_nbhd(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    """
    Final-round neighbourhood averages across all topologies — side-by-side
    grouped bar chart comparing how each topology allocated to each neighbourhood.
    """
    topos  = [t for t, m in all_metrics.items() if m]
    nbhds  = config.ALLOCATION_BUCKETS
    x      = np.arange(len(nbhds))
    width  = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, topo in enumerate(topos):
        metrics = all_metrics[topo]
        last_r  = max(tm.round_number for tm in metrics)
        last_m  = [tm for tm in metrics if tm.round_number == last_r]
        vals    = [
            float(np.mean([tm.neighborhood_totals.get(n, 0.0) for tm in last_m])) / 1e6
            for n in nbhds
        ]
        ax.bar(
            x + (i - (len(topos) - 1) / 2) * width, vals, width,
            label=_TOPO_LABEL.get(topo, topo),
            color=_TOPO_COLOR.get(topo, f"C{i}"),
            alpha=0.85, edgecolor="black", linewidth=0.5,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(nbhds, fontsize=10)
    ax.set_ylabel("Avg Final-Round Allocation ($M)", fontsize=10)
    ax.set_title(
        f"Final-Round Neighbourhood Shares — Topology Comparison "
        f"(exclusive neighborhoods + Shared)\n{experiment}",
        fontsize=12,
    )
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved cross-topology neighbourhood plot: %s", path)
    return path


def _plot_cross_topology_bias_flags(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    """
    Bar chart: number of judge bias-flags per round per topology.
    Shows whether the judge intervened more in certain topologies/rounds.
    """
    topos   = [t for t, m in all_metrics.items() if m]
    all_rounds = sorted(set(
        tm.round_number
        for metrics in all_metrics.values()
        for tm in metrics
    ))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(all_rounds))

    for i, topo in enumerate(topos):
        metrics = all_metrics[topo]
        counts  = [
            sum(1 for tm in metrics if tm.round_number == r and tm.judge_triggered)
            for r in all_rounds
        ]
        ax.bar(
            x + (i - (len(topos) - 1) / 2) * width, counts, width,
            label=_TOPO_LABEL.get(topo, topo),
            color=_TOPO_COLOR.get(topo, f"C{i}"),
            alpha=0.85, edgecolor="black", linewidth=0.5,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([f"Round {r}" for r in all_rounds])
    ax.set_ylabel("Judge Bias-Flag Count", fontsize=10)
    ax.set_title(
        f"Judge Bias-Flag Frequency by Round & Topology\n{experiment}",
        fontsize=12,
    )
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved cross-topology bias flags plot: %s", path)
    return path
