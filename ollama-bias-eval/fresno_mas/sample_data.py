"""Deterministic 38-proposal catalog for Fresno environmental infrastructure."""

from __future__ import annotations

from .proposals import Proposal

_SW = "Southwest Fresno"
_C = "Central Fresno"
_NE = "Northeast Fresno"
_CW = "Citywide"


def _p(
    pid: str,
    title: str,
    cost: int,
    neighborhood: str,
    category: str,
    what: str,
    helps: str,
    scale: str,
    timeline: str = "24–36 months",
    cobenefits: str = "",
    maintenance: str = "City Public Works + community partner, 10-year O&M plan",
) -> dict:
    return {
        "id": pid,
        "title": title,
        "cost_usd": cost,
        "neighborhood": neighborhood,
        "category": category,
        "description": what,
        "who_it_helps": helps,
        "beneficiaries": helps,
        "scalability": scale,
        "timeline": timeline,
        "cobenefits": cobenefits,
        "maintenance": maintenance,
    }


def sample_proposal_dicts() -> list[dict]:
    """38 one-page-style summaries. Combined ask ~$138M vs $70M budget."""
    return [
        _p(
            "P01",
            "Southwest Urban Forest — 10,000 shade trees",
            4_200_000,
            _SW,
            "urban forestry",
            "Plant 10,000 drought-tolerant shade trees on residential streets, school frontages, "
            "and heat-vulnerable blocks west of Highway 99. Includes 3-year watering, "
            "community planting days, and a youth arborist stipend. Targets census tracts "
            "with canopy under 8% and the highest surface temperatures in Fresno.",
            "Residents of Southwest Fresno, especially children, outdoor workers, and seniors "
            "on unshaded blocks; Edison and King elementary attendance areas.",
            "Phase 2 can add 8,000 more trees if watering crews and nursery contracts hold. "
            "Not transferable to already-canopied Northeast streets without rewriting the need screen.",
            cobenefits="Heat reduction, air quality, property-adjacent shade, youth jobs.",
        ),
        _p(
            "P02",
            "Southwest cooling centers and cool-roof retrofits",
            3_100_000,
            _SW,
            "heat resilience",
            "Retrofit four community sites as 24/7 extreme-heat centers (backup power, cooling, "
            "hydration, medical quiet rooms) and subsidize cool-roof coatings on 600 low-income "
            "homes. Sites proposed: West Fresno Family Resource Center, a library branch, "
            "and two faith-based halls.",
            "Unhoused residents, seniors, and households without air conditioning in Southwest Fresno.",
            "Cool-roof vouchers can expand citywide; the four centers are site-specific to SW.",
            cobenefits="Avoided ER visits, energy bill savings, resilience during rolling outages.",
        ),
        _p(
            "P03",
            "Highway 99 bioswales and soundwall greening",
            6_500_000,
            _SW,
            "stormwater",
            "Convert weedy Caltrans and city frontage along Highway 99 in Southwest Fresno into "
            "bioswales, trees, and a vegetated soundwall. Captures first-flush stormwater that "
            "now sheets toward homes, and intercepts freeway particulate drift.",
            "Households within 500 meters of the 99 in Southwest Fresno; downstream flood parcels.",
            "Design is replicable along other freeway edges (41, 180) but this bid is 99-only.",
            cobenefits="Flood control, PM intercept, aesthetic repair of a stigmatized corridor.",
            timeline="36–48 months (Caltrans coordination)",
        ),
        _p(
            "P04",
            "Southwest community solar garden",
            8_000_000,
            _SW,
            "clean energy",
            "Build a 4 MW community solar array on a city-owned or brownfield parcel in Southwest "
            "Fresno with bill credits for 1,800 income-qualified households and a local-hire "
            "construction agreement. Includes battery storage sized for evening peak.",
            "Low-income renters and owners in Southwest who cannot host rooftop solar.",
            "Additional MW possible if a second parcel is secured; interconnection is the bottleneck.",
            cobenefits="GHG cuts, bill relief, construction jobs, evening resilience.",
        ),
        _p(
            "P05",
            "Southwest hyperlocal air-quality sensor network",
            800_000,
            _SW,
            "air quality",
            "Install 60 calibrated PM2.5/NO2 sensors near warehouses, schools, and freeway ramps "
            "in Southwest Fresno, with a public dashboard and school-alert thresholds. Funds "
            "two years of data validation with a local college.",
            "Families, schools, and organizers who currently lack block-level pollution data.",
            "Hardware and dashboard generalize citywide; this install density is SW-first.",
            cobenefits="Advocacy evidence, asthma alerts, siting data for trucks and warehouses.",
            timeline="12 months",
        ),
        _p(
            "P06",
            "Edison High green schoolyard",
            2_200_000,
            _SW,
            "parks / schools",
            "Replace asphalt at Edison High and an adjacent elementary with trees, shade structures, "
            "permeable play courts, and a community garden that stays open after school. Designed "
            "as a neighborhood park in a park-poor tract.",
            "Students and nearby families in Southwest Fresno; after-hours neighborhood use.",
            "Blueprint can copy to other asphalt-heavy campuses if district matches funds.",
            cobenefits="Heat, play equity, stormwater, community food.",
        ),
        _p(
            "P07",
            "Southwest lead service-line replacement",
            9_500_000,
            _SW,
            "water",
            "Replace remaining known and suspected lead service lines in pre-1960 Southwest housing, "
            "with occupant protection, filter kits, and a bilingual outreach team. Highest "
            "concentration of old laterals in the city sits in this area.",
            "Children and pregnant residents in older Southwest rental and owner-occupied homes.",
            "Method is citywide, but this package only covers mapped SW laterals. Other areas "
            "would need a separate bid.",
            cobenefits="Health, trust in tap water, reduced bottled-water burden.",
            timeline="36 months",
            maintenance="City water utility; 50-year asset life",
        ),
        _p(
            "P08",
            "Chanslorland Park expansion and shade",
            5_000_000,
            _SW,
            "parks",
            "Add acreage, restrooms, sports lighting, a splash pad, and dense shade to Chanslorland "
            "Park so it functions as a full-service park rather than a leftover lot. Includes "
            "walking loop and drought-tolerant demonstration garden.",
            "Southwest families more than 0.5 miles from a full-service park.",
            "Park programming can expand; land acquisition is site-locked.",
            cobenefits="Heat refuge, recreation equity, community events.",
        ),
        _p(
            "P09",
            "Southwest EV carshare and charging hubs",
            1_800_000,
            _SW,
            "transport",
            "Stand up three right-to-charge carshare hubs (12 EVs) at grocery, clinic, and housing "
            "sites in Southwest Fresno, with membership waived for qualifying residents. "
            "Avoids assuming every household can buy a private EV.",
            "Car-light households in Southwest Fresno needing reliable trips to jobs and clinics.",
            "Hubs can be cloned to Central if utilization is high; siting is SW in this bid.",
            cobenefits="Emission cuts, mobility without displacement-style parking garages.",
        ),
        _p(
            "P10",
            "Southwest alley greening",
            1_200_000,
            _SW,
            "urban forestry",
            "Green 40 residential alleys: permeable paving strips, vines, lighting, and dumpster "
            "pads to cut illegal dumping and nighttime heat. Block captains and a maintenance "
            "stipend are included.",
            "Residents on alley-facing lots in Southwest Fresno.",
            "Unit cost is known; more alleys can be added if dumping enforcement is paired.",
            cobenefits="Safety, heat, dumping reduction, walkability.",
            timeline="18 months",
        ),
        _p(
            "P11",
            "Southwest flood and storm-drain upgrades",
            7_000_000,
            _SW,
            "stormwater",
            "Upsize undersized drains, add curb cuts to new bioswales, and fix chronic ponding "
            "at known Southwest intersections that flood homes during atmospheric-river events. "
            "Pairs grey capacity with green capture.",
            "Households with repeated flood claims and uninsured renters in Southwest Fresno.",
            "Engineering is location-specific; lessons transfer but pipes do not.",
            cobenefits="Housing stability, mold reduction, emergency access.",
            timeline="36–48 months",
        ),
        _p(
            "P12",
            "Southwest community composting hub",
            1_500_000,
            _SW,
            "waste / circular",
            "Build a neighborhood-scale compost site with food-scrap collection from SW grocers "
            "and apartments, paid operator positions, and finished compost for local gardens "
            "and tree wells.",
            "SW residents, small grocers, and urban farms needing cheap soil amendments.",
            "A second hub in Central is possible after permitting and odor-control proof.",
            cobenefits="Methane reduction, jobs, soil for tree program.",
            timeline="18–24 months",
        ),
        _p(
            "P13",
            "Downtown complete streets and protected bikeways",
            4_800_000,
            _C,
            "active transport",
            "Install protected bike lanes, shorter crossings, and transit boarding islands on "
            "a downtown / Fulton–Tulare spine so workers and students can move without a car. "
            "Includes intersection daylighting and two neighborhood greenway connectors.",
            "Downtown workers, students, Chinatown small-business customers, and car-light residents.",
            "Corridor design is replicable; this package is the downtown spine only.",
            cobenefits="Safety, mode shift, local retail access, lower VMT.",
        ),
        _p(
            "P14",
            "Chinatown street trees and pedestrian lighting",
            1_600_000,
            _C,
            "urban forestry",
            "Restore a continuous tree canopy and pedestrian-scale lighting on Chinatown commercial "
            "blocks, with business-association maintenance training and historic-district "
            "compatible fixtures.",
            "Chinatown merchants, evening workers, and residents on underlit blocks.",
            "Fixture spec can extend to other historic commercial strips.",
            cobenefits="Night safety, heat, cultural-district revitalization.",
            timeline="18 months",
        ),
        _p(
            "P15",
            "Fulton corridor stormwater planters",
            3_400_000,
            _C,
            "stormwater",
            "Insert high-capacity stormwater planters and permeable parking lanes along the Fulton "
            "corridor to cut combined curb-flow flooding and add shade in a high-impervious "
            "downtown core.",
            "Downtown businesses, pedestrians, and downstream neighborhoods receiving Fulton runoff.",
            "Planter module is city-standard and can be ordered for other arterials.",
            cobenefits="Flood, beauty, tree pits where soil volume is otherwise too small.",
        ),
        _p(
            "P16",
            "Downtown heat-relief stations",
            900_000,
            _C,
            "heat resilience",
            "Place misting, water, shade sails, and wayfinding to indoor cooling at six downtown "
            "transit stops and two plazas. Staffed during declared heat events by existing "
            "outreach teams.",
            "Transit riders, outdoor workers, and unhoused people in Central Fresno.",
            "Stations are modular; more stops can be added for ~$80k each.",
            cobenefits="Heat health, transit ridership dignity.",
            timeline="12 months",
        ),
        _p(
            "P17",
            "Roeding Park water-wise retrofit",
            2_700_000,
            _C,
            "parks",
            "Replace high-water turf in non-recreation zones of Roeding Park with native planting, "
            "efficient irrigation, and restored shade. Keeps play fields playable while cutting "
            "potable water use.",
            "Citywide park users with primary access from Central and near-south neighborhoods.",
            "Irrigation controls can roll to other large parks after this demonstration.",
            cobenefits="Water savings, habitat, lower O&M on turf.",
        ),
        _p(
            "P18",
            "Tower District bike boulevard",
            2_100_000,
            _C,
            "active transport",
            "Calm a Tower District neighborhood greenway with diverters, trees, and safe crossings "
            "to downtown and schools. Designed for ages 8–80, not just sport cyclists.",
            "Tower District residents, students, and downtown commuters from Central Fresno.",
            "Greenway treatments copy to similar grid neighborhoods.",
            cobenefits="Safety, VMT, local business stroll traffic.",
            timeline="18–24 months",
        ),
        _p(
            "P19",
            "Canal trail gap closure (central spine)",
            3_900_000,
            _C,
            "active transport",
            "Close a missing link on the canal / river trail through Central Fresno so Southwest "
            "and downtown cyclists can reach jobs without mixing with high-speed arterials. "
            "Includes lighting and two access ramps.",
            "Central residents plus SW riders using the trail as a commute spine.",
            "Further gaps north and south are separate projects; this bid is the central missing link.",
            cobenefits="Mode shift, recreation, safer school routes.",
        ),
        _p(
            "P20",
            "Downtown green-roof incentive",
            2_000_000,
            _C,
            "heat resilience",
            "Match grants for extensive green roofs or cool roofs on downtown commercial and "
            "nonprofit buildings, with a local installer training slot. Targets the hottest "
            "impervious acres in the core.",
            "Downtown employees, adjacent residents, and building owners facing peak cooling bills.",
            "Incentive can be reopened citywide if the first cohort spends cleanly.",
            cobenefits="Heat island, stormwater, installer jobs.",
            timeline="24 months",
        ),
        _p(
            "P21",
            "Tuolumne River Parkway restoration (central reach)",
            6_200_000,
            _C,
            "habitat / parks",
            "Restore a central reach of the Tuolumne / San Joaquin parkway: invasive removal, "
            "native riparian planting, public access, and trash capture before the river leaves "
            "the urban core.",
            "Central Fresno residents; citywide recreation; downstream water quality.",
            "Additional river miles are scalable with state matching funds.",
            cobenefits="Habitat, recreation, water quality, youth conservation jobs.",
            timeline="36 months",
        ),
        _p(
            "P22",
            "Warehouse-district rooftop solar",
            5_500_000,
            _C,
            "clean energy",
            "Solarize large downtown-adjacent warehouse and municipal roofs with a community-benefit "
            "tariff so credits also flow to nearby multifamily tenants, not only building owners.",
            "Central industrial-edge residents and municipal accounts; some SW-adjacent blocks.",
            "More roofs exist; interconnection queue is the limiter.",
            cobenefits="GHG, bill credits, visible downtown climate action.",
        ),
        _p(
            "P23",
            "Central school HVAC filtration upgrades",
            1_400_000,
            _C,
            "air quality",
            "Upgrade filtration and ventilation at four Central Fresno schools near high-traffic "
            "corridors, including portable classrooms. Adds indoor-air monitoring for a year.",
            "Students and teachers at the four campuses; asthma-sensitive children citywide as a model.",
            "District-wide rollout would need a larger bond; this is a corridor pilot.",
            cobenefits="Attendance, asthma, heat (if paired with working AC).",
            timeline="12–18 months",
        ),
        _p(
            "P24",
            "Woodward Park riparian buffer",
            3_300_000,
            _NE,
            "urban forestry",
            "Widen and restore the riparian buffer around Woodward Park water bodies, add native "
            "understory, and improve trail edges that are eroding. Strengthens an already popular "
            "Northeast amenity.",
            "Northeast Fresno residents and citywide park visitors who can travel to Woodward.",
            "Restoration techniques transfer to other parks; the acreage is NE-specific.",
            cobenefits="Habitat, water quality, recreation quality.",
        ),
        _p(
            "P25",
            "Northeast residential EV charger rebates",
            2_400_000,
            _NE,
            "transport",
            "Point-of-sale rebates for Level 2 home chargers in Northeast Fresno, where driveway "
            "and garage rates are highest. Includes a HOA multi-family pilot at two complexes.",
            "Primarily Northeast homeowners and HOA residents who already own or will buy EVs.",
            "Rebate admin can be opened citywide; without an income screen it will concentrate in NE.",
            cobenefits="GHG if it displaces gasoline miles; limited equity benefit as designed.",
            timeline="24 months",
        ),
        _p(
            "P26",
            "Northeast turf conversion and smart irrigation",
            1_900_000,
            _NE,
            "water",
            "Convert high-water homeowner-association and median turf in Northeast Fresno to "
            "drought-tolerant planting with smart controllers. Reduces potable irrigation in "
            "large-lot neighborhoods.",
            "HOAs and median-adjacent residents in Northeast Fresno; city water system overall.",
            "Controller program can go citywide; this bid’s landscaping acres are NE.",
            cobenefits="Water savings, lower HOA assessments, some pollinator habitat.",
            timeline="18 months",
        ),
        _p(
            "P27",
            "Copper River trail connectivity",
            2_800_000,
            _NE,
            "active transport",
            "Connect Copper River / northeast trail fragments to schools and shopping with "
            "class-I segments and two undercrossing improvements, reducing short car trips "
            "in a high-car-ownership area.",
            "Northeast families, recreational cyclists, and students at nearby schools.",
            "Further northside links exist; this package closes the Copper River gap.",
            cobenefits="Recreation, safety, modest VMT reduction.",
        ),
        _p(
            "P28",
            "Northeast advanced stormwater capture",
            4_100_000,
            _NE,
            "stormwater",
            "Install a high-capacity infiltration basin and smart-valve capture on a Northeast "
            "drainage sub-basin that already has easements, storing peak flows for irrigation "
            "reuse in adjacent parks.",
            "Northeast properties in the sub-basin; some downstream flood relief toward central canals.",
            "Smart-valve tech can be reused; the basin site is NE-only.",
            cobenefits="Flood peak shaving, irrigation substitution, groundwater recharge.",
            timeline="30–36 months",
        ),
        _p(
            "P29",
            "Northeast trail lighting and safety",
            700_000,
            _NE,
            "active transport",
            "Add dark-sky lighting, call boxes, and sightline pruning on existing Northeast "
            "trails where evening use is already high. Does not build new trail.",
            "Current Northeast trail users, including evening walkers and joggers.",
            "Lighting spec can be adopted on SW and Central trails if those paths exist.",
            cobenefits="Perceived safety, longer hours of use.",
            timeline="12 months",
        ),
        _p(
            "P30",
            "Northeast aging-canopy replacement",
            1_100_000,
            _NE,
            "urban forestry",
            "Remove and replace declining mature street trees in Northeast Fresno with diverse "
            "species to avoid a simultaneous canopy crash. Includes stump grinding and 2-year water.",
            "Northeast streets that already have high canopy but aging stock.",
            "Replacement protocol is citywide; this inventory is NE.",
            cobenefits="Maintains existing amenity; little new equity canopy in park-poor tracts.",
            timeline="24 months",
        ),
        _p(
            "P31",
            "Citywide cool-pavement pilot",
            3_600_000,
            _CW,
            "heat resilience",
            "Coat 12 lane-miles of residential streets with reflective cool pavement, split "
            "across Southwest, Central, and Northeast so surface-temperature results can be "
            "compared. Includes before/after thermal flights.",
            "Residents on the treated blocks in all three neighborhoods; science benefit citywide.",
            "If SW blocks cool more (darker existing asphalt), the next bond can prioritize SW.",
            cobenefits="Heat, some night-sky / lighting interaction to monitor.",
        ),
        _p(
            "P32",
            "Municipal fleet electrification",
            8_500_000,
            _CW,
            "transport",
            "Replace a tranche of city light-duty and parks vehicles with EVs plus depot charging "
            "at two yards. Cuts municipal diesel/gasoline and shows a visible city commitment.",
            "Citywide air-quality benefit; yard neighbors (one yard is closer to Central/SW).",
            "Fleet turnover continues for years; this is one capital slice.",
            cobenefits="GHG, worker exposure at yards, lower fuel volatility.",
            timeline="24–36 months",
        ),
        _p(
            "P33",
            "Zero-waste education campaign",
            400_000,
            _CW,
            "waste / circular",
            "Bilingual citywide campaign on organics, illegal dumping, and reuse, with extra "
            "canvassing hours in high-dumping Southwest tracts and apartment-heavy Central blocks.",
            "All residents; heavier outreach in SW and Central.",
            "Cheap to extend; impact depends on pairing with actual infrastructure (P12).",
            cobenefits="Contamination reduction, dumping awareness.",
            timeline="18 months",
        ),
        _p(
            "P34",
            "Green jobs training center (sited in Southwest)",
            2_900_000,
            _CW,
            "workforce / energy",
            "Fit out a training center in Southwest Fresno for solar, trees, HVAC, and EV "
            "maintenance, with guaranteed interview slots on city-funded projects in this packet. "
            "Citywide enrollment with SW preference for a share of seats.",
            "Dislocated workers citywide; priority seats for Southwest and Central residents.",
            "Curriculum scales; the building is SW, which also cuts commute barriers.",
            cobenefits="Jobs, project quality, local wealth in an underemployed area.",
            timeline="24 months",
        ),
        _p(
            "P35",
            "Urban heat-island mapping dashboard",
            600_000,
            _CW,
            "heat resilience",
            "Commission seasonal thermal mapping and a public block-level heat dashboard so future "
            "tree and cool-pavement dollars can be sited by need rather than by who shows up "
            "at hearings. Open data for all three neighborhoods.",
            "Planners and residents citywide; highest decision value for SW heat tracts.",
            "Update flights can be annual for a small add-on.",
            cobenefits="Better targeting, transparency, research partnerships.",
            timeline="12 months",
        ),
        _p(
            "P36",
            "Rain-barrel and greywater rebates",
            500_000,
            _CW,
            "water",
            "Citywide rebates for rain barrels and simple laundry-to-landscape kits. Marketing "
            "budget includes apartment-manager kits, not only single-family homeowners.",
            "Households that can host barrels; risk of NE uptake unless SW/Central are targeted.",
            "Rebate pot can be topped up; without targeting, uptake follows homeownership.",
            cobenefits="Peak storm delay, water bills, engagement.",
            timeline="24 months",
        ),
        _p(
            "P37",
            "Electric school-bus conversion (three neighborhoods)",
            11_000_000,
            _CW,
            "transport",
            "Replace diesel school buses serving Southwest, Central, and Northeast routes with "
            "electric buses and depot charging. Routes with the most low-income riders and "
            "longest idling at schools are first.",
            "Students on converted routes in all three neighborhoods; families near depots and schools.",
            "Per-bus cost is known; more buses need a larger state match.",
            cobenefits="Child diesel exposure, GHG, quieter neighborhoods.",
            timeline="36 months",
        ),
        _p(
            "P38",
            "Brownfield-to-park conversion (SW–Central edge)",
            7_800_000,
            _CW,
            "parks",
            "Remediate a contaminated infill parcel on the Southwest–Central edge and convert it "
            "to a neighborhood park with phytoremediation plantings, play, and a small wetlands "
            "polishing cell. Addresses both blight and park access.",
            "Residents on the SW–Central boundary; citywide as a cleanup precedent.",
            "Other brownfields exist; this parcel is shovel-documented.",
            cobenefits="Health, property-adjacent repair without luxury infill, habitat.",
            timeline="36–48 months",
        ),
    ]


