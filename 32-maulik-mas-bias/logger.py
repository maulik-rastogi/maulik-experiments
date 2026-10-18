"""
logger.py
Per-experiment output pack (when all 3 topologies finish):

  Star_transcript.txt / Parallel_transcript.txt / Ring_transcript.txt
  5 comparison graphs (all topologies on each figure)
  Star/ Parallel/ Ring/ — turn (30-point) and round (5-point) graphs each
  summary.md
  graph_data.json
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")   # headless-safe — no display required
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.lines import Line2D
from matplotlib.ticker import FormatStrFormatter, MultipleLocator
import numpy as np

import config
from metrics import TurnMetrics, final_round_consensus
from plot_standard import render_experiment_plots, render_topology_plots

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
_AGENT_COLOR = {
    "Sustainability Expert":     "#1b9e77",
    "Financial Expert":          "#d95f02",
    "Urban Planner":             "#7570b3",
    "Citizen (SW Fresno)":       "#e7298a",
    "Citizen (Chinatown)":       "#66a61e",
    "Citizen (Downtown Fresno)": "#e6ab02",
    "Sustainability Agent":      "#1b9e77",
    "Financial Agent":           "#d95f02",
    "Infrastructure Agent":      "#7570b3",
    "Resident (SW Fresno)":      "#e7298a",
    "Resident (Chinatown)":      "#66a61e",
    "Resident (Downtown Fresno)": "#e6ab02",
}
_PLOT_DISPLAY = {
    "Sustainability Expert":     "Sustainability Agent",
    "Financial Expert":          "Financial Agent",
    "Urban Planner":             "Infrastructure Agent",
    "Citizen (SW Fresno)":       "Resident (SW Fresno)",
    "Citizen (Chinatown)":       "Resident (Chinatown)",
    "Citizen (Downtown Fresno)": "Resident (Downtown Fresno)",
}
_PLOT_SHORT = {
    "Sustainability Expert":     "Sustainability",
    "Financial Expert":          "Financial",
    "Urban Planner":             "Infrastructure",
    "Citizen (SW Fresno)":       "Resident SW",
    "Citizen (Chinatown)":       "Resident CH",
    "Citizen (Downtown Fresno)": "Resident DT",
    "Sustainability Agent":      "Sustainability",
    "Financial Agent":           "Financial",
    "Infrastructure Agent":      "Infrastructure",
    "Resident (SW Fresno)":      "Resident SW",
    "Resident (Chinatown)":      "Resident CH",
    "Resident (Downtown Fresno)": "Resident DT",
}
_MONO_DOT = "#4c72b0"


# ===========================================================================
# RunLogger — the main interface called from main.py
# ===========================================================================

def topo_file_label(topology: str) -> str:
    return _TOPO_LABEL.get(topology, topology.capitalize())


def _uses_judge(experiment: str, payload: Optional[dict] = None) -> bool:
    if payload and "use_judge" in payload:
        return bool(payload["use_judge"])
    cfg = config.EXPERIMENTS.get(experiment) or {}
    return bool(cfg.get("use_judge"))


def _plot_name(speaker: str) -> str:
    return _PLOT_DISPLAY.get(speaker, speaker)


def _variant_path(
    path: str, *, threshold: bool = True, color: bool = True,
    judge: bool = True, band: bool = True,
) -> str:
    root, ext = os.path.splitext(path)
    bits = []
    if not color:
        bits.append("mono")
    if not threshold:
        bits.append("no_threshold")
    if not judge:
        bits.append("no_judge")
    if not band:
        bits.append("no_band")
    if not bits:
        return path
    return f"{root}_{'_'.join(bits)}{ext}"


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
        proposals=None,
        use_judge: Optional[bool] = None,
    ) -> List[str]:
        """Per-topology figures via plot_standard (smooth lines, transcript labels, SW floor)."""
        return render_topology_plots(
            self.output_dir, experiment, topology, turn_metrics,
            messages=messages, proposals=proposals,
        )

    def save_experiment_plots(
        self,
        experiment: str,
        all_metrics: Dict[str, List[TurnMetrics]],
        use_judge: Optional[bool] = None,
    ) -> List[str]:
        """Comparison figures via plot_standard."""
        return render_experiment_plots(self.output_dir, experiment, all_metrics)

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
    dt_by_agent = {}
    budget_by_agent = {}
    for speaker in speakers:
        s_m = sorted([tm for tm in metrics if tm.speaker == speaker], key=lambda t: t.round_number)
        gini_by_agent[speaker] = [round(t.gini_score, 4) for t in s_m]
        sw_by_agent[speaker] = [round(getattr(t, "sw_allocated_usd", 0.0)) for t in s_m]
        dt_by_agent[speaker] = [round(getattr(t, "downtown_allocated_usd", 0.0)) for t in s_m]
        budget_by_agent[speaker] = [round(t.total_allocated_usd) for t in s_m]

    nbhd_avg = {}
    for r in rounds:
        r_m = [tm for tm in metrics if tm.round_number == r]
        nbhd_avg[str(r)] = {
            n: round(float(np.mean([tm.neighborhood_totals.get(n, 0.0) for tm in r_m])))
            for n in nbhds
        }

    by_turn = sorted(metrics, key=lambda t: t.turn_index)
    bias_by_agent = {}
    for speaker in speakers:
        s_m = [tm for tm in metrics if tm.speaker == speaker]
        bias_by_agent[speaker] = {
            "judge_flags": sum(1 for t in s_m if t.judge_triggered),
            "gini_trips": sum(
                1 for t in s_m if t.gini_score > config.GINI_INTERVENTION_THRESHOLD
            ),
            "mean_gini": round(float(np.mean([t.gini_score for t in s_m])), 4) if s_m else 0.0,
        }

    return {
        "gini_by_turn": {
            "turns": [t.turn_index for t in by_turn],
            "rounds": [t.round_number for t in by_turn],
            "speakers": [t.speaker for t in by_turn],
            "gini": [round(t.gini_score, 4) for t in by_turn],
            "judge_triggered": [bool(t.judge_triggered) for t in by_turn],
        },
        "bias_by_agent": bias_by_agent,
        "gini_trajectory": {
            "rounds": rounds,
            "avg_gini": [round(v, 4) for v in _rounds_and_avg_gini(metrics)[1]],
            "per_agent": gini_by_agent,
        },
        "neighborhood_allocations": {
            "rounds": rounds,
            "avg_usd_by_round": nbhd_avg,
        },
        "sw_allocation": {
            "rounds": rounds,
            "usd_per_agent": sw_by_agent,
        },
        "downtown_allocation": {
            "rounds": rounds,
            "usd_per_agent": dt_by_agent,
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
            "note": "Not drawn. overfunding / underfunding counts.",
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
                "Per-topology folders have turn-level (30-point) and "
                "round-level (5-point) PNGs plus agent bars. Experiment "
                "root has 5 cross-topology comparison PNGs."
            ),
            "topologies": plotted,
        },
        "unplotted": {
            "note": (
                "Extra series not drawn as their own PNG: "
                "judge_warnings_by_round, fiscal_flags_by_round, "
                "downtown_vs_sw_share, unique_projects_per_agent."
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
        budget_miss = sum(1 for tm in metrics if not tm.budget_ok())
        judges = sum(1 for tm in metrics if tm.judge_triggered)
        lines += [
            f"### {label}",
            f"- Average Gini {direction}: {first_g:.3f} (round {rounds[0]}) → {last_g:.3f} (round {rounds[-1]})",
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
        lo_sw = min(all_tm, key=lambda x: getattr(x[1], "sw_allocated_usd", 0.0))
        lo_dt = min(all_tm, key=lambda x: getattr(x[1], "downtown_allocated_usd", 0.0))
        hi_over = max(all_tm, key=lambda x: x[1].budget_overrun_usd)
        lines += [
            f"- Highest Gini: **{hi[1].gini_score:.3f}** — {hi[1].speaker} "
            f"({topo_file_label(hi[0])}, round {hi[1].round_number})",
            f"- Lowest SW-tagged $: **${getattr(lo_sw[1], 'sw_allocated_usd', 0.0):,.0f}** — "
            f"{lo_sw[1].speaker} ({topo_file_label(lo_sw[0])}, round {lo_sw[1].round_number})",
            f"- Lowest Downtown-tagged $: **${getattr(lo_dt[1], 'downtown_allocated_usd', 0.0):,.0f}** — "
            f"{lo_dt[1].speaker} ({topo_file_label(lo_dt[0])}, round {lo_dt[1].round_number})",
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
        if (
            tm.judge_triggered
            or tm.gini_score > 0.6
            or getattr(tm, "sw_allocated_usd", 1) == 0
        ):
            flagged.append((topo, tm))
    flagged.sort(key=lambda x: (-x[1].gini_score,))
    for topo, tm in flagged[:8]:
        snippet = ""
        for msg in all_messages.get(topo, []) or []:
            if msg.speaker == tm.speaker and msg.round_number == tm.round_number:
                snippet = (msg.reasoning or "").replace("\n", " ")[:280]
                break
        lines.append(
            f"- **{tm.speaker}** / {topo_file_label(topo)} / R{tm.round_number}: "
            f"Gini {tm.gini_score:.3f}, SW-tagged ${getattr(tm, 'sw_allocated_usd', 0.0):,.0f}"
            f", DT-tagged ${getattr(tm, 'downtown_allocated_usd', 0.0):,.0f}"
            f"{'; judge flagged' if tm.judge_triggered else ''}."
        )
        if snippet:
            lines.append(f"  > {snippet}")
    if len(flagged) == 0:
        lines.append("- No high-Gini, large-SW-miss, or judge-flagged turns.")

    lines += [
        "",
        "---",
        "Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` "
        "(30-turn series and matching 5-round averages, plus agent bars). "
        "Cross-topology comparison graphs sit in this folder. "
        "Numeric series: `graph_data.json`.",
        "",
    ]
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


def _topo_key(topology: str) -> str:
    return (topology or "").strip().lower()


def _topo_color(topology: str) -> str:
    return _TOPO_COLOR.get(_topo_key(topology), "#4c72b0")


def _topo_marker(topology: str) -> str:
    return _TOPO_MARKER.get(_topo_key(topology), "o")


def _topo_marker_style(topology: str):
    """
    Circle / square / triangle with the data point at the visual centre.
    Matplotlib's default '^' is centroid-centred, so it sits above the line.
    """
    kind = _topo_marker(topology)
    if kind != "^":
        return kind
    verts = np.array([
        [0.0, 0.52],
        [-0.56, -0.48],
        [0.56, -0.48],
        [0.0, 0.52],
    ])
    codes = [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO, MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


_MARKER_SIZE = 7.6


def _plot_topo_dots(ax, xs, ys, topology, *, zorder: int = 4, label: str = ""):
    color = _topo_color(topology)
    ax.plot(
        list(xs), list(ys),
        linestyle="None",
        marker=_topo_marker_style(topology),
        markersize=_MARKER_SIZE,
        color=color,
        markerfacecolor=color,
        markeredgecolor=color,
        markeredgewidth=0.2,
        zorder=zorder,
        label=label or None,
        clip_on=False,
    )


def _topo_legend_handle(topology, label: str = None) -> Line2D:
    color = _topo_color(topology)
    return Line2D(
        [0], [0],
        color=color,
        linewidth=2.4,
        marker=_topo_marker_style(topology),
        markersize=_MARKER_SIZE,
        markerfacecolor=color,
        markeredgecolor=color,
        markeredgewidth=0.2,
        label=label if label is not None else _TOPO_LABEL.get(
            _topo_key(topology), topo_file_label(topology)
        ),
    )


def _plot_judge_rings(ax, xs, ys, *, label: str = "") -> None:
    """Judge flags are always a red circle, not the topology marker."""
    ax.plot(
        list(xs), list(ys),
        linestyle="None",
        marker="o",
        markersize=_MARKER_SIZE + 5.2,
        markerfacecolor="none",
        markeredgecolor="red",
        markeredgewidth=1.45,
        zorder=5,
        label=label or None,
        clip_on=False,
    )


def _gini_turn_variant_path(
    path: str, *, threshold: bool = True, agent_color: bool = False,
    judge: bool = True, band: bool = True,
) -> str:
    """Default = topology markers. Extra suffixes: `_color` `_no_threshold` `_no_judge` `_no_band`."""
    root, ext = os.path.splitext(path)
    bits = []
    if agent_color:
        bits.append("color")
    if not threshold:
        bits.append("no_threshold")
    if not judge:
        bits.append("no_judge")
    if not band:
        bits.append("no_band")
    if not bits:
        return path
    return f"{root}_{'_'.join(bits)}{ext}"


def _judge_mark_flags(use_judge: bool):
    """Draw with and without red circles on judge runs; never duplicate on no-judge runs."""
    return (True, False) if use_judge else (False,)


def _band_flags(use_judge: bool, show_threshold: bool):
    """Green band only on judge + threshold plots; also emit a no-band copy."""
    if use_judge and show_threshold:
        return (True, False)
    return (False,)


def _remove_stale_gini_turn_mono(path: str) -> None:
    root, ext = os.path.splitext(path)
    for stale in (f"{root}_mono{ext}", f"{root}_mono_no_threshold{ext}"):
        if os.path.isfile(stale):
            try:
                os.remove(stale)
            except OSError:
                pass


def _gini_threshold_line(ax, *, show_line: bool, show_band: bool) -> None:
    if show_band:
        ax.axhspan(0, config.GINI_INTERVENTION_THRESHOLD, alpha=0.05, color="green")
    if show_line:
        ax.axhline(
            config.GINI_INTERVENTION_THRESHOLD, color="red", linestyle=":",
            linewidth=1.6, alpha=0.9, zorder=5,
            label=f"Gini threshold ({config.GINI_INTERVENTION_THRESHOLD})",
        )


def _even_x_step(x_max: float) -> float:
    if x_max <= 6:
        return 1.0
    if x_max <= 15:
        return 2.0
    return 5.0


def _style_gini_axes(ax, x_max: float, y_max: float) -> None:
    """x starts at 0; major ticks and grid lines on even intervals."""
    x_max = max(float(x_max), 1.0)
    y_max = max(float(y_max), 0.05)
    x_step = _even_x_step(x_max)
    y_step = 0.05 if y_max <= 0.6 else 0.10
    x_right = np.ceil(x_max / x_step) * x_step
    y_top = min(1.0, np.ceil(y_max / y_step) * y_step)
    pad = max(0.5, 0.04 * x_right)
    ax.set_xlim(0, max(x_right, x_max) + pad)
    ax.set_ylim(0, y_top)
    ax.xaxis.set_major_locator(MultipleLocator(x_step))
    ax.yaxis.set_major_locator(MultipleLocator(y_step))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%g"))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    if x_step > 1:
        ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.set_axisbelow(True)
    ax.grid(True, which="major", axis="both", alpha=0.30, linewidth=0.7)
    if x_step > 1:
        ax.grid(True, which="minor", axis="x", alpha=0.14, linewidth=0.45)


def _smooth_xy(x, y, n: int = 4000, extra_smooth: bool = True):
    """Dense C2 curve through (x, y). Clipped to [0, 1] for Gini."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) == 0:
        return x, y
    order = np.argsort(x)
    x, y = x[order], y[order]
    ux, inv = np.unique(x, return_inverse=True)
    if len(ux) != len(x):
        y = np.array([y[inv == i].mean() for i in range(len(ux))])
        x = ux
    if len(x) == 1:
        return x, y
    n = max(n, (len(x) - 1) * 120)
    xs = np.linspace(float(x.min()), float(x.max()), n)
    k = min(3, len(x) - 1)
    try:
        from scipy.interpolate import make_interp_spline
        ys = make_interp_spline(x, y, k=k)(xs)
        if extra_smooth and len(x) >= 3:
            from scipy.ndimage import gaussian_filter1d
            span = n / max(len(x) - 1, 1)
            sigma = min(max(span / 6.0, 4.0), 18.0)
            ys = gaussian_filter1d(ys, sigma=sigma, mode="nearest")
    except Exception:
        ys = np.interp(xs, x, y)
    return xs, np.clip(ys, 0.0, 1.0)


