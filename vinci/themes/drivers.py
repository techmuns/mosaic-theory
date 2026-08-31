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
    "'broad AI market' adjacency. A silicon vendor's MODEL-AGNOSTIC software/developer-ecosystem "
    "MOAT economics (developer base, programming-model lock-in — the moat, not unit demand) "
    "belong to the ai-value-migration sibling, not here; the vendor's unit/capacity/build-out "
    "economics stay HERE. (Reciprocal boundary, the glp1 sibling-pair precedent — added "
    "2026-08-31 with the silicon-ecosystem-moat refinement.)"
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
        "EITHER side. RECORD EVERY APPLICABLE SIDE, NOT THE STRONGEST ONE: a company with "
        "material revenue in BOTH a suppressed category and a benefiting one is exposed twice "
        "over, and reporting one side would state the smaller truth — a nutrition portfolio "
        "whose snacking brands face volume decline while its protein brands face a tailwind is "
        "suppressed-volume AND benefiting-nutrition, and a meal-replacement product is both a "
        "weight-loss METHOD competing with incretins and nutrition support for incretin users. "
        "The sub-structure tags record which sides. Suppressed side: a company "
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
    multi_tag=True,   # a name can be suppressed in one category and helped in another
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

# --------------------------------------------------------------------------------------------------
# AI value migration — a WHERE-VALUE-ACCRUES theme over the AI software/platform stack, NOT the
# physical datacenter build-out (that is AI_DATACENTER, the sibling — but see the 2026-08-30
# boundary refinement below: what routes there is UNIT/CAPACITY demand, not a silicon vendor's
# software moat). LOAD-BEARING analyst judgment encoded from the OPERATOR's stated thesis
# (2026-08-29) — review verbatim at PR like the defense precedent: if the frontier-to-open
# catch-up window holds at ~3-6 months or compresses, raw model IP commoditizes and value capture
# migrates to the layers ABOVE (apps with workflow/user/data/regulatory moats) and BELOW
# (hyperscaler compute/distribution/data gravity). Direction matters, and one company can sit on
# BOTH sides (a hyperscaler owns frontier-model IP AND the platform layer) → multi_tag, the glp1
# precedent.
# BOUNDARY REFINEMENT (operator ruling 2026-08-30): the winners share one property —
# MODEL-AGNOSTIC value capture (they win whichever model wins, because the model layer is
# commoditized) — and the operator names three beneficiary classes: model-agnostic hyperscalers,
# model-agnostic app-layer moats, and model-agnostic SILICON vendors whose SOFTWARE/ECOSYSTEM
# bundle is the moat. The original blanket "chips → ai-datacenter" exclusion conflated two
# different economics: GPU UNIT/CAPACITY demand from the build-out (the sibling's territory,
# unchanged) vs a silicon vendor's model-agnostic software/developer-ecosystem moat capturing AI
# economics regardless of which model wins (THIS driver — the silicon-ecosystem-moat tag). The
# split is by ECONOMICS NAMED in the disclosure, not by company: one vendor can be candidate in
# both drivers, each lens reading its own facts.
# --------------------------------------------------------------------------------------------------
AI_VALUE_MIGRATION = DriverSpec(
    key="ai-value-migration",
    # NO mirror_slug — deliberate (the glp1 precedent): the theme page does not exist yet; the
    # slug is declared when the mirror is, not before.
    description=(
        "the MIGRATION OF AI VALUE CAPTURE across the software/platform stack — if the "
        "frontier-to-open-source model catch-up window stays at ~3-6 months or compresses, raw "
        "frontier-model IP commoditizes and durable AI economics migrate to the layers ABOVE the "
        "model (application software with workflow/user/data/regulatory moats monetizing AI on "
        "proprietary data and installed workflows) and BELOW it (hyperscaler compute, cloud "
        "distribution, data gravity). The structure is PARALLEL stack layers, not a supply "
        "chain: (1) app-workflow-moat — vertical / system-of-record software with disclosed AI "
        "monetization on proprietary data or regulated workflows; (2) hyperscaler-platform — "
        "cloud/compute/distribution capturing disclosed inference and AI-deployment economics; "
        "(3) model-ip — frontier-model licensing/API economics (the LOSING side if the window "
        "holds); (4) open-ecosystem — names whose disclosed economics benefit from open-weights "
        "adoption (tooling, serving, customization); (5) silicon-ecosystem-moat — silicon "
        "vendors whose MODEL-AGNOSTIC software/developer-ecosystem bundle (programming model, "
        "software stack, developer base) captures AI economics whichever model wins — the moat, "
        "never the unit volumes. BOTH DIRECTIONS ARE IN SCOPE and the tag "
        "says which side a name sits on. Exposure must be to the MIGRATION (which layer captures "
        "AI economics), grounded in disclosed activity — NOT generic 'AI' adjacency, NOT the "
        "physical AI-datacenter build-out chain (chips/HBM/packaging/cooling/power — build-out "
        "economics of ANY shape, unit demand and pricing/mix/contract revenue alike — the "
        "ai-datacenter driver; the ONE carve-out routed here is category (5) above), NOT "
        "consumer-device AI feature mentions."
    ),
    tie_taxonomy=(
        "driver-specific = disclosed economics tied to a NAMED layer of the migration, on EITHER "
        "side — RECORD EVERY APPLICABLE SIDE, NOT THE STRONGEST ONE: a hyperscaler that owns "
        "frontier-model IP AND the platform beneath it carries both tags. Tailwind side: "
        "application software with a disclosed workflow/user/data/regulatory moat monetizing AI "
        "(AI attach or module revenue on proprietary data, a regulated system-of-record "
        "position), platform/compute with disclosed inference or AI-deployment economics, or a "
        "silicon vendor with disclosed MODEL-AGNOSTIC software/developer-ecosystem economics "
        "(software attach revenue, developer base, programming-model lock-in) — the moat, not "
        "the unit volumes. "
        "Losing side: revenue disclosed as predominantly frontier-model IP monetization "
        "(per-token / API / model licensing) WITHOUT a moat layer above or below it. DIRECTION "
        "IS RECORDED, NOT SCORED — the tag says which way the migration points for this name; "
        "whether that is good for the equity is the human's call. "
        "indirect = 'AI-enabled' claims without disclosed layer economics — an AI feature "
        "mention carrying no attach revenue, no moat disclosure, and no platform economics. "
        "not-driver = the physical AI-datacenter build-out chain (chips, HBM, advanced "
        "packaging, thermal/cooling, power, optical — build-out economics of ANY shape: unit/"
        "capacity demand, ASP/mix, chain contract revenue — the ai-datacenter driver's "
        "territory). The ONE carve-out routing here is the tailwind clause above — a silicon "
        "vendor's model-agnostic software/developer-ecosystem MOAT economics; the split is by "
        "ECONOMICS NAMED in the disclosure, not by company. Also not-driver: consumer-device "
        "AI, or a name whose AI exposure is a minor undisclosed end-market."
    ),
    prefilter_terms=(
        # THE TWO GENERIC AI PHRASES ARE DELIBERATELY ABSENT (measured 2026-08-31, first full
        # sweep): "artificial intelligence" alone matched 2,579 of 2,907 names and "generative AI"
        # 985 — every modern 10-K says them, so the cheap filter was passing 92% of the universe
        # through to the expensive one (2,666 candidates, each costing filing fetches + one LLM
        # assessment). Dropping BOTH takes the candidate set to 1,266 (-53%) while every one of
        # the 12 operator-named beneficiaries still clears the filter on its layer vocabulary.
        # The prefilter buys RECALL and the semantic layer does the discriminating — but recall
        # bought with a phrase that matches everything is not recall, it is cost.
        "AI agent", "agentic", "copilot",
        "large language model", "foundation model", "open-source model", "open weights",
        "inference", "fine-tuning", "proprietary data", "system of record",
        "workflow automation", "vertical software", "per-seat", "consumption-based",
        "model licensing", "API pricing", "cloud platform", "hyperscaler",
        # NO silicon-specific prefilter terms, deliberately (review 2026-08-31): a silicon-AI
        # vendor's filing always matches the existing terms ("artificial intelligence",
        # "inference"), so moat terms here would buy no recall while costing one paced EFTS
        # query per CIK-batch each and recruiting generic developer-relations filers into full
        # LLM assessments. Tag keywords run free on candidates' evidence text regardless —
        # the ai-datacenter precedent (33 of its tag keywords are not prefilter terms).
    ),
    multi_tag=True,   # one company can own model IP AND the platform/app layers — record all
    provenance_tags=(
        ("app-workflow-moat",
         ("system of record", "workflow", "vertical", "regulated", "proprietary data",
          "copilot", "attach")),
        # 2026-08-31, MEASURED on the first real scan: the previous keywords
        # ("cloud", "hyperscaler", "inference", "platform", "distribution") tagged 12 of 12
        # scanned names — a tag that fires on everything carries no information, and the by-tag
        # volume read is the whole point of this layer. Bare "cloud"/"platform" match any SaaS
        # filer; "inference" matches any app-layer name describing an AI feature. These are the
        # PROVIDER's vocabulary instead — what a filer says when it SELLS the compute layer,
        # including the named segments the real hyperscalers report under. On the pilot: 12/12 →
        # 7/12, with all three genuine providers (MSFT/GOOGL/AMZN) retained.
        # NOTE the residual, which is NOT fixable here: a filer that NAMES a hyperscaler
        # ("we run on AWS") reads identically to one that IS one. SAP/PLTR/SNOW still tag on
        # exactly that. Mention-vs-identity is semantic, not lexical — the tag stays PROVENANCE
        # (approximate, inform-only; the human reads the verbatim fact), and the discrimination
        # that matters is the LLM's driver_tie grade, not this keyword read.
        # "inference" deliberately stays in the DESCRIPTION (it is a real part of this layer's
        # economics, and the description is what the grader reads) while leaving the keyword set.
        ("hyperscaler-platform",
         ("hyperscaler", "public cloud", "cloud infrastructure", "infrastructure-as-a-service",
          "iaas", "aws", "azure", "google cloud", "intelligent cloud")),
        ("model-ip",
         ("foundation model", "frontier", "model licensing", "per-token", "api pricing",
          "large language model")),
        ("open-ecosystem",
         ("open-source", "open weights", "fine-tuning", "customization", "serving")),
        # 2026-08-30 refinement — the operator's third model-agnostic beneficiary class. The
        # keywords name the SOFTWARE moat, deliberately never bare silicon terms ("gpu", "chip")
        # and never the vendor volume label "accelerated computing" (review 2026-08-31: it tagged
        # a GPU-shipments sentence, dissolving the boundary — pinned): a unit-demand sentence
        # must fall through to unspecified here and be read by the ai-datacenter lens, not
        # mis-tagged as a moat.
        ("silicon-ecosystem-moat",
         ("developer ecosystem", "programming model", "software stack")),
    ),
)

