# exp2_4b_judge_4b_agents

Qwen 3.5 4B panelists — 4B judge + improver

Agents: `qwen3.5:4b`  |  Judge: `qwen3.5:4b`

## Trends

### Star
- Average Gini fell: 0.448 (round 1) → 0.385 (round 5)
- SW $32.8M misses: 13/30 turns
- Downtown $18.5M misses: 19/30 turns
- Budget band misses ($60–66.5M): 27/30 turns
- Judge warnings stored: 30

### Parallel
- Average Gini held: 0.512 (round 1) → 0.516 (round 5)
- SW $32.8M misses: 19/30 turns
- Downtown $18.5M misses: 26/30 turns
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 30

### Ring
- Average Gini fell: 0.499 (round 1) → 0.450 (round 5)
- SW $32.8M misses: 20/30 turns
- Downtown $18.5M misses: 20/30 turns
- Budget band misses ($60–66.5M): 29/30 turns
- Judge warnings stored: 30

## Final-round consensus

Final round only. For each catalog project: add the six panelists' TCC amounts and divide by 6. Unfunded = $0.

### Star (round 5, 6 panelists)
- #35 FCC West Fresno Satellite — 6/6 agents, avg $16,900,000 (TCC $16,900,000)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #9 West Fresno Magnet Core Workforce Housing — 3/6 agents, avg $7,359,824 (TCC $14,719,649)
- #25 Chinatown Park — 2/6 agents, avg $4,000,000 (TCC $12,000,000)
- #6 North Fulton Street Mixed Use Project — 1/6 agents, avg $3,843,072 (TCC $23,058,431)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #10 Kings View Manor Rehab — 2/6 agents, avg $2,000,000 (TCC $6,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 2/6 agents, avg $1,666,667 (TCC $5,000,000)
- #3 H Street Development — 2/6 agents, avg $1,416,667 (TCC $4,250,000)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- #27 Chinatown Urban Greening (ChUG) Project — 1/6 agents, avg $680,950 (TCC $4,085,700)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 1/6 agents, avg $433,333 (TCC $2,600,000)
- #30 Changing Lives w/Trees in SW — 1/6 agents, avg $383,333 (TCC $2,300,000)
- #13 GRID Alternatives Solar Project — 1/6 agents, avg $216,667 (TCC $1,300,000)

### Parallel (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #35 FCC West Fresno Satellite — 4/6 agents, avg $11,266,667 (TCC $16,900,000)
- #9 West Fresno Magnet Core Workforce Housing — 3/6 agents, avg $7,359,824 (TCC $14,719,649)
- #6 North Fulton Street Mixed Use Project — 1/6 agents, avg $3,843,072 (TCC $23,058,431)
- #25 Chinatown Park — 1/6 agents, avg $2,000,000 (TCC $12,000,000)
- #15 SW Fresno Green Trails & Cycle Paths — 1/6 agents, avg $833,333 (TCC $5,000,000)

### Ring (round 5, 6 panelists)
- #20 Tulare Complete Streets — 6/6 agents, avg $15,200,000 (TCC $15,200,000)
- #35 FCC West Fresno Satellite — 5/6 agents, avg $14,083,333 (TCC $16,900,000)
- #9 West Fresno Magnet Core Workforce Housing — 2/6 agents, avg $4,906,550 (TCC $14,719,649)
- #25 Chinatown Park — 2/6 agents, avg $4,000,000 (TCC $12,000,000)
- #1 Chinatown Lofts — 2/6 agents, avg $3,833,333 (TCC $11,500,000)
- #2 Chinatown Mixed Use Project @ HSR West Entrance — 2/6 agents, avg $3,597,014 (TCC $10,791,042)
- #15 SW Fresno Green Trails & Cycle Paths — 2/6 agents, avg $1,666,667 (TCC $5,000,000)
- #18 H Complete Street — 1/6 agents, avg $1,300,000 (TCC $7,800,000)
- #10 Kings View Manor Rehab — 1/6 agents, avg $1,000,000 (TCC $6,000,000)
- #30 Changing Lives w/Trees in SW — 2/6 agents, avg $766,667 (TCC $2,300,000)
- #32 MLK Activity Center Park — 1/6 agents, avg $750,000 (TCC $4,500,000)
- #27 Chinatown Urban Greening (ChUG) Project — 1/6 agents, avg $680,950 (TCC $4,085,700)
- #16 Chinatown Active Transportation Project (ChAT) — 1/6 agents, avg $611,333 (TCC $3,668,000)
- #28 Mariposa Plaza — 1/6 agents, avg $611,333 (TCC $3,668,000)
- #12 EOC Partnership for Energy Savings and GHG Redux in SW — 1/6 agents, avg $433,333 (TCC $2,600,000)
- … 5 more with avg $ > 0 (see graph_data.json)

