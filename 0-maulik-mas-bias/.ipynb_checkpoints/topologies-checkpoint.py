"""
topologies.py
Routing logic for the 3 communication topologies compared in the study.

  Star      — every agent submits to a central Coordinator each round; agents
              only ever see the Coordinator's aggregated summary, never each
              other's full messages.  The Coordinator is a deterministic
              aggregation function, not an LLM call.

  Parallel  — fully-connected on *peer slates*: in rounds 2–5 every agent sees
              all six panelists' previous-round reasoning + funded lists
              (same snapshot). They do not see each other's current-round
              slates. Improver notes are a separate, persistent channel.

  Ring      — strict sequential hand-off:
                SustainabilityExpert → FinancialExpert → UrbanPlanner
                → Citizen(SW) → Citizen(Chinatown) → Citizen(Downtown) → (repeat)
              Each agent sees only the immediately preceding agent's message.

All three topologies share the same base class (NegotiationRun):
  • Same agent set and proposal list
  • Same per-turn metrics (Gini, neighborhood $, budget overrun)
  • Same optional judge/improver loop — after EVERY message the JudgeAgent
    detects bias (panelists never see Judge text).     If bias is flagged, ImproverAgent writes a steering message addressed
    to that agent. Notes stay on the board for the rest of THIS topology
    run only (they do not carry into Star/Parallel/Ring or other
    experiments) and are shown to every later speaker in rounds 2–5.
    Round 1 propose() stays clean — no Improver text. Gini is unchanged
    (raw 4-bucket Gini; tripwire 0.25).
  • Subclasses only override _run_functional_rounds()

Round structure (identical across topologies):
  Round 1   — agents propose() independently with no context
  Rounds 2-5 — agents negotiate() with topology-specific context
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import config
from agents import BaseAgent, ImproverAgent, JudgeAgent, Message
from metrics import (
    TurnMetrics,
    describe_ids,
    final_round_consensus,
    downtown_total,
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
        self.improver: Optional[ImproverAgent] = agents.get("improver") if use_judge else None
        self.proposal_map = {p.id: p for p in proposals}

        # Ordered list of the 6 panelist agents
        self.panelists: List[BaseAgent] = [agents[role] for role in AGENT_ORDER]

        self.messages: List[Message] = []
        self.turn_metrics: List[TurnMetrics] = []
        self._turn_counter: int = 0
        self._round_messages: Dict[int, List[Message]] = {}
        # Improver notes for THIS topology instance only. A new Star /
        # Parallel / Ring (or a new experiment) builds a new NegotiationRun,
        # so notes never leak across topologies or experiments.
        self.improver_board: List[Tuple[str, str]] = []

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
        dt_full = downtown_total(clean, self.proposals)
        gini_score = gini([nbhd_totals[k] for k in config.ALLOCATION_BUCKETS])
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
            sw_allocated_usd     = sw_full,
            downtown_allocated_usd = dt_full,
            budget_overrun_usd   = overrun,
            fiscal_flags         = fiscal_constraint_flags(total),
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
            total_allocated   = total,
            round_number      = round_number,
            sw_full_usd       = sw_full,
            downtown_full_usd = dt_full,
            funded_lines      = describe_ids(sorted(clean), self.proposals),
            fiscal_flags      = tm.fiscal_flags,
        )
        return tm

    def _conversation_text(self, last_n: int = 12) -> str:
        recent = self.messages[-last_n:]
        blocks = []
        for m in recent:
            bits = f"[{m.speaker} ({m.role})]: {m.reasoning or m.content}"
            blocks.append(bits)
        return "\n\n".join(blocks) if blocks else "(none)"

    def _broadcast_improver_block(self, log: bool = True) -> Optional[str]:
        if not self.improver_board:
            return None
        parts = []
        for speaker, text in self.improver_board:
            parts.append(
                f"ADDRESSED TO: {speaker}\n{(text or '').strip()}"
            )
        if log:
            print(
                f"  -> Improver broadcast ({len(parts)} note(s)) shown to this speaker"
            )
        return "\n\n".join(parts)

    def _judge_and_maybe_improve(self, msg: Message, tm: TurnMetrics) -> Optional[str]:
        if not self.use_judge or self.judge is None:
            return None

        funded_lines = describe_ids(sorted(msg.funded_projects), self.proposals)
        convo = self._conversation_text()
        judge_text = self.judge.evaluate(
            agent_message       = msg,
            gini_score          = tm.gini_score,
            neighborhood_totals = tm.neighborhood_totals,
            fiscal_flags        = tm.fiscal_flags,
            funded_lines        = funded_lines,
            conversation_context = convo,
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

        if not bias_detected:
            tm.improver_text = ""
            print(
                f"  Judge: no bias flagged for {msg.speaker} "
                f"(Gini={tm.gini_score:.3f})."
            )
            return None

        improver_text = ""
        if self.improver is not None:
            improver_text = self.improver.generate_correction(
                agent_message       = msg,
                qualitative_finding = judge_text,
                neighborhood_totals = tm.neighborhood_totals,
                fiscal_flags        = tm.fiscal_flags,
                funded_lines        = funded_lines,
                conversation_context = convo,
                gini_score          = tm.gini_score,
            )
        tm.improver_text = improver_text
        self.improver_board.append((msg.speaker, improver_text))
        self.transcript.log_improver(
            speaker        = msg.speaker,
            improver_text  = improver_text,
            turn_index     = tm.turn_index,
        )
        print(
            f"  BIAS DETECTED for {msg.speaker} "
            f"(Gini={tm.gini_score:.3f}"
            f"{'; instructed misses: ' + ', '.join(tm.fiscal_flags) if tm.fiscal_flags else ''}"
            f") — Improver note addressed to them, broadcast to all panelists."
        )
        return improver_text

    def _run_functional_rounds(self, rounds: int):
        raise NotImplementedError

    def run(self, rounds: int = None) -> Tuple[List[Message], List[TurnMetrics]]:
        rounds = rounds or config.NEGOTIATION_ROUNDS
        judge_label = "ENABLED" if self.use_judge else "DISABLED"
        print(
            f"\n{'=' * 70}\n"
            f"Topology: {self.name.upper()}  |  "
            f"Rounds: {rounds}  |  Judge+Improver: {judge_label}\n"
            f"{'=' * 70}"
        )
        self.transcript.log_section(
            f"NEGOTIATION — topology={self.name}  rounds={rounds}  "
            f"judge_improver={'on' if self.use_judge else 'off'}"
        )
        self.improver_board = []
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
            "(no neighborhood floor — this is what the panel funded on average)",
            f"Average Downtown-tagged (exclusive DT + shared-with-DT): "
            f"${sum(downtown_total(m.funded_projects, self.proposals) for m in prev) / n_agents:,.0f}  "
            "(no neighborhood floor)",
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
                    msg = agent.propose(self.proposals, round_number=r)
                else:
                    msg = agent.negotiate(
                        self.proposals, self._coordinator_summary(r),
                        round_number=r,
                        improver_note=self._broadcast_improver_block(),
                    )
                tm = self._record_message(msg, r)
                self._judge_and_maybe_improve(msg, tm)


# ===========================================================================
# Parallel topology
# ===========================================================================

class ParallelTopology(NegotiationRun):
    """
    Fully-connected on peer slates: in rounds 2–5 every agent sees all six
    previous-round messages (same snapshot). They do not see each other's
    current-round funded lists. Improver notes persist across rounds and
    are shown to every speaker from Round 2 onward.
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
                    msg = agent.propose(self.proposals, round_number=r)
                else:
                    msg = agent.negotiate(
                        self.proposals, context,
                        round_number=r,
                        improver_note=self._broadcast_improver_block(),
                    )
                tm = self._record_message(msg, r)
                self._judge_and_maybe_improve(msg, tm)


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
                    msg = agent.propose(self.proposals, round_number=r)
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
                        improver_note=self._broadcast_improver_block(),
                    )

                tm = self._record_message(msg, r)
                self._judge_and_maybe_improve(msg, tm)

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
