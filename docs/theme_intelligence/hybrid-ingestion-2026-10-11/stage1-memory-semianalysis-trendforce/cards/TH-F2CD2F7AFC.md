# GB300/GB200 vs AMD MI355X serving-cost leadership depends on latency constraints

**WATCH** · Investment thesis · evidence NEW · AI accelerators, GPUs, custom silicon and their direct supply chain · Global · horizon Next 2-4 quarters · status ACTIVE

Published 2026-09-28 (latest source) · first ingested by this registry 2026-10-11 10:16 UTC (new to the registry, not necessarily to the market) · analysed as of 2026-09-28 (a historical replay — a simulated date, not a detection) · last material update 2026-09-28

`TH-F2CD2F7AFC` · ai_infrastructure › ai_infrastructure.compute_semis

_Labels: MEASURED OBSERVATION — a figure or dated event the source reports · FORECAST — a projection or estimate in the source · SOURCE OPINION — the publisher's interpretation or argument, not an established market fact · MODEL INFERENCE — this tool's reasoning · EXTERNALLY VERIFIED — checked against an independent primary source. A line citing several claims carries the weakest label among them._

## 01 BOTTOM LINE
- **SOURCE OPINION:** In SemiAnalysis's InferenceX GLM-5.3 serving benchmark, NVIDIA GB300/GB200 lead on modeled cost at 150 tokens/sec (GB200 ~12% cheaper than MI355X on total tokens), but AMD MI355X ATOM leads at 100 tps and, under a two-second TTFT limit, is about 9% cheaper than B200; GB300 becomes cheapest only when the TTFT limit is relaxed to ten seconds. ⟨cited figures: approximate⟩ [C-c7bd056b369e12, C-6fade64836c7b6, C-823d6a6d53a4b7, C-b2f0fd1d0aed55, C-4cf472eaf9937f, C-75aeaa9783f71a, C-5977936b05a6f6]
- **SOURCE OPINION:** The article states that across the three streaming-speed targets neither system has a uniform cost advantage and that GB300's throughput lead is more than offset by its higher assumed hourly cost at the 150 tps target. ⟨cited figures: approximate⟩ [C-4cf472eaf9937f, C-eb8d1a116355cc, C-5dcc7ad51a4a1c]
- **MODEL INFERENCE:** No vendor has a uniform cost advantage across streaming-speed targets and latency constraints, so competitive positioning between NVIDIA and AMD in inference serving is workload- and constraint-dependent rather than decisively won by one side.

## 02 WHAT CHANGED?
- New to the registry — first ingested 2026-10-11 10:16 UTC, analysed as of 2026-09-28, from a source published 2026-09-28; not necessarily new to the market.
- novelty: novelty_unverified — the registry held no earlier verified baseline, so this is new TO THE REGISTRY, not demonstrated new to the market
- **SOURCE OPINION:** GB200 is about 12% lower cost than MI355X ATOM at the 150 tokens/sec target. ⟨cited figures: approximate⟩ (article date 2026-09-28) [C-b2f0fd1d0aed55]
- **SOURCE OPINION:** ATOM costs about 13% less than GB200 at 100 tokens/sec; GB200 costs about 5% less at 125 and 12% less at 150. ⟨cited figures: approximate⟩ (article date 2026-09-28) [C-4cf472eaf9937f]
- **SOURCE OPINION:** Under a two-second TTFT limit, MI355X ATOM costs $0.0607 per million total tokens vs $0.0666 for B200, about 9% less. (article date 2026-09-28) [C-75aeaa9783f71a]
- **SOURCE OPINION:** With a ten-second TTFT limit, GB300 with Dynamo-TRT-LLM costs $0.0451, about 26% below ATOM's $0.0607. ⟨cited figures: approximate⟩ (article date 2026-09-28) [C-5977936b05a6f6]
- **SOURCE OPINION:** GB300 delivers the lowest modeled serving cost at 150 tokens per second response speed in SemiAnalysis's comparison. (article date 2026-09-28) [C-c7bd056b369e12]
- **SOURCE OPINION:** At 150 tokens/sec, GB200 costs approximately $0.044 per million total tokens. ⟨cited figures: approximate⟩ (article date 2026-09-28) [C-6fade64836c7b6]
- **UNKNOWN:** showing 6 of 13 pieces of evidence from A-c051303aa7e1 — the rest are in 04 KEY EVIDENCE and the evidence ledger

