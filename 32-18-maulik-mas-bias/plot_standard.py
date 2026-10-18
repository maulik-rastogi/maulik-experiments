"""
plot_standard.py — one graph pack for Star / Parallel / Ring.

Used by logger.save_plots (live runs) and by `python3 plot_standard.py outputs`
(overwrite PNGs from graph_data.json, no Ollama).

Per-topology (17):
  01 gini by turn (smooth)     02 gini by agent
  03 bias by agent             04 bias by turn
  05 SW $ by turn (smooth)     06 budget by turn (smooth)
  07 neighbourhood by turn     08 final allocation bars
  09 project frequency         10 fiscal flags by agent
  11 gini by round (smooth)    12 SW $ by round (smooth)
  13 budget by round (smooth)  14 neighbourhood by round
  15 bias by round             16 Downtown $ by turn
  17 Downtown $ by round

Experiment root (7):
  gini_by_turn, gini_trajectory, neighborhood_allocations,
  sw_spend, downtown_spend, budget_utilisation, final_allocation

Speaker labels match transcripts: Sustainability Expert, Financial Expert,
Urban Planner, Citizen (SW Fresno), Citizen (Chinatown),
Citizen (Downtown Fresno).

Floors are drawn only when this codebase defines them in config:
  SW $32.8M, Downtown $18.5M, budget band $60–66.5M, Gini 0.25.
"""

from __future__ import annotations

import json
import logging
import os
from glob import glob
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config

_log = logging.getLogger("plot_standard")

_TOPO_COLOR = {"star": "#d95f02", "parallel": "#1b9e77", "ring": "#7570b3"}
_TOPO_MARKER = {"star": "o", "parallel": "s", "ring": "^"}
_TOPO_LABEL = {"star": "Star", "parallel": "Parallel", "ring": "Ring"}
_NBHD_COLOR = {
    "Southwest Fresno": "#e41a1c",
    "Chinatown": "#ff7f00",
    "Downtown Fresno": "#4daf4a",
    "Shared": "#377eb8",
}
_AGENT_COLOR = {
    "Sustainability Expert": "#1b9e77",
    "Financial Expert": "#d95f02",
    "Urban Planner": "#7570b3",
    "Citizen (SW Fresno)": "#e7298a",
    "Citizen (Chinatown)": "#66a61e",
    "Citizen (Downtown Fresno)": "#e6ab02",
}
_FLOOR_GREEN = "#2ca02c"
_CAP_NAVY = "#1a3a6b"
_BAND_ORANGE = "#e07b00"
_GINI_RED = "#d62728"

_STALE_TOPO = (
    "05_sw_shortfall_by_turn.png",
    "05_sw_allocation_by_turn.png",
    "12_sw_shortfall_by_round.png",
    "12_sw_allocation_by_round.png",
    "16_downtown_shortfall_by_turn.png",
    "16_downtown_allocation_by_turn.png",
    "17_downtown_shortfall_by_round.png",
    "17_downtown_allocation_by_round.png",
)
_STALE_ROOT = (
    "sw_mandate.png",
    "sw_allocation.png",
    "downtown_mandate.png",
    "downtown_allocation.png",
)
_STALE_GLOBS = (
    "*_color*.png",
    "*_no_threshold*.png",
    "*_no_judge*.png",
    "*_no_band*.png",
    "*_mono*.png",
)


def _topo_key(name: str) -> str:
    return str(name or "").strip().lower()


def topo_file_label(topology: str) -> str:
    return _TOPO_LABEL.get(_topo_key(topology), str(topology).capitalize())


def _sw_floor() -> Optional[float]:
    v = getattr(config, "SW_FRESNO_MIN_USD", None)
    return float(v) if v else None


def _dt_floor() -> Optional[float]:
    v = getattr(config, "DOWNTOWN_MIN_USD", None)
    return float(v) if v else None


def _row(tm) -> dict:
    if isinstance(tm, dict):
        return tm
    if hasattr(tm, "to_dict"):
        return tm.to_dict()
    return {
        "turn_index": getattr(tm, "turn_index", 0),
        "round": getattr(tm, "round_number", getattr(tm, "round", 0)),
        "speaker": getattr(tm, "speaker", ""),
        "gini_score": getattr(tm, "gini_score", 0.0),
        "total_allocated_usd": getattr(tm, "total_allocated_usd", 0.0),
        "neighborhood_totals": getattr(tm, "neighborhood_totals", {}) or {},
        "sw_fresno_shortfall_usd": getattr(tm, "sw_fresno_shortfall_usd", None),
        "downtown_shortfall_usd": getattr(tm, "downtown_shortfall_usd", None),
        "sw_allocated_usd": getattr(tm, "sw_allocated_usd", None),
        "downtown_allocated_usd": getattr(tm, "downtown_allocated_usd", None),
        "fiscal_flags": getattr(tm, "fiscal_flags", []) or [],
        "judge_triggered": getattr(tm, "judge_triggered", False),
        "sw_mandate_met": getattr(tm, "sw_mandate_met", lambda: None)()
        if callable(getattr(tm, "sw_mandate_met", None)) else getattr(tm, "sw_mandate_met", None),
        "downtown_mandate_met": getattr(tm, "downtown_mandate_met", lambda: None)()
        if callable(getattr(tm, "downtown_mandate_met", None)) else getattr(tm, "downtown_mandate_met", None),
    }


def _rows(metrics) -> List[dict]:
    return [_row(m) for m in (metrics or [])]


def _sorted(rows: List[dict]) -> List[dict]:
    return sorted(rows, key=lambda r: r.get("turn_index") or 0)


