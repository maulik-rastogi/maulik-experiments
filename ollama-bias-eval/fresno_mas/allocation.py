from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .config import NEIGHBORHOODS
from .proposals import Proposal, index_by_id

try:
    import json_repair
except Exception:  # noqa: BLE001
    json_repair = None


ALLOCATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "statement": {"type": "string"},
        "reasoning": {"type": "string"},
        "liked_projects": {"type": "array", "items": {"type": "string"}},
        "deprioritized_projects": {"type": "array", "items": {"type": "string"}},
        "allocations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "amount_usd": {"type": "integer"},
                    "rationale": {"type": "string"},
                },
                "required": ["project_id", "amount_usd"],
            },
        },
        "unfunded": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["allocations"],
}


@dataclass
class LineItem:
    project_id: str
    amount_usd: int
    rationale: str = ""


@dataclass
class Allocation:
    agent_id: str
    round_id: int
    items: list[LineItem] = field(default_factory=list)
    liked: list[str] = field(default_factory=list)
    deprioritized: list[str] = field(default_factory=list)
    unfunded: list[str] = field(default_factory=list)
    dropped_unknown_ids: list[str] = field(default_factory=list)
    reasoning: str = ""
    statement: str = ""
    raw_text: str = ""
    discussion: str = ""

    @property
    def total(self) -> int:
        return int(sum(i.amount_usd for i in self.items))

    def amount_map(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.items:
            out[item.project_id] = out.get(item.project_id, 0) + int(item.amount_usd)
        return out

    def funded_ids(self) -> set[str]:
        return {i.project_id for i in self.items if i.amount_usd > 0}

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "round_id": self.round_id,
            "total": self.total,
            "reasoning": self.reasoning,
            "statement": self.statement,
            "discussion": self.discussion,
            "liked_projects": self.liked,
            "deprioritized_projects": self.deprioritized,
            "unfunded": self.unfunded,
            "dropped_unknown_ids": self.dropped_unknown_ids,
            "raw_text": self.raw_text,
            "allocations": [
                {
                    "project_id": i.project_id,
                    "amount_usd": i.amount_usd,
                    "rationale": i.rationale,
                }
                for i in self.items
            ],
        }


def extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    blob = fence.group(1) if fence else None
    if blob is None:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            blob = text[start : end + 1]
    if not blob:
        return None
    for candidate in (blob,):
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            if json_repair is not None:
                try:
                    data = json_repair.loads(candidate)
                    if isinstance(data, dict):
                        return data
                except Exception:
                    return None
    return None


def parse_allocation(
    text: str,
    *,
    agent_id: str,
    round_id: int,
    proposals: Iterable[Proposal],
    budget: int,
) -> Allocation:
    catalog = index_by_id(proposals)
    data = extract_json(text) or {}
    discussion = text
    if "allocations" in text:
        pre = text.split("{", 1)[0].strip()
        if pre:
            discussion = pre
    items = []
    dropped: list[str] = []
    for raw in data.get("allocations") or []:
        if not isinstance(raw, dict):
            continue
        pid = str(raw.get("project_id") or raw.get("id") or "").strip().upper()
        if pid not in catalog:
            pid = _normalize_pid(pid, catalog)
        if pid not in catalog:
            dropped.append(str(raw.get("project_id") or raw.get("id") or ""))
            continue
        try:
            amt = int(float(raw.get("amount_usd") or raw.get("amount") or 0))
        except (TypeError, ValueError):
            amt = 0
        cap = catalog[pid].cost_usd if catalog[pid].cost_usd > 0 else amt
        if catalog[pid].cost_usd > 0:
            amt = max(0, min(amt, cap))
        else:
            amt = max(0, amt)
        if amt <= 0:
            continue
        items.append(LineItem(pid, amt, str(raw.get("rationale") or "")))

    def _keep(ids) -> list[str]:
        out = []
        for x in ids:
            pid = _normalize_pid(x, catalog)
            if pid in catalog:
                out.append(pid)
            else:
                dropped.append(str(x))
        return out

    statement = _compose_statement(text, data, discussion)
    alloc = Allocation(
        agent_id=agent_id,
        round_id=round_id,
        items=items,
        liked=_keep(data.get("liked_projects") or []),
        deprioritized=_keep(data.get("deprioritized_projects") or []),
        unfunded=_keep(data.get("unfunded") or []),
        dropped_unknown_ids=[x for x in dropped if x],
        reasoning=str(data.get("reasoning") or "").strip(),
        statement=statement,
        raw_text=text,
        discussion=statement or discussion,
    )
    return clip_to_budget(alloc, budget)


