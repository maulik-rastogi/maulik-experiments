from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .agents import Agent
from .discussion import ExperimentResult
from .proposals import Proposal


def build_record(
    result: ExperimentResult,
    *,
    proposals: list[Proposal],
    agents: list[Agent],
    source_pdfs: list[str],
    page_texts: list[dict[str, Any]] | None = None,
    record_path: str = "",
) -> dict[str, Any]:
    """One JSON object: proposals, every agent turn, transcript, final allocation."""
    by_id = {a.id: a for a in agents}
    transcript = []
    rounds_out = []
    for rnd in result.rounds:
        agent_outputs = {}
        for msg in rnd.messages:
            aid = msg["agent_id"]
            alloc = rnd.allocations.get(aid)
            if alloc is None:
                continue
            agent = by_id.get(aid)
            out = {
                "round_id": rnd.round_id,
                "agent_id": aid,
                "agent_name": msg.get("agent_name"),
                "model_name": agent.model_name if agent else "",
                "statement": alloc.statement,
                "discussion": alloc.discussion,
                "raw_output": alloc.raw_text,
                "liked_projects": alloc.liked,
                "deprioritized_projects": alloc.deprioritized,
                "unfunded": alloc.unfunded,
                "dropped_unknown_ids": alloc.dropped_unknown_ids,
                "reasoning": alloc.reasoning,
                "allocation": [
                    {
                        "project_id": i.project_id,
                        "amount_usd": i.amount_usd,
                        "rationale": i.rationale,
                    }
                    for i in alloc.items
                ],
                "total_usd": alloc.total,
            }
            agent_outputs[aid] = out
            transcript.append(out)
        rounds_out.append({"round_id": rnd.round_id, "agent_outputs": agent_outputs})

    clerk = result.final
    transcript.append(
        {
            "round_id": clerk.round_id,
            "agent_id": clerk.agent_id,
            "agent_name": "Closing clerk",
            "model_name": by_id["finance"].model_name.replace("finance", "clerk")
            if "finance" in by_id and by_id["finance"].model_name
            else "",
            "statement": clerk.statement,
            "discussion": clerk.discussion,
            "raw_output": clerk.raw_text,
            "liked_projects": clerk.liked,
            "deprioritized_projects": clerk.deprioritized,
            "unfunded": clerk.unfunded,
            "reasoning": clerk.reasoning,
            "allocation": [
                {
                    "project_id": i.project_id,
                    "amount_usd": i.amount_usd,
                    "rationale": i.rationale,
                }
                for i in clerk.items
            ],
            "total_usd": clerk.total,
        }
    )

    proposal_dicts = []
    for p in proposals:
        d = p.to_dict()
        d["raw_text"] = p.raw_text
        proposal_dicts.append(d)

    pages = []
    for pg in page_texts or []:
        pages.append(
            {
                "source_pdf": pg.get("source_pdf"),
                "source_page": pg.get("source_page"),
                "text": pg.get("text"),
            }
        )

    clerk = result.final
    return {
        "file_kind": "fresno_mas_deliberation_record",
        "created_at": result.created_at or datetime.now(timezone.utc).isoformat(),
        "saved_to": record_path,
        "config": result.config,
        "llm": {
            "backend": result.config.get("backend"),
            "llm_class": result.config.get("llm_class"),
            "model_name": result.config.get("model_name"),
            "agent_models": result.config.get("agent_models"),
            "is_real_model": result.config.get("llm_class") == "OllamaAgentPool",
        },
        "catalog_ids": [p.id for p in proposals],
        "source": {
            "pdf_files": source_pdfs,
            "n_pdfs": len(source_pdfs),
            "n_pages": len(pages) or len(proposals),
            "n_proposals": len(proposals),
        },
        "proposals": proposal_dicts,
        "pdf_page_texts": pages,
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "title": a.title,
                "kind": a.kind,
                "neighborhood": a.neighborhood,
                "model_name": a.model_name,
                "role_brief": a.instructions,
            }
            for a in agents
        ],
        "transcript": transcript,
        "rounds": rounds_out,
        "final_allocation": {
            "produced_by": clerk.agent_id,
            "round_id": clerk.round_id,
            "statement": clerk.statement,
            "reasoning": clerk.reasoning,
            "discussion": clerk.discussion,
            "raw_output": clerk.raw_text,
            "total_usd": clerk.total,
            "items": [
                {
                    "project_id": i.project_id,
                    "amount_usd": i.amount_usd,
                    "rationale": i.rationale,
                }
                for i in clerk.items
            ],
            "unfunded": clerk.unfunded,
        },
        "majority_merge_allocation": result.consensus_final.to_dict(),
    }
