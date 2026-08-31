---
id:
status: shipped
prs: [532]
date: 2026-08-31
supersedes:
superseded-by:
---

# Hyperscaler-platform tag precision — a tag that fired on 12 of 12 names now fires on 7, keeping all three providers

**WHAT.** `ai-value-migration`'s `hyperscaler-platform` provenance keywords change from
`("cloud", "hyperscaler", "inference", "platform", "distribution")` to the PROVIDER's vocabulary:
`("hyperscaler", "public cloud", "cloud infrastructure", "infrastructure-as-a-service", "iaas",
"aws", "azure", "google cloud", "intelligent cloud")`. Nothing else in the spec moves;
"inference" deliberately STAYS in the `description` (it is genuinely part of this layer's
economics, and the description is what the grader reads) while leaving the keyword set.

**WHY — MEASURED ON THE FIRST REAL SCAN, not supposed.** The bounded pilot of `ai-value-migration`
(12 operator-named beneficiaries: MSFT/GOOGL/AMZN/NVDA/META/CRM/NOW/VEEV/SAP/SNOW/MDB/PLTR,
12 assessed, 0 scan errors) tagged **12 of 12** with `hyperscaler-platform`. A tag that fires on
every name carries no information, and the by-tag volume read is the entire purpose of this
layer. Per-keyword measurement over the same committed assessments named the cause exactly:
bare `cloud` matched **12/12** (every SaaS filer says it) and `inference` matched **8/12** (any
app-layer name describing an AI feature). Re-running the resolver over those same real facts:

| keyword set | tagged | providers kept (MSFT/GOOGL/AMZN) | false |
|---|---|---|---|
| current | 12/12 | 3/3 | 9 |
| drop bare `platform`+`distribution` | 12/12 | 3/3 | 9 |
| **provider vocabulary (shipped)** | **7/12** | **3/3** | **4** |
| provider vocabulary + `inference` | 10/12 | 3/3 | 7 |

Precision 25% → 43% with zero loss of the names that genuinely sell the below-the-model layer.

**THE RESIDUAL, STATED AND PINNED.** Four false positives remain — SAP, PLTR, SNOW, NVDA — and
every one is a filer NAMING a hyperscaler ("our software is deployed on AWS", "we partner with
hyperscalers"), which is lexically identical to BEING one. No keyword set separates mention from
identity; that is semantic. The tag therefore stays what its own resolver docstring already
says it is — PROVENANCE, approximate, inform-only, with the human reading the verbatim fact —
and the discrimination that matters is the LLM's `driver_tie` grade, not this keyword read. The
residual is pinned as an assertion so a later reader sees it as a known limit rather than a bug.

**HOW VERIFIED.**
- `tests/test_themes_exposure.py::test_hyperscaler_platform_tags_the_provider_not_every_filer_that_says_cloud`
  — the sentences are VERBATIM from the pilot's committed assessments, frozen as fixtures (a
  value-level pin belongs on a frozen fixture, never on a re-drawn artifact; freezing them is
  also what makes this a corpus check rather than text invented to fit the keywords). Positive:
  Alphabet's two-segment sentence, Microsoft's Intelligent Cloud segment sentence, Amazon's AWS
  segment sentence. Negative: Veeva's "industry cloud solutions", ServiceNow's AI-governance
  sentence, and an app-layer "run inference on their own enterprise data". Residual: "deployed
  on AWS" still tags.
- ruff + `mypy --strict` clean; full offline suite green.

**SECOND CHANGE, SAME METHOD — the PREFILTER, one layer up.** The first full sweep exposed a
bigger cost than the tag: the prefilter passed **2,666 of 2,907 names (92%)** to the expensive
semantic layer, and each waved-through name costs filing fetches plus one LLM assessment. The
per-term measurement (over cached EFTS responses) named the cause exactly: **"artificial
intelligence" matched 2,579 on its own**, "generative AI" another 985 — every modern 10-K says
them — while ten other terms contributed ZERO unique names. Candidate sets evaluated by UNION and
by recall on the 12 operator-named beneficiaries (all known-real, every one assessed
driver-specific in the pilot):

| set | candidates | pilot recall |
|---|---|---|
| current (21 terms) | 2,666 (92%) | 12/12 |
| drop "artificial intelligence" | 1,652 (57%) | 12/12 |
| **drop BOTH generic phrases (shipped)** | **1,266 (44%)** | **12/12** |
| + drop the 10 zero-unique terms | 1,065 (37%) | 10/12 — loses META, PLTR |

Shipped the −53% cut; the deeper one drops two names the operator's card lists by name.

**THE RECALL CLAIM WAS THEN MEASURED, NOT ASSUMED.** 12/12 recall on twelve megacaps proves
little about a small-cap whose only AI language is the generic phrase — so the population the
narrowing GIVES UP was sampled directly: 20 names whose ONLY prefilter signal was the two generic
phrases, assessed through the real scan path. **0 of 20 carried REAL exposure** (11
aspirational-intent-only, 9 no-theme-exposure-disclosed); the sample is AEM, GATX, RLI, SAIA,
ABEV, ACGL and similar — a gold miner, a railcar lessor, an insurer, a trucker, a brewer. The
generic phrase was importing exactly that.

**THE SIBLING IS DELIBERATELY UNTOUCHED.** `ai-datacenter` keeps "artificial intelligence": its
other terms are hardware-chain vocabulary (HBM, liquid cooling, switchgear) that a software filer
never uses, so the generic phrase is that driver's only bridge to an AI-cloud name. Same word,
different job — measured per driver rather than swept out globally, and pinned.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- RECALL: a genuine provider that describes itself only as "cloud" with no provider vocabulary
  and no named segment now goes untagged (`unspecified`). Accepted — an untagged fact is still
  scanned, graded and rendered; only its by-layer bucket is missing, which is the cheaper error
  than a bucket that means nothing.
- The other four drivers' tags are untouched. The glp1-drug-value-chain pilot showed a clean
  spread across all four of its classes (manufacturing-infra 5 · next-gen-assets 4 ·
  incumbent-franchise 2 · access-distribution 2), so nothing there needs this treatment.
