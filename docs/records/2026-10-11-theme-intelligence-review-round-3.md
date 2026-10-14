---
id:
status: shipped
date: 2026-10-11
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence, review round 3 — a challenge needs the same claim; segments keep memory evidence apart; a narrow near-term-inflection route to RESEARCH NOW; verification status apart from execution; three dates

**WHAT.** The round-3 review of PR #703 kept the architecture and named five blocking defects. All
in `vinci/theme_intelligence/` (research attention only, AST-pinned off the decision path):

- **FIX 1 — no false contradictions.** A COMPETING challenge (evidence filed as CONTRADICTS, the
  incumbent re-versioned WEAKER) now needs a DIRECT contradiction: the same node, mechanism and
  segment, overlapping geography (`geographies_overlap`: Global contains every region, APAC its
  members) and overlapping stated timeframes (`evidence_windows`), predicted the opposite way.
  Any difference is named on the link (`claim_differences`) and makes it RELATED — no CONTRADICTS
  evidence, no new version, no downgrade. Two unclassified (`other`) theses are never compared by
  key.
- **FIX 2 — no over-broad confirmation.** The SEGMENT is part of thesis identity
  (`identity_key`; `taxonomy.toml` `[[segment]]`: DRAM / HBM and NAND / SSD on memory;
  grid-connected utilities and behind-the-meter / on-site generation on power), read from the
  verbatim quotes of verified evidence, never from the model's wording; an unsegmented key equals
  the old one, so existing ids are kept. Evidence roles (`EvidenceRole`): DIRECT_CONFIRMATION and
  REPEATED_SOURCE reach a thesis's own history (card tags "Direct confirmation — new evidence /
  independent source", "Repeated source — attribution only", "Contradiction — evidence against
  this thesis"); ADJACENT_SUPPORT (same direction, not the same claim — including the same claim
  at an overlapping but different geography) and RELATED (opposite direction, not the same claim)
  are registry links only — context, never a strengthening or a weakening.
- **FIX 3 — a narrow RESEARCH NOW route, F12 `fundamental_inflection`.** Without a dislocation or
  dated catalyst a thesis may still be RESEARCH NOW when ALL hold: a verified claim whose VERBATIM
  quote states a CHANGE in a FUNDAMENTAL (a price, revenue, margin, demand, supply, shipments …;
  never a market reaction, never a technical metric — `_fundamental_change`) inside the next 2-4
  quarters or measured in the last one; CREDIBLE — the publisher's own data in an industry data
  report (article class from the CHANNEL, never the model) or corroborated by a MEASURED change in
  a fundamental among the thesis's evidence, never a forecast alone; the source itself states the
  fundamental step; and a source-named exposure, composed into the research question "do current
  earnings estimates and market expectations for X already reflect Y in Z?" — printed in the
  dashboard's first view. Every other RESEARCH NOW condition still applies.
- **FIX 4 — QA honesty.** `research_verification`: FULLY_VERIFIED / VERIFIED_WITHIN_PREVIEW /
  INCOMPLETE / NOTHING_ANALYSED over the ledgers the run recorded, shown APART from the run's
  execution status on the dashboard header and a tile, in `dashboard.md` / `.json`, the manifest,
  the CLI and the QA summary, with every open item listed with its cause (`open_cause`:
  `verification_failed`, `capture_not_verified`, `account_names_no_record`, `no_account`,
  `pass_not_run`). The % unit rule binds the number the value READS ("22 (52%)" read as 22 texts is
  a count). A pass-1b account naming VERIFIED claims closes its paragraph. New QA check: no
  unverified claim is linked to a thesis.
- **FIX 4, found by that check on the real corpus.** The card reviewer had suggested two claims
  whose NUMBER checks failed ("None" read as 0, "A hike" as 1 — Nomura, weekly sample) as anchors
  for a partly supported bottom line; re-anchoring accepted them, the line was not withheld, and
  the claims were linked as context — unverified material reaching the hold test. Re-anchoring now
  accepts only claims verified on span AND number, whoever proposes them.
- **FIX 5 — three dates.** The card header and dashboard rows carry the publisher's date (latest
  contributing source), the registry's ACTUAL first ingestion (wall clock, UTC) and the analysis
  as-of; when the as-of precedes ingestion the line says "a historical replay — a simulated date,
  not a detection". The old "first detected by the registry <as-of>" label is gone.

