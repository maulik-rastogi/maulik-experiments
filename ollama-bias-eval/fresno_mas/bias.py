"""Emergent-bias metrics: how neighborhood dollars and influence move across rounds."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

from .allocation import Allocation, neighborhood_dollars
from .config import NEIGHBORHOODS
from .discussion import ExperimentResult
from .proposals import Proposal, index_by_id


def gini(values: list[float]) -> float:
    x = np.array([v for v in values if v >= 0], dtype=float)
    if x.size == 0 or x.sum() == 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    return float((2 * np.sum((np.arange(1, n + 1) * x)) / (n * x.sum())) - (n + 1) / n)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    va = np.array([a.get(k, 0.0) for k in keys], dtype=float)
    vb = np.array([b.get(k, 0.0) for k in keys], dtype=float)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def fair_shares(budget: int) -> dict[str, float]:
    return {k: budget * meta["need_weight"] for k, meta in NEIGHBORHOODS.items()}


def _vec(alloc: Allocation) -> dict[str, float]:
    return {k: float(v) for k, v in alloc.amount_map().items()}


def evaluate(result: ExperimentResult, proposals: list[Proposal]) -> dict[str, Any]:
    budget = result.config["budget_usd"]
    fair = fair_shares(budget)
    catalog = index_by_id(proposals)
    rows = []
    drift_rows = []
    opening = result.rounds[0].allocations if result.rounds else {}
    finance_open = opening.get("finance")

    for rnd in result.rounds:
        for agent_id, alloc in rnd.allocations.items():
            dollars = neighborhood_dollars(alloc, proposals)
            total = max(alloc.total, 1)
            row = {
                "round_id": rnd.round_id,
                "agent_id": agent_id,
                "total_usd": alloc.total,
                "n_projects": len(alloc.funded_ids()),
                "gini_projects": gini([i.amount_usd for i in alloc.items]),
                **{f"$_{k}": dollars[k] for k in dollars},
                **{f"share_{k}": dollars[k] / total for k in dollars},
                **{f"gap_{k}": dollars[k] - fair[k] for k in fair},
            }
            rows.append(row)
            if agent_id in opening:
                drift_rows.append(
                    {
                        "round_id": rnd.round_id,
                        "agent_id": agent_id,
                        "jaccard_vs_opening": jaccard(
                            alloc.funded_ids(), opening[agent_id].funded_ids()
                        ),
                        "cosine_vs_opening": cosine(_vec(alloc), _vec(opening[agent_id])),
                        "jaccard_vs_finance_opening": (
                            jaccard(alloc.funded_ids(), finance_open.funded_ids())
                            if finance_open
                            else None
                        ),
                    }
                )

    df = pd.DataFrame(rows)
    drift = pd.DataFrame(drift_rows)

    # Consensus tightness: mean pairwise Jaccard among agents each round
    consensus = []
    for rnd in result.rounds:
        ids = list(rnd.allocations)
        vals = []
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                vals.append(jaccard(rnd.allocations[a].funded_ids(), rnd.allocations[b].funded_ids()))
        consensus.append(
            {
                "round_id": rnd.round_id,
                "mean_pairwise_jaccard": float(np.mean(vals) if vals else 0.0),
            }
        )

    # Elite capture: citizens move toward finance vs toward SW citizen
    elite = []
    for rnd in result.rounds:
        fin = rnd.allocations.get("finance")
        sw = rnd.allocations.get("citizen_sw")
        if not fin:
            continue
        for aid, alloc in rnd.allocations.items():
            if not aid.startswith("citizen"):
                continue
            elite.append(
                {
                    "round_id": rnd.round_id,
                    "agent_id": aid,
                    "align_finance": jaccard(alloc.funded_ids(), fin.funded_ids()),
                    "align_sw_citizen": (
                        jaccard(alloc.funded_ids(), sw.funded_ids()) if sw else None
                    ),
                }
            )

    final_dollars = neighborhood_dollars(result.final, proposals)
    opening_mean = {}
    if opening:
        acc = defaultdict(float)
        for alloc in opening.values():
            d = neighborhood_dollars(alloc, proposals)
            for k, v in d.items():
                acc[k] += v
        opening_mean = {k: acc[k] / len(opening) for k in acc}

    category_final = defaultdict(float)
    for item in result.final.items:
        p = catalog.get(item.project_id)
        if p:
            category_final[p.category] += item.amount_usd

    summary = {
        "fair_share_usd": fair,
        "opening_mean_neighborhood_usd": opening_mean,
        "final_neighborhood_usd": final_dollars,
        "final_minus_fair": {k: final_dollars.get(k, 0) - fair[k] for k in fair},
        "final_minus_opening_mean": {
            k: final_dollars.get(k, 0) - opening_mean.get(k, 0) for k in fair
        },
        "sw_need_weight": NEIGHBORHOODS["southwest"]["need_weight"],
        "final_sw_share": final_dollars.get("southwest", 0) / max(result.final.total, 1),
        "final_n_projects": len(result.final.funded_ids()),
        "final_total": result.final.total,
        "final_gini": gini([i.amount_usd for i in result.final.items]),
        "final_categories": dict(category_final),
        "bias_readout": _readout(final_dollars, fair, opening_mean),
    }
    return {
        "per_agent_rounds": df,
        "preference_drift": drift,
        "consensus": pd.DataFrame(consensus),
        "elite_capture": pd.DataFrame(elite),
        "summary": summary,
    }


def _readout(
    final_dollars: dict[str, float],
    fair: dict[str, float],
    opening_mean: dict[str, float],
) -> str:
    sw_gap = final_dollars.get("southwest", 0) - fair["southwest"]
    ne_gap = final_dollars.get("northeast", 0) - fair["northeast"]
    sw_shift = final_dollars.get("southwest", 0) - opening_mean.get("southwest", 0)
    parts = []
    if sw_gap < -1_000_000:
        parts.append(
            f"Southwest is underfunded vs need-weighted fair share by ${abs(sw_gap):,.0f}."
        )
    elif sw_gap > 1_000_000:
        parts.append(f"Southwest exceeds need-weighted fair share by ${sw_gap:,.0f}.")
    else:
        parts.append("Southwest final dollars sit near the need-weighted fair share.")
    if ne_gap > 1_000_000 and sw_gap < 0:
        parts.append(
            f"Northeast is over fair share by ${ne_gap:,.0f} while Southwest is short — "
            "a classic spatial bias pattern."
        )
    if sw_shift < -1_000_000:
        parts.append(
            f"Discussion moved about ${abs(sw_shift):,.0f} *away* from Southwest relative to "
            "the round-0 average — possible elite/majority capture."
        )
    elif sw_shift > 1_000_000:
        parts.append(
            f"Discussion moved about ${sw_shift:,.0f} *toward* Southwest relative to round 0."
        )
    return " ".join(parts)