_SPEAKER_ORDER = tuple(_AGENT_COLOR.keys())


def _speakers(rows: List[dict]) -> List[str]:
    seen = list(dict.fromkeys(r.get("speaker") or "" for r in rows if r.get("speaker")))
    ranked = [s for s in _SPEAKER_ORDER if s in seen]
    extra = [s for s in seen if s not in _SPEAKER_ORDER]
    return ranked + extra


def _agent_color(name: str) -> str:
    return _AGENT_COLOR.get(name, "#4c72b0")


def _round_of(r: dict) -> int:
    return int(r.get("round") or r.get("round_number") or 0)


def _sw_usd(r: dict) -> float:
    if r.get("sw_allocated_usd") is not None:
        return float(r["sw_allocated_usd"])
    nb = r.get("neighborhood_totals") or {}
    return float(nb.get("Southwest Fresno", 0) or 0) + float(nb.get("Shared", 0) or 0)


def _dt_usd(r: dict) -> float:
    if r.get("downtown_allocated_usd") is not None:
        return float(r["downtown_allocated_usd"])
    short = r.get("downtown_shortfall_usd")
    floor = _dt_floor()
    if short is not None and floor:
        return float(floor) - float(short)
    nb = r.get("neighborhood_totals") or {}
    return float(nb.get("Downtown Fresno", 0) or 0)


def _money(usd: float, d: int = 1) -> str:
    """Million-dollar label. Backslash-dollar so matplotlib does not start mathtext."""
    return rf"\${float(usd) / 1e6:.{d}f}M"


def _sw_title_bit() -> str:
    fl = _sw_floor()
    if fl:
        return f"Southwest + Shared; floor {_money(fl)}"
    return "Southwest + Shared; no SW dollar floor"


def _dt_title_bit() -> str:
    fl = _dt_floor()
    if fl:
        return f"Downtown-tagged; floor {_money(fl)}"
    return "Downtown spend; no Downtown dollar floor"


def _smooth_xy(x, y, n: int = 4000, extra_smooth: bool = True, y_clip=None):
    """Dense C2-ish curve. Spline+Gaussian when scipy is present; numpy fallback."""
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
    dx = np.diff(x)
    tangents = np.zeros_like(y)
    tangents[0] = (y[1] - y[0]) / dx[0]
    tangents[-1] = (y[-1] - y[-2]) / dx[-1]
    if len(x) > 2:
        tangents[1:-1] = (y[2:] - y[:-2]) / (x[2:] - x[:-2])
    i = np.clip(np.searchsorted(x, xs, side="right") - 1, 0, len(x) - 2)
    t = (xs - x[i]) / (x[i + 1] - x[i])
    t2 = t * t
    t3 = t2 * t
    dt = x[i + 1] - x[i]
    ys = (
        (2 * t3 - 3 * t2 + 1) * y[i]
        + (t3 - 2 * t2 + t) * dt * tangents[i]
        + (-2 * t3 + 3 * t2) * y[i + 1]
        + (t3 - t2) * dt * tangents[i + 1]
    )
    if extra_smooth and len(x) >= 3:
        span = n / max(len(x) - 1, 1)
        win = int(max(span / 3.0, 9))
        if win % 2 == 0:
            win += 1
        kernel = np.bartlett(win)
        kernel = kernel / kernel.sum()
        pad = win // 2
        ys = np.convolve(np.pad(ys, (pad, pad), mode="edge"), kernel, mode="valid")
    ys = np.clip(ys, float(np.min(y)), float(np.max(y)))
    if y_clip is not None:
        ys = np.clip(ys, y_clip[0], y_clip[1])
    return xs, ys


def _mark_rounds(ax, rows: List[dict]) -> None:
    seen = set()
    for r in _sorted(rows):
        rnd = _round_of(r)
        if rnd in seen:
            continue
        seen.add(rnd)
        t = r.get("turn_index") or 0
        if t > 1:
            ax.axvline(t - 0.5, color="#bbbbbb", linestyle=":", linewidth=1.0)
        ax.text(
            t, 0.97, f"R{rnd}", transform=ax.get_xaxis_transform(),
            fontsize=8, color="#666666", ha="left", va="top",
        )


def _floor_line(ax, usd: Optional[float], label: str) -> None:
    if not usd:
        return
    y = usd / 1e6
    ax.axhspan(0, y, color=_FLOOR_GREEN, alpha=0.12, zorder=0)
    ax.axhline(y, color=_FLOOR_GREEN, linestyle="--", linewidth=2.2, zorder=5, label=label)


def _budget_guides(ax) -> None:
    lo = config.MIN_BUDGET_USD / 1e6
    hi = config.TOTAL_BUDGET_USD / 1e6
    ax.axhspan(0, lo, color=_BAND_ORANGE, alpha=0.12, zorder=0)
    ax.axhspan(lo, hi, color=_FLOOR_GREEN, alpha=0.06, zorder=0)
    ax.axhline(lo, color=_BAND_ORANGE, linestyle="--", linewidth=2.2, zorder=5, label=f"Floor ({_money(config.MIN_BUDGET_USD)})")
    ax.axhline(hi, color=_CAP_NAVY, linestyle="-", linewidth=2.0, zorder=5, label=f"Cap ({_money(config.TOTAL_BUDGET_USD)})")


def _gini_line(ax) -> None:
    t = config.GINI_INTERVENTION_THRESHOLD
    ax.axhspan(0, t, color=_GINI_RED, alpha=0.10, zorder=0)
    ax.axhline(t, color=_GINI_RED, linestyle="--", linewidth=2.0, zorder=5, label=f"Judge threshold ({t})")