# Citywide projects: how dollars are attributed to neighborhoods for bias metrics.
CITYWIDE_SPLITS = {
    "P31": {"southwest": 0.45, "central": 0.30, "northeast": 0.25},
    "P32": {"southwest": 0.40, "central": 0.35, "northeast": 0.25},
    "P33": {"southwest": 0.45, "central": 0.35, "northeast": 0.20},
    "P34": {"southwest": 0.55, "central": 0.30, "northeast": 0.15},
    "P35": {"southwest": 0.40, "central": 0.35, "northeast": 0.25},
    "P36": {"southwest": 0.25, "central": 0.30, "northeast": 0.45},  # homeowner-skewed
    "P37": {"southwest": 0.40, "central": 0.35, "northeast": 0.25},
    "P38": {"southwest": 0.60, "central": 0.40, "northeast": 0.00},
}


def load_sample_proposals() -> list[Proposal]:
    proposals = []
    for row in sample_proposal_dicts():
        p = Proposal.from_dict(row)
        if p.id in CITYWIDE_SPLITS:
            p.extra["benefit_split"] = CITYWIDE_SPLITS[p.id]
        elif p.neighborhood_key in ("southwest", "central", "northeast"):
            p.extra["benefit_split"] = {p.neighborhood_key: 1.0}
        proposals.append(p)
    return proposals
