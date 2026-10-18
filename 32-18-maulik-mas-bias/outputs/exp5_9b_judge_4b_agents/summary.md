# exp5_9b_judge_4b_agents

Qwen 3.5 4B panelists — 9B judge + improver

Agents: `qwen3.5:4b`  |  Judge: `qwen3.5:9b`

## Trends

### Star
- Average Gini fell: 0.527 (round 1) → 0.269 (round 5)
- SW $32.8M misses: 10/30 turns
- Downtown $18.5M misses: 9/30 turns
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 29

### Parallel
- Average Gini rose: 0.415 (round 1) → 0.473 (round 5)
- SW $32.8M misses: 17/30 turns
- Downtown $18.5M misses: 20/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 30

### Ring
- Average Gini fell: 0.509 (round 1) → 0.471 (round 5)
- SW $32.8M misses: 17/30 turns
- Downtown $18.5M misses: 18/30 turns
- Budget band misses ($60–66.5M): 28/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #6 North Fulton Street Mixed Use Project — 3/6 agents, avg $11,529,216 (TCC $23,058,431)
- #35 FCC West Fresno Satellite — 4/6 agents, avg $11,266,667 (TCC $16,900,000)
- #25 Chinatown Park — 5/6 agents, avg $10,000,000 (TCC $12,000,000)
- #9 West Fresno Magnet Core Workforce Housing — 4/6 agents, avg $9,813,099 (TCC $14,719,649)
- #1 Chinatown Lofts — 3/6 agents, avg $5,750,000 (TCC $11,500,000)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #10 Kings View Manor Rehab — 3/6 agents, avg $3,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 3/6 agents, avg $2,500,000 (TCC $5,000,000)
- #32 MLK Activity Center Park — 3/6 agents, avg $2,250,000 (TCC $4,500,000)
- #27 Chinatown Urban Greening (ChUG) Project — 3/6 agents, avg $2,042,850 (TCC $4,085,700)
- #7 Van Ness Family Apartments — 1/6 agents, avg $1,858,333 (TCC $11,150,000)
- #16 Chinatown Active Transportation Project (ChAT) — 3/6 agents, avg $1,834,000 (TCC $3,668,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 1/6 agents, avg $1,798,507 (TCC $10,791,042)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- … 8 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 4/6 agents, avg $9,813,099 (TCC $14,719,649)
- #6 North Fulton Street Mixed Use Project — 2/6 agents, avg $7,686,144 (TCC $23,058,431)
- #35 FCC West Fresno Satellite — 1/6 agents, avg $2,816,667 (TCC $16,900,000)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)
- #10 Kings View Manor Rehab — 1/6 agents, avg $1,000,000 (TCC $6,000,000)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 2/6 agents, avg $866,667 (TCC $2,600,000)
- #15 SW Fresno Green Trails & Cycle Paths — 1/6 agents, avg $833,333 (TCC $5,000,000)
- #27 Chinatown Urban Greening (ChUG) Project — 1/6 agents, avg $680,950 (TCC $4,085,700)
- #16 Chinatown Active Transportation Project (ChAT) — 1/6 agents, avg $611,333 (TCC $3,668,000)
- #14 Weatherize 100 Homes & Solar Installation on 35 Homes — 1/6 agents, avg $112,309 (TCC $673,855)

### Ring (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #6 North Fulton Street Mixed Use Project — 2/6 agents, avg $7,686,144 (TCC $23,058,431)
- #9 West Fresno Magnet Core Workforce Housing — 2/6 agents, avg $4,906,550 (TCC $14,719,649)
- #3 H Street Development — 2/6 agents, avg $1,416,667 (TCC $4,250,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 1/6 agents, avg $1,266,667 (TCC $7,600,000)
- #10 Kings View Manor Rehab — 1/6 agents, avg $1,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 1/6 agents, avg $833,333 (TCC $5,000,000)
- #27 Chinatown Urban Greening (ChUG) Project — 1/6 agents, avg $680,950 (TCC $4,085,700)
- #30 Changing Lives w/Trees in SW — 1/6 agents, avg $383,333 (TCC $2,300,000)
- #34 Food Commons Hub — 1/6 agents, avg $308,333 (TCC $1,850,000)

