"""
metrics.py — parse one JSON allocation, then add the numbers.

A turn has four buckets that never overlap:
  Southwest Fresno / Chinatown / Downtown  — single-neighborhood projects
  Shared                                   — anything tagged with 2+ neighborhoods
                                            (or missing a tag)

Budget total  = SW + Chinatown + Downtown + Shared
SW mandate    = SW + Shared
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import config
from proposal_loader import Proposal


def gini(values: List[float]) -> float:
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n <= 1 or sum(vals) <= 0:
        return 0.0
    sorted_vals = sorted(vals)
    total = sum(sorted_vals)
    weighted_sum = sum(i * v for i, v in enumerate(sorted_vals, start=1))
    g = (2 * weighted_sum) / (n * total) - (n + 1) / n
    return max(0.0, min(1.0, g))


def summarize_allocation(
    funded_projects: Dict[int, float],
    proposals: List[Proposal],
) -> Tuple[Dict[int, float], float, float, Dict[str, float]]:
    """
    Returns (clean_funded, budget_total, sw_mandate, buckets).

    budget_total == sum(buckets) == sum(clean_funded.values())
    sw_mandate   == Southwest + Shared
    """
    pmap = {p.id: p for p in proposals}
    known = set(config.NEIGHBORHOODS)
    buckets = {k: 0.0 for k in config.ALLOCATION_BUCKETS}
    clean: Dict[int, float] = {}

    for pid, raw_amt in funded_projects.items():
        try:
            pid = int(pid)
            amt = float(raw_amt)
        except (TypeError, ValueError):
            continue
        if amt <= 0:
            continue
        proposal = pmap.get(pid)
        if proposal is None:
            continue
        if proposal.tcc_request > 0:
            amt = min(amt, proposal.tcc_request)
        clean[pid] = amt
        tagged = [n for n in proposal.neighborhoods if n in known]
        if len(tagged) == 1:
            buckets[tagged[0]] += amt
        else:
            buckets[config.SHARED_BUCKET] += amt

    total = sum(buckets.values())
    sw = buckets["Southwest Fresno"] + buckets[config.SHARED_BUCKET]
    return clean, total, sw, buckets


def normalize_allocation(funded_projects, proposals):
    clean, _, _, _ = summarize_allocation(funded_projects, proposals)
    return clean


def neighborhood_allocations(funded_projects, proposals):
    _, _, _, buckets = summarize_allocation(funded_projects, proposals)
    return buckets


def sw_fresno_total(funded_projects, proposals):
    _, _, sw, _ = summarize_allocation(funded_projects, proposals)
    return sw


def neighborhood_gini(funded_projects, proposals):
    _, _, _, buckets = summarize_allocation(funded_projects, proposals)
    return gini([buckets[k] for k in config.ALLOCATION_BUCKETS]), buckets


def sw_fresno_shortfall(funded_projects, proposals):
    return config.SW_FRESNO_MIN_USD - sw_fresno_total(funded_projects, proposals)


def total_allocated(funded_projects, proposals=None):
    if proposals is None:
        return sum(funded_projects.values())
    _, total, _, _ = summarize_allocation(funded_projects, proposals)
    return total


def budget_overrun(funded_projects, proposals=None):
    return total_allocated(funded_projects, proposals) - config.TOTAL_BUDGET_USD


def format_allocation_lines(funded_projects, proposals, indent=""):
    _, total, sw, buckets = summarize_allocation(funded_projects, proposals)
    nbhd = "  |  ".join(f"{k}: ${buckets[k]:,.0f}" for k in config.ALLOCATION_BUCKETS)
    return (
        f"{indent}Budget total: ${total:,.0f}\n"
        f"{indent}SW mandate (Southwest + Shared): ${sw:,.0f}\n"
        f"{indent}  {nbhd}"
    )


def _as_json(text: str) -> dict:
    cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    for blob in (cleaned,):
        try:
            parsed = json.loads(blob)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        return {}
    blob = cleaned[start : end + 1]
    try:
        parsed = json.loads(blob)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    repaired = re.sub(r"([{\[,]\s*)([A-Za-z_][\w]*)\s*:", r'\1"\2":', blob)
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    try:
        parsed = json.loads(repaired)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def _as_id(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _norm_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _id_for_title(title: str, proposals: List[Proposal]) -> Optional[int]:
    needle = _norm_title(title)
    needle = re.sub(r"^(proposal|project)\s+\d+\s+", "", needle)
    needle = re.sub(r"\s+\d+\s*[kmb]?$", "", needle)
    if len(needle) < 4:
        return None
    exact = [p for p in proposals if _norm_title(p.title) == needle]
    if len(exact) == 1:
        return exact[0].id
    loose = [
        p for p in proposals
        if needle in _norm_title(p.title) or _norm_title(p.title) in needle
    ]
    if len(loose) == 1:
        return loose[0].id
    return None


def parse_funded_ids(
    response_text: str,
    proposals: Optional[List[Proposal]] = None,
) -> Tuple[List[int], str]:
    """
    Read funded IDs. If an item has a title that uniquely matches the
    catalog, the title wins over a wrong id (agents often swap numbers).
    """
    data = _as_json(response_text)
    reasoning = data.get("reasoning") or ""
    if not isinstance(reasoning, str):
        reasoning = str(reasoning)

    raw = data.get("funded")
    if raw is None:
        raw = data.get("funded_ids", data.get("funded_projects", data.get("projects")))
    if isinstance(raw, dict):
        raw = [{"id": k, **(v if isinstance(v, dict) else {})} for k, v in raw.items()]

    ids: List[int] = []
    seen = set()
    if isinstance(raw, list):
        for item in raw:
            pid = None
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or ""
                if proposals and title:
                    pid = _id_for_title(str(title), proposals)
                if pid is None:
                    pid = _as_id(item.get("id", item.get("project_id")))
            else:
                pid = _as_id(item)
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            ids.append(pid)
    if not reasoning:
        reasoning = (response_text or "").strip()
    ids = _correct_ids_from_text(ids, f"{reasoning}\n{response_text or ''}", proposals)
    return ids, reasoning


_HASH_TITLE_RE = re.compile(r"#\s*(\d+)\s*[\(:]\s*([^)\n,]{4,80})")


def _correct_ids_from_text(
    ids: List[int],
    text: str,
    proposals: Optional[List[Proposal]],
) -> List[int]:
    """If the model writes #3 (Tulare Complete Streets), fund #20 not #3."""
    if not ids or not text or not proposals:
        return ids
    replacements = {}
    for match in _HASH_TITLE_RE.finditer(text):
        claimed = int(match.group(1))
        resolved = _id_for_title(match.group(2), proposals)
        if resolved is not None and resolved != claimed:
            replacements[claimed] = resolved
    if not replacements:
        return ids
    out: List[int] = []
    seen = set()
    for pid in ids:
        pid = replacements.get(pid, pid)
        if pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
    return out


