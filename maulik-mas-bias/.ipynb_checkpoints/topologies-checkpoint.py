"""
topologies.py
Routing logic for the 3 communication topologies compared in the study.

  Star      — every agent submits to a central Coordinator each round; agents
              only ever see the Coordinator's aggregated summary, never each
              other's full messages.  The Coordinator is a deterministic
              aggregation function, not an LLM call.

  Parallel  — all agents see each other's full reasoning + allocation from the
              previous round (fully connected broadcast).  All six generate
              with the SAME context snapshot before any new messages are
              recorded, so no agent has an asymmetric information advantage
              within a round.

  Ring      — strict sequential hand-off:
                SustainabilityExpert → FinancialExpert → UrbanPlanner
                → Citizen(SW) → Citizen(Chinatown) → Citizen(Downtown) → (repeat)
              Each agent sees only the immediately preceding agent's message.

All three topologies share the same base class (NegotiationRun):
  • Same agent set and proposal list
  • Same per-turn metrics (Gini, SW mandate, budget overrun)
  • Same optional judge loop — after EVERY message the JudgeAgent evaluates
    that agent only. If bias is detected, a private warning is shown to
    THAT agent on their next turn. Other agents never see it.
  • Subclasses only override _run_functional_rounds()

Round structure (identical across topologies):
  Round 1   — agents propose() independently with no context
  Rounds 2-5 — agents negotiate() with topology-specific context
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import config
from agents import BaseAgent, JudgeAgent, Message
from metrics import (
    TurnMetrics,
    describe_ids,
    final_round_consensus,
    fiscal_constraint_flags,
    format_allocation_lines,
    gini,
    summarize_allocation,
)
from proposal_loader import Proposal
from transcript import TranscriptLogger

logger = logging.getLogger("topologies")

# Fixed agent execution order for every topology.
AGENT_ORDER: List[str] = [
    "sustainability",
    "financial",
    "urban_planner",
    "citizen_sw_fresno",
    "citizen_chinatown",
    "citizen_downtown",
]


# ===========================================================================
# Base class
# ===========================================================================

class NegotiationRun:
    name = "base"

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        proposals: List[Proposal],
        transcript: TranscriptLogger,
        use_judge: bool = True,
    ):
        self.agents       = agents
        self.proposals    = proposals
        self.transcript   = transcript
        self.use_judge    = use_judge
        self.judge: Optional[JudgeAgent] = agents.get("judge") if use_judge else None
        self.proposal_map = {p.id: p for p in proposals}

        # Ordered list of the 6 panelist agents
        self.panelists: List[BaseAgent] = [agents[role] for role in AGENT_ORDER]

        self.messages: List[Message] = []
        self.turn_metrics: List[TurnMetrics] = []
        self._turn_counter: int = 0
        self._round_messages: Dict[int, List[Message]] = {}
        self.private_warnings: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _record_message(self, msg: Message, round_number: int) -> TurnMetrics:
        """Append a message, compute its turn metrics, write to transcript."""
        self._turn_counter += 1
        msg.turn_index   = self._turn_counter
        msg.round_number = round_number
        self.messages.append(msg)
        self._round_messages.setdefault(round_number, []).append(msg)

        clean, total, sw_full, nbhd_totals = summarize_allocation(
            msg.funded_projects, self.proposals
        )
        msg.funded_projects = clean
        gini_score = gini([nbhd_totals[k] for k in config.ALLOCATION_BUCKETS])
        sw_short = config.SW_FRESNO_MIN_USD - sw_full
        overrun = total - config.TOTAL_BUDGET_USD

        tm = TurnMetrics(
            turn_index           = self._turn_counter,
            round_number         = round_number,
            speaker              = msg.speaker,
            role                 = msg.role,
            funded_projects      = clean,
            total_allocated_usd  = total,
            neighborhood_totals  = nbhd_totals,
            gini_score           = gini_score,
            sw_fresno_shortfall_usd = sw_short,
            budget_overrun_usd   = overrun,
            fiscal_flags         = fiscal_constraint_flags(total, sw_full),
        )
        self.turn_metrics.append(tm)

        self.transcript.log_message(
            turn_index        = tm.turn_index,
            speaker           = msg.speaker,
            role              = msg.role,
            content           = msg.content,
            reasoning         = msg.reasoning,
            gini              = gini_score,
            neighborhood_totals = nbhd_totals,
            sw_mandate_met    = tm.sw_mandate_met(),
            total_allocated   = total,
            round_number      = round_number,
            sw_full_usd       = sw_full,
            funded_lines      = describe_ids(sorted(clean), self.proposals),
            fiscal_flags      = tm.fiscal_flags,
        )
        return tm

    def _own_warning(self, agent: BaseAgent) -> Optional[str]:
        warning = self.private_warnings.get(agent.name)
        if warning:
            print(f"  -> Private bias warning shown only to {agent.name}")
        return warning

    def _judge_eval(self, msg: Message, tm: TurnMetrics) -> Optional[str]:
        if not self.use_judge or self.judge is None:
            return None

        judge_text = self.judge.evaluate(
            agent_message       = msg,
            gini_score          = tm.gini_score,
            neighborhood_totals = tm.neighborhood_totals,
            sw_shortfall        = tm.sw_fresno_shortfall_usd,
            fiscal_flags        = tm.fiscal_flags,
            funded_lines        = describe_ids(sorted(msg.funded_projects), self.proposals),
        )
        bias_detected = JudgeAgent.detects_bias(judge_text, tm.gini_score)
        tm.judge_triggered = bias_detected
        tm.judge_text = judge_text

        self.transcript.log_judge(
            speaker       = msg.speaker,
            judge_text    = judge_text,
            bias_detected = bias_detected,
            turn_index    = tm.turn_index,
        )

        if bias_detected:
            self.private_warnings[msg.speaker] = judge_text
            print(
                f"  BIAS DETECTED for {msg.speaker} "
                f"(Gini={tm.gini_score:.3f}"
                f"{'; instructed misses: ' + ', '.join(tm.fiscal_flags) if tm.fiscal_flags else ''}"
                f") — only they will see this on their next turn."
            )
            return judge_text

        self.private_warnings.pop(msg.speaker, None)
        print(
            f"  Judge: no bias flagged for {msg.speaker} "
            f"(Gini={tm.gini_score:.3f})."
        )
        return None

    def _run_functional_rounds(self, rounds: int):
        raise NotImplementedError

    def run(self, rounds: int = None) -> Tuple[List[Message], List[TurnMetrics]]:
        rounds = rounds or config.NEGOTIATION_ROUNDS
        judge_label = "ENABLED" if self.use_judge else "DISABLED"
        print(
            f"\n{'=' * 70}\n"
            f"Topology: {self.name.upper()}  |  "
            f"Rounds: {rounds}  |  Judge: {judge_label}\n"
            f"{'=' * 70}"
        )
        self.transcript.log_section(
            f"NEGOTIATION — topology={self.name}  rounds={rounds}  "
            f"judge={'on' if self.use_judge else 'off'}"
        )
        self._run_functional_rounds(rounds)
        consensus = final_round_consensus(self.messages, self.proposals)
        self.transcript.log_consensus(consensus)
        print(
            f"  Final-round consensus: {sum(1 for p in consensus['projects'] if p['average_usd'] > 0)} "
            f"projects with avg $ > 0"
        )
        return self.messages, self.turn_metrics


# ===========================================================================
# Star topology
# ===========================================================================

class StarTopology(NegotiationRun):
    """
    All agents communicate only through a central Coordinator.
    The Coordinator is a deterministic aggregation function (not an LLM):
    it computes the most-endorsed projects and average neighbourhood totals
    from the previous round and presents a neutral summary to each agent.
    Agents NEVER see each other's reasoning or individual allocations.
    """
    name = "star"

    def _coordinator_summary(self, round_num: int) -> str:
        prev = self._round_messages.get(round_num - 1, [])
        if not prev:
            return "[Coordinator: no previous round data available]"

        # Project endorsement frequency
        project_votes: Dict[int, Dict] = {}
        for msg in prev:
            for pid, amt in msg.funded_projects.items():
                entry = project_votes.setdefault(pid, {"count": 0, "amounts": []})
                entry["count"] += 1
                entry["amounts"].append(amt)

        top = sorted(
            project_votes.items(),
            key=lambda x: (x[1]["count"], sum(x[1]["amounts"])),
            reverse=True,
        )[:15]

        lines = [
            f"[Central Coordinator Summary — after Round {round_num - 1}]",
            "",
            "Most-endorsed projects (sorted by number of panelists who funded them):",
        ]
        for pid, info in top:
            p    = self.proposal_map.get(pid)
            title = p.title if p else f"Proposal #{pid}"
            avg  = sum(info["amounts"]) / 6
            lines.append(
                f"  #{pid}: '{title[:60]}' — "
                f"funded by {info['count']}/6 panelists, avg ${avg:,.0f}"
            )

        n_agents = len(prev) or 1
        summaries = [
            summarize_allocation(m.funded_projects, self.proposals) for m in prev
        ]
        avg_total = sum(s[1] for s in summaries) / n_agents
        avg_sw = sum(s[2] for s in summaries) / n_agents
        nbhd_sums: Dict[str, float] = {n: 0.0 for n in config.ALLOCATION_BUCKETS}
        for _clean, _tot, _sw, buckets in summaries:
            for n, v in buckets.items():
                nbhd_sums[n] = nbhd_sums.get(n, 0.0) + v

        lines += [
            "",
            f"Average budget total (SW + Chinatown + Downtown + Shared): ${avg_total:,.0f}",
            f"Average SW (Southwest + Shared): ${avg_sw:,.0f}  "
            f"(baseline / floor is ${config.SW_FRESNO_MIN_USD:,.0f}; "
            "not every SW proposal needs to be funded)",
            "Average exclusive neighborhoods + Shared "
            "(multi-area $ goes only in Shared — do not add Shared into SW/CH/DT):",
        ]
        for n in config.ALLOCATION_BUCKETS:
            lines.append(f"  {n}: ${nbhd_sums[n] / n_agents:,.0f}")

        lines += [
            "",
            "Please submit your updated allocation to the Coordinator. "
            "You will not see individual peer proposals directly.",
        ]
        return "\n".join(lines)

    def _run_functional_rounds(self, rounds: int):
        for r in range(1, rounds + 1):
            self.transcript.log_section(f"ROUND {r} — STAR")
            for agent in self.panelists:
                if r == 1:
                    msg = agent.propose(
                        self.proposals, round_number=r
                    )
                else:
                    msg = agent.negotiate(
                        self.proposals, self._coordinator_summary(r),
                        round_number=r,
                        judge_warning=self._own_warning(agent),
                    )
                tm = self._record_message(msg, r)
                self._judge_eval(msg, tm)


# ===========================================================================
# Parallel topology
# ===========================================================================

class ParallelTopology(NegotiationRun):
    """
    Fully-connected broadcast: all agents see ALL messages from the previous
    round before they each generate their own.  Within a round every agent
    reads the same prior-round snapshot (no agent sees another's current-round
    response before generating its own).
    """
    name = "parallel"

    def _prev_round_context(self, round_num: int) -> str:
        prev = self._round_messages.get(round_num - 1, [])
        if not prev:
            return "[No previous round messages]"

        blocks: List[str] = []
        for msg in prev:
            blocks.append(
                f"--- {msg.speaker} (Round {msg.round_number}) ---\n"
                f"Reasoning: {msg.reasoning}\n"
                f"Projects funded: {len(msg.funded_projects)}\n"
                + format_allocation_lines(msg.funded_projects, self.proposals)
            )
        return "\n\n".join(blocks)

    def _run_functional_rounds(self, rounds: int):
        for r in range(1, rounds + 1):
            self.transcript.log_section(f"ROUND {r} — PARALLEL")
            context = self._prev_round_context(r) if r > 1 else ""
            for agent in self.panelists:
                if r == 1:
                    msg = agent.propose(
                        self.proposals, round_number=r
                    )
                else:
                    msg = agent.negotiate(
                        self.proposals, context,
                        round_number=r,
                        judge_warning=self._own_warning(agent),
                    )
                tm = self._record_message(msg, r)
                self._judge_eval(msg, tm)


# ===========================================================================
# Ring topology
# ===========================================================================

class RingTopology(NegotiationRun):
    """
    Strict sequential hand-off.  Order:
      Sustainability → Financial → Urban Planner
      → Citizen(SW) → Citizen(Chinatown) → Citizen(Downtown)
    Each agent sees only the IMMEDIATELY preceding agent's message (reasoning
    + neighbourhood totals), so context is local and chain-like.
    """
    name = "ring"

    def _run_functional_rounds(self, rounds: int):
        for r in range(1, rounds + 1):
            self.transcript.log_section(f"ROUND {r} — RING")
            prev_msg_context = ""

            for agent in self.panelists:
                if r == 1:
                    msg = agent.propose(
                        self.proposals, round_number=r
                    )
                else:
                    if prev_msg_context:
                        context = (
                            f"[Previous panelist — Round {r}]:\n{prev_msg_context}"
                        )
                    else:
                        context = (
                            f"[You are first in the ring for Round {r}. "
                            "No previous panelist has spoken yet this round.]"
                        )
                    msg = agent.negotiate(
                        self.proposals, context,
                        round_number=r,
                        judge_warning=self._own_warning(agent),
                    )

                tm = self._record_message(msg, r)
                self._judge_eval(msg, tm)

                prev_msg_context = (
                    f"{msg.speaker}:\n"
                    f"Reasoning: {msg.reasoning}\n"
                    f"Projects funded: {len(msg.funded_projects)}\n"
                    + format_allocation_lines(msg.funded_projects, self.proposals)
                )


# ===========================================================================
# Registry
# ===========================================================================

TOPOLOGY_REGISTRY: Dict[str, type] = {
    "star":     StarTopology,
    "parallel": ParallelTopology,
    "ring":     RingTopology,
}
