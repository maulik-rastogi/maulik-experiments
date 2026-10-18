from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import seaborn as sns

from .allocation import Allocation, neighborhood_dollars
from .discussion import ExperimentResult
from .proposals import Proposal
from .topologies import topology_graph

sns.set_theme(style="whitegrid", context="notebook")


def plot_topology(agents, topology: str, ax=None):
    g = topology_graph(agents, topology)
    ax = ax or plt.gca()
    pos = nx.spring_layout(g, seed=42)
    colors = []
    for n in g.nodes:
        if n == "finance":
            colors.append("#1f4e79")
        elif n == "sustainability":
            colors.append("#2e7d32")
        elif n.endswith("_sw"):
            colors.append("#c62828")
        elif n.endswith("_ne"):
            colors.append("#1565c0")
        else:
            colors.append("#ef6c00")
    nx.draw(g, pos, ax=ax, with_labels=True, node_color=colors, node_size=1600, font_size=8, arrows=True)
    ax.set_title(f"Discussion topology: {topology}")
    return ax


def plot_neighborhood_trajectory(eval_pack: dict, path: Path | None = None):
    df: pd.DataFrame = eval_pack["per_agent_rounds"]
    cols = ["$_southwest", "$_central", "$_northeast"]
    mean = df.groupby("round_id")[cols].mean()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    mean.plot(ax=ax, marker="o")
    fair = eval_pack["summary"]["fair_share_usd"]
    ax.axhline(fair["southwest"], ls="--", c="#c62828", alpha=0.5, label="fair SW")
    ax.axhline(fair["northeast"], ls="--", c="#1565c0", alpha=0.5, label="fair NE")
    ax.set_ylabel("Mean $ allocated (across agents)")
    ax.set_title("Neighborhood dollars over discussion rounds")
    ax.legend(loc="best")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=140)
    return fig


def plot_consensus(eval_pack: dict, path: Path | None = None):
    c = eval_pack["consensus"]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(c["round_id"], c["mean_pairwise_jaccard"], marker="o")
    ax.set_ylim(0, 1)
    ax.set_xlabel("round")
    ax.set_ylabel("mean pairwise Jaccard of funded sets")
    ax.set_title("Consensus tightness over rounds")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=140)
    return fig


def plot_elite_capture(eval_pack: dict, path: Path | None = None):
    e: pd.DataFrame = eval_pack["elite_capture"]
    if e.empty:
        return None
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for aid, sub in e.groupby("agent_id"):
        ax.plot(sub["round_id"], sub["align_finance"], marker="o", label=f"{aid} → finance")
    ax.set_ylim(0, 1)
    ax.set_title("Citizen alignment with the Financial Officer (Jaccard)")
    ax.set_xlabel("round")
    ax.legend()
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=140)
    return fig


def plot_final_bars(result: ExperimentResult, proposals: list[Proposal], path: Path | None = None):
    dollars = neighborhood_dollars(result.final, proposals)
    fair = {k: result.config["budget_usd"] * w for k, w in
            (("southwest", 0.50), ("central", 0.30), ("northeast", 0.20))}
    labels = ["southwest", "central", "northeast"]
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], [fair[k] for k in labels], width=0.36, label="need-weighted fair")
    ax.bar([i + 0.18 for i in x], [dollars.get(k, 0) for k in labels], width=0.36, label="final package")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Southwest", "Central", "Northeast"])
    ax.set_ylabel("USD")
    ax.set_title("Final allocation vs need-weighted fair share")
    ax.legend()
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=140)
    return fig


def allocation_table(alloc: Allocation, proposals: list[Proposal]) -> pd.DataFrame:
    catalog = {p.id: p for p in proposals}
    rows = []
    for item in sorted(alloc.items, key=lambda x: -x.amount_usd):
        p = catalog.get(item.project_id)
        rows.append(
            {
                "id": item.project_id,
                "title": p.title if p else "",
                "neighborhood": p.neighborhood if p else "",
                "category": p.category if p else "",
                "ask": p.cost_usd if p else None,
                "funded": item.amount_usd,
                "pct_of_ask": (item.amount_usd / p.cost_usd) if p and p.cost_usd else None,
                "rationale": item.rationale,
            }
        )
    return pd.DataFrame(rows)
