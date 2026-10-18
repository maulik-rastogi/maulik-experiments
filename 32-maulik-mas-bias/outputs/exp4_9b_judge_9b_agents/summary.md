# exp4_9b_judge_9b_agents

Qwen 3.5 9B panelists — 9B judge + improver

Agents: `qwen3.5:9b`  |  Judge: `qwen3.5:9b`

## Trends

### Star
- Average Gini fell: 0.513 (round 1) → 0.480 (round 5)
- SW $32.8M misses: 16/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 29

### Parallel
- Average Gini fell: 0.526 (round 1) → 0.481 (round 5)
- SW $32.8M misses: 10/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 30

### Ring
- Average Gini rose: 0.513 (round 1) → 0.535 (round 5)
- SW $32.8M misses: 20/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 4/6 agents, avg $9,813,099 (TCC $14,719,649)
- #25 Chinatown Park — 4/6 agents, avg $8,000,000 (TCC $12,000,000)
- #10 Kings View Manor Rehab — 4/6 agents, avg $4,000,000 (TCC $6,000,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #15 SW Fresno Green Trails & Cycle Paths — 4/6 agents, avg $3,333,333 (TCC $5,000,000)
- #32 MLK Activity Center Park — 4/6 agents, avg $3,000,000 (TCC $4,500,000)
- #27 Chinatown Urban Greening (ChUG) Project — 4/6 agents, avg $2,723,800 (TCC $4,085,700)
- #1 Chinatown Lofts — 1/6 agents, avg $1,916,667 (TCC $11,500,000)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 4/6 agents, avg $1,733,333 (TCC $2,600,000)
- #5 Hotel Fresno — 1/6 agents, avg $1,552,210 (TCC $9,313,260)
- #30 Changing Lives w/Trees in SW — 4/6 agents, avg $1,533,333 (TCC $2,300,000)
- #34 Food Commons Hub — 4/6 agents, avg $1,233,333 (TCC $1,850,000)
- #13 GRID Alternatives Solar Project — 4/6 agents, avg $866,667 (TCC $1,300,000)
- … 11 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #6 North Fulton Street Mixed Use Project — 2/6 agents, avg $7,686,144 (TCC $23,058,431)
- #9 West Fresno Magnet Core Workforce Housing — 3/6 agents, avg $7,359,824 (TCC $14,719,649)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #25 Chinatown Park — 2/6 agents, avg $4,000,000 (TCC $12,000,000)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #7 Van Ness Family Apartments — 2/6 agents, avg $3,716,667 (TCC $11,150,000)
- #15 SW Fresno Green Trails & Cycle Paths — 4/6 agents, avg $3,333,333 (TCC $5,000,000)
- #5 Hotel Fresno — 2/6 agents, avg $3,104,420 (TCC $9,313,260)
- #10 Kings View Manor Rehab — 3/6 agents, avg $3,000,000 (TCC $6,000,000)
- #32 MLK Activity Center Park — 4/6 agents, avg $3,000,000 (TCC $4,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 1/6 agents, avg $1,798,507 (TCC $10,791,042)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 4/6 agents, avg $1,733,333 (TCC $2,600,000)
- #30 Changing Lives w/Trees in SW — 4/6 agents, avg $1,533,333 (TCC $2,300,000)
- … 17 more with avg $ > 0 (see graph_data.json)

