from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agents import Agent, default_agents
from .allocation import (
    Allocation,
    looks_like_fake_output,
    majority_merge,
    parse_allocation,
    spoken_text,
)
from .config import ExperimentConfig
from .llm import LLMBackend
from .prompts import later_round_user_prompt, round0_user_prompt, synthesizer_prompt
from .proposals import Proposal
from .topologies import format_transcript, topology_graph


@dataclass
class RoundRecord:
    round_id: int
    allocations: dict[str, Allocation] = field(default_factory=dict)
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ExperimentResult:
    config: dict[str, Any]
    proposals: list[dict[str, Any]]
    agents: list[dict[str, Any]]
    rounds: list[RoundRecord]
    final: Allocation
    consensus_final: Allocation
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "config": self.config,
            "proposals": self.proposals,
            "agents": self.agents,
            "rounds": [
                {
                    "round_id": r.round_id,
                    "messages": r.messages,
                    "allocations": {k: v.to_dict() for k, v in r.allocations.items()},
                }
                for r in self.rounds
            ],
            "final": self.final.to_dict(),
            "consensus_final": self.consensus_final.to_dict(),
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_jsonable(), indent=2))
        return path


def _order_agents(agents: list[Agent], round_id: int, cfg: ExperimentConfig) -> list[Agent]:
    ordered = list(agents)
    if cfg.speaker_order == "fixed":
        return ordered
    if cfg.speaker_order == "random":
        rng = random.Random(cfg.seed + round_id)
        rng.shuffle(ordered)
        return ordered
    # rotate
    k = round_id % max(1, len(ordered))
    return ordered[k:] + ordered[:k]


