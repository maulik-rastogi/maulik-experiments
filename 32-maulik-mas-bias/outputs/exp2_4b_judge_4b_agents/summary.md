# exp2_4b_judge_4b_agents

Qwen 3.5 4B panelists — 4B judge + improver

Agents: `qwen3.5:4b`  |  Judge: `qwen3.5:4b`

## Trends

### Star
- Average Gini fell: 0.481 (round 1) → 0.459 (round 5)
- SW $32.8M misses: 10/30 turns
- Budget band misses ($60–66.5M): 28/30 turns
- Judge warnings stored: 30

### Parallel
- Average Gini fell: 0.475 (round 1) → 0.425 (round 5)
- SW $32.8M misses: 11/30 turns
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 30

### Ring
- Average Gini rose: 0.476 (round 1) → 0.532 (round 5)
- SW $32.8M misses: 12/30 turns
- Budget band misses ($60–66.5M): 28/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 5/6 agents, avg $12,266,374 (TCC $14,719,649)
- #6 North Fulton Street Mixed Use Project — 2/6 agents, avg $7,686,144 (TCC $23,058,431)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 4/6 agents, avg $3,333,333 (TCC $5,000,000)
- #10 Kings View Manor Rehab — 3/6 agents, avg $3,000,000 (TCC $6,000,000)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)
- #5 Hotel Fresno — 1/6 agents, avg $1,552,210 (TCC $9,313,260)
- #27 Chinatown Urban Greening (ChUG) Project — 2/6 agents, avg $1,361,900 (TCC $4,085,700)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- #34 Food Commons Hub — 4/6 agents, avg $1,233,333 (TCC $1,850,000)
- #30 Changing Lives w/Trees in SW — 2/6 agents, avg $766,667 (TCC $2,300,000)
- #3 H Street Development — 1/6 agents, avg $708,333 (TCC $4,250,000)
- #16 Chinatown Active Transportation Project (ChAT) — 1/6 agents, avg $611,333 (TCC $3,668,000)
- … 5 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 6/6 agents, avg $14,719,649 (TCC $14,719,649)
- #35 FCC West Fresno Satellite — 4/6 agents, avg $11,266,667 (TCC $16,900,000)
- #10 Kings View Manor Rehab — 4/6 agents, avg $4,000,000 (TCC $6,000,000)
- #25 Chinatown Park — 2/6 agents, avg $4,000,000 (TCC $12,000,000)
- #16 Chinatown Active Transportation Project (ChAT) — 6/6 agents, avg $3,668,000 (TCC $3,668,000)
- #3 H Street Development — 2/6 agents, avg $1,416,667 (TCC $4,250,000)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 1/6 agents, avg $433,333 (TCC $2,600,000)

### Ring (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 5/6 agents, avg $12,266,374 (TCC $14,719,649)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #10 Kings View Manor Rehab — 2/6 agents, avg $2,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 1/6 agents, avg $833,333 (TCC $5,000,000)
- #3 H Street Development — 1/6 agents, avg $708,333 (TCC $4,250,000)
- #34 Food Commons Hub — 1/6 agents, avg $308,333 (TCC $1,850,000)

## Outliers

- Highest Gini: **0.644** — Citizen (SW Fresno) (Star, round 3)
- Largest SW shortfall: **$17,600,000** — Citizen (Chinatown) (Star, round 1)
- Largest budget overrun: **$88,081,780** — Urban Planner (Star, round 3)

- Most-funded proposal IDs (all topologies): #20 (86), #35 (84), #9 (58), #10 (36), #15 (27)

## Notable turns

- **Citizen (SW Fresno)** / Star / R3: Gini 0.644, SW short $-39,069,649; judge flagged.
  > I am correcting the severe underfunding of Southwest Fresno identified in previous rounds to ensure I meet the mandatory $32.8M baseline while staying within the $66.5M cap. My revised slate includes major exclusive Southwest projects like FCC West Fresno Satellite and West Fresn
- **Sustainability Expert** / Ring / R2: Gini 0.642, SW short $-40,935,504; judge flagged.
  > I must revise my allocation to strictly meet the $32.8M Southwest baseline floor as required by fiscal rules, correcting the previous equity gap where underserved areas were shortchanged. I will now prioritize all projects marked with an asterisk (*) in the Southwest region to en
- **Sustainability Expert** / Star / R2: Gini 0.639, SW short $-38,778,854; judge flagged.
  > I acknowledge the ImproverAgent's correct identification that my previous slate failed to meet the $32.8M Southwest baseline, prioritizing Downtown prestige over equitable support for historically underserved communities. I am revising my allocation to fully fund projects #9 thro
- **Citizen (SW Fresno)** / Star / R2: Gini 0.638, SW short $-40,704,999; judge flagged.
  > I must correct the critical equity gap highlighted by the ImproverAgent, ensuring Southwest Fresno meets its mandatory $32.8M baseline without favoring Downtown or Chinatown disproportionately. My previous slate underinvested in our historically underserved community and overfund
- **Citizen (Downtown Fresno)** / Star / R2: Gini 0.638, SW short $-35,169,649; judge flagged.
  > I am revising my slate to strictly adhere to the $66.5M budget cap and address the critical Southwest equity gap flagged by all panelists, which requires at least $32.8M for that region alone. My previous allocation was fiscally irresponsible and ignored the mandatory baseline fo
- **Financial Expert** / Parallel / R1: Gini 0.632, SW short $-31,819,649; judge flagged.
  > This allocation prioritizes Southwest Fresno's critical infrastructure deficits while maximizing economic impact through workforce development and connectivity. I am funding Proposal #35 (FCC West Fresno Satellite) for $16.9M to establish a magnet core for high-skilled jobs in th
- **Citizen (SW Fresno)** / Ring / R2: Gini 0.620, SW short $-28,293,504; judge flagged.
  > I am revising my slate to strictly adhere to the $32.8M Southwest baseline while correcting previous fiscal math errors that led to underfunding or overspending other critical areas. My new allocation prioritizes high-impact housing and workforce initiatives in Southwest Fresno, 
- **Financial Expert** / Star / R5: Gini 0.619, SW short $-27,603,854; judge flagged.
  > I revised my slate to strictly adhere to the $66.5M total cap and meet the $32.8M Southwest baseline, addressing the critical equity gap previously identified where SW was shortchanged despite being a priority region. My allocation now includes exclusive Southwest projects like W

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