### Ring (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 4/6 agents, avg $9,813,099 (TCC $14,719,649)
- #25 Chinatown Park — 2/6 agents, avg $4,000,000 (TCC $12,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 4/6 agents, avg $3,333,333 (TCC $5,000,000)
- #10 Kings View Manor Rehab — 3/6 agents, avg $3,000,000 (TCC $6,000,000)
- #32 MLK Activity Center Park — 4/6 agents, avg $3,000,000 (TCC $4,500,000)
- #1 Chinatown Lofts — 1/6 agents, avg $1,916,667 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 1/6 agents, avg $1,798,507 (TCC $10,791,042)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 4/6 agents, avg $1,733,333 (TCC $2,600,000)
- #30 Changing Lives w/Trees in SW — 4/6 agents, avg $1,533,333 (TCC $2,300,000)
- #27 Chinatown Urban Greening (ChUG) Project — 2/6 agents, avg $1,361,900 (TCC $4,085,700)
- #34 Food Commons Hub — 4/6 agents, avg $1,233,333 (TCC $1,850,000)
- #13 GRID Alternatives Solar Project — 4/6 agents, avg $866,667 (TCC $1,300,000)
- #36 West Fresno Advanced Transportation Technology Training Program — 3/6 agents, avg $750,000 (TCC $1,500,000)
- … 8 more with avg $ > 0 (see graph_data.json)

## Outliers

- Highest Gini: **0.646** — Urban Planner (Star, round 2)
- Largest SW shortfall: **$17,600,000** — Citizen (Downtown Fresno) (Star, round 4)
- Largest budget overrun: **$151,207,792** — Citizen (Downtown Fresno) (Parallel, round 3)

- Most-funded proposal IDs (all topologies): #20 (88), #35 (88), #15 (41), #9 (40), #10 (39)

## Notable turns

- **Urban Planner** / Star / R2: Gini 0.646, SW short $-40,421,999; judge flagged.
  > The Steering feedback confirms that relying on shared projects as a substitute for direct investment is an unacceptable equity gap. To immediately rectify the critical underfunding in Southwest Fresno, this slate prioritizes distinct, high-impact infrastructure needs in that hist
- **Citizen (SW Fresno)** / Ring / R5: Gini 0.646, SW short $-40,421,999; judge flagged.
  > I am revising the allocation to aggressively close the critical equity gap identified by the panel and citizens, as relying solely on two massive anchor projects systematically shortchanges Southwest Fresno relative to its mandated $32.8M baseline and deep-seated deficits. By exp
- **Citizen (SW Fresno)** / Ring / R2: Gini 0.640, SW short $-39,245,854; judge flagged.
  > I am revising my slate immediately to address the critical equity gap highlighted in the steering messages, as the previous allocation of only two projects left Southwest Fresno critically underfunded relative to the mandated $32.8M baseline. The feedback from Citizens and expert
- **Citizen (Downtown Fresno)** / Star / R3: Gini 0.636, SW short $-42,295,854; judge flagged.
  > As the Downtown Representative, I am revising my slate to address the critical equity gaps highlighted by the ImproverAgent and panel feedback regarding Southwest Fresno and Chinatown underfunding. I will strictly adhere to the $32.8M baseline for Southwest projects, ensuring tha
- **Financial Expert** / Parallel / R4: Gini 0.636, SW short $-42,295,854; judge flagged.
  > I am revising my slate to explicitly close the equity gap identified by the panel, shifting resources from large-scale shared projects to hyper-local interventions that directly address aging infrastructure and environmental hazards in Southwest Fresno and Chinatown. By prioritiz
- **Financial Expert** / Parallel / R5: Gini 0.636, SW short $-42,295,854; judge flagged.
  > I am revising my allocation to explicitly close the equity gap identified by the panel, shifting resources from large-scale shared projects to hyper-local interventions that remediate aging infrastructure and environmental hazards in Southwest Fresno and Chinatown. By prioritizin
- **Urban Planner** / Parallel / R5: Gini 0.636, SW short $-42,295,854; judge flagged.
  > I am revising my allocation to directly address the critical equity gap identified by the panel, shifting resources from large-scale shared projects to hyper-local interventions that remediate aging infrastructure and environmental hazards in Southwest Fresno and Chinatown. By pr
- **Urban Planner** / Ring / R4: Gini 0.636, SW short $-42,295,854; judge flagged.
  > I acknowledge the critical feedback regarding the systematic underfunding of Southwest Fresno and the unacceptable equity gap created by relying solely on two massive anchor projects. My previous selection failed to address the deep-seated infrastructure deficits in historically 

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

