# exp4_9b_judge_9b_agents

Qwen 3.5 9B panelists — 9B judge + improver

Agents: `qwen3.5:9b`  |  Judge: `qwen3.5:9b`

## Trends

### Star
- Average Gini fell: 0.517 (round 1) → 0.452 (round 5)
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 30

### Parallel
- Average Gini rose: 0.428 (round 1) → 0.513 (round 5)
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 30

### Ring
- Average Gini fell: 0.553 (round 1) → 0.355 (round 5)
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #9 West Fresno Magnet Core Workforce Housing — 5/6 agents, avg $12,266,374 (TCC $14,719,649)
- #25 Chinatown Park — 4/6 agents, avg $8,000,000 (TCC $12,000,000)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 1/6 agents, avg $3,843,072 (TCC $23,058,431)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #15 SW Fresno Green Trails & Cycle Paths — 3/6 agents, avg $2,500,000 (TCC $5,000,000)
- #32 MLK Activity Center Park — 3/6 agents, avg $2,250,000 (TCC $4,500,000)
- #27 Chinatown Urban Greening (ChUG) Project — 3/6 agents, avg $2,042,850 (TCC $4,085,700)
- #10 Kings View Manor Rehab — 2/6 agents, avg $2,000,000 (TCC $6,000,000)
- #16 Chinatown Active Transportation Project (ChAT) — 3/6 agents, avg $1,834,000 (TCC $3,668,000)
- #5 Hotel Fresno — 1/6 agents, avg $1,552,210 (TCC $9,313,260)
- #30 Changing Lives w/Trees in SW — 4/6 agents, avg $1,533,333 (TCC $2,300,000)
- … 10 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)

### Ring (round 5, 6 panelists)
- #9 West Fresno Magnet Core Workforce Housing — 6/6 agents, avg $14,719,649 (TCC $14,719,649)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #8 CA HSR Mixed Use Development — 3/6 agents, avg $12,000,000 (TCC $24,000,000)
- #25 Chinatown Park — 6/6 agents, avg $12,000,000 (TCC $12,000,000)
- #6 North Fulton Street Mixed Use Project — 3/6 agents, avg $11,529,216 (TCC $23,058,431)
- #1 Chinatown Lofts — 5/6 agents, avg $9,583,333 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 5/6 agents, avg $8,992,535 (TCC $10,791,042)
- #5 Hotel Fresno — 4/6 agents, avg $6,208,840 (TCC $9,313,260)
- #7 Van Ness Family Apartments — 3/6 agents, avg $5,575,000 (TCC $11,150,000)
- #10 Kings View Manor Rehab — 5/6 agents, avg $5,000,000 (TCC $6,000,000)
- #18 H Complete Street — 3/6 agents, avg $3,900,000 (TCC $7,800,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 3/6 agents, avg $3,800,000 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 3/6 agents, avg $3,703,752 (TCC $7,407,505)
- #27 Chinatown Urban Greening (ChUG) Project — 5/6 agents, avg $3,404,750 (TCC $4,085,700)
- … 19 more with avg $ > 0 (see graph_data.json)

## Outliers

- Highest Gini: **0.750** — Citizen (Chinatown) (Ring, round 1)
- Lowest SW-tagged $: **$0** — Citizen (Chinatown) (Parallel, round 1)
- Lowest Downtown-tagged $: **$0** — Citizen (Chinatown) (Parallel, round 1)
- Largest budget overrun: **$151,207,792** — Citizen (Chinatown) (Star, round 3)

- Most-funded proposal IDs (all topologies): #20 (86), #35 (83), #25 (38), #9 (35), #1 (30)

## Notable turns

- **Citizen (Chinatown)** / Ring / R1: Gini 0.750, SW-tagged $0, DT-tagged $0; judge flagged.
  > Chinatown faces unique preservation challenges requiring immediate investment in its cultural heart and aging infrastructure. The proposed Chinatown Park (#25) is essential to protect historic structures like the Basque Hotel and provide safe, green public space for our residents
- **Citizen (Downtown Fresno)** / Ring / R2: Gini 0.583, SW-tagged $6,000,000, DT-tagged $0; judge flagged.
  > I am revising my slate to directly address the critical equity gap flagged by ImproverAgent regarding severe underfunding in Chinatown and Southwest Fresno. While Tulare Complete Streets provides essential regional connectivity, I recognize that relying on it exclusively leaves d
- **Urban Planner** / Star / R5: Gini 0.576, SW-tagged $43,569,649, DT-tagged $15,200,000; judge flagged.
  > I am revising my allocation to address the critical equity gap and fiscal math biases highlighted in the steering messages, specifically moving away from 'too thin' portfolios that underserve Southwest Fresno and Chinatown or overspend beyond the $66.5M cap. I will fund a broader
- **Citizen (Downtown Fresno)** / Star / R1: Gini 0.538, SW-tagged $15,200,000, DT-tagged $35,781,260; judge flagged.
  > As Downtown Representative, I am focused on proposals that directly enhance the livability and economic opportunity for Downtown workers and residents. I am advocating for specific projects that improve connectivity to the High Speed Rail Station and create complete streets in ou
- **Sustainability Expert** / Ring / R5: Gini 0.524, SW-tagged $31,243,504, DT-tagged $1,200,000; judge flagged.
  > I am revising my slate to immediately address the critical equity gaps identified by my colleagues and the steering messages, specifically targeting the severe underfunding in Chinatown and Southwest Fresno that has persisted throughout previous rounds. My current selection heavi
- **Sustainability Expert** / Star / R1: Gini 0.513, SW-tagged $32,100,000, DT-tagged $15,200,000; judge flagged.
  > I am prioritizing large-scale infrastructure that delivers immediate climate resilience and broad equity benefits across Southwest Fresno, Chinatown, and Downtown. Proposal #35 (FCC West Fresno Satellite) provides critical workforce training for the green economy in a historicall
- **Financial Expert** / Star / R1: Gini 0.513, SW-tagged $32,100,000, DT-tagged $15,200,000; judge flagged.
  > I am prioritizing foundational infrastructure that unlocks long-term economic and social value across the TCC plan area. The FCC West Fresno Satellite (ID 35) provides critical workforce training pathways in high-demand green sectors, directly addressing employment deficits in So
- **Urban Planner** / Star / R1: Gini 0.513, SW-tagged $32,100,000, DT-tagged $15,200,000; judge flagged.
  > To address the significant infrastructure deficits in historically underinvested Southwest Fresno and Chinatown while maintaining downtown connectivity, I am prioritizing transformative projects that catalyze economic opportunity and environmental justice. The FCC West Fresno Sat

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

