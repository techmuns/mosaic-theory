"""Driver specs — one per theme. The semantic exposure classifier (``vinci.themes.exposure``) is
driver-AGNOSTIC and takes a ``DriverSpec``; AI-datacenter is the FIRST instance (Stage-3
build-1/2), demoted here from hardcoded to config. Adding a theme = adding a ``DriverSpec`` here,
NOT editing the classifier. No AI-datacenter-specific string lives in the classifier code path —
it all lives below.
"""
from __future__ import annotations

from vinci.themes.schemas import DriverSpec

# --------------------------------------------------------------------------------------------------
# AI-datacenter value chain — the first driver (build-1/2). NOTE: the build-1 "~50% from
# HBM/advanced-packaging" example was DROPPED (a CAMT-specific number that must not generalize).
# --------------------------------------------------------------------------------------------------
_AI_DC_DESCRIPTION = (
    "the AI-DATACENTER VALUE CHAIN — any layer of the chain that builds or supplies AI-datacenter "
    "compute: chips/GPU → HBM & memory → advanced packaging → thermal/cooling → power DELIVERED TO "
    "AI datacenters → optical interconnect → colocation/operator → AI-cloud. UPSTREAM ENABLERS ARE "
    "IN SCOPE (e.g. HBM / advanced-packaging metrology with quantified revenue) — they need not be "
    "datacenters themselves. Exposure must be DRIVER-SPECIFIC (a named layer) and grounded in "
    "disclosed activity — NOT generic power/equipment that merely 'could' feed a datacenter, NOT "
    "edge/on-device AI (the opposite of a datacenter), NOT a 'broad AI market' adjacency."
)

# what driver-specific / indirect / not-driver MEAN for AI-datacenter (was hardcoded in the
# classifier _SYSTEM; moved here, with the "~50%" example removed).
_AI_DC_TIE_TAXONOMY = (
    "driver-specific = a fact tied to a NAMED layer of the AI-datacenter value chain — "
    "GPU/compute, HBM/memory, advanced packaging, thermal/cooling, power DELIVERED TO AI "
    "datacenters, optical interconnect, colocation/operator, or AI-cloud. UPSTREAM ENABLERS ARE "
    "IN SCOPE: a chip/HBM/packaging/thermal/power/optical supplier with quantified "
    "chain-attributable revenue is driver-specific, even though it is not itself a datacenter. "
    "indirect = a generic/weak tie — generic power or equipment 'for data center applications' "
    "with NO AI/GPU language. not-driver = edge/on-device AI (the OPPOSITE of a datacenter) or a "
    "'broad AI market' adjacency."
)

# DELIBERATELY BROAD pre-filter over the whole value chain's vocabulary (build 2): a chain enabler
# describes its business in these terms even when it never says 'AI'. Broad for RECALL — the
# semantic layer then discriminates driver-specific from indirect/not-driver.
_AI_DC_PREFILTER = (
    "data center", "hyperscaler", "colocation", "high-performance computing", "GPU", "accelerator",
    "high bandwidth memory", "advanced packaging", "liquid cooling", "thermal management",
    "data center power", "switchgear", "optical interconnect", "silicon photonics", "AI cloud",
    "AI inference", "neocloud", "artificial intelligence",
)

# provenance tags: which value-chain LAYER a fact names (a keyword read for by-layer volume, NOT a
# grade). Most-specific first so 'HBM for data centers' tags HBM (not colocation).
_AI_DC_LAYERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("HBM/memory", ("high bandwidth memory", "high-bandwidth memory", "hbm", "dram", "memory")),
    ("packaging", ("advanced packaging", "packaging", "chiplet", "interposer", "hybrid bonding")),
    ("optical/interconnect", ("optical", "photonic", "transceiver", "interconnect", "fiber")),
    ("thermal/cooling", ("liquid cooling", "cooling", "thermal", "immersion", "heat rejection")),
    ("AI-cloud", ("ai cloud", "gpu-as-a-service", "gpuaas", "neocloud", "inference")),
    ("chips/GPU", ("gpu", "accelerator", "asic", "high-performance comput", "compute")),
    ("power/electrical", ("power", "electrical", "grid", "switchgear", "transformer", "fuel cell",
                          "megawatt", "energy")),
    ("colocation/operator", ("colocation", "data center", "datacenter", "hosting", "campus")),
)