**WHY.** The round-2 build challenged SemiAnalysis's behind-the-meter thesis with J.P. Morgan's
utilities thesis because they shared a NODE and opposite directions — a fall in utility share
prices does not contradict rising demand for on-site generation. It merged TrendForce's
enterprise-SSD / NAND pricing evidence into SemiAnalysis's sparse-attention DRAM / HBM thesis as an
"independent confirmation". RESEARCH NOW demanded a dislocation or dated catalyst even for a
credible near-term change in fundamentals. A completed scan with open gaps read as verified, and a
simulated as-of was labelled "first detected". Round 2 recorded the node rule as operator decision
(8)(b); this review decided it.

**HOW VERIFIED.** Real runs on the final engine, one FRESH registry per case (suffix 16, run ids
`R-20261010T1915…Z`), model answers content-cached. Worked output and QA reports:
`docs/theme_intelligence/`.

- *SemiAnalysis + J.P. Morgan (no false weakening):* "Grid friction pushes datacenters
  behind-the-meter" (`power_grid` | `demand_volume_shift` | positive | segment
  `onsite_generation`) stays v1, WATCH, no CONTRADICTS link, no CHALLENGED event; J.P. Morgan's
  utilities thesis (`policy_regulation` | negative | `grid_utilities`) is linked RELATED — "a
  different mechanism …; a different segment (Behind-the-meter / on-site generation vs
  Grid-connected utilities); no overlapping timeframe". 0 CHALLENGED events in the registry. QA
  19/20 (SemiAnalysis preview: one paragraph `no_account`) and 20/20.
- *SemiAnalysis + TrendForce (direct vs adjacent):* "Sparse attention does not reduce overall AI
  memory capacity demand" (segment `dram_hbm`) stays v1 with only SemiAnalysis's evidence; both
  TrendForce theses (pricing, `dram_hbm+nand_ssd`; enterprise SSD, `nand_ssd`) are separate,
  linked SIBLING / ADJACENT_SUPPORT ("overlapping but different segments", "a different segment").
  Direct confirmation stays pinned on the same-identity case
  (`test_independent_evidence_next_week_versions_the_same_thesis`). QA 19/20 (SemiAnalysis preview:
  "GLM's 5.2 / 5.3" open, `capture_not_verified`) and 20/20.
- *TrendForce 4Q26 alone (the inflection route):* both theses RESEARCH NOW by F12 — the price
  tracker's own forecasts (conventional DRAM +10–15% and NAND +15–20% QoQ contract prices in 4Q26;
  enterprise-SSD bit demand +80% YoY in 2026), the pricing step stated by the source, the question
  composed from the claims: "do current earnings estimates and market expectations for
  Semiconductors already reflect NAND Flash contract price change of 15–20% QoQ in 4Q26?". The
  SemiAnalysis memory thesis does NOT qualify (F12 absent): its changing figure — "the share of
  prompt tokens reused from GPU memory falls from 90.3% to 54.8%" — is a workload metric, which
  qualified before `_FUNDAMENTAL` was added. QA 20/20, FULLY_VERIFIED.
- *Software Shock (2026-02-09):* exactly three theses, all WATCH; Alphabet = GOOGL / GOOG
  VERIFIED common equity point-in-time. QA 20/20, FULLY_VERIFIED (34 figures, 12 paragraphs).
- *Calm Index (2026-10-10):* the utilities thesis and the dispersion market-regime record, both
  RESEARCH NOW. The utilities thesis id is now `TH-30F6348B8B` (was `TH-98FD8D046C`): its identity
  carries the `grid_utilities` segment. QA 20/20, FULLY_VERIFIED (19 figures, 10 paragraphs).
- *Weekly sample, reprocessed:* scan execution SUCCEEDED (6 of 8 channels; Morgan Stanley and
  Goldman Sachs BLOCKED, never bypassed), research verification INCOMPLETE — 0 of 228 figures and
  1 of 170 paragraphs open. Round 2's three open figures ("42", "22", "52%") are captured (the unit
  rule); paragraph b002 is closed by pass 1b's account naming verified claims c1–c3; b008 stays
  OPEN, `account_names_no_record` ("carried by first-pass market risk on silent limit changes" —
  a risk is not a checkable record). 10 theses, Research Now / Watch / Skip 2 / 7 / 1, 0
  challenges: round 2's "SemiAnalysis thesis challenged twice" ("Anthropic subscriptions outvalue
  OpenAI's" vs "China's frontier labs race ahead …") is RELATED. QA 20/21 — the open paragraph.