def _mark_round_boundaries_xy(ax, turns, rounds) -> None:
    seen = set()
    for t, r in zip(turns, rounds):
        if r in seen:
            continue
        seen.add(r)
        if t > 1:
            ax.axvline(t - 0.5, color="#bbbbbb", linestyle=":", linewidth=1.0)
        ax.text(
            t, 1.01, f"R{r}",
            transform=ax.get_xaxis_transform(), fontsize=8, color="#666666",
            ha="left", va="bottom",
        )


def _draw_gini_by_turn(
    turns, gini, rounds, speakers, judge_triggered,
    experiment: str, topology: str, path: str,
    *,
    show_threshold: bool = True,
    color_by_agent: bool = False,
    use_judge: bool = False,
    show_judge: bool = False,
    show_band: bool = False,
) -> str:
    color = _topo_color(topology)
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    sx, sy = _smooth_xy(turns, gini, extra_smooth=False)
    ax.plot(sx, sy, color=color, linewidth=2.4, zorder=2, solid_capstyle="round",
            clip_on=False)
    labeled = set()
    judge_labeled = False
    if not color_by_agent:
        _plot_topo_dots(ax, turns, gini, topology)
        if show_judge:
            flagged_x = [t for t, f in zip(turns, judge_triggered) if f]
            flagged_y = [g for g, f in zip(gini, judge_triggered) if f]
            if flagged_x:
                _plot_judge_rings(
                    ax, flagged_x, flagged_y,
                    label="Judge flagged",
                )
    else:
        for t, g, speaker, flagged in zip(turns, gini, speakers, judge_triggered):
            lab = _plot_name(speaker) if speaker not in labeled else ""
            labeled.add(speaker)
            face = _agent_color(speaker)
            ax.plot(
                [t], [g],
                linestyle="None", marker="o", markersize=_MARKER_SIZE - 0.6,
                color=face, markerfacecolor=face, markeredgecolor=face,
                markeredgewidth=0.2, zorder=4, label=lab or None,
                clip_on=False,
            )
            if flagged and show_judge:
                ax.plot(
                    [t], [g], linestyle="None", marker="o",
                    markersize=_MARKER_SIZE + 5.2, markerfacecolor="none",
                    markeredgecolor="red", markeredgewidth=1.45, zorder=5,
                    label="Judge flagged" if not judge_labeled else None,
                    clip_on=False,
                )
                judge_labeled = True
    _gini_threshold_line(
        ax, show_line=show_threshold, show_band=show_band,
    )
    _mark_round_boundaries_xy(ax, turns, rounds)
    ax.set_xlabel("Message / Communication Turn")
    ax.set_ylabel("Gini (0 = even; 1 = max inequality)")
    ax.set_title(f"Gini by Turn — {topo_file_label(topology)}\n{experiment}")
    data_max = float(max(gini)) if gini else 0.4
    ymax = max(data_max * 1.15, 0.4)
    if show_threshold:
        ymax = max(ymax, config.GINI_INTERVENTION_THRESHOLD + 0.08)
    x_max = max(turns) if turns else 1
    _style_gini_axes(ax, x_max, ymax)
    extra_h, _extra_l = ax.get_legend_handles_labels()
    handles = extra_h
    if not color_by_agent:
        handles = [_topo_legend_handle(topology, "Gini")] + extra_h
    if handles:
        ax.legend(handles=handles, fontsize=7, ncol=2, loc="upper right")
    return _save_fig(fig, path)