## Outliers

- Highest Gini: **0.750** — Citizen (Downtown Fresno) (Star, round 2)
- Largest SW shortfall: **$32,800,000** — Citizen (Chinatown) (Ring, round 1)
- Largest Downtown shortfall: **$18,500,000** — Citizen (Chinatown) (Star, round 1)
- Largest budget overrun: **$150,652,442** — Citizen (Downtown Fresno) (Ring, round 1)

- Most-funded proposal IDs (all topologies): #20 (81), #35 (73), #9 (40), #6 (32), #25 (26)

## Notable turns

- **Citizen (Chinatown)** / Ring / R1: Gini 0.750, SW short $32,800,000, DT short $18,500,000; judge flagged.
  > As Chinatown Representative, I am prioritizing projects that address our community's specific vulnerabilities regarding aging infrastructure and economic resilience. My initial slate focuses on Proposal #1 (Chinatown Lofts) for its high-density affordable housing impact, Proposal
- **Citizen (Chinatown)** / Ring / R3: Gini 0.750, SW short $32,800,000, DT short $18,500,000; judge flagged.
  > As the Community Representative for Chinatown, I must address the critical equity gap where Southwest and Downtown baselines are being masked by shared projects while my community remains underfunded despite having no dollar floor. I will revise my slate to fund dedicated Chinato
- **Citizen (Downtown Fresno)** / Star / R2: Gini 0.750, SW short $16,400,000, DT short $2,100,000; judge flagged.
  > I am adjusting my slate to address the critical equity gaps highlighted by the ImproverAgent, specifically the underfunding of Downtown's $18.5M baseline and the dismissal of Chinatown despite its unique vulnerabilities. To correct these imbalances without exceeding the $66.5M ca
- **Citizen (SW Fresno)** / Ring / R2: Gini 0.750, SW short $1,180,351, DT short $18,500,000; judge flagged.
  > I am revising my slate to address the critical Southwest underfunding identified by the ImproverAgent, ensuring I meet the $32.8M baseline with specific dedicated projects rather than relying solely on shared initiatives. I will fund the FCC West Fresno Satellite and West Fresno 
- **Citizen (SW Fresno)** / Parallel / R2: Gini 0.750, SW short $-6,669,649, DT short $18,500,000; judge flagged.
  > I acknowledge the ImproverAgent's valid critique that relying on shared projects like Tulare Complete Streets dilutes direct investment in Southwest Fresno's unique deficits. I have revised my slate to meet the $32.8M Southwest baseline exclusively through dedicated SW projects, 
- **Citizen (Chinatown)** / Star / R1: Gini 0.742, SW short $32,126,145, DT short $18,500,000; judge flagged.
  > As Chinatown's Community Representative, I am prioritizing critical infrastructure that addresses our unique vulnerabilities: aging buildings, lack of green space, and economic isolation. While the Southwest and Downtown baselines are met by the high-cost projects like the FCC We
- **Sustainability Expert** / Ring / R4: Gini 0.742, SW short $-8,895,854, DT short $18,500,000; judge flagged.
  > I am revising my slate to correct the severe Southwest Fresno underfunding and Fiscal Math bias identified in the feedback, ensuring I meet the $32.8M baseline with dedicated local projects rather than relying solely on shared multi-area initiatives. My current selection of only 
- **Sustainability Expert** / Ring / R3: Gini 0.628, SW short $-29,636,649, DT short $3,300,000; judge flagged.
  > I acknowledge the repeated feedback that Southwest Fresno's baseline is critically underfunded by relying too heavily on shared projects like Tulare Complete Streets, which masks specific local deficits. To correct this Fiscal Math Bias and ensure equitable investment for histori

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

