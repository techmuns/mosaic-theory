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
drivers, each lens reading its own facts. NO prefilter terms added (the initial three were
REVERTED at review — see REVIEW ROUND below). Taxonomy text is LOAD-BEARING analyst judgment
(the defense precedent) — reviewed verbatim at PR.

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
- Suite: ruff clean, `mypy --strict` clean (136 files), offline pytest **3122 passed, 132
  skipped, exit 0** (= main's 3120 + the new exposure pin + this record's own per-file hygiene
  parametrization).

**REVIEW ROUND (2026-08-31, medium code-review of this PR — four findings applied).**
1. `accelerated computing` was a tag keyword at birth and DISSOLVED the boundary: executed
   during review, `"record demand for our accelerated computing platform drove data center
   revenue up 60% on GPU shipments"` — a pure GPU-shipments volumes fact — tagged
   `silicon-ecosystem-moat`. The keyword is the vendor's VOLUME label, not a moat term. Removed
   (three keywords remain), and the realistic sentence is now a regression pin — the original
   negative pin's sentence contained no new keyword, so it could not catch this.
2. The three prefilter terms were reverted: recall was already covered (a silicon-AI vendor's
   filing always matches `artificial intelligence`/`inference`), each term costs one paced EFTS
   query per CIK-batch per scan, `developer ecosystem`/`programming model` recruit generic
   developer-relations filers into full LLM assessments, and every term's tokens widen the
   `_driver_vocab` grounding stop-list (a marginal weakening of the fabrication check). Tag
   keywords run free on candidate evidence text regardless — the ai-datacenter precedent: 33 of
   its tag keywords are not prefilter terms.
3. The not-driver exclusion had NARROWED to "volumes", leaving non-volume chain economics
   (ASP/mix-driven HBM revenue, packaging contract revenue) excluded by neither clause.
   Restored: the build-out chain is excluded in economics of ANY shape, with category (5) the
   single named carve-out.
4. The boundary is now RECIPROCAL (the glp1 sibling-pair precedent): `_AI_DC_TIE_TAXONOMY`
   gained one sentence routing a silicon vendor's model-agnostic software/ecosystem MOAT
   economics to this sibling while keeping unit/capacity/build-out economics there. That
   sentence is the one edit to the sibling's judgment text — review it verbatim.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A vendor's platform-language sentence ("accelerated computing **platform**") still carries the
  pre-existing `hyperscaler-platform` keyword `platform` — multi-tag records it. Inform-only
  by design (the human reads the verbatim fact), and sometimes TRUE (a hyperscaler running its
  own silicon + software stack genuinely holds both positions). Accepted, not patched.
- `software stack` remains a tag keyword and is not silicon-exclusive prose — an app-layer fact
  saying "our software stack" can carry the moat tag alongside its own. Multi-tag inform-only;
  accepted, watched at the first real scan (the corpus check).
- The remaining tag keywords still add their tokens (`developer`, `ecosystem`, `programming`,
  `stack`) to this driver's `_driver_vocab` grounding stop-list — the structural cost of any
  vocabulary entry, halved by the prefilter revert. Accepted, stated.