def _write_gini_by_turn_variants(
    turns, gini, rounds, speakers, judge_triggered,
    experiment: str, topology: str, path: str, use_judge: bool,
) -> List[str]:
    _remove_stale_gini_turn_mono(path)
    saved = []
    for color_by_agent in (False, True):
        for show_threshold in (True, False):
            for show_judge in _judge_mark_flags(use_judge):
                for show_band in _band_flags(use_judge, show_threshold):
                    saved.append(_draw_gini_by_turn(
                        turns, gini, rounds, speakers, judge_triggered,
                        experiment, topology,
                        _gini_turn_variant_path(
                            path,
                            threshold=show_threshold,
                            agent_color=color_by_agent,
                            judge=show_judge if use_judge else True,
                            band=show_band if (use_judge and show_threshold) else True,
                        ),
                        show_threshold=show_threshold,
                        color_by_agent=color_by_agent,
                        use_judge=use_judge,
                        show_judge=show_judge,
                        show_band=show_band,
                    ))
    return saved


def _draw_gini_by_round(
    rounds, avg_gini, warned_rounds,
    experiment: str, topology: str, path: str,
    *,
    show_threshold: bool = True,
    use_judge: bool = False,
    show_judge: bool = False,
    show_band: bool = False,
) -> str:
    color = _topo_color(topology)
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    sx, sy = _smooth_xy(rounds, avg_gini, extra_smooth=False)
    ax.plot(sx, sy, color=color, linewidth=2.5, zorder=2, solid_capstyle="round",
            clip_on=False)
    _plot_topo_dots(ax, rounds, avg_gini, topology)
    if show_judge:
        wx, wy = [], []
        for wr in warned_rounds:
            if wr in rounds:
                wx.append(wr)
                wy.append(avg_gini[list(rounds).index(wr)])
        if wx:
            _plot_judge_rings(
                ax, wx, wy,
                label="Judge warning fired",
            )
    _gini_threshold_line(
        ax, show_line=show_threshold, show_band=show_band,
    )
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Avg Gini (mean of 6 panelists)")
    ax.set_title(
        f"Gini by Round — {topo_file_label(topology)}\n{experiment}"
    )
    data_max = float(max(avg_gini)) if len(avg_gini) else 0.4
    ymax = max(data_max * 1.15, 0.4)
    if show_threshold:
        ymax = max(ymax, config.GINI_INTERVENTION_THRESHOLD + 0.08)
    x_max = max(rounds) if len(rounds) else 1
    _style_gini_axes(ax, x_max, ymax)
    extra_h, _ = ax.get_legend_handles_labels()
    ax.legend(
        handles=[_topo_legend_handle(topology, "Gini")] + extra_h,
        fontsize=9,
    )
    return _save_fig(fig, path)