def _consensus_hint(allocations: list[Allocation]) -> str:
    if not allocations:
        return ""
    counts: Counter[str] = Counter()
    for alloc in allocations:
        counts.update(alloc.funded_ids())
    n = len(allocations)
    popular = [pid for pid, c in counts.most_common(12) if c >= max(2, n // 2)]
    rare = [pid for pid, c in counts.most_common()[::-1] if c == 1][:8]
    lines = []
    if popular:
        lines.append("Projects funded by at least half of the agents you can see: " + ", ".join(popular))
    if rare:
        lines.append("Projects funded by only one visible agent: " + ", ".join(rare))
    return "\n".join(lines)


def _message_from_alloc(agent: Agent, alloc: Allocation) -> dict[str, Any]:
    spoken = spoken_text(alloc)
    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "round_id": alloc.round_id,
        "statement": alloc.statement,
        "discussion": spoken,
        "reasoning": alloc.reasoning,
        "text": alloc.raw_text,
        "funded": list(alloc.amount_map().items()),
        "liked": alloc.liked,
        "deprioritized": alloc.deprioritized,
    }


RETRY_SPEAK = (
    "Your previous reply did not include a spoken STATEMENT to the other agents. "
    "Write 4–8 sentences addressed to the room (name catalog project IDs, what you "
    "support, what you reject, and why). Then output the JSON object again. "
    "Do not reply with JSON only."
)


def _reject_fake(text: str, *, agent_id: str) -> None:
    if looks_like_fake_output(text):
        raise RuntimeError(
            f"Refusing {agent_id!r} output: it looks like the old mock heuristic, not Qwen. "
            "This codebase only runs Ollama qwen2.5:3b. Confirm `ollama serve` is running."
        )
    if not (text or "").strip():
        raise RuntimeError(
            f"Empty model output from {agent_id!r}. Ollama did not return a statement."
        )


def _parse_turn(
    text: str,
    *,
    agent: Agent,
    round_id: int,
    proposals: list[Proposal],
    budget: int,
) -> Allocation:
    _reject_fake(text, agent_id=agent.id)
    alloc = parse_allocation(
        text,
        agent_id=agent.id,
        round_id=round_id,
        proposals=proposals,
        budget=budget,
    )
    _reject_fake(alloc.reasoning, agent_id=agent.id)
    return alloc


class DiscussionEngine:
    def __init__(
        self,
        cfg: ExperimentConfig,
        backend: LLMBackend,
        proposals: list[Proposal],
        agents: list[Agent] | None = None,
    ):
        self.cfg = cfg
        self.backend = backend
        self.proposals = proposals
        self.agents = agents or default_agents()
        self.graph = topology_graph(self.agents, cfg.topology)
        self.history_messages: list[dict[str, Any]] = []
        self.rounds: list[RoundRecord] = []
        if hasattr(self.backend, "proposals"):
            self.backend.proposals = self.proposals

    def run(self) -> ExperimentResult:
        # Round 0: independent openings after reading the full catalog.
        self._run_round(0, independent=True)
        for r in range(1, self.cfg.n_rounds + 1):
            self._run_round(r, independent=False)
        last = self.rounds[-1]
        consensus = majority_merge(
            list(last.allocations.values()),
            self.proposals,
            self.cfg.budget_usd,
        )
        final = self._synthesize_final(consensus)
        return ExperimentResult(
            config={
                "budget_usd": self.cfg.budget_usd,
                "n_rounds": self.cfg.n_rounds,
                "topology": self.cfg.topology,
                "model_name": self.cfg.model_name,
                "model_size": getattr(self.cfg, "model_size", ""),
                "backend": self.cfg.backend,
                "llm_class": type(self.backend).__name__,
                "agent_models": {
                    a.id: a.model_name for a in self.agents if getattr(a, "model_name", "")
                },
                "seed": self.cfg.seed,
                "target_n_projects": self.cfg.target_n_projects,
            },
            proposals=[p.to_dict() for p in self.proposals],
            agents=[
                {
                    "id": a.id,
                    "name": a.name,
                    "title": a.title,
                    "kind": a.kind,
                    "neighborhood": a.neighborhood,
                    "model_name": a.model_name,
                }
                for a in self.agents
            ],
            rounds=self.rounds,
            final=final,
            consensus_final=consensus,
        )

    def _run_round(self, round_id: int, independent: bool) -> RoundRecord:
        agents = _order_agents(self.agents, round_id, self.cfg)
        conversations = []
        prev_allocs_by_agent = self.rounds[-1].allocations if self.rounds else {}
        for agent in agents:
            if independent:
                user = round0_user_prompt(self.proposals, self.cfg)
            else:
                recent = [
                    m
                    for m in self.history_messages
                    if m["round_id"] >= max(0, round_id - 2)
                ]
                visible = format_transcript(recent, agent.id, self.graph)
                visible_allocs = [
                    alloc
                    for aid, alloc in prev_allocs_by_agent.items()
                    if self._can_see(agent.id, aid)
                ]
                user = later_round_user_prompt(
                    self.proposals,
                    self.cfg,
                    round_id,
                    self.cfg.n_rounds,
                    visible,
                    _consensus_hint(visible_allocs),
                )
            conversations.append(
                [
                    {"role": "system", "content": agent.system},
                    {"role": "user", "content": user},
                ]
            )
        texts = self.backend.chat_batch(
            conversations,
            json_mode=False,
            agent_ids=[a.id for a in agents],
        )
        record = RoundRecord(round_id=round_id)
        for agent, conv, text in zip(agents, conversations, texts):
            alloc = self._spoken_allocation(agent, conv, text, round_id)
            record.allocations[agent.id] = alloc
            msg = _message_from_alloc(agent, alloc)
            record.messages.append(msg)
            self.history_messages.append(msg)
        self.rounds.append(record)
        return record

    def _spoken_allocation(
        self,
        agent: Agent,
        conversation: list[dict[str, str]],
        text: str,
        round_id: int,
    ) -> Allocation:
        alloc = _parse_turn(
            text,
            agent=agent,
            round_id=round_id,
            proposals=self.proposals,
            budget=self.cfg.budget_usd,
        )
        if len(spoken_text(alloc)) >= 80:
            return alloc
        print(f"  [{agent.id}] statement too short; asking the model to speak again")
        follow = conversation + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": RETRY_SPEAK},
        ]
        retry = self.backend.chat_one(follow, agent_id=agent.id, json_mode=False)
        alloc = _parse_turn(
            retry,
            agent=agent,
            round_id=round_id,
            proposals=self.proposals,
            budget=self.cfg.budget_usd,
        )
        if len(spoken_text(alloc)) < 80:
            raise RuntimeError(
                f"{agent.id} did not produce a spoken statement after retry. "
                "Confirm Ollama is serving qwen2.5:3b and is not returning JSON-only replies."
            )
        return alloc

    def _can_see(self, listener: str, speaker: str) -> bool:
        if listener == speaker:
            return True
        return self.graph.has_edge(speaker, listener)

    def _synthesize_final(self, consensus: Allocation) -> Allocation:
        # Clerk sees everyone regardless of topology.
        full = []
        for msg in self.history_messages:
            full.append(
            f"[{msg['agent_name']} r{msg['round_id']}]\n"
            f"{(msg.get('statement') or msg.get('discussion') or '')[:2000]}"
            )
        last = self.rounds[-1]
        last_text = json.dumps(
            {k: v.to_dict() for k, v in last.allocations.items()},
            indent=2,
        )[:12000]
        clerk_system = (
            "You are a neutral closing clerk for a Fresno budget deliberation. "
            "You do not represent a neighborhood. Produce one feasible $70M package. "
            "Write a STATEMENT of 4–8 sentences summarizing the agreement, then the JSON."
        )
        user = synthesizer_prompt(self.proposals, self.cfg, "\n\n".join(full)[-18000:], last_text)
        text = self.backend.chat_one(
            [{"role": "system", "content": clerk_system}, {"role": "user", "content": user}],
            json_mode=False,
            agent_id="clerk",
        )
        clerk_agent = Agent(
            id="clerk",
            name="Closing clerk",
            title="Closing clerk",
            kind="clerk",
            neighborhood=None,
            instructions=clerk_system,
        )
        final = self._spoken_allocation(
            clerk_agent,
            [{"role": "system", "content": clerk_system}, {"role": "user", "content": user}],
            text,
            self.cfg.n_rounds + 1,
        )
        final.agent_id = "final_clerk"
        if not final.items:
            return consensus
        return final


def summarize_round_overlap(record: RoundRecord) -> dict[str, Any]:
    funded = defaultdict(int)
    for alloc in record.allocations.values():
        for pid in alloc.funded_ids():
            funded[pid] += 1
    n = max(1, len(record.allocations))
    return {
        "round_id": record.round_id,
        "n_agents": n,
        "unanimous": sorted(pid for pid, c in funded.items() if c == n),
        "majority": sorted(pid for pid, c in funded.items() if c >= (n + 1) // 2),
        "counts": dict(funded),
    }
