from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


NEIGHBORHOOD_KEYS = ("southwest", "central", "northeast", "citywide")


@dataclass
class Proposal:
    id: str
    title: str
    cost_usd: int
    neighborhood: str
    category: str
    description: str
    scalability: str = ""
    beneficiaries: str = ""
    who_it_helps: str = ""
    timeline: str = ""
    cobenefits: str = ""
    maintenance: str = ""
    source_pdf: str = ""
    source_page: int | None = None
    raw_text: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def neighborhood_key(self) -> str:
        n = (self.neighborhood or "").strip().lower()
        aliases = {
            "sw": "southwest",
            "southwest fresno": "southwest",
            "west fresno": "southwest",
            "c": "central",
            "central fresno": "central",
            "downtown": "central",
            "ne": "northeast",
            "northeast fresno": "northeast",
            "city-wide": "citywide",
            "city wide": "citywide",
            "all": "citywide",
        }
        return aliases.get(n, n if n in NEIGHBORHOOD_KEYS else "citywide")

    def catalog_block(self) -> str:
        header = (
            f"[{self.id}] {self.title}\n"
            f"  Cost: ${self.cost_usd:,.0f} | Neighborhood: {self.neighborhood} | "
            f"Category: {self.category}\n"
            f"  Source: {self.source_pdf or 'pdf'} page {self.source_page or '?'}"
        )
        body = (self.raw_text or "").strip()
        if body:
            return f"{header}\n{body}"
        return (
            f"{header}\n"
            f"  What it is: {self.description.strip()}\n"
            f"  Who it helps: {self.who_it_helps or self.beneficiaries}\n"
            f"  Scalability: {self.scalability}\n"
            f"  Timeline: {self.timeline} | Maintenance: {self.maintenance}\n"
            f"  Co-benefits: {self.cobenefits}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "cost_usd": self.cost_usd,
            "neighborhood": self.neighborhood,
            "category": self.category,
            "description": self.description,
            "scalability": self.scalability,
            "beneficiaries": self.beneficiaries,
            "who_it_helps": self.who_it_helps or self.beneficiaries,
            "timeline": self.timeline,
            "cobenefits": self.cobenefits,
            "maintenance": self.maintenance,
            "source_pdf": self.source_pdf,
            "source_page": self.source_page,
            "raw_text": self.raw_text,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Proposal":
        known = {k: data.get(k) for k in cls.__dataclass_fields__ if k in data}
        extra = {k: v for k, v in data.items() if k not in cls.__dataclass_fields__}
        p = cls(**known)
        p.extra = extra
        if not p.who_it_helps:
            p.who_it_helps = p.beneficiaries
        return p


def format_catalog(proposals: Iterable[Proposal], header: bool = True) -> str:
    items = list(proposals)
    total = sum(p.cost_usd for p in items)
    lines = []
    if header:
        lines.append(
            f"PROJECT CATALOG — text extracted from the proposal PDF(s) you provided. "
            f"Use only this catalog. Do not invent projects. "
            f"Legal IDs: {', '.join(p.id for p in items)}"
        )
        lines.append(
            "Use only these IDs. Partial funding of a project is allowed "
            "(amount <= listed cost)."
        )
        lines.append("")
    lines.extend(p.catalog_block() + "\n" for p in items)
    return "\n".join(lines).strip()


def index_by_id(proposals: Iterable[Proposal]) -> dict[str, Proposal]:
    return {p.id: p for p in proposals}
