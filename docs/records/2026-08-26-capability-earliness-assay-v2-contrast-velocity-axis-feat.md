---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **Earliness-assay v2 — CONTRAST velocity axis (`feat/assay-v2`; ZERO LLM, backend-only, nothing

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

- _Pre-merge audit (3 independent reviewers): NO critical/high bug — incumbency boundary, contrast
  criterion (fuzz-verified), recorded-basis byte-identity, no-lookahead, zero-LLM all confirmed.
  Corrected 2 accuracy defects + 1 latent crash: (i) the `anchored_specific` schema comment falsely
  asserted `= incumbent + new_listings + unknown` — `new_listings` is an ALL-tier gauge, not the
  SPECIFIC-tier partition's middle term (comment fixed; the counts were already correct); (ii) removed
  the unsupported "Apple in / Cipher-Mining-2020-SPAC out" worked-example — per-CIK in/out is emitted
  by NO card, so the machinery claim now rests only on the (9d) decomposition, which IS shown; (iii)
  hardened `filing_history` vs blank `filingDate` / null `recent` (opaque fromisoformat/AttributeError
  crash → UNKNOWN), regression-pinned. ACCEPTED, no fix: the same-date 8-K/10-K form-split tie is
  prefilter-order-deterministic and affects only the split, never the headline `incumbent_specific`._
- _Whole suite green (ruff + mypy --strict clean; `pytest -m "not network"` passes)._
