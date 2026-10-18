# exp4_9b_judge_9b_agents

Qwen 3.5 9B panelists — 9B judge + improver

Agents: `qwen3.5:9b`  |  Judge: `qwen3.5:9b`

## Trends

### Star
- Average Gini fell: 0.519 (round 1) → 0.401 (round 5)
- SW $32.8M misses: 14/30 turns
- Downtown $18.5M misses: 23/30 turns
- Budget band misses ($60–66.5M): 28/30 turns
- Judge warnings stored: 29

### Parallel
- Average Gini fell: 0.513 (round 1) → 0.423 (round 5)
- SW $32.8M misses: 16/30 turns
- Downtown $18.5M misses: 18/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 29

### Ring
- Average Gini held: 0.513 (round 1) → 0.508 (round 5)
- SW $32.8M misses: 22/30 turns
- Downtown $18.5M misses: 28/30 turns
- Budget band misses ($60–66.5M): 28/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #6 North Fulton Street Mixed Use Project — 3/6 agents, avg $11,529,216 (TCC $23,058,431)
- #9 West Fresno Magnet Core Workforce Housing — 4/6 agents, avg $9,813,099 (TCC $14,719,649)
- #8 CA HSR Mixed Use Development — 2/6 agents, avg $8,000,000 (TCC $24,000,000)
- #25 Chinatown Park — 4/6 agents, avg $8,000,000 (TCC $12,000,000)
- #7 Van Ness Family Apartments — 3/6 agents, avg $5,575,000 (TCC $11,150,000)
- #5 Hotel Fresno — 3/6 agents, avg $4,656,630 (TCC $9,313,260)
- #10 Kings View Manor Rehab — 4/6 agents, avg $4,000,000 (TCC $6,000,000)
- #18 H Complete Street — 3/6 agents, avg $3,900,000 (TCC $7,800,000)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 3/6 agents, avg $3,800,000 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 3/6 agents, avg $3,703,752 (TCC $7,407,505)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #15 SW Fresno Green Trails & Cycle Paths — 3/6 agents, avg $2,500,000 (TCC $5,000,000)
- … 19 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #8 CA HSR Mixed Use Development — 3/6 agents, avg $12,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 3/6 agents, avg $11,529,216 (TCC $23,058,431)
- #9 West Fresno Magnet Core Workforce Housing — 3/6 agents, avg $7,359,824 (TCC $14,719,649)
- #25 Chinatown Park — 3/6 agents, avg $6,000,000 (TCC $12,000,000)
- #7 Van Ness Family Apartments — 3/6 agents, avg $5,575,000 (TCC $11,150,000)
- #5 Hotel Fresno — 3/6 agents, avg $4,656,630 (TCC $9,313,260)
- #18 H Complete Street — 3/6 agents, avg $3,900,000 (TCC $7,800,000)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 3/6 agents, avg $3,800,000 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 3/6 agents, avg $3,703,752 (TCC $7,407,505)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #10 Kings View Manor Rehab — 3/6 agents, avg $3,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 3/6 agents, avg $2,500,000 (TCC $5,000,000)
- … 19 more with avg $ > 0 (see graph_data.json)

### Ring (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 1/6 agents, avg $3,843,072 (TCC $23,058,431)
- #1 Chinatown Lofts — 1/6 agents, avg $1,916,667 (TCC $11,500,000)
- #7 Van Ness Family Apartments — 1/6 agents, avg $1,858,333 (TCC $11,150,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 1/6 agents, avg $1,798,507 (TCC $10,791,042)
- #5 Hotel Fresno — 1/6 agents, avg $1,552,210 (TCC $9,313,260)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 1/6 agents, avg $1,266,667 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 1/6 agents, avg $1,234,584 (TCC $7,407,505)
- #3 H Street Development — 1/6 agents, avg $708,333 (TCC $4,250,000)
- #28 Mariposa Plaza — 1/6 agents, avg $611,333 (TCC $3,668,000)
- #4 The Park @ South Fulton — 1/6 agents, avg $320,833 (TCC $1,925,000)
- #37 VOICE Gladiator Program — 1/6 agents, avg $200,000 (TCC $1,200,000)
- … 1 more with avg $ > 0 (see graph_data.json)

