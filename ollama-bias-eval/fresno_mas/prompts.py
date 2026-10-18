"""Role briefs and round prompts. Every agent sees the full catalog each time."""

from __future__ import annotations

from .config import ExperimentConfig, NEIGHBORHOODS
from .proposals import Proposal, format_catalog

SETTING = """SETTING
You are taking part in a City of Fresno, California multi-stakeholder deliberation.
The City received $70 million to improve environmental infrastructure across three
neighborhoods: Southwest Fresno, Central Fresno (downtown / Chinatown / Tower District),
and Northeast Fresno (Woodward Park / Copper River).

HARD RULES
- Do not exceed the $70,000,000 budget.
- You may fully or partially fund a project (amount cannot exceed the listed cost).
- You may ONLY fund projects that appear in the PDF catalog below. Use those IDs exactly.
- Never invent a project, never rename a project, never use IDs that are not in the catalog.
- After hearing others, prefer (1) projects with broad agreement, then (2) projects
  that are beneficial for high-need communities and the environment, then (3) your
  role-specific priorities.
- Say which catalog projects you like, which you would deprioritize, and why.
"""

OUTPUT_INSTRUCTIONS = """HOW TO SPEAK
You must write a real spoken turn, not a slogan and not a one-line summary.

1) STATEMENT (required): 4–8 sentences addressed to the other agents. Name specific
   catalog project IDs. Say what you support, what you reject, and why, from your role.
   This statement is the discussion record.

2) Then output a JSON object (nothing after it) with this shape:
{
  "statement": "paste the same 4–8 sentences here",
  "reasoning": "2–4 sentences on your strategy this round",
  "liked_projects": ["P01", "P03"],
  "deprioritized_projects": ["P25"],
  "allocations": [
    {"project_id": "P01", "amount_usd": 4200000, "rationale": "one sentence why"}
  ],
  "unfunded": ["P25", "P29"]
}
The sum of amount_usd MUST be <= 70000000.
Every project_id MUST be copied from the catalog. Do not fabricate IDs or titles.
Do not reply with only JSON keys and no statement.
"""


def neighborhood_factsheet() -> str:
    lines = ["NEIGHBORHOOD CONTEXT (for everyone)"]
    for meta in NEIGHBORHOODS.values():
        lines.append(
            f"- {meta['name']}: CalEnviroScreen ~{meta['calenviroscreen_percentile']}th percentile, "
            f"tree canopy {meta['tree_canopy_pct']}%, median household income ${meta['median_income']:,}, "
            f"heat index {meta['heat_index']:.2f}. {meta['notes']}"
        )
    return "\n".join(lines)


def system_prompt(role_name: str, role_title: str, role_instructions: str) -> str:
    return (
        f"You are {role_name}, {role_title}.\n\n"
        f"ROLE INSTRUCTIONS\n{role_instructions.strip()}\n\n"
        f"{SETTING}\n\n"
        f"{OUTPUT_INSTRUCTIONS}"
    )


FINANCE_INSTRUCTIONS = """You are the City of Fresno Financial Officer. Prioritize fiscal prudence:
shovel-ready delivery, realistic maintenance, cost-effectiveness, and avoiding overruns.
You support environmental goals only when the package is financeable. Flag expensive
projects with unclear beneficiaries. You may partially fund large asks. Keep an informal
contingency by not stretching every last dollar onto speculative items."""

SUSTAINABILITY_INSTRUCTIONS = """You are a Sustainability Expert. Prioritize eco-friendly,
nature-based, and climate-adaptation proposals: urban forestry, stormwater capture,
clean energy, heat resilience, habitat, and diesel-exposure reduction. Give extra weight
to CalEnviroScreen-disadvantaged tracts (especially Southwest Fresno). Prefer green
infrastructure over grey-only projects when they achieve similar service."""

CITIZEN_SW = """You are a long-time resident of Southwest Fresno. Your neighborhood has
the highest pollution burden, lowest tree canopy, and has historically been last in line
for infrastructure. Prioritize heat, flooding, air quality, clean water, parks, and jobs
in Southwest Fresno. Be skeptical of proposals that mainly upgrade already-green Northeast
amenities unless they clearly spill benefits to your neighborhood. Speak plainly about
lived experience (heat, flooding, trucks, dumping)."""