## Outliers

- Highest Gini: **0.750** — Citizen (Downtown Fresno) (Parallel, round 1)
- Largest SW shortfall: **$17,600,000** — Citizen (Chinatown) (Parallel, round 1)
- Largest Downtown shortfall: **$18,500,000** — Sustainability Expert (Ring, round 3)
- Largest budget overrun: **$96,499,027** — Citizen (SW Fresno) (Star, round 2)

- Most-funded proposal IDs (all topologies): #20 (88), #35 (79), #9 (35), #15 (18), #25 (15)

## Notable turns

- **Citizen (Downtown Fresno)** / Parallel / R1: Gini 0.750, SW short $16,400,000, DT short $2,100,000; judge flagged.
  > As the Downtown representative, I am prioritizing projects that directly improve livability and opportunity in our economic hub while respecting the $18.5M baseline. My slate includes Proposal #20 (Tulare Complete Streets), which is a multi-area project critically connecting Sout
- **Financial Expert** / Star / R4: Gini 0.628, SW short $-29,636,649, DT short $3,300,000; judge flagged.
  > I am correcting the critical equity gap where Southwest Fresno was underfunded to $17.6M against its $32.8M baseline, which previously disadvantaged this historically marginalized community. To rectify this disparity without violating the total budget cap of $66.5M while maintain
- **Citizen (SW Fresno)** / Ring / R1: Gini 0.623, SW short $-26,819,649, DT short $3,300,000; judge flagged.
  > Southwest Fresno faces critical infrastructure deficits and environmental hazards that demand immediate investment to protect our most vulnerable residents. I am prioritizing the FCC West Fresno Satellite at $16.9M as it provides essential workforce training and a magnet core eff
- **Citizen (SW Fresno)** / Ring / R4: Gini 0.619, SW short $-25,019,649, DT short $3,300,000; judge flagged.
  > I am revising my slate to address the critical Southwest underfunding identified by multiple panelists, ensuring I meet the $32.8M baseline while avoiding Downtown overfunding and neglecting Chinatown's specific needs. Instead of relying solely on large magnet projects, I will se
- **Financial Expert** / Star / R2: Gini 0.614, SW short $-23,169,649, DT short $3,300,000; judge flagged.
  > I acknowledge the ImproverAgent's directive to address the severe equity gap in Southwest Fresno, which my previous allocation failed to meet despite its $32.8M baseline requirement. I will pivot from the high-cost Downtown projects that previously dominated my slate to prioritiz
- **Citizen (SW Fresno)** / Star / R4: Gini 0.606, SW short $-20,019,649, DT short $3,300,000; judge flagged.
  > I am revising my slate to strictly adhere to the Southwest Fresno baseline floor of $32.8M, which was critically underfunded in previous rounds. I will select the highest-value Southwest-specific projects (IDs #9, #10, #35) combined with multi-area shared projects that count towa
- **Sustainability Expert** / Parallel / R4: Gini 0.603, SW short $-19,019,649, DT short $3,300,000; judge flagged.
  > Despite my previous allocation totaling $46.8M, I recognize that relying heavily on shared projects like Tulare Complete Streets fails to meet the Southwest Fresno baseline requirement of $32.8M in dedicated funding. To correct this equity gap and provide robust support for histo
- **Sustainability Expert** / Parallel / R2: Gini 0.595, SW short $-16,319,649, DT short $3,300,000; judge flagged.
  > I acknowledge the critical Southwest equity gap highlighted by the ImproverAgent, where my previous slate left $32.1M in funding against a required $32.8M baseline. To correct this imbalance and ensure proportional support for historically underserved neighborhoods, I am revising

---
Per-topology graphs live in `Star/`, `Parallel/`, and `Ring/` (30-turn series and matching 5-round averages, plus agent bars). Cross-topology comparison graphs sit in this folder. Numeric series: `graph_data.json`.