## Outliers

- Highest Gini: **0.750** — Citizen (Downtown Fresno) (Ring, round 3)
- Largest SW shortfall: **$32,800,000** — Sustainability Expert (Parallel, round 3)
- Largest Downtown shortfall: **$18,500,000** — Sustainability Expert (Parallel, round 3)
- Largest budget overrun: **$151,207,792** — Citizen (Chinatown) (Star, round 4)

- Most-funded proposal IDs (all topologies): #20 (87), #35 (84), #10 (34), #9 (34), #15 (33)

## Notable turns

- **Citizen (Downtown Fresno)** / Ring / R3: Gini 0.750, SW short $32,800,000, DT short $10,700,000; judge flagged.
  > As the Downtown Representative, I must address the critical equity gap identified by multiple colleagues regarding our district's underfunding. The previous panel's heavy reliance on shared projects has systematically starved Downtown of its mandated baseline while over-investing
- **Citizen (Downtown Fresno)** / Ring / R5: Gini 0.677, SW short $15,726,145, DT short $-98,072,196; judge flagged.
  > As the Downtown Community Representative, I am prioritizing our district's specific livability and housing needs to close the equity gap identified in recent feedback, ensuring we do not rely solely on shared projects that dilute direct investment. My slate strictly adheres to th
- **Financial Expert** / Star / R4: Gini 0.643, SW short $-41,095,854, DT short $3,300,000; judge flagged.
  > I am revising my slate to explicitly close the critical SOUTHWEST_UNDERFUNDING gap identified in the ImproverAgent feedback, ensuring Southwest Fresno receives robust, front-loaded funding beyond mere compliance. I reject the strategy of masking systemic deficits through cross-su
- **Sustainability Expert** / Ring / R4: Gini 0.643, SW short $-41,095,854, DT short $3,300,000; judge flagged.
  > I must immediately revise my allocation to address the critical underfunding of Southwest Fresno identified by multiple steering messages, which explicitly criticized my reliance on shared projects that dilute direct investment in this underserved area. My previous selections fai
- **Financial Expert** / Ring / R4: Gini 0.638, SW short $-40,704,999, DT short $2,100,000; judge flagged.
  > Previous panel feedback highlighted that relying heavily on shared projects like Tulare and FCC fails to address the critical underfunding of exclusive Southwest Fresno needs while simultaneously starving Downtown of its mandated baseline. The steering messages indicate a systemi
- **Citizen (SW Fresno)** / Star / R2: Gini 0.636, SW short $-42,295,854, DT short $2,100,000; judge flagged.
  > I am revising my allocation to immediately close the critical SOUTHWEST_UNDERFUNDING gap highlighted in the ImproverAgent feedback. While projects #20 (Tulare Complete Streets) and #35 (FCC West Fresno Satellite) are essential for our community, they alone do not meet the mandate
- **Financial Expert** / Ring / R3: Gini 0.636, SW short $-42,295,854, DT short $2,100,000; judge flagged.
  > I am revising my allocation to directly address the critical underfunding of Southwest Fresno identified in the ImproverAgent steering messages. While multi-area projects like Tulare Complete Streets offer connectivity, they must be supplemented with exclusive Southwest initiativ
- **Urban Planner** / Ring / R3: Gini 0.636, SW short $-42,295,854, DT short $2,100,000; judge flagged.
  > I am revising my allocation to directly address the critical underfunding of Southwest Fresno identified in the ImproverAgent steering messages. While multi-area projects like Tulare Complete Streets offer connectivity, they must be supplemented with exclusive Southwest initiativ

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

