# exp3_9b_no_judge

Qwen 3.5 9B panelists — no judge / no improver

Agents: `qwen3.5:9b`  |  Judge: OFF

## Trends

### Star
- Average Gini fell: 0.519 (round 1) → 0.496 (round 5)
- SW $32.8M misses: 26/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 0

### Parallel
- Average Gini fell: 0.510 (round 1) → 0.339 (round 5)
- SW $32.8M misses: 14/30 turns
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 0

### Ring
- Average Gini fell: 0.553 (round 1) → 0.513 (round 5)
- SW $32.8M misses: 26/30 turns
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 0

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 1/6 agents, avg $3,843,072 (TCC $23,058,431)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)
- #7 Van Ness Family Apartments — 1/6 agents, avg $1,858,333 (TCC $11,150,000)
- #5 Hotel Fresno — 1/6 agents, avg $1,552,210 (TCC $9,313,260)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 1/6 agents, avg $1,266,667 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 1/6 agents, avg $1,234,584 (TCC $7,407,505)
- #3 H Street Development — 1/6 agents, avg $708,333 (TCC $4,250,000)
- #27 Chinatown Urban Greening (ChUG) Project — 1/6 agents, avg $680,950 (TCC $4,085,700)
- #4 The Park @ South Fulton — 1/6 agents, avg $320,833 (TCC $1,925,000)
- #37 VOICE Gladiator Program — 1/6 agents, avg $200,000 (TCC $1,200,000)
- #26 Santa Clara Permaculture Garden — 1/6 agents, avg $65,833 (TCC $395,000)

### Parallel (round 5, 6 panelists)
- #8 CA HSR Mixed Use Development — 5/6 agents, avg $20,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 5/6 agents, avg $19,215,359 (TCC $23,058,431)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 5/6 agents, avg $12,266,374 (TCC $14,719,649)
- #25 Chinatown Park — 5/6 agents, avg $10,000,000 (TCC $12,000,000)
- #1 Chinatown Lofts — 5/6 agents, avg $9,583,333 (TCC $11,500,000)
- #7 Van Ness Family Apartments — 5/6 agents, avg $9,291,667 (TCC $11,150,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 5/6 agents, avg $8,992,535 (TCC $10,791,042)
- #5 Hotel Fresno — 5/6 agents, avg $7,761,050 (TCC $9,313,260)
- #18 H Complete Street — 5/6 agents, avg $6,500,000 (TCC $7,800,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 5/6 agents, avg $6,333,333 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 5/6 agents, avg $6,172,921 (TCC $7,407,505)
- #10 Kings View Manor Rehab — 5/6 agents, avg $5,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 5/6 agents, avg $4,166,667 (TCC $5,000,000)
- … 19 more with avg $ > 0 (see graph_data.json)

### Ring (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)

## Outliers

- Highest Gini: **0.750** — Citizen (Chinatown) (Ring, round 1)
- Largest SW shortfall: **$17,600,000** — Citizen (Chinatown) (Parallel, round 1)
- Largest budget overrun: **$151,207,792** — Citizen (SW Fresno) (Parallel, round 2)

- Most-funded proposal IDs (all topologies): #35 (89), #20 (89), #25 (25), #9 (23), #5 (23)

## Notable turns

- **Citizen (Chinatown)** / Ring / R1: Gini 0.750, SW short $15,900,000.
  > Chinatown faces urgent needs for cultural preservation and economic revitalization, yet the current proposal slate lacks sufficient dedicated funding for our specific community priorities. While multi-area projects like #20 Tulare Complete Streets offer some benefit, they cannot 
- **Citizen (SW Fresno)** / Ring / R2: Gini 0.636, SW short $-42,295,854.
  > I am significantly expanding the Southwest baseline to address our community's critical infrastructure deficits and social vulnerability, moving well beyond the previous slate's minimal investment. While Tulare Complete Streets provides essential connectivity for all areas, it is
- **Financial Expert** / Parallel / R2: Gini 0.627, SW short $-28,919,649.
  > The current slate from Round 1 significantly underfunds Southwest Fresno's exclusive needs while over-funding Chinatown, violating the spirit of equitable infrastructure investment. Although Citizen (Chinatown) justified their heavy allocation for #25 and #16, relying on shared p
- **Financial Expert** / Star / R3: Gini 0.619, SW short $-25,019,649.
  > In Round 2, the panel prioritized high-cost Downtown projects like CA HSR Mixed Use Development and North Fulton Street Mixed Use Project, which pushed our exclusive neighborhood funding low. To correct this imbalance, I am shifting focus to Southwest Fresno in Round 3, as these 

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