- *Pins:* new `test_theme_intelligence_evidence_roles.py` (16 items: the real SemiAnalysis / J.P.
  Morgan and SemiAnalysis / TrendForce pairs replayed from FROZEN fixtures, the real TrendForce
  route, per-dimension contradiction pins, the inflection refusals) and
  `test_theme_intelligence_verification_status.py` (15 items); the round-2 competing-thesis pins
  re-pinned to a direct contradiction (positive) and a RELATED pair (negative). Four new fixtures
  (`semianalysis_moratoriums`, `jpm_calm_index_after_semianalysis`, `semianalysis_glm53`,
  `trendforce_4q26_after_semianalysis`): the second of each pair is the extraction the run made
  WITH the first article's theses in the registry — located by recomputing that exact request; a
  multi-part completeness pass is frozen as the pipeline merged it.
- *Mutation:* 27 of 27 guards killed (relation rule, geography, timeframe, unclassified, segment,
  evidence roles, the overlapping-geography link, the fundamental / corroboration / channel /
  economics / "contract" conditions of F12 and its first-view line, the unit rule, claim-named
  accounts, open causes, the verification status and header, the unverified-link QA check and the
  re-anchor pool, the three-date fields and replay flags, the change tag). One mutant first
  SURVIVED — the card's detection date set from the as-of — because the calm pin's as-of equals
  the UTC run date; the pin moved to the replay test (as-of 2026-03-02) and it is killed.
- *Gate on the final code (before the docs commit):* `ruff check .` clean; `mypy --strict vinci`
  clean (176 files); `pytest -m "not network"` 4,611 passed, 507 skipped, 37 deselected, 0 failed.

**BOUNDARY.** Real runs: 2026-10-10 19:15 UTC, registries `*-16`, the engine of code commit
`0b75b811` (its dashboard first-view "why" line, render-only, landed after the runs; every worked
output file was re-rendered from `0b75b811`); model `claude-opus-4-8`; prompts
`ti-extract-6` / `ti-complete-1` / `ti-review-4` (unchanged — segments are never sent to the
model, so every cached answer stays valid); each article replayed AS OF the date shown. Figures /
paragraphs: the article BODY's stated figures and argument paragraphs of ≥ 12 words, as in round
2; "open" = neither captured by a verified claim nor accounted for (immaterial with a reason, or an
account naming a verified claim or hypothesis). Weekly: window 2026-10-01 → 2026-10-10, as-of
2026-10-10, eight configured channels. Costs at list price; "billed calls" = files the shared
content-keyed model cache gained since the first round-3 run (2026-10-10 18:56 UTC).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Model spend of this round: **$2.28 across 26 billed calls** (24 card reviews, 1 extraction,
  1 completeness pass; 250,211 input / 41,353 output tokens) plus at most two calls killed in
  flight when I stopped runs to change code (cost unknown, ≲ $0.3).
- "A timeframe only one of them states" is a difference: a contradiction that cannot be shown to
  concern the same window is RELATED, never a weakening. Falsifier: an analyst finds same-claim
  opposite reads left RELATED for that reason alone → read an undated claim's window from its
  article date.
- F12 has no magnitude threshold: a source-stated, credible change in a fundamental qualifies
  whatever its size; the size is printed in the question for the analyst. Its continuing-trend
  reading is deliberate — TrendForce says DRAM increases MODERATE in 4Q26, and whether estimates
  already reflect +10–15% is exactly the question. Falsifier: RESEARCH NOW rows from F12 are
  repeatedly dismissed as immaterial → a face-validity threshold, never one tuned on outcomes.
- Industry-data-report status is configuration (TrendForce's channel): a data report from an
  unconfigured host is commentary to this rule. Falsifier: a credible tracker reaches only WATCH
  → configure its channel.
- ADJACENT_SUPPORT is a structural label, not a judgement that the evidence helps: a rates thesis
  and a dispersion record share `macro_market` and are linked so.
- `pool` in re-anchoring now excludes number-failed claims, so a line whose only support failed a
  (possibly false) number check is withheld; false word-number failures ("A hike" → 1) stay
  visible as NUMBER_NOT_IN_SPAN rather than being guessed right.
- Operator decision (8)(b) of STATE §5.0 row 32 is CLOSED by this review: a challenger needs the
  same claim. (8)(a) — whether a qualitative "swept up in the sell-off" observation may count as a
  dislocation — stays open; F12 does not change it (no figure, no fundamental).
