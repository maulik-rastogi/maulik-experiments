from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .prompts import (
    CITIZEN_C,
    CITIZEN_NE,
    CITIZEN_SW,
    FINANCE_INSTRUCTIONS,
    SUSTAINABILITY_INSTRUCTIONS,
    system_prompt,
)


@dataclass
class Agent:
    id: str
    name: str
    title: str
    kind: str  # finance | sustainability | citizen
    neighborhood: str | None
    instructions: str
    extra: dict[str, Any] = field(default_factory=dict)
    model_name: str = ""

    @property
    def system(self) -> str:
        return system_prompt(self.name, self.title, self.instructions)


def default_agents() -> list[Agent]:
    return [
        Agent(
            id="finance",
            name="Alex Navarro",
            title="Financial Officer, City of Fresno",
            kind="finance",
            neighborhood=None,
            instructions=FINANCE_INSTRUCTIONS,
        ),
        Agent(
            id="sustainability",
            name="Dr. Priya Menon",
            title="Sustainability Expert",
            kind="sustainability",
            neighborhood=None,
            instructions=SUSTAINABILITY_INSTRUCTIONS,
        ),
        Agent(
            id="citizen_sw",
            name="Rosa Delgado",
            title="Resident of Southwest Fresno",
            kind="citizen",
            neighborhood="southwest",
            instructions=CITIZEN_SW,
        ),
        Agent(
            id="citizen_c",
            name="Marcus Lee",
            title="Resident of Central Fresno",
            kind="citizen",
            neighborhood="central",
            instructions=CITIZEN_C,
        ),
        Agent(
            id="citizen_ne",
            name="Helen Park",
            title="Resident of Northeast Fresno",
            kind="citizen",
            neighborhood="northeast",
            instructions=CITIZEN_NE,
        ),
    ]


def agent_by_id(agents: list[Agent], aid: str) -> Agent:
    for a in agents:
        if a.id == aid:
            return a
    raise KeyError(aid)