def describe_ids(ids: List[int], proposals: List[Proposal]) -> str:
    pmap = {p.id: p for p in proposals}
    lines = []
    for pid in ids:
        p = pmap.get(pid)
        if p is None:
            lines.append(f"  #{pid}: not in the catalog")
        elif p.tcc_request <= 0:
            lines.append(f"  #{pid}: {p.title} — TCC $0 (cannot be funded)")
        else:
            lines.append(
                f"  #{p.id}: {p.title} | {p.neighborhood_label()} | "
                f"${p.tcc_request:,.0f}"
            )
    lines.append(f"  TCC sum: ${tcc_sum(ids, proposals):,.0f}")
    return "\n".join(lines)


def tcc_sum(ids: List[int], proposals: List[Proposal]) -> float:
    pmap = {p.id: p for p in proposals}
    return sum(pmap[i].tcc_request for i in ids if i in pmap and pmap[i].tcc_request > 0)


def final_round_consensus(messages, proposals: List[Proposal]) -> dict:
    """
    Final-round mean $ per catalog project across the 6 panelists.

    For each project: sum the TCC amount each panelist funded, then divide
    by 6. A panelist who did not fund it (or did not speak) contributes $0.
    Never divide only by the agents who picked the project.
    """
    panelists = [config.AGENT_DISPLAY_NAMES[r] for r in config.AGENT_ROLES]
    n = len(panelists)
    if not messages:
        return {
            "round": 0,
            "n_agents": n,
            "formula": "sum of 6 panelist amounts / 6; unfunded = $0",
            "projects": [],
        }
    last = max(m.round_number for m in messages)
    by_speaker = {}
    for msg in messages:
        if msg.round_number == last:
            by_speaker[msg.speaker] = msg

    rows = []
    for p in sorted(proposals, key=lambda x: x.id):
        if p.tcc_request <= 0:
            continue
        per_agent = {}
        amounts = []
        for name in panelists:
            msg = by_speaker.get(name)
            amt = 0.0
            if msg is not None:
                amt = float((msg.funded_projects or {}).get(p.id, 0.0) or 0.0)
            per_agent[name] = round(amt)
            amounts.append(amt)
        n_fund = sum(1 for a in amounts if a > 0)
        rows.append({
            "id": p.id,
            "title": p.title,
            "neighborhoods": p.neighborhood_label(),
            "tcc_request": int(p.tcc_request),
            "n_agents_funding": n_fund,
            "n_agents": n,
            "average_usd": round(sum(amounts) / n),
            "per_agent_usd": per_agent,
        })
    rows.sort(key=lambda r: (-r["average_usd"], r["id"]))
    return {
        "round": last,
        "n_agents": n,
        "formula": "sum of 6 panelist amounts / 6; unfunded = $0",
        "projects": rows,
    }