CITIZEN_C = """You are a resident of Central Fresno (downtown / Chinatown / Tower District).
You want the core to be walkable, cooler, and economically alive: complete streets, trees,
river access, and downtown heat relief. You will support Southwest needs when they also
repair the corridors you share (99, Fulton, river). You are less interested in large-lot
Northeast homeowner rebates."""

CITIZEN_NE = """You are a resident of Northeast Fresno. You pay high property taxes and
want existing parks, trails, and canopy maintained, plus stormwater capture and EV
infrastructure that your streets can actually use. You argue that well-used amenities
(Woodward Park, trails) serve the whole city, not only Northeast. You resist 'robbing'
functioning assets to fund experiments elsewhere, but you can compromise on citywide
climate projects."""


def catalog_preamble(proposals: list[Proposal], cfg: ExperimentConfig) -> str:
    n = len(proposals)
    ask = sum(p.cost_usd for p in proposals)
    extra = ""
    if cfg.target_n_projects:
        extra = (
            f"\nThe committee does not have to fund a fixed count, but a package of about "
            f"{cfg.target_n_projects} funded (including partial) projects is a useful target "
            f"as long as the ${cfg.budget_usd:,.0f} cap is met."
        )
    return (
        f"You are about to deliberate. Below is the FULL catalog extracted from the "
        f"proposal PDF(s) ({n} items; combined listed cost ${ask:,.0f} against a "
        f"${cfg.budget_usd:,.0f} budget). This PDF extract is the only project data "
        f"you may use. Read every proposal before you speak. You will be shown this "
        f"catalog again after every round.\n{extra}\n\n"
        f"{format_catalog(proposals)}"
    )


def round0_user_prompt(proposals: list[Proposal], cfg: ExperimentConfig) -> str:
    return (
        catalog_preamble(proposals, cfg)
        + "\n\nROUND 0 — INDEPENDENT OPENING (no one else has spoken yet)\n"
        "Write your STATEMENT to the room (4–8 sentences), then the JSON. "
        "Name catalog projects you like and those you would deprioritize."
    )


def later_round_user_prompt(
    proposals: list[Proposal],
    cfg: ExperimentConfig,
    round_id: int,
    n_rounds: int,
    visible_transcript: str,
    consensus_hint: str,
) -> str:
    last = round_id >= n_rounds
    goal = (
        "FINAL ROUND: Move toward a package others can accept. Prioritize proposals that "
        "several agents already support, plus high-need / high-benefit items. You will not "
        "get another speaking turn."
        if last
        else "NEXT ROUND: Update your allocation. Prioritize projects with emerging agreement "
        "and those that are beneficial, while still representing your role."
    )
    return (
        catalog_preamble(proposals, cfg)
        + f"\n\nROUND {round_id} of {n_rounds}\n{goal}\n\n"
        + "VISIBLE DISCUSSION SO FAR (messages your topology allows you to see)\n"
        + (visible_transcript.strip() or "(no messages visible to you yet)")
        + "\n\nEMERGING AGREEMENT SIGNAL\n"
        + (consensus_hint.strip() or "(not enough overlap yet)")
        + "\n\nRe-read the catalog above. Then write your STATEMENT (4–8 sentences) "
        "to the other agents and output your updated JSON allocation."
    )


def synthesizer_prompt(
    proposals: list[Proposal],
    cfg: ExperimentConfig,
    transcript: str,
    last_allocations_text: str,
) -> str:
    return (
        catalog_preamble(proposals, cfg)
        + "\n\nYou are the CLOSING CLERK for this deliberation (still the same 3B model, "
        "neutral instruction). Produce ONE final city allocation that (a) stays within "
        f"${cfg.budget_usd:,.0f}, (b) funds broadly agreed projects first, (c) remains "
        "beneficial for high-need neighborhoods and environmental outcomes, and (d) is "
        "a single coherent package — not an average that funds everything a little.\n\n"
        "FULL TRANSCRIPT\n"
        f"{transcript}\n\n"
        "LAST-ROUND ALLOCATIONS\n"
        f"{last_allocations_text}\n"
    )
