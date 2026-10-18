# exp3_9b_no_judge

Qwen 3.5 9B panelists — no judge / no improver

Agents: `qwen3.5:9b`  |  Judge: OFF

## Trends

### Star
- Average Gini fell: 0.513 (round 1) → 0.474 (round 5)
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 0

### Parallel
- Average Gini fell: 0.492 (round 1) → 0.460 (round 5)
- Budget band misses ($60–66.5M): 28/30 turns
- Judge warnings stored: 0

### Ring
- Average Gini rose: 0.500 (round 1) → 0.543 (round 5)
- Budget band misses ($60–66.5M): 30/30 turns
- Judge warnings stored: 0

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #20 Tulare Complete Streets — 5/6 agents, avg $12,666,667 (TCC $15,200,000)
- #35 FCC West Fresno Satellite — 4/6 agents, avg $11,266,667 (TCC $16,900,000)
- #9 West Fresno Magnet Core Workforce Housing — 2/6 agents, avg $4,906,550 (TCC $14,719,649)
- #8 CA HSR Mixed Use Development — 1/6 agents, avg $4,000,000 (TCC $24,000,000)
- #6 North Fulton Street Mixed Use Project — 1/6 agents, avg $3,843,072 (TCC $23,058,431)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)
- #7 Van Ness Family Apartments — 1/6 agents, avg $1,858,333 (TCC $11,150,000)
- #5 Hotel Fresno — 1/6 agents, avg $1,552,210 (TCC $9,313,260)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- #17 High Speed Rail Station Area Complete Streets Connectivity Project — 1/6 agents, avg $1,266,667 (TCC $7,600,000)
- #19 Clean Shared Mobility Network — 1/6 agents, avg $1,234,584 (TCC $7,407,505)
- #10 Kings View Manor Rehab — 1/6 agents, avg $1,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 1/6 agents, avg $833,333 (TCC $5,000,000)
- #32 MLK Activity Center Park — 1/6 agents, avg $750,000 (TCC $4,500,000)
- #28 Mariposa Plaza — 1/6 agents, avg $611,333 (TCC $3,668,000)
- … 11 more with avg $ > 0 (see graph_data.json)

### Parallel (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)

### Ring (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #4 The Park @ South Fulton — 1/6 agents, avg $320,833 (TCC $1,925,000)

## Outliers

- Highest Gini: **0.750** — Citizen (Chinatown) (Star, round 5)
- Lowest SW-tagged $: **$0** — Financial Expert (Star, round 5)
- Lowest Downtown-tagged $: **$0** — Financial Expert (Star, round 5)
- Largest budget overrun: **$151,207,792** — Urban Planner (Parallel, round 2)

- Most-funded proposal IDs (all topologies): #20 (86), #35 (81), #25 (11), #27 (9), #9 (7)

## Notable turns

- **Citizen (Chinatown)** / Star / R5: Gini 0.750, SW-tagged $15,200,000, DT-tagged $15,200,000.
  > I must prioritize the aging infrastructure and cultural heritage of Chinatown, ensuring that critical projects like #25 (Chinatown Park) and #1 (Chinatown Lofts) are funded to prevent community displacement. While I recognize the high cost of shared projects like #35 and #20, I c
- **Citizen (Downtown Fresno)** / Ring / R5: Gini 0.694, SW-tagged $15,200,000, DT-tagged $17,125,000.
  > I acknowledge the strategic priority placed on regional mobility and digital equity in the previous turn, which aligns with our mandate to ensure Downtown workers have reliable access to transit and connectivity. While the FCC West Fresno Satellite is a critical broadband investm
- **Financial Expert** / Star / R4: Gini 0.684, SW-tagged $15,200,000, DT-tagged $115,372,196.
  > I am recalibrating the portfolio to address the severe underfunding of Downtown Fresno infrastructure, which currently shows $0 in exclusive allocation despite having high-capacity projects like the North Fulton Street Mixed Use Project and CA HSR Development. While Southwest Fre
- **Citizen (SW Fresno)** / Star / R5: Gini 0.640, SW-tagged $74,421,999, DT-tagged $16,400,000.
  > As the Community Representative for Southwest Fresno, I must prioritize projects that directly address our documented infrastructure deficits and environmental hazards in this historically underinvested community. While Downtown and Chinatown have valid needs, my lived experience
- **Citizen (SW Fresno)** / Parallel / R3: Gini 0.640, SW-tagged $74,421,999, DT-tagged $16,400,000.
  > As the Southwest Fresno Community Representative, I must address the critical equity gap highlighted by our Chinatown colleague who argues that their urgent needs are being ignored. While Proposal #20 (Tulare Complete Streets) and Proposal #35 (FCC West Fresno Satellite) offer hi
- **Citizen (SW Fresno)** / Star / R2: Gini 0.619, SW-tagged $58,019,649, DT-tagged $15,200,000.
  > As the Community Representative for Southwest Fresno, I am advocating against excluding projects that serve our most vulnerable residents. While #35 and #20 received universal support, our community faces acute deficits in housing stability and active transportation infrastructur
- **Citizen (Chinatown)** / Star / R3: Gini 0.617, SW-tagged $15,200,000, DT-tagged $15,200,000.
  > As the Community Representative for Chinatown, I must prioritize our unique needs where other neighborhoods are already adequately served by large-scale housing and mobility projects like #35 and #20. Our aging infrastructure requires immediate investment in cultural heritage pre
- **Citizen (Chinatown)** / Ring / R1: Gini 0.553, SW-tagged $0, DT-tagged $7,800,000.
  > As the Community Representative for Chinatown, I am submitting an initial allocation that prioritizes immediate cultural preservation and physical infrastructure while acknowledging the need for cross-regional connectivity. My team identifies Proposal #25 (Chinatown Park) as non-

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