def _compose_statement(text: str, data: dict[str, Any], discussion: str) -> str:
    chunks: list[str] = []
    for key in ("statement", "speech", "message"):
        val = str(data.get(key) or "").strip()
        if val:
            chunks.append(val)
    pre = (discussion or "").strip()
    if pre and not pre.startswith("{") and pre not in chunks:
        chunks.insert(0, pre)
    reason = str(data.get("reasoning") or "").strip()
    if reason and not looks_like_fake_output(reason) and reason not in chunks:
        chunks.append(reason)
    seen: list[str] = []
    for c in chunks:
        if c and c not in seen:
            seen.append(c)
    statement = "\n\n".join(seen).strip()
    if len(statement) < 40:
        leftover = (text or "").strip()
        if leftover.startswith("{"):
            leftover = ""
        statement = leftover or statement
    return statement


def looks_like_fake_output(text: str) -> bool:
    low = (text or "").lower()
    return "mock heuristic allocation" in low or "heuristic score=" in low


def spoken_text(alloc: Allocation) -> str:
    return (alloc.statement or alloc.discussion or alloc.reasoning or "").strip()


def _normalize_pid(pid: str, catalog: dict[str, Proposal]) -> str:
    raw = str(pid).strip().upper().replace("PROPOSAL", "P").replace(" ", "")
    if raw in catalog:
        return raw
    m = re.search(r"(\d+)", raw)
    if m:
        cand = f"P{int(m.group(1)):02d}"
        if cand in catalog:
            return cand
    return raw


def clip_to_budget(alloc: Allocation, budget: int) -> Allocation:
    if alloc.total <= budget:
        return alloc
    # Keep highest amounts first, then scale the last items.
    ordered = sorted(alloc.items, key=lambda x: x.amount_usd, reverse=True)
    kept: list[LineItem] = []
    running = 0
    for item in ordered:
        if running + item.amount_usd <= budget:
            kept.append(item)
            running += item.amount_usd
        else:
            remain = budget - running
            if remain > 0:
                kept.append(LineItem(item.project_id, remain, item.rationale + " [budget clip]"))
                running += remain
            break
    alloc.items = kept
    return alloc


def neighborhood_dollars(alloc: Allocation, proposals: Iterable[Proposal]) -> dict[str, float]:
    catalog = index_by_id(proposals)
    shares = {k: 0.0 for k in ("southwest", "central", "northeast")}
    for item in alloc.items:
        p = catalog.get(item.project_id)
        if not p:
            continue
        split = p.extra.get("benefit_split")
        if not split:
            key = p.neighborhood_key
            if key in shares:
                shares[key] += item.amount_usd
            else:
                # unknown / citywide: split by need weights
                for k, meta in NEIGHBORHOODS.items():
                    shares[k] += item.amount_usd * meta["need_weight"]
            continue
        for k, w in split.items():
            if k in shares:
                shares[k] += item.amount_usd * float(w)
    return shares


def majority_merge(
    allocations: list[Allocation],
    proposals: Iterable[Proposal],
    budget: int,
    min_supporters: int | None = None,
) -> Allocation:
    catalog = index_by_id(proposals)
    n = max(1, len(allocations))
    min_supporters = min_supporters or max(2, (n + 1) // 2)
    votes: dict[str, int] = {}
    sums: dict[str, list[int]] = {}
    for alloc in allocations:
        amap = alloc.amount_map()
        for pid, amt in amap.items():
            votes[pid] = votes.get(pid, 0) + 1
            sums.setdefault(pid, []).append(amt)
    ranked = sorted(
        votes,
        key=lambda pid: (votes[pid], int(sum(sums[pid]) / len(sums[pid]))),
        reverse=True,
    )
    items: list[LineItem] = []
    running = 0
    for pid in ranked:
        if pid not in catalog:
            continue
        if votes[pid] < min_supporters and running > 0:
            # after filling consensus items, still allow high-mean leftovers
            pass
        mean_amt = int(sum(sums[pid]) / len(sums[pid]))
        mean_amt = min(mean_amt, catalog[pid].cost_usd, budget - running)
        if mean_amt <= 0:
            continue
        items.append(
            LineItem(
                pid,
                mean_amt,
                f"{votes[pid]}/{n} agents funded; mean ask ${mean_amt:,}",
            )
        )
        running += mean_amt
        if running >= budget:
            break
    return Allocation(agent_id="consensus", round_id=-1, items=items, reasoning="majority_merge")