AI_DATACENTER = DriverSpec(
    key="ai-datacenter",
    mirror_slug="ai-datacenter",   # frontend/themes/ai-datacenter.json
    description=_AI_DC_DESCRIPTION,
    tie_taxonomy=_AI_DC_TIE_TAXONOMY,
    prefilter_terms=_AI_DC_PREFILTER,
    provenance_tags=_AI_DC_LAYERS,
)

# --------------------------------------------------------------------------------------------------
# Defense demand-shift — theme #2 (the refactor's proof-of-generalization). A DEMAND-shaped theme:
# PARALLEL capability categories, NOT a sequential supply chain (that shape mismatch is finding 4b).
# LOAD-BEARING analyst judgment, encoded VERBATIM in tie_taxonomy (do NOT re-draft it — it IS the
# experiment): legacy/exquisite-platform primes are INDIRECT (not driver-specific), so they do NOT
# clear the bar — the edge is the tailwind side (attritable/autonomous/mass), not "every name the
# budget lifts". Finding 4a tests whether this text-encoding holds or whether DriverTie needs a
# structured direction field. Verbatim from the analyst-approved defense_demand_shift_spec.py.
# --------------------------------------------------------------------------------------------------
DEFENSE_DEMAND_SHIFT = DriverSpec(
    key="defense-demand-shift",
    mirror_slug="defense",   # frontend/themes/defense.json
    description=(
        "the COMPOSITIONAL SHIFT in defense demand — spending moving FROM exquisite, few, "
        "crewed/legacy platforms TOWARD attritable, mass-producible, autonomous, and "
        "software-defined systems, driven by higher global defense budgets (US, Europe, Japan, "
        "India, Gulf) AND recent-conflict lessons that mass + attritability + autonomy beat "
        "exquisite-but-scarce. The structure is PARALLEL capability categories, not a sequential "
        "supply chain: (1) attritable air — low-cost UAVs, loitering / one-way-attack munitions; "
        "(2) counter-UAS — detection and defeat of drones; (3) defense autonomy & AI — targeting, "
        "ISR autonomy, mission software; (4) munitions-at-scale — rebuilt/expanded production of "
        "artillery, missiles, solid rocket motors (magazine depth); (5) electronic warfare & "
        "cyber; (6) enabling components SPECIFIC to these — drone turbojets, seekers, solid rocket "
        "motors, specific sensors. Exposure must be to the SHIFT (the tailwind side), grounded in "
        "disclosed activity — NOT generic defense-budget exposure, NOT a legacy-platform prime, "
        "NOT commercial/consumer drones or aerospace."
    ),
    tie_taxonomy=(
        "driver-specific = tied to a NAMED category of the shift ON THE TAILWIND SIDE — makes/"
        "supplies attritable UAVs or loitering munitions, counter-UAS, defense autonomy/AI "
        "software, scaled (new/expanded) munitions production, EW/cyber for defense, or a "
        "shift-specific component (drone turbojets, seekers, solid rocket motors for the new "
        "munitions). Direction matters: exposure must be to the mass/attritable/autonomous side "
        "demand is shifting TOWARD. "
        "indirect = budget-exposed but not shift-exposed — a legacy/exquisite-platform prime or "
        "generic defense supplier that benefits from the overall budget rise but is not on the "
        "tailwind side (a crewed-aircraft or large-ship prime is INDIRECT here even though it is "
        "deeply in defense, because demand is shifting away from it); also a dual-use component "
        "whose defense/shift use isn't disclosed. "
        "not-driver = adjacent-but-distinct — commercial/consumer/enterprise drones, commercial "
        "aerospace, or a general-industrial name listing 'defense' as one minor end-market."
    ),
    prefilter_terms=(
        "unmanned aerial", "UAV", "drone", "loitering munition", "one-way attack", "counter-UAS",
        "counter-drone", "autonomy", "autonomous systems", "electronic warfare", "directed energy",
        "munitions", "solid rocket motor", "artillery", "missile", "hypersonic", "ISR", "seeker",
        "defense", "military", "warfighter",
    ),
    provenance_tags=(
        ("attritable-air", ("unmanned aerial", "uav", "drone", "loitering", "one-way attack")),
        ("counter-uas", ("counter-uas", "counter-drone", "c-uas", "anti-drone")),
        ("defense-autonomy", ("autonomy", "autonomous", "targeting", "mission software", "ai")),
        ("munitions-scale",
         ("munitions", "artillery", "solid rocket motor", "missile", "magazine")),
        ("ew-cyber", ("electronic warfare", "directed energy", "cyber", "signals")),
        ("space-isr", ("isr", "satellite", "space", "surveillance", "reconnaissance")),
        ("components", ("turbojet", "seeker", "sensor", "propulsion", "warhead")),
    ),
)