# --------------------------------------------------------------------------------------------------
# GLP-1 drug value chain — the DRUG-SIDE sibling GLP1_DEMAND_SHIFT explicitly carves out ("the
# incretin MANUFACTURERS and their CDMO/device supply chain (a separate driver)" — its not-driver
# text). LOAD-BEARING analyst judgment encoded from the OPERATOR's stated thesis (2026-08-29) —
# review verbatim at PR: no demand peak; a SECOND GROWTH PHASE driven by affordability/access,
# supply-constraint resolution, orals, direct-to-patient distribution, generic expansion, and a
# chronic induction-to-maintenance model — volumes UP, manufacturer pricing COMPRESSED, share
# FRAGMENTING. The best equity may not be the fastest-growing incumbent → per-name, both-sided
# tagging (multi_tag): an incumbent franchise is volume-tailwind AND price/share-headwind at once.
# --------------------------------------------------------------------------------------------------
GLP1_DRUG_VALUE_CHAIN = DriverSpec(
    key="glp1-drug-value-chain",
    # NO mirror_slug yet — same rule as above.
    description=(
        "the GLP-1 DRUG VALUE CHAIN's SECOND GROWTH PHASE — incretin therapy transitioning from "
        "supply-constrained scarcity to a volume-driven, price-competitive, chronic-treatment "
        "market: affordability/access expansion, resolution of supply constraints, oral "
        "formulations, direct-to-patient distribution, generic/compounded entry, and an "
        "induction-to-maintenance chronic model. Treated patient VOLUMES rise while manufacturer "
        "PRICING compresses and market share FRAGMENTS — so the equity question is per-name, not "
        "category-level. The structure is PARALLEL categories: (1) incumbent-franchise — "
        "marketed incretin franchises (two-sided: volume tailwind AND price/share headwind); "
        "(2) next-gen-assets — differentiated pipelines (orals, amylin, multi-agonists, "
        "muscle-preserving combinations); (3) manufacturing-infra — peptide API, CDMO / "
        "fill-finish capacity, devices/auto-injectors (the infrastructure-economics leg); "
        "(4) access-distribution — direct-to-patient, pharmacy/telehealth fulfillment, and "
        "generic distribution WITH disclosed incretin volume linkage. BOTH DIRECTIONS ARE IN "
        "SCOPE and the tag says which side a name sits on. Exposure must be to the drug value "
        "chain, grounded in disclosed activity — NOT the food/beverage consumption shift (the "
        "glp1-demand-shift SIBLING driver), NOT payers/PBMs without disclosed incretin "
        "economics, NOT fitness or weight-management services."
    ),
    tie_taxonomy=(
        "driver-specific = MATERIAL disclosed revenue or pipeline in a named category of the "
        "chain, on EITHER side — RECORD EVERY APPLICABLE SIDE, NOT THE STRONGEST ONE: an "
        "incumbent incretin franchise is volume-tailwind AND price/share-headwind at once and "
        "carries both readings; a CDMO or fill-finish supplier with disclosed incretin capacity "
        "is infrastructure-tailwind; a differentiated next-generation asset (oral, amylin, "
        "multi-agonist, muscle-preserving) with disclosed clinical progress is pipeline-side. "
        "DIRECTION IS RECORDED, NOT SCORED — the tag says which way the second phase points for "
        "this name; whether the market misprices it is the human's call. "
        "indirect = category-exposed without the chain being disclosed as material — a broad "
        "pharma, CDMO, or device maker serving injectables generally with no incretin "
        "attribution, or distribution with no disclosed GLP-1 volume linkage. "
        "not-driver = the consumption-shift side (food, beverage, nutrition — the "
        "glp1-demand-shift sibling driver), payers/PBMs, fitness and coaching services, and "
        "general pharmacy retail without disclosed incretin economics."
    ),
    prefilter_terms=(
        # MEASURED 2026-08-31 (first full sweep, then a per-term read of the cached EFTS
        # responses): this filter passed 1,772 of 2,907 names, and FOUR generic ENGLISH words
        # carried nearly all of it — "compounded" 993 matches / 578 unique, "generic" 663/152,
        # "contract manufacturing" 471/78, "capacity expansion" 308/144 — while every specific
        # molecule term (semaglutide, tirzepatide, incretin, amylin) matched 5-30 and contributed
        # ZERO unique names.
        #
        # THE TRAP THIS AVOIDS: two of those words are ALSO terms of art in this thesis —
        # compounded semaglutide from compounding pharmacies IS the access-channel leg, and
        # generic entry after expiry IS the price-compression leg. Deleting them would have cut
        # real signal. So the bare words are REPLACED by phrases that carry the meaning AND have
        # no parent term already in this list: "compounding pharmacy" (5 names), "generic entry"
        # (27), "generic competition" (164), "loss of exclusivity" (167 — the most precise
        # vocabulary pharma has for that leg).
        #
        # REVIEW 2026-08-31: the first draft also added "compounded semaglutide", "compounded
        # GLP-1" and "peptide manufacturing". Each is a strict SUPERSET STRING of a term still
        # listed below ("semaglutide", "GLP-1", "peptide"), so it can never match a filing the
        # parent does not already match — verified against the live universe (SUBSET=True for all
        # three). They bought nothing and cost ~30 paced EFTS queries apiece per scan, so they are
        # gone. A candidate phrase must clear that test: does anything already here contain it?
        # The same check also caught a PRE-EXISTING instance — "peptide synthesis" (5 names) is
        # covered by "peptide" (135) and predates this change; removed here because the rule is
        # now machine-checked for every driver and a list that fails its own invariant is worse
        # than the one line saved.
        #
        # Result: 1,772 -> 531 candidates (-70%) with 11/11 recall on the names
        # the first pilot proved driver-specific, and the 1,244 names given up were SAMPLED
        # through the real scan path: 0 of 20 carried real exposure, 18 of 20 disclosed none at
        # all (Adobe, Jacobs, Sonoco, Zebra, W.P. Carey, Rivian — what "compounded" as ordinary
        # English was importing).
        #
        # The manufacturing leg the card names stays covered by the SPECIFIC terms below (CDMO,
        # fill-finish, sterile injectable, peptide synthesis/manufacturing) rather than by bare
        # "contract manufacturing", which matched every manufacturer in the universe.
        "GLP-1", "GLP1", "incretin", "semaglutide", "tirzepatide", "obesity",
        "weight management", "amylin", "dual agonist", "triple agonist", "oral formulation",
        "peptide", "fill-finish",
        "sterile injectable", "auto-injector", "prefilled", "CDMO", "telehealth",
        "direct-to-patient", "compounding pharmacy",
        "generic entry", "generic competition", "loss of exclusivity",
    ),
    multi_tag=True,   # an incumbent is suppressed on price and helped on volume — record both
    provenance_tags=(
        ("incumbent-franchise",
         ("semaglutide", "tirzepatide", "franchise", "net price", "market share")),
        ("next-gen-assets",
         ("oral", "amylin", "agonist", "phase 2", "phase 3", "muscle", "pipeline")),
        ("manufacturing-infra",
         ("peptide", "fill-finish", "cdmo", "sterile", "capacity", "auto-injector",
          "contract manufacturing")),
        ("access-distribution",
         ("telehealth", "direct-to-patient", "pharmacy", "compounded", "generic",
          "distribution")),
    ),
)

# registry — adding a theme = adding its DriverSpec instance here
DRIVER_SPECS: dict[str, DriverSpec] = {
    AI_DATACENTER.key: AI_DATACENTER,
    AI_VALUE_MIGRATION.key: AI_VALUE_MIGRATION,
    DEFENSE_DEMAND_SHIFT.key: DEFENSE_DEMAND_SHIFT,
    GLP1_DEMAND_SHIFT.key: GLP1_DEMAND_SHIFT,
    GLP1_DRUG_VALUE_CHAIN.key: GLP1_DRUG_VALUE_CHAIN,
    TRUCKLOAD_SUPPLY_PURGE.key: TRUCKLOAD_SUPPLY_PURGE,
}
