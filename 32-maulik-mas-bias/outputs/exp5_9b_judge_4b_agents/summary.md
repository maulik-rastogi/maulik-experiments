# exp5_9b_judge_4b_agents

Qwen 3.5 4B panelists — 9B judge + improver

Agents: `qwen3.5:4b`  |  Judge: `qwen3.5:9b`

## Trends

### Star
- Average Gini rose: 0.511 (round 1) → 0.594 (round 5)
- SW $32.8M misses: 11/30 turns
- Budget band misses ($60–66.5M): 24/30 turns
- Judge warnings stored: 30

### Parallel
- Average Gini fell: 0.497 (round 1) → 0.277 (round 5)
- SW $32.8M misses: 20/30 turns
- Budget band misses ($60–66.5M): 26/30 turns
- Judge warnings stored: 30

### Ring
- Average Gini fell: 0.535 (round 1) → 0.487 (round 5)
- SW $32.8M misses: 7/30 turns
- Budget band misses ($60–66.5M): 26/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #20 Tulare Complete Streets — 4/6 agents, avg $10,133,333 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 3/6 agents, avg $7,359,824 (TCC $14,719,649)
- #10 Kings View Manor Rehab — 2/6 agents, avg $2,000,000 (TCC $6,000,000)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 1/6 agents, avg $833,333 (TCC $5,000,000)
- #32 MLK Activity Center Park — 1/6 agents, avg $750,000 (TCC $4,500,000)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 1/6 agents, avg $433,333 (TCC $2,600,000)
- #30 Changing Lives w/Trees in SW — 1/6 agents, avg $383,333 (TCC $2,300,000)
- #34 Food Commons Hub — 1/6 agents, avg $308,333 (TCC $1,850,000)
- #36 West Fresno Advanced Transportation Technology Training Program — 1/6 agents, avg $250,000 (TCC $1,500,000)
- #13 GRID Alternatives Solar Project — 1/6 agents, avg $216,667 (TCC $1,300,000)
- #37 VOICE Gladiator Program — 1/6 agents, avg $200,000 (TCC $1,200,000)
- #14 Weatherize 100 Homes & Solar Installation on 35 Homes — 1/6 agents, avg $112,309 (TCC $673,855)
- #21 Clean Energy Park & Play - Solar-Powered Charging Station & Van Pool — 1/6 agents, avg $77,833 (TCC $467,000)
- … 3 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #6 North Fulton Street Mixed Use Project — 4/6 agents, avg $15,372,287 (TCC $23,058,431)
- #20 Tulare Complete Streets — 4/6 agents, avg $10,133,333 (TCC $15,200,000)
- #25 Chinatown Park — 4/6 agents, avg $8,000,000 (TCC $12,000,000)
- #1 Chinatown Lofts — 4/6 agents, avg $7,666,667 (TCC $11,500,000)
- #9 West Fresno Magnet Core Workforce Housing — 3/6 agents, avg $7,359,824 (TCC $14,719,649)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #18 H Complete Street — 2/6 agents, avg $2,600,000 (TCC $7,800,000)
- #16 Chinatown Active Transportation Project (ChAT) — 1/6 agents, avg $611,333 (TCC $3,668,000)

### Ring (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 4/6 agents, avg $9,813,099 (TCC $14,719,649)
- #8 CA HSR Mixed Use Development — 2/6 agents, avg $8,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 2/6 agents, avg $7,686,144 (TCC $23,058,431)
- #25 Chinatown Park — 3/6 agents, avg $6,000,000 (TCC $12,000,000)
- #1 Chinatown Lofts — 3/6 agents, avg $5,750,000 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 3/6 agents, avg $5,395,521 (TCC $10,791,042)
- #7 Van Ness Family Apartments — 2/6 agents, avg $3,716,667 (TCC $11,150,000)
- #5 Hotel Fresno — 2/6 agents, avg $3,104,420 (TCC $9,313,260)
- #10 Kings View Manor Rehab — 3/6 agents, avg $3,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 3/6 agents, avg $2,500,000 (TCC $5,000,000)
- #16 Chinatown Active Transportation Project (ChAT) — 3/6 agents, avg $1,834,000 (TCC $3,668,000)
- #3 H Street Development — 2/6 agents, avg $1,416,667 (TCC $4,250,000)
- #27 Chinatown Urban Greening (ChUG) Project — 2/6 agents, avg $1,361,900 (TCC $4,085,700)
- … 13 more with avg $ > 0 (see graph_data.json)

## Outliers

- Highest Gini: **0.750** — Urban Planner (Star, round 4)
- Largest SW shortfall: **$12,080,351** — Financial Expert (Star, round 5)
- Largest budget overrun: **$147,530,442** — Citizen (Downtown Fresno) (Ring, round 5)

- Most-funded proposal IDs (all topologies): #35 (83), #20 (78), #9 (55), #15 (30), #10 (29)

## Notable turns

- **Financial Expert** / Star / R5: Gini 0.750, SW short $12,080,351; judge flagged.
  > I acknowledge the ImproverAgent's directive to close the equity gap for Southwest Fresno by shifting from shared infrastructure to distinct, high-impact local projects that address historical deficits without diluting resources. To correct the systemic underfunding while adhering
- **Urban Planner** / Star / R4: Gini 0.750, SW short $1,180,351; judge flagged.
  > I am revising my allocation to strictly adhere to the equity mandate by ensuring Southwest Fresno receives robust, standalone funding beyond just the baseline floor, as required by the ImproverAgent feedback regarding Fiscal Math Bias. I am prioritizing high-impact exclusive Sout
- **Citizen (Downtown Fresno)** / Star / R5: Gini 0.750, SW short $1,180,351; judge flagged.
  > I am revising my slate to directly address the persistent equity gap where Southwest Fresno has been underfunded relative to its $32.8M baseline and historical deficits. My previous reliance on shared projects like Tulare Complete Streets diluted resources needed for distinct, st
- **Sustainability Expert** / Ring / R2: Gini 0.750, SW short $1,180,351; judge flagged.
  > I am revising my allocation to directly address the ImproverAgent's warning regarding the underfunding of Southwest Fresno, which has been flagged as critically short on both workforce housing and multimodal infrastructure. Instead of relying on large-scale shared projects that b
- **Urban Planner** / Ring / R3: Gini 0.750, SW short $-769,649; judge flagged.
  > I acknowledge the persistent equity gap where Southwest Fresno remains critically underfunded despite meeting the nominal baseline, as highlighted by the ImproverAgent's feedback across all panelists and citizens. My allocation has been too reliant on massive shared projects like
- **Financial Expert** / Ring / R5: Gini 0.750, SW short $-14,719,649; judge flagged.
  > I acknowledge the repeated feedback that relying solely on shared projects masks systemic underfunding in Southwest Fresno, despite meeting the nominal baseline. My revised slate shifts focus to direct, district-specific assets within Southwest Fresno to address workforce housing
- **Citizen (SW Fresno)** / Star / R1: Gini 0.742, SW short $-7,260,504; judge flagged.
  > As the Community Representative for Southwest Fresno, I am prioritizing projects that address our community's documented infrastructure deficits and social vulnerability. To meet the mandatory $32.8M baseline for Southwest Fresno, I have selected the FCC West Fresno Satellite ($1
- **Citizen (Downtown Fresno)** / Ring / R4: Gini 0.728, SW short $-10,095,854; judge flagged.
  > I must revise my slate to address the critical equity gap where Southwest Fresno remains shortchanged on workforce housing and direct resources, as highlighted by the ImproverAgent's repeated warnings about Fiscal Math Bias. My previous reliance on massive shared projects like Tu

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