# --------------------------------------------------------------------------------------------------
# LOAD-BEARING analyst judgment, encoded VERBATIM in tie_taxonomy (do NOT re-draft). Headwind side
# (brokers/3PLs) is encoded as INDIRECT with opposite sign per the defense precedent — finding-4a
# data point #2. source=component-a (cluster T007, harvest 2026-06-17, disposition 2026-07-13).
# --------------------------------------------------------------------------------------------------
TRUCKLOAD_SUPPLY_PURGE = DriverSpec(
    key="truckload-supply-purge",
    mirror_slug="truckload-supply-purge",   # frontend/themes/truckload-supply-purge.json
    description=(
        "the TRUCKLOAD SUPPLY PURGE — a regulatory-driven contraction of US for-hire truckload "
        "capacity: FMCSA enforcement removing non-domiciled CDL holders (final rule live "
        "2026-03), purges of fraudulent ELD/hours-of-service records, and the unanimous SCOTUS "
        "broker-liability ruling (2026-05) raising the cost of using marginal carriers — "
        "shifting pricing power TOWARD compliant, asset-based truckload carriers and the "
        "services that supply compliant capacity, while freight DEMAND stays weak (a "
        "supply-driven, not demand-driven, upcycle). The structure is the TL-capacity value "
        "chain: shipper → broker/3PL → asset-based TL carrier → owner-operator/small fleet (the "
        "exiting capacity) → driver supply (training/recruiting) → compliance/telematics → "
        "tractor-trailer equipment. Exposure must be to the TAILWIND side of the purge, grounded "
        "in disclosed activity — NOT generic logistics/supply-chain, NOT parcel/rail/ocean/air, "
        "NOT a demand-recovery claim."
    ),
    tie_taxonomy=(
        "driver-specific = tied to the TAILWIND side of the capacity purge — an asset-based "
        "truckload carrier (company tractors, company or leased drivers) whose disclosed revenue "
        "is TL freight priced off spot/contract TL rates; a provider of CDL driver training, "
        "licensing, or recruiting monetizing demand for compliant drivers; a compliance/ELD/"
        "telematics vendor with disclosed enforcement-driven demand; or a disclosed "
        "capacity-consolidation beneficiary (fleet growth or acquisitions into exiting "
        "capacity). Direction matters: exposure must be to the side pricing power is shifting "
        "TOWARD. "
        "indirect = freight-exposed but not purge-tailwind — an LTL-majority carrier "
        "(contract-priced consolidated networks on a different cycle) even though it is deeply "
        "in trucking; an asset-light or brokerage-majority model or 3PL, which is exposed to "
        "this driver on the LOSING side (buy-rate squeeze and post-SCOTUS liability) — flag, "
        "does not clear; intermodal/drayage; tractor-trailer OEMs and dealers (ambiguous "
        "near-term: exiting capacity raises used-truck supply); a logistics conglomerate "
        "without disclosed TL-rate linkage. "
        "not-driver = adjacent-but-distinct — parcel/last-mile, rail, ocean or air freight, "
        "shippers and retailers, warehouse/industrial REITs, generic supply-chain software "
        "without TL-rate or compliance linkage, or a name whose trucking exposure is a minor "
        "end-market."
    ),
    prefilter_terms=(
        "truckload", "less-than-truckload", "for-hire", "spot rate", "contract rate",
        "freight brokerage", "owner-operator", "linehaul", "revenue per loaded mile", "tractor",
        "trailer", "commercial driver", "CDL", "driver training", "driver recruiting",
        "electronic logging", "ELD", "hours of service", "FMCSA", "carrier capacity",
        "purchased transportation", "drayage", "intermodal", "telematics", "3PL",
    ),
    provenance_tags=(
        ("ltl", ("less-than-truckload", "ltl", "tonnage per day", "shipment weight")),
        ("brokerage-3pl",
         ("brokerage", "3pl", "purchased transportation", "freight broker", "asset-light")),
        ("driver-supply",
         ("cdl", "driver training", "driver recruiting", "driver pay", "driving school")),
        ("compliance-telematics",
         ("eld", "electronic logging", "hours of service", "telematics", "fmcsa", "compliance")),
        ("intermodal-dray", ("intermodal", "drayage", "container")),
        # asset-based-tl precedes equipment: a TL carrier names its own tractors/trailers, so those
        # generic-vehicle keywords must not shadow the tailwind bucket (truckload/linehaul). First-
        # match order is load-bearing (regression-pinned). Only the precedence of these two
        # layers changed — the keyword SETS stay analyst-ratified verbatim.
        ("asset-based-tl",
         ("truckload", "linehaul", "loaded mile", "company driver", "irregular route")),
        ("equipment", ("tractor", "trailer", "used truck", "dealer", "fleet sales")),
    ),
)


