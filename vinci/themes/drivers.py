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
    description=_AI_DC_DESCRIPTION,
    tie_taxonomy=_AI_DC_TIE_TAXONOMY,
    prefilter_terms=_AI_DC_PREFILTER,
    provenance_tags=_AI_DC_LAYERS,
)

# registry — adding a theme = adding its DriverSpec instance here
DRIVER_SPECS: dict[str, DriverSpec] = {AI_DATACENTER.key: AI_DATACENTER}
