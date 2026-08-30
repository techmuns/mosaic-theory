---
id:
status: shipped
date: 2026-08-30
prs: [520]
supersedes:
superseded-by:
---

# Silicon-ecosystem-moat — the third model-agnostic beneficiary class enters `ai-value-migration` (`vinci/themes/drivers.py`)

**WHAT.** Operator ruling 2026-08-30, arrived as a question that found a boundary error: the
operator names THREE model-agnostic beneficiary classes of open-source proliferation —
hyperscalers, app-layer moats, and **silicon vendors whose SOFTWARE/developer-ecosystem bundle is
the moat**. The first two already existed as `hyperscaler-platform` / `app-workflow-moat`; the
third was blanket-excluded by the original spec's "chips → ai-datacenter" not-driver line, which
conflated two different economics. The amendment splits them: GPU **unit/capacity demand** from
the build-out stays the ai-datacenter sibling's territory, unchanged; a silicon vendor's
**model-agnostic software/ecosystem moat** (programming model, software stack, developer base)
is now in scope HERE as a fifth provenance tag, `silicon-ecosystem-moat`. The split is by
ECONOMICS NAMED in the disclosure, never by company — one vendor can be candidate in both
drivers, each lens reading its own facts. Three prefilter terms added for recall
(`accelerated computing`, `developer ecosystem`, `programming model`). Taxonomy text is
LOAD-BEARING analyst judgment (the defense precedent) — reviewed verbatim at PR.

**WHY.** The operator's three-class framing also settled the thesis card's mechanism
(supply-side: all three winners capture value *whichever model wins*, because the model layer is
commoditized — one supply shock, three landing zones). A scan run before this amendment would
have read a CUDA-shaped moat disclosure as not-driver and silently routed the operator's third
beneficiary class out of its own theme.

**HOW VERIFIED.**
- Tag-resolution sanity run through the real resolver (`provenance_tags_of`) on filing-shaped
  sentences: the moat sentence tags `silicon-ecosystem-moat`; an HBM/packaging unit-demand
  sentence falls through to `unspecified` (the deliberate design — the keywords name only the
  software moat, never bare silicon terms, so a volumes fact stays the sibling's); the existing
  app/hyperscaler sentences tag exactly as before. No live exposure corpus exists yet for this
  driver (no scan has run since it entered the registry 2026-08-29), so there is no committed
  evidence set to replay — stated, not skipped silently; the first real scan is the corpus check.
- Boundary pinned:
  `tests/test_themes_exposure.py::test_silicon_ecosystem_moat_tags_the_software_moat_never_unit_demand`
  (moat tags, unit-demand falls through, multi_tag on).
- Suite: ruff clean, `mypy --strict` clean (136 files), offline pytest exit 0 at [100%]
  (3253 collected; the doubled `-q` from addopts suppresses the count line — exit code is the
  verdict).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A vendor's platform-language sentence ("accelerated computing **platform**") also carries the
  pre-existing `hyperscaler-platform` keyword `platform` — multi-tag records both. Inform-only
  by design (the human reads the verbatim fact), and sometimes TRUE (a hyperscaler running its
  own silicon + software stack genuinely holds both positions). Accepted, not patched.
- The ai-datacenter spec is untouched (hold scope): its taxonomy grades build-out economics, and
  a software-moat sentence carries no capacity signal there anyway. If the first real
  ai-value-migration scan shows moat facts still leaking to the sibling, the fix is a sibling
  taxonomy clarification — noted, not built.