GLP1_DEMAND_SHIFT = DriverSpec(
    key="glp1-demand-shift",
    # NO `mirror_slug` YET — DELIBERATE. The binding pin refuses a slug pointing at a mirror that
    # does not exist, and `frontend/themes/glp1.json` is CREATED BY THE FIRST SCAN+FREEZE. The
    # field's own docstring records that a real driver exists before its theme does, so the slug
    # is declared when the mirror is, not before. Declaring it early would bind this driver to a
    # file nothing has written — the declared-vs-enforced shape, in the registry.
    description=(
        "the GLP-1 DEMAND SHIFT — incretin (GLP-1/GIP) therapy at population scale re-shaping "
        "FOOD AND BEVERAGE consumption: users eat materially less by volume and re-weight what "
        "they do eat toward protein and satiety, so demand moves AWAY from high-volume "
        "discretionary calories and TOWARD protein-dense, portion-controlled and "
        "satiety-positioned products. BOTH DIRECTIONS ARE IN SCOPE and the sub-structure tag "
        "says which side a name sits on — this is deliberate: a single company can be "
        "suppressed in one category and helped in another (a nutrition portfolio whose "
        "snacking brands face volume decline while its protein brands face a tailwind), and a "
        "one-sided driver would mis-grade exactly those names. The structure is PARALLEL "
        "consumption categories, not a supply chain: (1) suppressed volume — sweet and salty "
        "snacking, confectionery, baked goods, sugared beverages, quick-service restaurants, "
        "alcohol; (2) benefiting nutrition — high-protein foods and shakes, portion-controlled "
        "and meal-replacement formats, satiety/fibre positioning, medical and active nutrition; "
        "(3) adjacent — distribution, private-label manufacture and delivery INTO either side. "
        "Exposure must be to the SHIFT, grounded in disclosed activity — NOT generic packaged-"
        "food exposure, NOT the incretin MANUFACTURERS or their supply chain (that is a "
        "different driver), NOT the PRESCRIBING AND TELEHEALTH CHANNELS through which incretins "
        "are dispensed, and NOT fitness or coaching services. **Product-based meal replacement is "
        "IN SCOPE, not excluded** — it is sold as a product and its exposure is genuinely "
        "two-sided: as a weight-loss METHOD it competes with incretins and is suppressed, and as "
        "nutrition support for incretin users it benefits. The scan decides which; a wording that "
        "pre-excluded the category would defeat the classifier it is meant to configure."
    ),
    tie_taxonomy=(
        "driver-specific = MATERIAL disclosed revenue in a named category of the shift, on "
        "EITHER side, with the sub-structure tag recording which. Suppressed side: a company "
        "whose disclosed volumes sit in snacking, confectionery, sugared beverage, QSR or "
        "alcohol categories facing the consumption decline. Benefiting side: a company whose "
        "disclosed revenue sits in high-protein, portion-controlled, meal-replacement or "
        "satiety-positioned nutrition. DIRECTION IS RECORDED, NOT SCORED — the tag says which "
        "way the shift points for this name; it does not say whether that is good for the "
        "equity, which is the human's call. A name material on BOTH sides is driver-specific "
        "and carries both tags. "
        "indirect = exposed to an affected category without the shift being disclosed as "
        "material — a broadline distributor or contract manufacturer serving snacking or "
        "nutrition among many end-markets, an ingredient supplier whose protein or sweetener "
        "volumes are not broken out, or a retailer whose category mix is not disclosed. "
        "not-driver = adjacent-but-distinct — a food or beverage company with no disclosed "
        "position in an affected category, the incretin drug manufacturers and their CDMO/"
        "device supply chain (a separate driver), the pharmacy and telehealth CHANNELS that "
        "prescribe or dispense incretins, fitness and coaching SERVICES, and general grocery. "
        "The exclusion is of CHANNELS and SERVICES, never of products: a meal-replacement or "
        "portion-control PRODUCT company is driver-specific on whichever side(s) its disclosed "
        "revenue sits, and may carry both tags."
    ),
    prefilter_terms=(
        "GLP-1", "GLP1", "incretin", "semaglutide", "tirzepatide", "weight management",
        "snacking", "snack", "confectionery", "candy", "baked goods", "salty snacks",
        "sugared beverage", "carbonated soft drink", "quick service restaurant", "alcohol",
        "beer", "spirits", "protein", "high-protein", "protein shake", "nutrition bar",
        "meal replacement", "portion control", "satiety", "fiber", "active nutrition",
        "medical nutrition", "ready-to-drink", "private label", "consumer packaged goods",
    ),
    provenance_tags=(
        ("suppressed-volume",
         ("snack", "snacking", "confectionery", "candy", "baked", "cookie", "chip",
          "carbonated", "sugared beverage", "quick service", "restaurant", "alcohol",
          "beer", "spirits", "wine")),
        ("benefiting-nutrition",
         ("protein", "shake", "nutrition bar", "meal replacement", "portion control",
          "satiety", "fiber", "fibre", "active nutrition", "medical nutrition",
          "ready-to-drink", "rtd")),
        ("adjacent",
         ("distribution", "distributor", "private label", "contract manufactur", "co-man",
          "foodservice", "delivery", "ingredient")),
    ),
)

# registry — adding a theme = adding its DriverSpec instance here
DRIVER_SPECS: dict[str, DriverSpec] = {
    AI_DATACENTER.key: AI_DATACENTER,
    DEFENSE_DEMAND_SHIFT.key: DEFENSE_DEMAND_SHIFT,
    GLP1_DEMAND_SHIFT.key: GLP1_DEMAND_SHIFT,
    TRUCKLOAD_SUPPLY_PURGE.key: TRUCKLOAD_SUPPLY_PURGE,
}
