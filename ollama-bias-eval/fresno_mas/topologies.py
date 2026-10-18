"""Who hears whom. Topology is a bias lever: star/hierarchy can mute neighborhood voice."""

from __future__ import annotations

from collections import defaultdict

import networkx as nx

from .agents import Agent

HUB_ID = "finance"


def topology_graph(agents: list[Agent], topology: str) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_nodes_from(a.id for a in agents)
    ids = [a.id for a in agents]
    if topology == "fully_connected":
        for a in ids:
            for b in ids:
                if a != b:
                    g.add_edge(a, b)
    elif topology == "star":
        hub = HUB_ID if HUB_ID in ids else ids[0]
        for a in ids:
            if a != hub:
                g.add_edge(a, hub)
                g.add_edge(hub, a)
    elif topology == "ring":
        for i, a in enumerate(ids):
            g.add_edge(a, ids[(i + 1) % len(ids)])
            g.add_edge(a, ids[(i - 1) % len(ids)])
    elif topology == "hierarchical":
        experts = [a.id for a in agents if a.kind in {"finance", "sustainability"}]
        citizens = [a.id for a in agents if a.kind == "citizen"]
        for c in citizens:
            for e in experts:
                g.add_edge(c, e)  # citizens speak upward
                g.add_edge(e, c)  # experts broadcast down
        for e1 in experts:
            for e2 in experts:
                if e1 != e2:
                    g.add_edge(e1, e2)
        # citizens do not hear other neighborhoods directly
    elif topology == "neighborhood_clusters":
        by_n: dict[str, list[str]] = defaultdict(list)
        experts = []
        for a in agents:
            if a.kind == "citizen" and a.neighborhood:
                by_n[a.neighborhood].append(a.id)
            else:
                experts.append(a.id)
        for members in by_n.values():
            for a in members:
                for b in members:
                    if a != b:
                        g.add_edge(a, b)
                for e in experts:
                    g.add_edge(a, e)
                    g.add_edge(e, a)
        for e1 in experts:
            for e2 in experts:
                if e1 != e2:
                    g.add_edge(e1, e2)
    else:
        raise ValueError(f"Unknown topology: {topology}")
    return g


def visible_agent_ids(graph: nx.DiGraph, listener_id: str) -> set[str]:
    # edge speaker -> listener means listener can hear speaker
    return {src for src, dst in graph.in_edges(listener_id)} | {listener_id}


def format_transcript(
    messages: list[dict],
    listener_id: str,
    graph: nx.DiGraph,
    *,
    include_allocations: bool = True,
) -> str:
    allowed = visible_agent_ids(graph, listener_id)
    blocks = []
    for msg in messages:
        if msg["agent_id"] not in allowed:
            continue
        if msg["agent_id"] == listener_id and msg.get("hide_self"):
            continue
        head = f"[{msg['agent_name']} | {msg['agent_id']} | round {msg['round_id']}]"
        body = (msg.get("statement") or msg.get("discussion") or msg.get("text") or "").strip()
        tail = ""
        if include_allocations and msg.get("funded"):
            tail = "\nFunded this round: " + ", ".join(
                f"{pid}=${amt:,.0f}" for pid, amt in msg["funded"][:20]
            )
        blocks.append(f"{head}\n{body}{tail}")
    return "\n\n".join(blocks)