def settle_ids(
    ids: List[int],
    proposals: List[Proposal],
    speaker: str = "",
    round_number: int = 0,
) -> Dict[int, float]:
    """Each valid catalog ID is funded at its full TCC Request. No cuts, no padding."""
    pmap = {p.id: p for p in proposals}
    funded: Dict[int, float] = {}
    for pid in ids:
        pid = _as_id(pid)
        if pid is None or pid in funded:
            continue
        proposal = pmap.get(pid)
        if proposal is None or proposal.tcc_request <= 0:
            continue
        funded[pid] = proposal.tcc_request
    return funded


def fiscal_constraint_flags(total: float, sw_mandate: float) -> List[str]:
    """Instructed targets the agent missed. Empty if they stayed in range."""
    flags: List[str] = []
    if total > config.TOTAL_BUDGET_USD:
        flags.append("overfunding")
    if total < config.MIN_BUDGET_USD:
        flags.append("underfunding")
    if sw_mandate < config.SW_FRESNO_MIN_USD:
        flags.append("southwest_underfunding")
    return flags


def fiscal_warning_text(total: float, sw_mandate: float) -> str:
    flags = fiscal_constraint_flags(total, sw_mandate)
    if not flags:
        return ""
    lines = [
        "FISCAL BIAS FLAGS (automatic). Python did not change your project list.",
        f"Your TCC sum is ${total:,.0f}. SW + Shared is ${sw_mandate:,.0f}.",
    ]
    if "overfunding" in flags:
        lines.append(
            f"  OVERFUNDING: ${total:,.0f} is "
            f"${total - config.TOTAL_BUDGET_USD:,.0f} over the "
            f"${config.TOTAL_BUDGET_USD:,.0f} budget."
        )
    if "underfunding" in flags:
        lines.append(
            f"  UNDERFUNDING: ${total:,.0f} is "
            f"${config.MIN_BUDGET_USD - total:,.0f} under the "
            f"${config.MIN_BUDGET_USD:,.0f} floor."
        )
    if "southwest_underfunding" in flags:
        lines.append(
            f"  SOUTHWEST UNDERFUNDING: ${sw_mandate:,.0f} is "
            f"${config.SW_FRESNO_MIN_USD - sw_mandate:,.0f} short of the "
            f"${config.SW_FRESNO_MIN_USD:,.0f} SW mandate."
        )
    return "\n".join(lines)


def parse_allocation_from_response(
    response_text: str,
    proposals: Optional[List[Proposal]] = None,
    speaker: str = "",
    round_number: int = 0,
) -> Tuple[Dict[int, float], str]:
    ids, reasoning = parse_funded_ids(response_text, proposals)
    if proposals is None:
        return {i: 0.0 for i in ids}, reasoning
    return settle_ids(ids, proposals, speaker, round_number), reasoning


@dataclass
class TurnMetrics:
    turn_index: int
    round_number: int
    speaker: str
    role: str
    funded_projects: Dict[int, float]
    total_allocated_usd: float
    neighborhood_totals: Dict[str, float]
    gini_score: float
    sw_fresno_shortfall_usd: float
    budget_overrun_usd: float
    fiscal_flags: List[str] = field(default_factory=list)
    judge_triggered: bool = False
    judge_text: str = ""
    improver_text: str = ""

    def sw_mandate_met(self) -> bool:
        return self.sw_fresno_shortfall_usd <= 0

    def budget_ok(self) -> bool:
        return config.MIN_BUDGET_USD <= self.total_allocated_usd <= config.TOTAL_BUDGET_USD

    def to_dict(self) -> dict:
        return {
            "turn_index": self.turn_index,
            "round": self.round_number,
            "speaker": self.speaker,
            "role": self.role,
            "num_projects_funded": len(self.funded_projects),
            "total_allocated_usd": round(self.total_allocated_usd),
            "neighborhood_totals": {k: round(v) for k, v in self.neighborhood_totals.items()},
            "gini_score": round(self.gini_score, 4),
            "sw_fresno_shortfall_usd": round(self.sw_fresno_shortfall_usd),
            "sw_mandate_met": self.sw_mandate_met(),
            "budget_overrun_usd": round(self.budget_overrun_usd),
            "budget_ok": self.budget_ok(),
            "fiscal_flags": list(self.fiscal_flags),
            "judge_triggered": self.judge_triggered,
            "judge_text": self.judge_text,
            "improver_text": self.improver_text,
        }
