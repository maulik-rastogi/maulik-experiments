"""transcript.py — per-experiment human-readable negotiation log."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Dict, Optional


class TranscriptLogger:
    def __init__(self, path: str, echo_to_terminal: bool = True):
        self.path = path
        self.echo = echo_to_terminal
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._fh = open(path, "w", encoding="utf-8")
        self._write(
            f"\n{'=' * 90}\n"
            f"EXPERIMENT TRANSCRIPT  {datetime.now(timezone.utc).isoformat()}\n"
            f"File: {path}\n"
            f"{'=' * 90}\n"
        )

    def log_topology_header(
        self,
        topology: str,
        experiment: str,
        model: str,
        rounds: int,
        use_judge: bool,
    ):
        self._write(
            f"\n\n{'#' * 90}\n"
            f"# TOPOLOGY: {topology.upper()}\n"
            f"# Experiment: {experiment}\n"
            f"# {model}\n"
            f"# Rounds: {rounds}  |  Judge+Improver: {'ON' if use_judge else 'OFF'}\n"
            f"# Started: {datetime.now(timezone.utc).isoformat()}\n"
            f"{'#' * 90}\n"
        )

    # ------------------------------------------------------------------
    # Internal writer
    # ------------------------------------------------------------------

    def _write(self, text: str):
        self._fh.write(text)
        self._fh.flush()
        if self.echo:
            sys.stdout.write(text)
            sys.stdout.flush()

    # ------------------------------------------------------------------
    # Public logging methods
    # ------------------------------------------------------------------

    def log_section(self, title: str):
        self._write(f"\n{'─' * 70}\n  {title}\n{'─' * 70}\n")

    def log_message(
        self,
        turn_index: int,
        speaker: str,
        role: str,
        content: str,
        reasoning: str,
        gini: float,
        neighborhood_totals: Dict[str, float],
        total_allocated: float,
        round_number: int,
        sw_full_usd: float = 0.0,
        downtown_full_usd: float = 0.0,
        funded_lines: str = "",
        fiscal_flags: Optional[list] = None,
    ):
        # Header total is always the bucket sum so the four lines cannot drift.
        bucket_sum = sum(neighborhood_totals.values())
        display_total = bucket_sum
        sw_display = sw_full_usd if sw_full_usd else (
            neighborhood_totals.get("Southwest Fresno", 0.0)
            + neighborhood_totals.get("Shared", 0.0)
        )
        dt_display = downtown_full_usd if downtown_full_usd else (
            neighborhood_totals.get("Downtown Fresno", 0.0)
        )
        nbhd_str = "  |  ".join(
            f"{k}: ${v:,.0f}" for k, v in neighborhood_totals.items()
        )
        flag_str = ", ".join(fiscal_flags) if fiscal_flags else "none"
        header = (
            f"\n[Round {round_number} | Turn {turn_index:03d}]  "
            f"{speaker}  ({role})\n"
            f"  Gini: {gini:.4f}\n"
            f"  Budget total (sum of project $ = SW + CH + DT + Shared): "
            f"${display_total:,.0f}\n"
            f"  SW-tagged (Southwest + Shared): ${sw_display:,.0f}\n"
            f"  Downtown-tagged: ${dt_display:,.0f}\n"
            f"  Budget-band flags: {flag_str}\n"
            f"  Neighborhoods + Shared (sum ${bucket_sum:,.0f}):\n"
            f"    {nbhd_str}\n"
        )
        divider = "─" * 80
        funded_block = (
            f"FUNDED (each ID at catalog TCC; sum is the budget total):\n{funded_lines.strip()}\n\n"
            if funded_lines.strip() else ""
        )
        body = (
            f"{divider}\n"
            f"{funded_block}"
            f"REASONING:\n{reasoning.strip()}\n\n"
            f"FULL RESPONSE:\n{content.strip()}\n"
        )
        self._write(f"{header}{body}")

    def log_judge(
        self,
        speaker: str,
        judge_text: str,
        bias_detected: bool,
        turn_index: int,
    ):
        flag  = "BIAS DETECTED" if bias_detected else "No significant bias"
        block = (
            f"\n  ┌─ JUDGE EVALUATION of {speaker} (Turn {turn_index:03d}) ─────\n"
            f"  │  {flag}\n"
        )
        for line in judge_text.strip().split("\n"):
            block += f"  │  {line}\n"
        block += "  └" + "─" * 60 + "\n"
        self._write(block)

    def log_improver(
        self,
        speaker: str,
        improver_text: str,
        turn_index: int,
    ):
        block = (
            f"\n  ┌─ IMPROVER NOTE for {speaker} (Turn {turn_index:03d}) ─────\n"
            f"  │  Broadcast to all panelists — addressed to {speaker}\n"
        )
        for line in (improver_text or "").strip().split("\n"):
            block += f"  │  {line}\n"
        block += "  └" + "─" * 60 + "\n"
        self._write(block)

    def log_note(self, text: str):
        self._write(f"\n[NOTE] {text}\n")

    def log_consensus(self, consensus: dict):
        rnd = consensus.get("round", 0)
        n = consensus.get("n_agents", 0)
        rows = consensus.get("projects") or []
        funded = [r for r in rows if r.get("average_usd", 0) > 0]
        lines = [
            "",
            "=" * 90,
            f"FINAL-ROUND CONSENSUS  (round {rnd}, {n} panelists)",
            "Each project: (sum of 6 panelists' TCC amounts) / 6. Unfunded = $0.",
            "=" * 90,
        ]
        if not funded:
            lines.append("  (no projects funded in the final round)")
        for r in funded:
            lines.append(
                f"  #{r['id']:<3} {r['title'][:48]:<48}  "
                f"{r['neighborhoods']:<28}  "
                f"{r['n_agents_funding']}/{r['n_agents']} agents  "
                f"avg ${r['average_usd']:,.0f}  "
                f"(TCC ${r['tcc_request']:,.0f})"
            )
        zero = len(rows) - len(funded)
        if zero:
            lines.append(f"  … {zero} catalog projects averaged $0")
        lines.append("=" * 90 + "\n")
        self._write("\n".join(lines))

    def close(self):
        self._write(
            f"\n{'=' * 90}\n"
            f"TRANSCRIPT END  {datetime.now(timezone.utc).isoformat()}\n"
            f"{'=' * 90}\n"
        )
        self._fh.close()