## 03 WHY COULD STOCKS BENEFIT OR SUFFER?
- _Industry shift_ **SOURCE OPINION:** GLM-5.3 agentic serving is benchmarked across NVIDIA GB300/GB200 and AMD MI355X using different inference engines and latency targets. ⟨cited figures: approximate⟩ [C-c7bd056b369e12, C-823d6a6d53a4b7]
- _Pricing_ **SOURCE OPINION:** Modeled serving cost per million tokens shifts between vendors with the streaming-speed target and TTFT limit; GB200 ~12% cheaper at 150 tps, MI355X ~13% cheaper at 100 tps. ⟨cited figures: approximate⟩ [C-b2f0fd1d0aed55, C-4cf472eaf9937f, C-75aeaa9783f71a]
- _Listed-company earnings_ **MODEL INFERENCE:** Relative serving-cost competitiveness could influence accelerator demand and vendor share, but the article does not quantify any effect on NVIDIA's or AMD's earnings.

## 04 KEY EVIDENCE & NUMBERS
| Evidence | Value | Period / as-of | Type | Upstream origin | Anchor |
|---|---|---|---|---|---|
| cost advantage at 100 tps — “ATOM costs about 13% less than GB200 at 100 tokens per second. GB200 costs about 5% less at 125 and 12% less at 150.” | about 13%   | — / as of — | mixed · APPROXIMATE · about · ATOM vs GB200 at 100 tps | InferenceX | SemiAnalysis | A-c051303aa7e1 b015 (C-4cf472eaf9937f; supports; novelty_unverified) |
| cost per million total tokens (10s TTFT limit) — “If the limit is relaxed to ten seconds, GB300 with Dynamo-TRT-LLM becomes eligible at $0.0451, about 26% below ATOM’s $0.0607.” | $0.0451 USD per million tokens  | — / as of — | mixed · APPROXIMATE · GB300 Dynamo-TRT-LLM · ten-second limit · about 26% below ATOM | InferenceX | SemiAnalysis | A-c051303aa7e1 b018 (C-5977936b05a6f6; supports; novelty_unverified) |
| GPU hourly cost assumption — “we assume $2.31 per GB300 GPU hour versus $1.86 for GB200” | $2.31 USD per GPU hour  | — / as of — | mixed · assumed · GB300 | publisher's own analysis | A-c051303aa7e1 b014 (C-5dcc7ad51a4a1c; supports; novelty_unverified) |
| cost per million total tokens — “At 150 tokens per second, GB200 costs approximately $0.044 per million total tokens, compared with $0.049 for MI355X running ATOM.” | $0.044 USD per million tokens  | — / as of — | mixed · APPROXIMATE · approximately · GB200 · estimated from measured curves | InferenceX | SemiAnalysis | A-c051303aa7e1 b011 (C-6fade64836c7b6; supports; novelty_unverified) |
| cost per million total tokens (2s TTFT limit) — “MI355X with ATOM at $0.0607 per million total tokens versus $0.0666 for B200 with Dynamo-SGLang. ATOM costs about 9% less with the two-second first-token limit.” | $0.0607 USD per million tokens  | — / as of — | mixed · MI355X ATOM · two-second first-token limit | InferenceX | SemiAnalysis | A-c051303aa7e1 b018 (C-75aeaa9783f71a; supports; novelty_unverified) |
| cost per million total tokens — “compared with $0.049 for MI355X running ATOM” | $0.049 USD per million tokens  | — / as of — | mixed · APPROXIMATE · MI355X running ATOM · estimated from measured curves | InferenceX | SemiAnalysis | A-c051303aa7e1 b011 (C-823d6a6d53a4b7; supports; novelty_unverified) |
| TTFT constraint — “achieved at least 150 tokens per second with p90 TTFT at most two seconds” | two seconds   | — / as of — | actual · at least 150 tokens per second · p90 TTFT at most | InferenceX | A-c051303aa7e1 b018 (C-8f3575137f8a6d; supports; novelty_unverified) |
| cost per million output tokens — “GB200 costs $5.92 per million output tokens at a response speed of 150 tokens per second, which is about 11% less than $6.68 for MI355X ATOM” | $5.92 USD per million output tokens  | — / as of — | mixed · GB200 · output tokens only | InferenceX | SemiAnalysis | A-c051303aa7e1 b016 (C-98d18432eb7ced; supports; novelty_unverified) |
| cost advantage — “That is about 12% lower cost at the same streaming-speed target.” | about 12%   | — / as of — | mixed · APPROXIMATE · about · GB200 vs MI355X | InferenceX | SemiAnalysis | A-c051303aa7e1 b011 (C-b2f0fd1d0aed55; supports; novelty_unverified) |
| throughput per GPU — “GB300 serves roughly 13950 total tokens per second per GPU here, a 17.5% throughput advantage versus 11873 total tokens for GB200” | 13950 tokens per second per GPU  | — / as of — | mixed · APPROXIMATE · roughly · Dynamo-SGLang | InferenceX | SemiAnalysis | A-c051303aa7e1 b014 (C-bf61a78f94ecdc; supports; novelty_unverified) |
| serving cost ranking — “GB300 delivers the lowest modeled serving cost in our comparison at a response speed of 150 tokens per second” | 150 tokens per second  | — / as of — | mixed · lowest modeled serving cost · modeled | InferenceX | SemiAnalysis | A-c051303aa7e1 b009 (C-c7bd056b369e12; supports; novelty_unverified) |
| throughput advantage — “a 17.5% throughput advantage versus 11873 total tokens for GB200” | 17.5%   | — / as of — | mixed · GB300 vs GB200 · Dynamo-SGLang | InferenceX | SemiAnalysis | A-c051303aa7e1 b014 (C-eb8d1a116355cc; supports; novelty_unverified) |
| For GLM-5.3 on the TileRT low-latency inference engine, AMD's MI355X was the first supported hardware. — “For GLM5.3 on TileRT, AMD MI355X was supported first.” | —   | — / as of — | actual · TileRT compiles decoding into a single persistent kernel | publisher's own analysis | A-c051303aa7e1 b027 (C-b3de575b6e5515; supports; novelty_unverified) |