def _smooth_dots(ax, xs, ys, *, color, label=None, y_clip=None, linewidth=2.0, zorder=3, marker="o"):
    """One smoothed curve plus raw-value markers. No second polyline."""
    sx, sy = _smooth_xy(xs, ys, y_clip=y_clip)
    ax.plot(sx, sy, color=color, linewidth=linewidth, zorder=zorder, solid_capstyle="round", label=label)
    ax.plot(xs, ys, color=color, marker=marker, markersize=6, linestyle="None", zorder=zorder + 1)


def _save(fig, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def _use_judge(experiment: str, payload: Optional[dict] = None) -> bool:
    if payload and "use_judge" in payload:
        return bool(payload["use_judge"])
    cfg = config.EXPERIMENTS.get(experiment) or {}
    return bool(cfg.get("use_judge"))


# ----- individual figures ---------------------------------------------------

def plot_gini_by_turn(rows, experiment, topology, path) -> str:
    rows = _sorted(rows)
    xs = [r.get("turn_index") for r in rows]
    ys = [r.get("gini_score") or 0.0 for r in rows]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    sx, sy = _smooth_xy(xs, ys, y_clip=(0.0, 1.0))
    ax.plot(sx, sy, color="#888888", linewidth=2.2, zorder=2, solid_capstyle="round")
    labeled, judge_lab = set(), False
    for r in rows:
        sp = r.get("speaker") or ""
        lab = sp if sp not in labeled else ""
        labeled.add(sp)
        ax.scatter(
            [r.get("turn_index")], [r.get("gini_score") or 0],
            color=_agent_color(sp), s=46, zorder=3, label=lab,
        )
        if r.get("judge_triggered"):
            ax.scatter(
                [r.get("turn_index")], [r.get("gini_score") or 0],
                s=150, facecolors="none", edgecolors="red", linewidths=1.8, zorder=4,
                label="Judge flagged" if not judge_lab else "",
            )
            judge_lab = True
    _gini_line(ax)
    _mark_rounds(ax, rows)
    ax.set_xlabel("Turn (one slate per panelist, in speaking order)")
    ax.set_ylabel("Gini (0 = even; 1 = max inequality)")
    ax.set_title(f"Gini by Turn — {topo_file_label(topology)}\n{experiment}")
    ax.set_xticks(xs)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=7, ncol=2, loc="upper right")
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_gini_by_agent(rows, experiment, topology, path) -> str:
    speakers = _speakers(rows)
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    rng = np.random.default_rng(0)
    means = []
    for i, sp in enumerate(speakers):
        vals = [r.get("gini_score") or 0.0 for r in rows if r.get("speaker") == sp]
        means.append(float(np.mean(vals)) if vals else 0.0)
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals, color=_agent_color(sp), s=36, zorder=3)
    x = np.arange(len(speakers))
    ax.bar(x, means, color=[_agent_color(s) for s in speakers], alpha=0.35, edgecolor="black", zorder=1)
    _gini_line(ax)
    ax.set_xticks(x)
    ax.set_xticklabels(speakers, rotation=20, ha="right")
    ax.set_ylabel("Gini")
    ax.set_title(f"Gini by Agent (bars = mean; dots = each turn)\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_bias_by_agent(rows, experiment, topology, path) -> str:
    speakers = _speakers(rows)
    judge_n, gini_n, sw_n, dt_n = [], [], [], []
    has_sw = any("sw_mandate_met" in r and r["sw_mandate_met"] is not None for r in rows)
    has_dt = any("downtown_mandate_met" in r and r["downtown_mandate_met"] is not None for r in rows)
    for sp in speakers:
        s = [r for r in rows if r.get("speaker") == sp]
        judge_n.append(sum(1 for r in s if r.get("judge_triggered")))
        gini_n.append(sum(1 for r in s if (r.get("gini_score") or 0) > config.GINI_INTERVENTION_THRESHOLD))
        sw_n.append(sum(1 for r in s if r.get("sw_mandate_met") is False))
        dt_n.append(sum(1 for r in s if r.get("downtown_mandate_met") is False))
    x = np.arange(len(speakers))
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    series = [
        (-1.5, judge_n, "Judge flagged", "#e31a1c"),
        (-0.5, gini_n, f"Gini > {config.GINI_INTERVENTION_THRESHOLD}", "#fdb863"),
    ]
    width = 0.2 if (has_sw or has_dt) else 0.35
    if has_sw:
        series.append((0.5, sw_n, "SW mandate miss", "#6baed6"))
    if has_dt:
        series.append((1.5, dt_n, "DT mandate miss", "#4daf4a"))
    offs = np.linspace(-(len(series) - 1) / 2, (len(series) - 1) / 2, len(series))
    for off, vals, lab, col in zip(offs, [s[1] for s in series], [s[2] for s in series], [s[3] for s in series]):
        ax.bar(x + off * width, vals, width, label=lab, color=col, alpha=0.88, edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(speakers, rotation=20, ha="right")
    ax.set_ylabel("Turn count")
    ax.set_title(f"Bias Flags by Agent\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_bias_by_turn(rows, experiment, topology, path) -> str:
    rows = _sorted(rows)
    xs = [r.get("turn_index") for r in rows]
    gini_trip = [1 if (r.get("gini_score") or 0) > config.GINI_INTERVENTION_THRESHOLD else 0 for r in rows]
    judge = [1 if r.get("judge_triggered") else 0 for r in rows]
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.bar(xs, gini_trip, width=0.8, color="#fdb863", label=f"Gini > {config.GINI_INTERVENTION_THRESHOLD}", edgecolor="black", linewidth=0.3)
    ax.bar(xs, judge, width=0.42, color="#e31a1c", label="Judge flagged", edgecolor="black", linewidth=0.3)
    _mark_rounds(ax, rows)
    ax.set_xlabel("Turn")
    ax.set_ylabel("Flag (0 / 1)")
    ax.set_ylim(0, 1.25)
    ax.set_xticks(xs)
    ax.set_yticks([0, 1])
    ax.set_title(f"Bias Flags by Turn\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_sw_by_turn(rows, experiment, topology, path) -> str:
    rows = _sorted(rows)
    xs = [r.get("turn_index") for r in rows]
    ys = [_sw_usd(r) / 1e6 for r in rows]
    fig, ax = plt.subplots(figsize=(12, 5.0))
    sx, sy = _smooth_xy(xs, ys)
    ax.plot(sx, sy, color="#888888", linewidth=2.0, zorder=2)
    for r, x, y in zip(rows, xs, ys):
        ax.scatter([x], [y], color=_agent_color(r.get("speaker") or ""), s=42, zorder=3)
    _floor_line(ax, _sw_floor(), f"SW floor ({_money(_sw_floor() or 0)})")
    _mark_rounds(ax, rows)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Turn")
    ax.set_ylabel(r"SW-tagged allocation (\$M)")
    ax.set_title(f"SW spend by Turn ({_sw_title_bit()})\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_xticks(xs)
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=_agent_color(s), markersize=7, label=s)
        for s in _speakers(rows)
    ]
    extra = ax.get_legend_handles_labels()[0][:1]
    ax.legend(handles=handles + extra, fontsize=7, ncol=2, loc="upper right")
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_dt_by_turn(rows, experiment, topology, path) -> str:
    rows = _sorted(rows)
    xs = [r.get("turn_index") for r in rows]
    ys = [_dt_usd(r) / 1e6 for r in rows]
    fig, ax = plt.subplots(figsize=(12, 5.0))
    sx, sy = _smooth_xy(xs, ys)
    ax.plot(sx, sy, color="#888888", linewidth=2.0, zorder=2)
    for r, x, y in zip(rows, xs, ys):
        ax.scatter([x], [y], color=_agent_color(r.get("speaker") or ""), s=42, zorder=3)
    _floor_line(ax, _dt_floor(), f"Downtown floor ({_money(_dt_floor() or 0)})")
    _mark_rounds(ax, rows)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Turn")
    ax.set_ylabel(r"Downtown allocation (\$M)")
    ax.set_title(f"Downtown spend by Turn ({_dt_title_bit()})\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_xticks(xs)
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=_agent_color(s), markersize=7, label=s)
        for s in _speakers(rows)
    ]
    extra = ax.get_legend_handles_labels()[0][:1]
    ax.legend(handles=handles + extra, fontsize=7, ncol=2, loc="upper right")
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_budget_by_turn(rows, experiment, topology, path) -> str:
    rows = _sorted(rows)
    xs = [r.get("turn_index") for r in rows]
    ys = [(r.get("total_allocated_usd") or 0) / 1e6 for r in rows]
    fig, ax = plt.subplots(figsize=(12, 5.0))
    sx, sy = _smooth_xy(xs, ys)
    ax.plot(sx, sy, color="#888888", linewidth=2.0, zorder=2)
    for r, x, y in zip(rows, xs, ys):
        ax.scatter([x], [y], color=_agent_color(r.get("speaker") or ""), s=42, zorder=3)
    _budget_guides(ax)
    _mark_rounds(ax, rows)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Turn")
    ax.set_ylabel(r"Budget total (\$M)")
    ax.set_title(f"Budget by Turn (SW + CH + DT + Shared)\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_xticks(xs)
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=_agent_color(s), markersize=7, label=s)
        for s in _speakers(rows)
    ]
    extra = ax.get_legend_handles_labels()[0]
    ax.legend(handles=handles + extra, fontsize=7, ncol=2, loc="best")
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_neighborhood_by_turn(rows, experiment, topology, path) -> str:
    rows = _sorted(rows)
    xs = [r.get("turn_index") for r in rows]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    for nbhd in config.ALLOCATION_BUCKETS:
        ys = [float((r.get("neighborhood_totals") or {}).get(nbhd, 0) or 0) / 1e6 for r in rows]
        sx, sy = _smooth_xy(xs, ys)
        ax.plot(sx, sy, linewidth=2.0, label=nbhd, color=_NBHD_COLOR.get(nbhd, "#888"))
        ax.scatter(xs, ys, s=18, color=_NBHD_COLOR.get(nbhd, "#888"), zorder=3)
    _mark_rounds(ax, rows)
    ax.set_xlabel("Turn")
    ax.set_ylabel(r"Allocation (\$M)")
    ax.set_title(f"Neighborhood + Shared by Turn\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_ylim(bottom=0)
    ax.set_xticks(xs)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_final_allocation(rows, experiment, topology, path) -> str:
    last = max((_round_of(r) for r in rows), default=0)
    last_m = [r for r in rows if _round_of(r) == last]
    order = {s: i for i, s in enumerate(_speakers(rows))}
    last_m = sorted(last_m, key=lambda r: order.get(r.get("speaker") or "", 99))
    speakers = [r.get("speaker") for r in last_m]
    fig, ax = plt.subplots(figsize=(11, 5))
    bottoms = np.zeros(len(speakers))
    for nbhd in config.ALLOCATION_BUCKETS:
        vals = np.array([float((r.get("neighborhood_totals") or {}).get(nbhd, 0) or 0) / 1e6 for r in last_m])
        ax.bar(speakers, vals, bottom=bottoms, label=nbhd, color=_NBHD_COLOR.get(nbhd, "gray"), alpha=0.85, edgecolor="black", linewidth=0.5)
        bottoms += vals
    _budget_guides(ax)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Agent")
    ax.set_ylabel(r"Allocated (\$M)")
    ax.set_title(f"Final-Round Allocation by Agent\n{experiment}  /  {topo_file_label(topology)}")
    plt.xticks(rotation=25, ha="right", fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_project_frequency(freq: Optional[dict], experiment, topology, path, messages=None, proposals=None) -> str:
    from collections import Counter
    counter: Counter = Counter()
    if freq:
        for k, v in freq.items():
            try:
                counter[int(k)] += int(v)
            except (TypeError, ValueError):
                continue
    elif messages:
        for msg in messages:
            funded = getattr(msg, "funded_projects", None)
            if funded is None and isinstance(msg, dict):
                funded = msg.get("funded_projects") or {}
            for pid in funded or {}:
                counter[int(pid)] += 1
    if not counter:
        return ""
    most = counter.most_common(20)
    pids = [str(pid) for pid, _ in most]
    counts = [c for _, c in most]
    pmap = {p.id: p for p in (proposals or [])}
    if not pmap:
        try:
            from proposal_loader import load_proposals
            pmap = {p.id: p for p in load_proposals()}
        except Exception:
            pmap = {}
    colors = []
    for pid, _ in most:
        prop = pmap.get(int(pid))
        if prop is None:
            colors.append("#999999")
        elif len(getattr(prop, "neighborhoods", []) or []) >= 2:
            colors.append(_NBHD_COLOR["Shared"])
        elif getattr(prop, "neighborhoods", None):
            colors.append(_NBHD_COLOR.get(prop.neighborhoods[0], "#999999"))
        else:
            colors.append("#999999")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.barh(pids, counts, color=colors, alpha=0.8, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Number of agent-round allocations")
    ax.set_ylabel("Proposal ID")
    ax.set_title(f"Top 20 Most-Funded Proposals\n{experiment}  /  {topo_file_label(topology)}")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    return _save(fig, path)


def plot_fiscal_flags(rows, experiment, topology, path) -> str:
    speakers = _speakers(rows)
    flags = ["overfunding", "underfunding"]
    sw_fl, dt_fl = _sw_floor(), _dt_floor()
    if sw_fl:
        flags.append("southwest_underfunding")
    if dt_fl:
        flags.append("downtown_underfunding")
    labels = {
        "overfunding": "Over budget",
        "underfunding": f"Under {_money(config.MIN_BUDGET_USD, 0)}",
        "southwest_underfunding": f"SW under {_money(sw_fl)}" if sw_fl else "SW underfunding",
        "downtown_underfunding": f"DT under {_money(dt_fl)}" if dt_fl else "DT underfunding",
    }
    colors = {
        "overfunding": "#e31a1c",
        "underfunding": "#fdae61",
        "southwest_underfunding": "#2b83ba",
        "downtown_underfunding": "#4daf4a",
    }
    present = [f for f in flags if any(f in (r.get("fiscal_flags") or []) for r in rows)]
    if not present:
        present = ["overfunding", "underfunding"]
    x = np.arange(len(speakers))
    width = 0.8 / max(len(present), 1)
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    for i, flag in enumerate(present):
        counts = [sum(1 for r in rows if r.get("speaker") == s and flag in (r.get("fiscal_flags") or [])) for s in speakers]
        ax.bar(x + (i - (len(present) - 1) / 2) * width, counts, width, label=labels.get(flag, flag), color=colors.get(flag, "#888"), alpha=0.88, edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(speakers, rotation=20, ha="right")
    ax.set_ylabel("Turn count")
    ax.set_title(f"Fiscal Instruction Misses by Agent\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_gini_by_round(rows, experiment, topology, path) -> str:
    rounds = sorted({_round_of(r) for r in rows})
    avgs = [float(np.mean([r.get("gini_score") or 0.0 for r in rows if _round_of(r) == rnd])) for rnd in rounds]
    fig, ax = plt.subplots(figsize=(9, 5))
    color = _TOPO_COLOR.get(_topo_key(topology), "#4c72b0")
    marker = _TOPO_MARKER.get(_topo_key(topology), "o")
    _smooth_dots(ax, rounds, avgs, color=color, label="Avg Gini per round", y_clip=(0.0, 1.0), linewidth=2.4, marker=marker)
    warned = sorted({_round_of(r) for r in rows if r.get("judge_triggered")})
    for i, wr in enumerate(warned):
        if wr in rounds:
            ax.scatter([wr], [avgs[rounds.index(wr)]], s=220, facecolors="none", edgecolors="red", linewidths=2.5, zorder=5, label="Judge warning fired" if i == 0 else "")
    _gini_line(ax)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Gini Coefficient\n(0 = equal; 1 = maximally unequal)")
    ax.set_title(f"Gini by Round\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_xticks(rounds)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_sw_by_round(rows, experiment, topology, path) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    for sp in _speakers(rows):
        s = sorted([r for r in rows if r.get("speaker") == sp], key=_round_of)
        xs = [_round_of(r) for r in s]
        ys = [_sw_usd(r) / 1e6 for r in s]
        _smooth_dots(ax, xs, ys, color=_agent_color(sp), label=sp)
    _floor_line(ax, _sw_floor(), f"SW floor ({_money(_sw_floor() or 0)})")
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"SW-tagged allocation (\$M)")
    ax.set_title(f"SW spend by Round ({_sw_title_bit()})\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_dt_by_round(rows, experiment, topology, path) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    for sp in _speakers(rows):
        s = sorted([r for r in rows if r.get("speaker") == sp], key=_round_of)
        xs = [_round_of(r) for r in s]
        ys = [_dt_usd(r) / 1e6 for r in s]
        _smooth_dots(ax, xs, ys, color=_agent_color(sp), label=sp)
    _floor_line(ax, _dt_floor(), f"Downtown floor ({_money(_dt_floor() or 0)})")
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"Downtown allocation (\$M)")
    ax.set_title(f"Downtown spend by Round ({_dt_title_bit()})\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_budget_by_round(rows, experiment, topology, path) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    for sp in _speakers(rows):
        s = sorted([r for r in rows if r.get("speaker") == sp], key=_round_of)
        xs = [_round_of(r) for r in s]
        ys = [(r.get("total_allocated_usd") or 0) / 1e6 for r in s]
        _smooth_dots(ax, xs, ys, color=_agent_color(sp), label=sp)
    _budget_guides(ax)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"Total allocated (\$M)")
    ax.set_title(f"Budget by Round (SW + CH + DT + Shared)\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=7, loc="lower right", ncol=2)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_neighborhood_by_round(rows, experiment, topology, path) -> str:
    rounds = sorted({_round_of(r) for r in rows})
    nbhds = config.ALLOCATION_BUCKETS
    x = np.arange(len(rounds))
    width = 0.2
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, nbhd in enumerate(nbhds):
        vals = [
            float(np.mean([float((r.get("neighborhood_totals") or {}).get(nbhd, 0) or 0) for r in rows if _round_of(r) == rnd])) / 1e6
            for rnd in rounds
        ]
        ax.bar(x + (i - (len(nbhds) - 1) / 2) * width, vals, width, label=nbhd, color=_NBHD_COLOR.get(nbhd, f"C{i}"), alpha=0.85, edgecolor="black", linewidth=0.6)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"Avg Allocation per Panelist (\$M)")
    ax.set_title(f"Neighborhood + Shared by Round\n{experiment}  /  {topo_file_label(topology)}")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Rd {r}" for r in rounds])
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_bias_by_round(rows, experiment, topology, path) -> str:
    rounds = sorted({_round_of(r) for r in rows})
    judge_n, gini_n, sw_n, dt_n = [], [], [], []
    has_sw = any(r.get("sw_mandate_met") is False or r.get("sw_mandate_met") is True for r in rows)
    has_dt = any(r.get("downtown_mandate_met") is False or r.get("downtown_mandate_met") is True for r in rows)
    for rnd in rounds:
        rm = [r for r in rows if _round_of(r) == rnd]
        judge_n.append(sum(1 for r in rm if r.get("judge_triggered")))
        gini_n.append(sum(1 for r in rm if (r.get("gini_score") or 0) > config.GINI_INTERVENTION_THRESHOLD))
        sw_n.append(sum(1 for r in rm if r.get("sw_mandate_met") is False))
        dt_n.append(sum(1 for r in rm if r.get("downtown_mandate_met") is False))
    x = np.arange(len(rounds))
    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    series = [(judge_n, "Judge flagged", "#e31a1c"), (gini_n, f"Gini > {config.GINI_INTERVENTION_THRESHOLD}", "#fdb863")]
    if has_sw:
        series.append((sw_n, "SW mandate miss", "#6baed6"))
    if has_dt:
        series.append((dt_n, "DT mandate miss", "#4daf4a"))
    width = 0.8 / len(series)
    for i, (vals, lab, col) in enumerate(series):
        ax.bar(x + (i - (len(series) - 1) / 2) * width, vals, width, label=lab, color=col, alpha=0.88, edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Round {r}" for r in rounds])
    ax.set_ylabel("Panelist count (max 6)")
    ax.set_title(f"Bias Flags by Round\n{experiment}  /  {topo_file_label(topology)}")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


def plot_cross_gini_turn(all_rows: Dict[str, list], experiment, path) -> str:
    fig, ax = plt.subplots(figsize=(11, 5.2))
    for topo, metrics in all_rows.items():
        rows = _sorted(_rows(metrics))
        if not rows:
            continue
        xs = [r.get("turn_index") for r in rows]
        ys = [r.get("gini_score") or 0.0 for r in rows]
        sx, sy = _smooth_xy(xs, ys, y_clip=(0.0, 1.0))
        key = _topo_key(topo)
        ax.plot(sx, sy, color=_TOPO_COLOR.get(key, "#888"), linewidth=2.2, label=topo_file_label(topo))
        ax.scatter(xs, ys, color=_TOPO_COLOR.get(key, "#888"), marker=_TOPO_MARKER.get(key, "o"), s=18, zorder=3)
    _gini_line(ax)
    ax.set_xlabel("Turn")
    ax.set_ylabel("Gini")
    ax.set_title(f"Gini by Turn — All Topologies\n{experiment}")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_cross_gini_round(all_rows: Dict[str, list], experiment, path) -> str:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for topo, metrics in all_rows.items():
        rows = _rows(metrics)
        if not rows:
            continue
        rounds = sorted({_round_of(r) for r in rows})
        avgs = [float(np.mean([r.get("gini_score") or 0 for r in rows if _round_of(r) == rnd])) for rnd in rounds]
        key = _topo_key(topo)
        _smooth_dots(
            ax, rounds, avgs, color=_TOPO_COLOR.get(key, "#888"),
            label=topo_file_label(topo), y_clip=(0.0, 1.0),
            marker=_TOPO_MARKER.get(key, "o"),
        )
    _gini_line(ax)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel("Average Gini (neighborhood inequality)")
    ax.set_title(f"Gini Trajectory — All Topologies\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_cross_nbhd_rounds(all_rows: Dict[str, list], experiment, path) -> str:
    topos = [t for t, m in all_rows.items() if m]
    if not topos:
        return ""
    nbhds = config.ALLOCATION_BUCKETS
    fig, axes = plt.subplots(1, len(topos), figsize=(4.2 * len(topos), 4.8), sharey=True)
    if len(topos) == 1:
        axes = [axes]
    for ax, topo in zip(axes, topos):
        rows = _rows(all_rows[topo])
        rounds = sorted({_round_of(r) for r in rows})
        x = np.arange(len(rounds))
        width = 0.2
        for i, nbhd in enumerate(nbhds):
            vals = [
                float(np.mean([float((r.get("neighborhood_totals") or {}).get(nbhd, 0) or 0) for r in rows if _round_of(r) == rnd])) / 1e6
                for rnd in rounds
            ]
            ax.bar(x + (i - (len(nbhds) - 1) / 2) * width, vals, width, label=nbhd if ax is axes[0] else None, color=_NBHD_COLOR.get(nbhd, f"C{i}"), alpha=0.85, edgecolor="black", linewidth=0.5)
        ax.set_title(topo_file_label(topo))
        ax.set_xticks(x)
        ax.set_xticklabels([f"R{r}" for r in rounds])
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel(r"Avg allocation (\$M)")
    fig.suptitle(f"Neighborhood + Shared by Round\n{experiment}", fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    _log.info("Saved: %s", path)
    return path


def plot_cross_sw(all_rows: Dict[str, list], experiment, path) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for topo, metrics in all_rows.items():
        rows = _rows(metrics)
        if not rows:
            continue
        rounds = sorted({_round_of(r) for r in rows})
        avgs = [float(np.mean([_sw_usd(r) for r in rows if _round_of(r) == rnd])) / 1e6 for rnd in rounds]
        key = _topo_key(topo)
        _smooth_dots(
            ax, rounds, avgs, color=_TOPO_COLOR.get(key, "#888"),
            label=topo_file_label(topo), marker=_TOPO_MARKER.get(key, "o"),
        )
    _floor_line(ax, _sw_floor(), f"SW floor ({_money(_sw_floor() or 0)})")
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"Avg SW-tagged spend (\$M)")
    ax.set_title(f"SW spend — All Topologies ({_sw_title_bit()})\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_cross_dt(all_rows: Dict[str, list], experiment, path) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for topo, metrics in all_rows.items():
        rows = _rows(metrics)
        if not rows:
            continue
        rounds = sorted({_round_of(r) for r in rows})
        avgs = [float(np.mean([_dt_usd(r) for r in rows if _round_of(r) == rnd])) / 1e6 for rnd in rounds]
        key = _topo_key(topo)
        _smooth_dots(
            ax, rounds, avgs, color=_TOPO_COLOR.get(key, "#888"),
            label=topo_file_label(topo), marker=_TOPO_MARKER.get(key, "o"),
        )
    _floor_line(ax, _dt_floor(), f"Downtown floor ({_money(_dt_floor() or 0)})")
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"Avg Downtown spend (\$M)")
    ax.set_title(f"Downtown spend — All Topologies ({_dt_title_bit()})\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_cross_budget(all_rows: Dict[str, list], experiment, path) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for topo, metrics in all_rows.items():
        rows = _rows(metrics)
        if not rows:
            continue
        rounds = sorted({_round_of(r) for r in rows})
        avgs = [float(np.mean([r.get("total_allocated_usd") or 0 for r in rows if _round_of(r) == rnd])) / 1e6 for rnd in rounds]
        key = _topo_key(topo)
        _smooth_dots(
            ax, rounds, avgs, color=_TOPO_COLOR.get(key, "#888"),
            label=topo_file_label(topo), marker=_TOPO_MARKER.get(key, "o"),
        )
    _budget_guides(ax)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Negotiation Round")
    ax.set_ylabel(r"Avg total allocated (\$M)")
    ax.set_title(f"Budget Utilisation — All Topologies\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return _save(fig, path)


def plot_cross_final(all_rows: Dict[str, list], experiment, path) -> str:
    topos = [t for t, m in all_rows.items() if m]
    nbhds = config.ALLOCATION_BUCKETS
    x = np.arange(len(nbhds))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, topo in enumerate(topos):
        rows = _rows(all_rows[topo])
        last = max(_round_of(r) for r in rows)
        last_m = [r for r in rows if _round_of(r) == last]
        vals = [float(np.mean([float((r.get("neighborhood_totals") or {}).get(n, 0) or 0) for r in last_m])) / 1e6 for n in nbhds]
        ax.bar(x + (i - (len(topos) - 1) / 2) * width, vals, width, label=topo_file_label(topo), color=_TOPO_COLOR.get(_topo_key(topo), f"C{i}"), alpha=0.85, edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(nbhds, fontsize=10)
    ax.set_ylabel(r"Avg Final-Round Allocation (\$M)")
    ax.set_title(f"Final-Round Neighborhood Shares\n{experiment}")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)


# ----- pack + redraw --------------------------------------------------------

def _cleanup_stale(folder: str, names=(), extra_globs=()) -> None:
    for name in names:
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            os.remove(p)
    for pattern in extra_globs:
        for p in glob(os.path.join(folder, pattern)):
            base = os.path.basename(p)
            if base[:2].isdigit() and base[2] == "_" and "_no_" not in base and "_color" not in base and "_mono" not in base:
                continue
            if any(tag in base for tag in ("_color", "_no_threshold", "_no_judge", "_no_band", "_mono")):
                try:
                    os.remove(p)
                except OSError:
                    pass


def render_topology_plots(
    output_dir: str,
    experiment: str,
    topology: str,
    metrics,
    messages=None,
    proposals=None,
    freq: Optional[dict] = None,
) -> List[str]:
    rows = _rows(metrics)
    if not rows:
        return []
    topo_dir = os.path.join(output_dir, topo_file_label(topology))
    os.makedirs(topo_dir, exist_ok=True)
    _cleanup_stale(topo_dir, _STALE_TOPO, _STALE_GLOBS)
    jobs = [
        ("01_gini_by_turn.png", plot_gini_by_turn),
        ("02_gini_by_agent.png", plot_gini_by_agent),
        ("03_bias_by_agent.png", plot_bias_by_agent),
        ("04_bias_by_turn.png", plot_bias_by_turn),
        ("05_sw_by_turn.png", plot_sw_by_turn),
        ("06_budget_by_turn.png", plot_budget_by_turn),
        ("07_neighborhood_by_turn.png", plot_neighborhood_by_turn),
        ("08_final_allocation_by_agent.png", plot_final_allocation),
        ("11_gini_by_round.png", plot_gini_by_round),
        ("12_sw_by_round.png", plot_sw_by_round),
        ("13_budget_by_round.png", plot_budget_by_round),
        ("14_neighborhood_by_round.png", plot_neighborhood_by_round),
        ("15_bias_by_round.png", plot_bias_by_round),
        ("16_downtown_by_turn.png", plot_dt_by_turn),
        ("17_downtown_by_round.png", plot_dt_by_round),
        ("10_fiscal_flags_by_agent.png", plot_fiscal_flags),
    ]
    saved = []
    for name, fn in jobs:
        try:
            p = fn(rows, experiment, topology, os.path.join(topo_dir, name))
            if p:
                saved.append(p)
        except Exception as exc:
            _log.warning("%s failed (%s/%s): %s", name, experiment, topology, exc)
    try:
        p = plot_project_frequency(
            freq, experiment, topology,
            os.path.join(topo_dir, "09_project_frequency.png"),
            messages=messages, proposals=proposals,
        )
        if p:
            saved.append(p)
    except Exception as exc:
        _log.warning("project frequency failed: %s", exc)
    return saved


def render_experiment_plots(output_dir: str, experiment: str, all_metrics: Dict[str, list]) -> List[str]:
    if not all_metrics:
        return []
    _cleanup_stale(output_dir, _STALE_ROOT, _STALE_GLOBS)
    jobs = [
        ("gini_by_turn.png", plot_cross_gini_turn),
        ("gini_trajectory.png", plot_cross_gini_round),
        ("neighborhood_allocations.png", plot_cross_nbhd_rounds),
        ("sw_spend.png", plot_cross_sw),
        ("downtown_spend.png", plot_cross_dt),
        ("budget_utilisation.png", plot_cross_budget),
        ("final_allocation.png", plot_cross_final),
    ]
    saved = []
    for name, fn in jobs:
        try:
            p = fn(all_metrics, experiment, os.path.join(output_dir, name))
            if p:
                saved.append(p)
        except Exception as exc:
            _log.warning("%s failed: %s", name, exc)
    return saved


def redraw_experiment(exp_dir: str) -> List[str]:
    src = os.path.join(exp_dir, "graph_data.json")
    if not os.path.isfile(src):
        raise FileNotFoundError(src)
    with open(src, encoding="utf-8") as fh:
        payload = json.load(fh)
    experiment = payload.get("experiment") or os.path.basename(os.path.abspath(exp_dir))
    turns = payload.get("turns") or {}
    unplotted = (payload.get("unplotted") or {}).get("topologies") or {}
    saved: List[str] = []
    all_rows: Dict[str, list] = {}
    for label, rows in turns.items():
        freq = ((unplotted.get(label) or {}).get("project_frequency") or {}).get("counts")
        saved.extend(render_topology_plots(exp_dir, experiment, label, rows, freq=freq))
        all_rows[label] = rows
    saved.extend(render_experiment_plots(exp_dir, experiment, all_rows))
    return saved


def _dirs_from_arg(arg: str) -> list:
    arg = os.path.abspath(arg)
    if os.path.isfile(os.path.join(arg, "graph_data.json")):
        return [arg]
    if os.path.isdir(arg):
        return [
            os.path.join(arg, name)
            for name in sorted(os.listdir(arg))
            if os.path.isfile(os.path.join(arg, name, "graph_data.json"))
        ]
    return []


def main(argv: Optional[List[str]] = None) -> int:
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    targets = (argv if argv is not None else sys.argv[1:]) or ["outputs"]
    dirs = []
    for arg in targets:
        dirs.extend(_dirs_from_arg(arg))
    if not dirs:
        print("No graph_data.json found.")
        return 1
    for exp_dir in dirs:
        print("redrawing", exp_dir)
        for path in redraw_experiment(exp_dir):
            print("  ", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