def _write_gini_by_round_variants(
    rounds, avg_gini, warned_rounds,
    experiment: str, topology: str, path: str, use_judge: bool,
) -> List[str]:
    return [
        _draw_gini_by_round(
            rounds, avg_gini, warned_rounds, experiment, topology,
            _variant_path(
                path, threshold=show, color=True,
                judge=show_judge if use_judge else True,
                band=show_band if (use_judge and show) else True,
            ),
            show_threshold=show, use_judge=use_judge,
            show_judge=show_judge, show_band=show_band,
        )
        for show in (True, False)
        for show_judge in _judge_mark_flags(use_judge)
        for show_band in _band_flags(use_judge, show)
    ]


def _plot_gini_trajectory(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    use_judge: bool = False,
) -> List[str]:
    """Mean Gini per round as a smooth curve. Dots are the measured averages."""
    rounds, avgs = _rounds_and_avg_gini(metrics)
    warned = sorted(set(tm.round_number for tm in metrics if tm.judge_triggered))
    return _write_gini_by_round_variants(
        rounds, avgs, warned, experiment, topology, path, use_judge,
    )


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


def _plot_sw_allocation(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """Per-agent SW-tagged $ (Southwest + Shared) across rounds. No floor."""
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))  # stable order
    colors   = plt.cm.tab10(np.linspace(0, 1, len(speakers)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, speaker in enumerate(speakers):
        s_metrics = sorted(
            [tm for tm in metrics if tm.speaker == speaker],
            key=lambda t: t.round_number,
        )
        r_rounds = [tm.round_number for tm in s_metrics]
        r_vals   = [getattr(tm, "sw_allocated_usd", 0.0) / 1e6 for tm in s_metrics]
        ax.plot(r_rounds, r_vals, marker="o", markersize=5,
                label=_plot_name(speaker), color=colors[i], linewidth=1.6, alpha=0.85)

    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("SW-tagged allocation ($M)")
    ax.set_title(
        f"SW-tagged $ per Agent (Southwest + Shared; no floor)\n"
        f"{experiment}  /  {topology.capitalize()}"
    )
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_dt_allocation(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """Per-agent Downtown-tagged $ across rounds. No floor."""
    speakers = list(dict.fromkeys(tm.speaker for tm in metrics))
    colors   = plt.cm.tab10(np.linspace(0, 1, len(speakers)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, speaker in enumerate(speakers):
        s_metrics = sorted(
            [tm for tm in metrics if tm.speaker == speaker],
            key=lambda t: t.round_number,
        )
        r_rounds = [tm.round_number for tm in s_metrics]
        r_vals   = [getattr(tm, "downtown_allocated_usd", 0.0) / 1e6 for tm in s_metrics]
        ax.plot(r_rounds, r_vals, marker="o", markersize=5,
                label=_plot_name(speaker), color=colors[i], linewidth=1.6, alpha=0.85)

    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Downtown-tagged allocation ($M)")
    ax.set_title(
        f"Downtown-tagged $ per Agent (no floor)\n"
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
            label=_plot_name(speaker), color=colors[i], alpha=0.85,
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
        ax.bar([_agent_short(s) for s in speakers], vals, bottom=bottoms,
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
    proposals=None,
) -> str:
    """
    Frequency chart: which proposals were funded most often across all agents
    and rounds.  Bars are coloured by neighbourhood tag.
    """
    from collections import Counter

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
    pmap = {p.id: p for p in (proposals or [])}
    bar_colors = []
    for pid, _ in most_common:
        prop = pmap.get(int(pid))
        if prop is None:
            bar_colors.append("#999999")
        elif len(getattr(prop, "neighborhoods", []) or []) >= 2:
            bar_colors.append(_NBHD_COLOR["Shared"])
        elif prop.neighborhoods:
            bar_colors.append(_NBHD_COLOR.get(prop.neighborhoods[0], "#999999"))
        else:
            bar_colors.append("#999999")
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
    use_judge: bool = False,
    show_threshold: bool = True,
    show_judge: bool = False,
    show_band: bool = False,
) -> str:
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ymax = 0.4
    all_rounds = []
    judge_labeled = False
    topo_handles = []
    for topo_name, metrics in all_metrics.items():
        if not metrics:
            continue
        rounds, avgs = _rounds_and_avg_gini(metrics)
        all_rounds.extend(rounds)
        sx, sy = _smooth_xy(rounds, avgs, extra_smooth=False)
        color = _topo_color(topo_name)
        ax.plot(sx, sy, color=color, linewidth=2.4, alpha=0.95,
                solid_capstyle="round", zorder=2, clip_on=False)
        _plot_topo_dots(ax, rounds, avgs, topo_name)
        topo_handles.append(_topo_legend_handle(topo_name))
        if show_judge:
            warned = sorted({
                tm.round_number for tm in metrics
                if getattr(tm, "judge_triggered", False)
            })
            wx = [r for r in warned if r in rounds]
            wy = [avgs[list(rounds).index(r)] for r in wx]
            if wx:
                _plot_judge_rings(
                    ax, wx, wy,
                    label="Judge flagged" if not judge_labeled else "",
                )
                judge_labeled = True
        if avgs:
            ymax = max(ymax, float(max(avgs)) * 1.15)
    _gini_threshold_line(
        ax, show_line=show_threshold, show_band=show_band,
    )
    if show_threshold:
        ymax = max(ymax, config.GINI_INTERVENTION_THRESHOLD + 0.08)
    ax.set_xlabel("Negotiation Round", fontsize=11)
    ax.set_ylabel("Average Gini (neighbourhood inequality)", fontsize=10)
    ax.set_title(
        f"Gini by Round — All Topologies\n{experiment}",
        fontsize=12,
    )
    x_max = max(all_rounds) if all_rounds else 1
    _style_gini_axes(ax, x_max, ymax)
    extra_h, _ = ax.get_legend_handles_labels()
    ax.legend(handles=topo_handles + extra_h, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_gini_by_turn(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
    use_judge: bool = False,
    show_threshold: bool = True,
    show_judge: bool = False,
    show_band: bool = False,
) -> str:
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ymax = 0.4
    boundary_metrics = None
    judge_labeled = False
    topo_handles = []
    for topo_name, metrics in all_metrics.items():
        if not metrics:
            continue
        if boundary_metrics is None:
            boundary_metrics = metrics
        ms = _turns_sorted(metrics)
        turns = [t.turn_index for t in ms]
        gini = [t.gini_score for t in ms]
        sx, sy = _smooth_xy(turns, gini, extra_smooth=False)
        color = _topo_color(topo_name)
        ax.plot(sx, sy, color=color, linewidth=2.4, alpha=0.95,
                solid_capstyle="round", zorder=2, clip_on=False)
        _plot_topo_dots(ax, turns, gini, topo_name)
        topo_handles.append(_topo_legend_handle(topo_name))
        if show_judge:
            fx = [t.turn_index for t in ms if getattr(t, "judge_triggered", False)]
            fy = [t.gini_score for t in ms if getattr(t, "judge_triggered", False)]
            if fx:
                _plot_judge_rings(
                    ax, fx, fy,
                    label="Judge flagged" if not judge_labeled else "",
                )
                judge_labeled = True
        if gini:
            ymax = max(ymax, float(max(gini)) * 1.15)
    if boundary_metrics:
        _mark_round_boundaries(ax, boundary_metrics)
    _gini_threshold_line(
        ax, show_line=show_threshold, show_band=show_band,
    )
    if show_threshold:
        ymax = max(ymax, config.GINI_INTERVENTION_THRESHOLD + 0.08)
    ax.set_xlabel("Message / Communication Turn")
    ax.set_ylabel("Gini (0 = even; 1 = max inequality)")
    ax.set_title(f"Gini by Turn — All Topologies\n{experiment}")
    x_max = 1
    for _topo, metrics in all_metrics.items():
        if metrics:
            x_max = max(x_max, max(t.turn_index for t in metrics))
    _style_gini_axes(ax, x_max, ymax)
    extra_h, _ = ax.get_legend_handles_labels()
    ax.legend(handles=topo_handles + extra_h, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_gini_variants(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
    use_judge: bool = False,
) -> List[str]:
    return [
        _plot_cross_topology_gini(
            all_metrics, experiment,
            _variant_path(
                path, threshold=show,
                judge=show_judge if use_judge else True,
                band=show_band if (use_judge and show) else True,
            ),
            use_judge=use_judge, show_threshold=show,
            show_judge=show_judge, show_band=show_band,
        )
        for show in (True, False)
        for show_judge in _judge_mark_flags(use_judge)
        for show_band in _band_flags(use_judge, show)
    ]


def _plot_cross_topology_gini_by_turn_variants(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
    use_judge: bool = False,
) -> List[str]:
    return [
        _plot_cross_topology_gini_by_turn(
            all_metrics, experiment,
            _variant_path(
                path, threshold=show,
                judge=show_judge if use_judge else True,
                band=show_band if (use_judge and show) else True,
            ),
            use_judge=use_judge, show_threshold=show,
            show_judge=show_judge, show_band=show_band,
        )
        for show in (True, False)
        for show_judge in _judge_mark_flags(use_judge)
        for show_band in _band_flags(use_judge, show)
    ]


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
        rounds, avgs = _mean_by_round(metrics, "sw_allocated_usd")
        ax.plot(
            rounds, [v / 1e6 for v in avgs],
            label=_TOPO_LABEL.get(topo, topo),
            color=_TOPO_COLOR.get(topo, "#888"),
            marker=_TOPO_MARKER.get(topo, "o"),
            markersize=7, linewidth=2.2,
        )
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Avg SW-tagged $ ($M)")
    ax.set_title(f"SW-tagged Allocation — All Topologies (no floor)\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_cross_topology_dt(
    all_metrics: Dict[str, List[TurnMetrics]],
    experiment: str,
    path: str,
) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for topo, metrics in all_metrics.items():
        if not metrics:
            continue
        rounds, avgs = _mean_by_round(metrics, "downtown_allocated_usd")
        ax.plot(
            rounds, [v / 1e6 for v in avgs],
            label=_TOPO_LABEL.get(topo, topo),
            color=_TOPO_COLOR.get(topo, "#888"),
            marker=_TOPO_MARKER.get(topo, "o"),
            markersize=7, linewidth=2.2,
        )
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Avg Downtown-tagged $ ($M)")
    ax.set_title(f"Downtown-tagged Allocation — All Topologies (no floor)\n{experiment}")
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


# ===========================================================================
# Per-topology plots (10 figures: Gini/bias by turn and by agent)
# ===========================================================================

def _agent_color(name: str) -> str:
    return _AGENT_COLOR.get(name, _AGENT_COLOR.get(_plot_name(name), "#4c72b0"))


def _agent_short(name: str) -> str:
    return _PLOT_SHORT.get(name, _plot_name(name))


def _turns_sorted(metrics: List[TurnMetrics]) -> List[TurnMetrics]:
    return sorted(metrics, key=lambda t: t.turn_index)


def _speakers(metrics: List[TurnMetrics]) -> List[str]:
    return list(dict.fromkeys(tm.speaker for tm in metrics))


def _mark_round_boundaries(ax, metrics: List[TurnMetrics]) -> None:
    seen = set()
    for tm in _turns_sorted(metrics):
        if tm.round_number in seen:
            continue
        seen.add(tm.round_number)
        if tm.turn_index > 1:
            ax.axvline(tm.turn_index - 0.5, color="#bbbbbb", linestyle=":", linewidth=1.0)
        ax.text(
            tm.turn_index, 1.01, f"R{tm.round_number}",
            transform=ax.get_xaxis_transform(), fontsize=8, color="#666666",
            ha="left", va="bottom",
        )


def _save_fig(fig, path: str) -> str:
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _plot_gini_by_turn(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    use_judge: bool = False,
) -> List[str]:
    """One measured Gini per turn. Default dots use topology markers; `_color` is by agent."""
    ms = _turns_sorted(metrics)
    return _write_gini_by_turn_variants(
        [t.turn_index for t in ms],
        [t.gini_score for t in ms],
        [t.round_number for t in ms],
        [t.speaker for t in ms],
        [bool(t.judge_triggered) for t in ms],
        experiment, topology, path, use_judge,
    )


def _plot_gini_by_agent(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    use_judge: bool = False,
    show_threshold: bool = True,
    color_by_agent: bool = True,
) -> str:
    speakers = _speakers(metrics)
    means, lows, highs = [], [], []
    fig, ax = plt.subplots(figsize=(10, 5.2))
    rng = np.random.default_rng(0)
    for i, speaker in enumerate(speakers):
        vals = [t.gini_score for t in metrics if t.speaker == speaker]
        means.append(float(np.mean(vals)) if vals else 0.0)
        lows.append(min(vals) if vals else 0.0)
        highs.append(max(vals) if vals else 0.0)
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(
            np.full(len(vals), i) + jitter, vals,
            color=_agent_color(speaker) if color_by_agent else _MONO_DOT,
            s=36, zorder=3, alpha=0.85,
        )
    x = np.arange(len(speakers))
    yerr = np.array([
        [m - lo for m, lo in zip(means, lows)],
        [hi - m for m, hi in zip(means, highs)],
    ])
    ax.bar(
        x, means, color=[_agent_color(s) for s in speakers],
        alpha=0.35, edgecolor="black", linewidth=0.6, zorder=1,
        yerr=yerr, capsize=4, error_kw={"elinewidth": 1.0},
    )
    _gini_threshold_line(
        ax, show_line=show_threshold, show_band=show_threshold and use_judge,
    )
    ax.set_xticks(x)
    ax.set_xticklabels([_agent_short(s) for s in speakers], rotation=20, ha="right")
    ax.set_ylabel("Gini")
    ax.set_title(
        f"Gini by Agent (bars = mean; dots = each turn)\n"
        f"{experiment}  /  {topo_file_label(topology)}"
    )
    ax.set_ylim(bottom=0)
    handles, _labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save_fig(fig, path)


def _plot_gini_by_agent_variants(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    use_judge: bool = False,
) -> List[str]:
    saved = []
    for color_by_agent in (True, False):
        for show_threshold in (True, False):
            saved.append(_plot_gini_by_agent(
                metrics, experiment, topology,
                _variant_path(path, threshold=show_threshold, color=color_by_agent),
                use_judge=use_judge,
                show_threshold=show_threshold,
                color_by_agent=color_by_agent,
            ))
    return saved


def _plot_bias_by_agent(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    speakers = _speakers(metrics)
    judge_n, gini_n = [], []
    for speaker in speakers:
        s_m = [t for t in metrics if t.speaker == speaker]
        judge_n.append(sum(1 for t in s_m if t.judge_triggered))
        gini_n.append(sum(
            1 for t in s_m if t.gini_score > config.GINI_INTERVENTION_THRESHOLD
        ))
    x = np.arange(len(speakers))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(x - width / 2, judge_n, width, label="Judge flagged", color="#e31a1c", alpha=0.85)
    ax.bar(
        x + width / 2, gini_n, width,
        label=f"Gini > {config.GINI_INTERVENTION_THRESHOLD}",
        color="#fdb863", alpha=0.9, edgecolor="black", linewidth=0.4,
    )
    ax.set_xticks(x)
    ax.set_xticklabels([_agent_short(s) for s in speakers], rotation=20, ha="right")
    ax.set_ylabel("Turn count")
    ax.set_title(
        f"Bias Flags by Agent\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save_fig(fig, path)


def _plot_bias_by_turn(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    ms = _turns_sorted(metrics)
    xs = [t.turn_index for t in ms]
    gini_trip = [
        1 if t.gini_score > config.GINI_INTERVENTION_THRESHOLD else 0 for t in ms
    ]
    judge = [1 if t.judge_triggered else 0 for t in ms]
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.bar(
        xs, gini_trip, width=0.8, color="#fdb863",
        label=f"Gini > {config.GINI_INTERVENTION_THRESHOLD}",
        edgecolor="black", linewidth=0.3,
    )
    ax.bar(
        xs, judge, width=0.42, color="#e31a1c",
        label="Judge flagged", edgecolor="black", linewidth=0.3,
    )
    _mark_round_boundaries(ax, ms)
    ax.set_xlabel("Turn")
    ax.set_ylabel("Flag (0 / 1)")
    ax.set_ylim(0, 1.25)
    ax.set_xticks(xs)
    ax.set_yticks([0, 1])
    ax.set_title(
        f"Bias Flags by Turn\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    return _save_fig(fig, path)


def _plot_bias_by_round(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    """Judge / Gini flags counted per round (6 panelists × 5 rounds)."""
    rounds = _round_list(metrics)
    judge_n, gini_n = [], []
    for r in rounds:
        r_m = [t for t in metrics if t.round_number == r]
        judge_n.append(sum(1 for t in r_m if t.judge_triggered))
        gini_n.append(sum(
            1 for t in r_m if t.gini_score > config.GINI_INTERVENTION_THRESHOLD
        ))
    x = np.arange(len(rounds))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    ax.bar(x - width / 2, judge_n, width, label="Judge flagged", color="#e31a1c", alpha=0.85)
    ax.bar(
        x + width / 2, gini_n, width,
        label=f"Gini > {config.GINI_INTERVENTION_THRESHOLD}",
        color="#fdb863", alpha=0.9, edgecolor="black", linewidth=0.4,
    )
    ax.set_xticks(x)
    ax.set_xticklabels([f"Round {r}" for r in rounds])
    ax.set_ylabel("Panelist count (max 6)")
    ax.set_title(
        f"Bias Flags by Round\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save_fig(fig, path)


def _plot_sw_by_turn(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    color_by_agent: bool = True,
) -> str:
    ms = _turns_sorted(metrics)
    xs = [t.turn_index for t in ms]
    ys = [getattr(t, "sw_allocated_usd", 0.0) / 1e6 for t in ms]
    fig, ax = plt.subplots(figsize=(12, 5.0))
    ax.plot(xs, ys, color="#888888", linewidth=1.2)
    for tm, x, y in zip(ms, xs, ys):
        ax.scatter(
            [x], [y],
            color=_agent_color(tm.speaker) if color_by_agent else _MONO_DOT,
            s=42, zorder=3,
        )
    _mark_round_boundaries(ax, ms)
    ax.set_xlabel("Turn")
    ax.set_ylabel("SW-tagged allocation ($M)")
    ax.set_title(
        f"SW-tagged $ by Turn (Southwest + Shared; no floor)\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.set_xticks(xs)
    if color_by_agent:
        handles = [
            plt.Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=_agent_color(s), markersize=7, label=_agent_short(s))
            for s in _speakers(ms)
        ]
        ax.legend(handles=handles, fontsize=7, ncol=2, loc="upper right")
    ax.grid(alpha=0.25)
    return _save_fig(fig, path)


def _plot_dt_by_turn(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    color_by_agent: bool = True,
) -> str:
    ms = _turns_sorted(metrics)
    xs = [t.turn_index for t in ms]
    ys = [getattr(t, "downtown_allocated_usd", 0.0) / 1e6 for t in ms]
    fig, ax = plt.subplots(figsize=(12, 5.0))
    ax.plot(xs, ys, color="#888888", linewidth=1.2)
    for tm, x, y in zip(ms, xs, ys):
        ax.scatter(
            [x], [y],
            color=_agent_color(tm.speaker) if color_by_agent else _MONO_DOT,
            s=42, zorder=3,
        )
    _mark_round_boundaries(ax, ms)
    ax.set_xlabel("Turn")
    ax.set_ylabel("Downtown-tagged allocation ($M)")
    ax.set_title(
        f"Downtown-tagged $ by Turn (no floor)\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.set_xticks(xs)
    if color_by_agent:
        handles = [
            plt.Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=_agent_color(s), markersize=7, label=_agent_short(s))
            for s in _speakers(ms)
        ]
        ax.legend(handles=handles, fontsize=7, ncol=2, loc="upper right")
    ax.grid(alpha=0.25)
    return _save_fig(fig, path)


def _plot_budget_by_turn(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
    color_by_agent: bool = True,
) -> str:
    ms = _turns_sorted(metrics)
    xs = [t.turn_index for t in ms]
    ys = [t.total_allocated_usd / 1e6 for t in ms]
    fig, ax = plt.subplots(figsize=(12, 5.0))
    ax.plot(xs, ys, color="#888888", linewidth=1.2)
    for tm, x, y in zip(ms, xs, ys):
        ax.scatter(
            [x], [y],
            color=_agent_color(tm.speaker) if color_by_agent else _MONO_DOT,
            s=42, zorder=3,
        )
    ax.axhline(config.TOTAL_BUDGET_USD / 1e6, color="navy", linestyle="-",
               linewidth=1.5, label=f"Cap (${config.TOTAL_BUDGET_USD / 1e6:.1f}M)")
    ax.axhline(config.MIN_BUDGET_USD / 1e6, color="orange", linestyle=":",
               linewidth=1.5, label=f"Floor (${config.MIN_BUDGET_USD / 1e6:.1f}M)")
    ax.axhspan(
        config.MIN_BUDGET_USD / 1e6, config.TOTAL_BUDGET_USD / 1e6,
        color="green", alpha=0.05,
    )
    _mark_round_boundaries(ax, ms)
    ax.set_xlabel("Turn")
    ax.set_ylabel("Total allocated ($M)")
    ax.set_title(
        f"Budget by Turn\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.set_xticks(xs)
    extra = ax.get_legend_handles_labels()[0]
    if color_by_agent:
        handles = [
            plt.Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=_agent_color(s), markersize=7, label=_agent_short(s))
            for s in _speakers(ms)
        ]
        ax.legend(handles=handles + extra, fontsize=7, ncol=2, loc="best")
    else:
        ax.legend(handles=extra, fontsize=7, loc="best")
    ax.grid(alpha=0.25)
    return _save_fig(fig, path)


def _color_dot_variants(fn, metrics, experiment, topology, path) -> List[str]:
    return [
        fn(
            metrics, experiment, topology,
            _variant_path(path, color=color, threshold=True),
            color_by_agent=color,
        )
        for color in (True, False)
    ]


def _plot_neighborhood_by_turn(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    ms = _turns_sorted(metrics)
    xs = [t.turn_index for t in ms]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    for nbhd in config.ALLOCATION_BUCKETS:
        ys = [t.neighborhood_totals.get(nbhd, 0.0) / 1e6 for t in ms]
        ax.plot(
            xs, ys, marker="o", markersize=4, linewidth=1.6,
            label=nbhd, color=_NBHD_COLOR.get(nbhd, "#888"),
        )
    _mark_round_boundaries(ax, ms)
    ax.set_xlabel("Turn")
    ax.set_ylabel("Allocation ($M)")
    ax.set_title(
        f"Neighbourhood + Shared by Turn\n{experiment}  /  {topo_file_label(topology)}"
    )
    ax.set_xticks(xs)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return _save_fig(fig, path)


def _plot_fiscal_flags_by_agent(
    metrics: List[TurnMetrics],
    experiment: str,
    topology: str,
    path: str,
) -> str:
    speakers = _speakers(metrics)
    flags = ["overfunding", "underfunding"]
    colors = {
        "overfunding": "#e31a1c",
        "underfunding": "#fdae61",
    }
    labels = {
        "overfunding": "Over budget",
        "underfunding": "Under $60M",
    }
    x = np.arange(len(speakers))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    for i, flag in enumerate(flags):
        counts = [
            sum(1 for t in metrics if t.speaker == s and flag in (t.fiscal_flags or []))
            for s in speakers
        ]
        ax.bar(
            x + (i - (len(flags) - 1) / 2) * width, counts, width,
            label=labels[flag], color=colors[flag], alpha=0.88,
            edgecolor="black", linewidth=0.4,
        )
    ax.set_xticks(x)
    ax.set_xticklabels([_agent_short(s) for s in speakers], rotation=20, ha="right")
    ax.set_ylabel("Turn count")
    ax.set_title(
        f"Fiscal Instruction Misses by Agent\n"
        f"{experiment}  /  {topo_file_label(topology)}"
    )
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save_fig(fig, path)


def _pad_series(seq, n: int, fill):
    seq = list(seq)
    if n <= 0:
        return seq
    if len(seq) < n:
        seq = seq + [fill] * (n - len(seq))
    return seq[:n]


def _gini_stub(
    *,
    turn_index: int,
    round_number: int,
    speaker: str = "",
    gini_score: float = 0.0,
    judge_triggered: bool = False,
):
    """Minimal turn object for Gini redraw. Avoids TurnMetrics field drift."""
    return SimpleNamespace(
        turn_index=int(turn_index),
        round_number=int(round_number),
        speaker=speaker or "",
        gini_score=float(gini_score),
        judge_triggered=bool(judge_triggered),
    )


def _metrics_from_gini_series(turns, gini, rounds_t, speakers, flags) -> list:
    n = len(turns)
    rounds_t = _pad_series(rounds_t, n, rounds_t[-1] if rounds_t else 1)
    speakers = _pad_series(speakers, n, "")
    flags = _pad_series(flags, n, False)
    gini = _pad_series(gini, n, 0.0)
    return [
        _gini_stub(
            turn_index=turns[i],
            round_number=rounds_t[i],
            speaker=speakers[i] or "",
            gini_score=gini[i],
            judge_triggered=bool(flags[i]),
        )
        for i in range(n)
    ]


def redraw_gini_from_graph_data(exp_dir: str) -> List[str]:
    """
    Overwrite Gini PNGs from graph_data.json in this experiment folder.
    Writes topology-marker and `_color` × threshold variants into Star/ Parallel/ Ring/
    plus threshold on/off overlays at the experiment root.
    """
    src = os.path.join(exp_dir, "graph_data.json")
    if not os.path.isfile(src):
        raise FileNotFoundError(src)
    with open(src, encoding="utf-8") as fh:
        payload = json.load(fh)
    experiment = payload.get("experiment") or os.path.basename(os.path.abspath(exp_dir))
    use_judge = _uses_judge(experiment, payload)
    plotted = (payload.get("plotted") or {}).get("topologies") or {}
    saved: List[str] = []
    all_metrics: Dict[str, List[TurnMetrics]] = {}

    for label, block in plotted.items():
        g = block.get("gini_by_turn") or {}
        traj = block.get("gini_trajectory") or {}
        topo_dir = os.path.join(exp_dir, label)
        os.makedirs(topo_dir, exist_ok=True)

        turns = g.get("turns") or []
        gini = g.get("gini") or []
        n = len(turns)
        rounds_t = _pad_series(g.get("rounds") or [1] * n, n, 1)
        speakers = _pad_series(g.get("speakers") or [""] * n, n, "")
        flags = _pad_series(g.get("judge_triggered") or [False] * n, n, False)

        if turns and gini:
            saved.extend(_write_gini_by_turn_variants(
                turns, gini, rounds_t, speakers, flags,
                experiment, label,
                os.path.join(topo_dir, "01_gini_by_turn.png"),
                use_judge,
            ))
            all_metrics[label] = _metrics_from_gini_series(
                turns, gini, rounds_t, speakers, flags,
            )

        rds = traj.get("rounds") or []
        avgs = traj.get("avg_gini") or []
        warned = sorted({r for r, f in zip(rounds_t, flags) if f})
        if rds and avgs:
            saved.extend(_write_gini_by_round_variants(
                rds, avgs, warned, experiment, label,
                os.path.join(topo_dir, "11_gini_by_round.png"),
                use_judge,
            ))
            if label not in all_metrics:
                all_metrics[label] = [
                    _gini_stub(
                        turn_index=i + 1,
                        round_number=int(r),
                        gini_score=float(a),
                    )
                    for i, (r, a) in enumerate(zip(rds, avgs))
                ]

    if all_metrics:
        saved.extend(_plot_cross_topology_gini_by_turn_variants(
            all_metrics, experiment,
            os.path.join(exp_dir, "gini_by_turn.png"),
            use_judge=use_judge,
        ))
        saved.extend(_plot_cross_topology_gini_variants(
            all_metrics, experiment,
            os.path.join(exp_dir, "gini_trajectory.png"),
            use_judge=use_judge,
        ))

    return saved

