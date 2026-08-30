---
id:
status: shipped
date: 2026-08-29
prs: [519]
supersedes:
superseded-by:
---

# Opus 5 default + two new drivers (`vinci/config.py::graph_llm_model`, `vinci/themes/drivers.py`) — the operator's model ruling and the operator's two theses enter the registry

**WHAT.** Two operator rulings of 2026-08-29, shipped together and independent of the open
theme-thesis PRs (#516/#517/#518 — this branch is off main; pre-existing files only).

1. **`graph_llm_model` default: `claude-opus-4-8` → `claude-opus-5`.** The same
   strongest-available-model policy that picked Opus 4.8 ("accuracy gates the moat hypothesis"),
   applied to the new generation, on the operator's explicit instruction. The stale
   current-default statements in `vinci/graph/llm.py`'s docstring and the `graph-test0 --model`
   help were updated; the HISTORICAL benchmark references stay as history. The knob remains a
   swap-the-config parameter, not a router, and `--model claude-opus-4-8` remains the named
   diagnostic baseline.
2. **Two `DriverSpec`s** appended to `DRIVER_SPECS` (registry now six drivers):
   - **`ai-value-migration`** — WHERE AI value accrues across the software/platform stack if the
     frontier-to-open catch-up window holds at ~3-6 months: app-workflow-moat /
     hyperscaler-platform (tailwind) vs model-ip (losing side) vs open-ecosystem; `multi_tag`
     (a hyperscaler owns model IP AND the platform — both sides recorded). Explicit boundary:
     the physical datacenter build-out chain is NOT-DRIVER here and routes to the
     `ai-datacenter` sibling.
   - **`glp1-drug-value-chain`** — the drug-side sibling the existing `glp1-demand-shift` spec
     explicitly carved out ("the incretin MANUFACTURERS and their CDMO/device supply chain (a
     separate driver)"): second-growth-phase incretin economics — volumes up, manufacturer
     pricing compressed, share fragmenting — across incumbent-franchise (two-sided) /
     next-gen-assets / manufacturing-infra / access-distribution; `multi_tag`.
   Both carry NO `mirror_slug` (the glp1 precedent — the slug is declared when the theme page
   is, not before), so every mirror-bound registry test passes them through untouched.

**WHY.** The drivers encode the OPERATOR's two stated theses (2026-08-29 message), in the
registry's own contract: adding a theme = adding a `DriverSpec`; the classifier code path is
untouched. The tie taxonomies are LOAD-BEARING analyst judgment in the defense-precedent sense —
the PR review IS the verbatim check, and re-drafting them later without the operator is the
thing the defense comment forbids. The model bump is the operator applying the standing
strongest-model policy to the current generation.

**HOW VERIFIED.**
- Suite green: ruff clean, `mypy --strict` clean on the three touched modules,
  `pytest -m "not network"` **3073 passed** — including every mirror-bound registry pin passing
  the two slugless drivers through by design (no test edits needed: the registry grew exactly the
  way its tests said it could).
- REAL registry read: `themes-exposure --driver bogus` refuses with all SIX keys in its own
  choices list — both new drivers are live at every registry-gated CLI without further wiring.
- REAL model smoke through the production path: `AnthropicLlmClient.from_config()` on the new
  default ran one tool-forced `extract` — `claude-opus-5` accepted, returned validated
  structured output (`{'ticker': 'WERN'}` from a one-line prompt), `last_usage` telemetry
  intact (534 in / 36 out). The model id is real and the tool-choice path works; nothing beyond
  the smoke was spent.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The 4.8-era groundedness benchmark has NOT been re-run on Opus 5** (vs Sonnet 4.6 it showed
  ~1/3 the untraceable figures, 0 mis-cites, ~3.5x more stable). ACCEPTED with its falsifier,
  also stated at the config knob: untraceable figures or mis-cites appearing in fresh
  extractions are the signal to re-run graph Test 0 on a sample (`graph-test0 --model` compares
  directly against the 4.8 baseline) and flip the knob back if it degrades. Until a fresh
  extraction runs, no committed artifact changes — the bump binds future runs only.
- The two drivers ship with NO exposure scan, NO basket, NO assay candidate, and NO thesis card
  yet — deliberately: the scan is an operator-triggered spend, the card's words are the
  operator's (draft cards with DRAFT markers were handed over in-session, scratchpad-only), and
  the cards cannot be declared until the thesis-card machinery (#517) merges. Nothing here
  fabricates evidence or judgment; the registry entries are the theses' STRUCTURE only.
- `ai-value-migration`'s natural first names skew megacap/FPI — the standing §5.0 readiness
  ruling (megacap MC1–MC4 / FPI1–FPI5) governs how far the funnel can carry them; the
  quality-book path is the working precedent meanwhile. Stated so the driver's first scan does
  not read as a machinery failure.