## 05 AFFECTED COMPANIES / SECTORS
**Sectors / themes the source names as exposed:**
- none named by the source
**Stock exposures of this thesis:**
- AMD — — — UNRESOLVED — the source states: comparator (hardware vendor whose MI355X is compared against NVIDIA systems) — this thesis reads it as potential beneficiary [MODEL INFERENCE] — positive — not_a_recommendation
- NVIDIA GPUs — — — UNRESOLVED — the source states: comparator (GPU maker referenced in TileRT interactivity analysis) — this thesis reads it as potential beneficiary [MODEL INFERENCE] — positive — not_a_recommendation
**Named instruments / indices:**
- none
**Private or unlisted:**
- none
**Named, not securities (products, baskets, agencies):**
- GB300 — — — NOT_A_SECURITY — the source states: comparator (NVIDIA GPU system benchmarked as lowest-cost at 150 tps in InferenceX) — positive — not_a_recommendation
- GB200 — — — NOT_A_SECURITY — the source states: comparator (NVIDIA GPU system benchmarked in InferenceX serving-cost comparison) — positive — not_a_recommendation
- MI355X — — — NOT_A_SECURITY — the source states: comparator (AMD GPU benchmarked against NVIDIA in serving-cost comparison) — positive — not_a_recommendation
- InferenceX — — — NOT_A_SECURITY — the source states: data_source (SemiAnalysis's realtime benchmark platform used for serving-cost estimates) — neutral — not_a_recommendation
- TileRT — — — NOT_A_SECURITY — the source states: context (Low-latency LLM inference engine that supported AMD MI355X first for GLM-5.3) — neutral — not_a_recommendation
- GB300 NVL72 — — — NOT_A_SECURITY — the source states: comparator (NVIDIA GB300 NVL72 rack-scale system used as interactivity comparator) — neutral — not_a_recommendation
- MI335X — — — NOT_A_SECURITY — the source states: comparator (AMD GPU config used as interactivity comparator against FP8 TileRT MI355X) — neutral — not_a_recommendation
**Also named in the source — mentions, NOT exposures of this thesis:**
- Z.ai — — — PRIVATE — the source states: disruptor (developer of the GLM-5 model series analyzed in the article) — neutral — not_a_recommendation
- DeepSeek — — — PRIVATE — the source states: comparator (developer of DeepSeek Sparse Attention and V3.2 compared against GLM-5) — neutral — not_a_recommendation
- Moore Threads MTT S4000 — — — NOT_A_SECURITY — the source states: potential_beneficiary (Chinese GPU suspected as GLM-5's target hardware) — positive — not_a_recommendation
- Moore Threads — — — PRIVATE — the source states: potential_beneficiary (Chinese GPU vendor collaborating with Z.ai, suspected target hardware for GLM-5) — positive — not_a_recommendation
- H800 — — — NOT_A_SECURITY — the source states: comparator (NVIDIA GPU whose roofline DeepSeek designed around) — neutral — not_a_recommendation
- SGLang — — — UNRESOLVED — the source states: context (team/engine behind HiSparse hierarchical memory system) — neutral — not_a_recommendation
- vLLM — — — NOT_A_SECURITY — the source states: context (open-source inference engine referenced for optimizations) — neutral — not_a_recommendation
- SemiAnalysis — — — UNRESOLVED — the source states: publisher (publisher of the article and owner of InferenceX benchmark platform) — neutral — not_a_recommendation
- ATOM — — — NOT_A_SECURITY — the source states: context (inference engine for AMD MI355X in benchmarks) — neutral — not_a_recommendation
- slime — — — NOT_A_SECURITY — the source states: context (Open-source RL training framework used by Z.ai as post-training infrastructure) — neutral — not_a_recommendation
- DeepSeek V3.2 — — — NOT_A_SECURITY — the source states: comparator (DeepSeek model that introduced DeepSeek Sparse Attention, compared to GLM-5) — neutral — not_a_recommendation
- PyTorch — — — NOT_A_SECURITY — the source states: context (Framework whose tensors are used in slime's teacher-switching implementation) — neutral — not_a_recommendation
**Sector labels:** AI accelerators, GPUs, datacenter compute
**Cited baskets (members not named by the source):**
- none
**Enrichment — external hypotheses, not named by the source:** none

## 06 WHY NOW? (NEXT 2-4 QUARTERS)
**Near term:**
- **WITHHELD — failed source verification:** NUMBER_NOT_IN_CITED_CLAIMS — s06.0 prints '28', which none of its cited claims carry: 'Using the September 28 AgentX snapshot, the article shows the vendor cost ranking flips with the lat'
**Longer-term / structural:**
- **SOURCE OPINION:** Serving-cost competitiveness between NVIDIA and AMD accelerators is not uniform and depends heavily on interactivity and TTFT constraints, making headline cost-per-token comparisons misleading without the latency context. ⟨cited figures: approximate⟩ [C-4cf472eaf9937f, C-cabbe248e6e697, C-75aeaa9783f71a]
**Catalyst window:** UNKNOWN — the source names no dated catalyst or earnings window
**Consensus / valuation:** NOT ASSESSED — NOT_ASSESSED — the registry holds no consensus, market-expectation or valuation data; an opportunity here is not valuation proof

## 07 WHAT COULD GO WRONG?
**Counter-evidence:**
- none in the sources so far
**Alternative mechanisms / competing hypotheses:**
- **SOURCE OPINION:** At a single 150 tps target on total tokens, GB200/GB300 appear to clearly lead on cost, which in isolation would favor NVIDIA. [C-c7bd056b369e12, C-b2f0fd1d0aed55]
- **MODEL INFERENCE:** Registry link — SIBLING with TH-B931F456C4: same parent sector (ai_infrastructure), different child economics (ai_infrastructure.memory vs ai_infrastructure.compute_semis)
**Market-level risks:**
- none
**Disconfirming signals:**
- Hyperscalers standardizing on one vendor for GLM-class serving regardless of latency constraint
- Changes in assumed GPU hourly costs that remove the flip in cost leadership
**Unknowns:**
- Premise the source makes it conditional on: Which hardware wins on serving cost depends on the chosen streaming-speed target and the time-to-first-token latency constraint applied.
- Whether these modeled serving costs translate into realized hardware purchasing decisions and vendor revenue share
- Whether the assumed GPU hourly costs reflect actual market pricing
- Whether NVIDIA's or AMD's earnings reflect this competitive dynamic

## 08 DECISION & NEXT TRIGGER
**WATCH** — research attention only; never a purchase or sale.
- **MODEL INFERENCE:** Investigate whether AMD MI355X's low-TTFT cost advantage and NVIDIA's high-throughput advantage map to actual accelerator procurement mix at hyperscalers serving agentic LLM workloads.
**Would raise priority:**
- Hyperscalers disclose GLM-class or agentic serving hardware mix
- AMD or NVIDIA guidance references inference serving cost competitiveness
**Would lower priority:**
- Benchmark assumptions (GPU hourly cost) shown to be unrepresentative
- One vendor demonstrably dominates across all latency targets
**Investment readiness:** NOT_ASSESSED — the registry holds no consensus, market-expectation or valuation data; an opportunity here is not valuation proof
**Decision trace (audit):**
- WATCH (RESEARCH NOW unmet: no source-named exposure (no point-in-time-verified listed company, no sector the source names); no verified dislocation or catalyst; premise is conditional in the source; retrieval PARTIAL)

## 09 SOURCES & CHANGE HISTORY
- [Inside GLM-5.3: How Sparse Attention Affects DRAM Memory TAM](https://newsletter.semianalysis.com/p/sparse-savings-persistent-demand-inside-glm53) — Kimbo Chen; Alec Ibarra; Wenyao Gao; Pratt Bhatt; Bryan Shan; Dylan Patel — SemiAnalysis — article date 2026-09-28 — independent_research — retrieval PARTIAL — origins: InferenceX, InferenceX | SemiAnalysis, publisher's own analysis — novelty_unverified (13 claim refs; A-c051303aa7e1)
**Version history:**
- v1 as of 2026-09-28 — WATCH — evidence NEW — Initial record — created from A-c051303aa7e1 (initial assessment — WATCH (RESEARCH NOW unmet: no source-named exposure (no point-in-time-verified listed company, no sector the source names); no verified dislocation or catalyst; premise is conditional in the source; retrieval PARTIAL))

_Generated 2026-10-11 10:43 UTC from the registry (ti-engine-2; run R-20261011T101628Z-article, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
