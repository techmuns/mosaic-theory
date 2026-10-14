---
id:
status: shipped
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — thesis coverage and identity: one technology per thesis, one thesis per story, the source's own risks accounted for

**WHAT.** The review of the analytical safeguards left: one lost proposition (part 4), fuel cells
merged into gas generation on one key (0 of 17 supporting claims shared), the low-cost US gas
argument on no card, two risks the first reading put on no card, seven same-article siblings, and
four page alerts. One approved paid call (the part-4 re-ask, $0.5278); everything else at $0 from
saved answers. No other model call, no card-review call.

- **P0 · the part-4 re-ask** (`reask-part --doc D-c6f361d4d57a6196 --part 4 --max-cost 1.20`, run
  `R-20261012T073736Z-ingest`): ONE call, **$0.5278**; the chain reproduced from the cache
  first (the command refuses otherwise); all 41 cached answer files byte-unchanged (sha256), one
  added beside the paid original (`<key>.reask-1.json`).
  Recovered 15 claims, 4 mentions, 3 additions to hypotheses, 25 figure and 26 paragraph reviews
  — and **no new hypothesis**: the regulatory-reform proposition ("…large-load grid connection
  creates electric wires and generation investment opportunity") is not proposed again, so it has
  no thesis and no RESEARCH NOW / WATCH / SKIP. It is now listed as DROPPED with that reason
  (`completeness.py`: a proposition the paid answer named and its re-ask did not propose again
  stays accounted for). Its evidence was attached elsewhere: interconnection queues and wait times
  → the transformer thesis; 50GW / MISO 43% / 25 cancellations and the FERC 90-day plan → gas
  generation; "before 2030" and specialist shortages → skilled labour. The nearest held thesis,
  "Uneven U.S. regional power regulation creates selective wires and generation investment
  opportunity", is **SKIP-2** (no fundamental transmission step) — the justified class.
- **P0 · one technology per thesis** (`taxonomy.toml`, `engine.py`). On-site generation is three
  taxonomy products — `gas_turbines`, `reciprocating_engines`, `fuel_cells` — under a generic
  `onsite_generation` that covers them; mechanisms carry a `family` (volume, price_cost,
  competition, valuation, policy, market_structure). A thesis's PRODUCT is the one its own
  statement names (exactly one), else the one at least `PRODUCT_MIN_SHARE` (a fifth) of its cited
  claims name. Two hypotheses on one key with NO shared supporting claim whose products differ are
  SEPARATE theses (`|prod:<product>` on the second's key; `PRODUCT_SPLIT`), and a market risk the
  model tied to the first that names only the second's product follows it. An existing thesis
  found by key is validated the same way (a different product and no shared sentence → a separate
  thesis). The card's registry link names the product difference. No product is special-cased.
- **P0 · low-cost US natural gas.** In a registry holding the first reading, the cleaned re-read
  RE-VERIFIES the existing card (`engine._reverify`: 4 of its 4 cited sentences re-stated, no new
  evidence) and re-assesses it under today's rules: **WATCH → SKIP-3** (longer-term only — its one
  dated element is the LNG glut "towards the end of this decade"). The nine-section card is in the
  worked outputs. In a FRESH registry the cleaned run's model proposed no hypothesis for page 37,
  and the engine never writes a thesis without one (assemble, never conclude) — the four facts
  stay a coverage alert; a targeted re-ask of that paragraph would need approval.
- **P1 · risks the source states** (`coverage.scan_source_risks`, `pipeline._place_source_risks`).
  Every sentence of a readable argument paragraph that states a DOWNSIDE in the source's own
  construction ("risks remaining", "might put downward pressure", "did not materialize",
  "execution risk remains", "pose uncertainty" — never the bare word "risk", and never a risk said
  to be absent: "little risk of oversupply") is checked against what already carries it: a
  proposed risk, a counter-claim or a card's ALTERNATIVE MECHANISM restating it (≥ half the
  shorter text's words, ≥ 4 shared), a cited evidence quote, or a proposed risk drawn from its
  paragraph. One nothing carries goes into 07 of ONLY the theses whose evidence shares its
  paragraph — the verbatim sentence, cited to itself, labelled SOURCE OPINION — and is flagged
  there (`SOURCE_RISK_OMITTED`) and as a coverage alert; with no such thesis, or cut by a page
  break, it is alerted and placed nowhere.
- **P1 · one thesis per story across versions** (`engine._earlier_match`, `_identity_differences`,
  `_reverify`). A later version's hypothesis that holds ≥ half its sentences on a thesis an
  earlier version of the SAME article created is that thesis — updated, its id kept
  (`SAME_ARTICLE_MATCH`) — when direction, geography, mechanism FAMILY, segment, product and time
  horizon agree; a different value-chain NODE label is stated, never blocking. Any other
  difference: created, `REVIEW_NEEDED`, held from RESEARCH NOW ("identity under review"), flagged
  `SAME_ARTICLE_SIBLING`. An earlier thesis whose sentences the new version re-states (≥ half)
  but no hypothesis took is re-verified and re-assessed (a version only when the assessment
  changes). Sentence overlap alone never merges.
- **Two re-read defects found and fixed on the way**: the same sentence read twice counted twice
  as material evidence (the gas thesis read 4 → 8 with nothing new; `F2` now counts a re-read
  sentence once), and "EV sales reached ~75K units" scaled two ways (75,000 units / 75 thousand)
  made a duplicate row — the figure AS WRITTEN now decides (`verify.same_sentence_reread`).

**WHY.** The paid acceptance run's review: a fuel-cell share story inside a gas-turbine thesis,
a structural gas-price advantage on no card, risks the source states left off the cards that
cite its paragraphs, and every re-read of one article spawning a second thesis per relabelled
story — each turns one source into apparently independent research opportunities.

**HOW VERIFIED.** *Real, $0 except the one approved call* —
`docs/theme_intelligence/coverage-identity-2026-10-12/`:
1. The re-ask: one request (part 4), $0.5278; paid-call ledger 41 → 42 calls, $11.7015 →
   $12.2294 (registry `glyph-paid`; the $0.0001 gap is rounding); cache files 41 → 42, the 41
   byte-unchanged.
2. Gridlock (cleaned) replayed from the paid answers + the re-ask, fresh registry, cache only:
   **before** (previous code, `glyph-reask-replay`) 14 theses, WATCH 3 / SKIP 11, fuel cells
   MERGED into gas generation (0 shared / 17 own); **after** (`identity-replay`,
   `R-20261012T083630Z-ingest`) **15 theses, WATCH 4 / SKIP 11, RESEARCH NOW 0** — fuel cells a
   separate thesis (`…|US|seg:onsite_generation|prod:fuel_cells`, WATCH: no verified dislocation or
   catalyst — not RESEARCH NOW), gas generation unchanged, the scandium/SOFC risk on the fuel-cell
   card (it had been on the gas card). Open items 5 + 4 both runs.
3. Risk scan, final run: **18 risk sentences in 287 argument paragraphs — 12 carried, 4 placed,
   2 alerted** (cut by a page break). Placed (SOURCE OPINION, none withheld): three timeline /
   regulatory-uncertainty sentences (pp. 40, 41, 45) on the regional-regulation thesis, "execution
   risk remains" (p. 52) on the China buildout and energy-infrastructure theses. **The two named
   risks: in THIS reading the model wrote both as alternative mechanisms on the right cards** —
   "bragawatts" on European grid, raw-material inflation on ESS returns on the storage card — so
   they are carried, not duplicated. The flag path on both was shown on the same answers before
   alternatives counted as carried (`R-20261012T081536Z-ingest`): each was placed on exactly that
   card. On other publishers' stored text (9 articles, 798 paragraph sentences — Nomura,
   TrendForce, SemiAnalysis, J.P. Morgan) the cue fired 7 times, each a genuine risk statement.
4. Re-read of the real PDF into a copy of the baseline (`identity-reread`,
   `R-20261012T083646Z-ingest`, the labelled harness: alignment hints off): of the first reading's
   16 Gridlock theses **7 MATCHED and updated** (transformer 61 of 68 sentences; powered land,
   China, power scarcity, midstream, labour, energy security — five of them only a node label
   apart), 7 updated by their unchanged key, **2 RE-VERIFIED** (low-cost gas WATCH → SKIP-3; the
   first fuel-cell thesis, WATCH kept), 1 untouched; **1 held for review** (the cleaned fuel-cell
   hypothesis: 14 of 17 sentences on the first fuel-cell thesis, but a different mechanism family —
   share shift vs demand volume); 1 created (below). **0 duplicate rows, 0 independent
   confirmations, 0 paid calls.** Before this pass: 7 siblings, 0 matches.
5. Alert triage (final fresh run; facts in `6-…txt`):

   | Alert | Class | Why |
   |---|---|---|
   | page 7 — 6 facts | **background — its headline figures represented** | US data-centre capacity sizing (>50 GW, 24% CAGR, MISO 43%, AI 4.3 GW → ~110 GW): the demand premise every power thesis shares, no mechanism of its own. Its two headline figures are on the gas-generation card from page 14's restatement (written "more than 50GW", "~43%" there — "50-GW+", "43%" here, so the same-figure check does not pair them); 2 of the 6 are a chart's table labels / a caption fragment (156 vector objects on the page) |
   | page 14 | **represented** | no longer an alert: its 3 verified facts (more than 50GW, MISO ~43%, 25 cancellations) are on the gas-generation card, attached by the re-ask |
   | page 16 — 600 GW vs 183 GW | **unresolved — relevant to an existing thesis** | power scarcity / speed-to-power; the power-scarcity thesis holds no verified material evidence (SKIP-1) and this is not attached to it — a reviewer's call, never attached automatically |
   | page 16 — "1GW or more dropped off" | **risk / counter-evidence** | the NERC load-volatility risk on the cards carries the argument; the figure itself is not cited by it |
   | page 37 — 4 facts | **distinct thesis** | the low-cost US gas mechanism: its own card where the first reading made one (re-verified, SKIP-3); in a fresh registry no model proposal → alert stays (above) |

6. Tests: `tests/test_theme_intelligence_safeguards.py` +7 (8 new, 1 replaced: product split with real-shape
   evidence, product follows a risk, statement-first and minimum-share product, registry link
   names the product, the risk scan placing / not flagging / alerting, a whole sentence in an
   alert, a placed line never withheld), `test_theme_intelligence_glyph_quarantine.py` +4 (6 cases: a re-read
   relabelling the same claim updates the same thesis, a different direction or mechanism family
   is held for review, a re-read sentence counted once, under half re-stated is carried not
   re-verified; one extended: an orphaned thesis re-verified), `test_theme_intelligence_long_articles.py`
   +1 (a re-ask that proposes again lists nothing lost; one existing test updated for the new
   accounting). **32 mutants of this pass's guards, all killed** (3 survived the first round and
   were pinned; the previous pass's carry rule survived once re-verification made it redundant in
   its test and was re-pinned); the previous pass's 22 applicable mutants re-run, all killed. Full
   offline suite on the final tree: **4,935 passed, 511 skipped, 0 failed**; ruff and
   `mypy --strict vinci` clean.

**BOUNDARY.** Article `A-82a8a9210bae` (Citi, 60 pages, as of 2026-10-11). Paid answers: registry
`glyph-paid` (`R-20261012T050655Z-ingest`, $11.70) + the re-ask (`R-20261012T073736Z-ingest`,
$0.5278). Fresh replay `identity-replay` / `R-20261012T083630Z-ingest`; re-read `identity-reread`
(copy of `final-a`) / `R-20261012T083646Z-ingest`; both final code, cache only, no card-review
pass (`--no-review` — that pass is paid; holds it would add affect RESEARCH NOW only, of which
there is none). Risk sentences = sentences of the completeness ledger's argument paragraphs
matching `RISK_CUE`, not `RISK_NEGATED`, ≥ 8 words. Theses counted = those the Gridlock article
contributed to. **New API spend this pass: $0.5278** (the approved call; nothing else).

**WHAT IT COSTS / WHAT IS ACCEPTED / STILL OPEN.**
- *A placed source risk is a new card line*: in production that card's pass-2 review re-runs (the
  normal cost of a changed card); here it ran with `--no-review`.
- *The low-cost gas mechanism has no card in a fresh registry* — a model proposal is required;
  re-asking the page-37 paragraph would cost about as much as the part-4 re-ask. Not run.
- *The cleaned fuel-cell hypothesis is held for review* beside the first fuel-cell thesis (14 of 17
  sentences shared, mechanism family different) — the human decides whether they are one thesis.
- *An evidence-less proposition cannot be identity-checked*: "Citi Wealth recommends selective AI
  capex / supply-chain exposure" (SKIP-1, no verified material evidence) is created beside the
  first reading's like-titled thesis (also SKIP-1) — nothing to compare; it never reaches an
  action. Falsifier: such a pair with evidence.
- *The transformer thesis is keyed segment `onsite_generation`* (it was in the paid run too) — a
  segment-classification question, not changed here.
- *Face-validity constants*: `RISK_CUE` constructions, `RISK_SHARED_MIN` 4, `PRODUCT_MIN_SHARE`
  0.2, `SIBLING_SHARE` 0.5. Falsifiers: a downside sentence a reviewer finds the cue missed, a
  model paraphrase sharing < 4 words, a thesis whose subject product is named in under a fifth of
  its claims, a relabelled story re-stating under half its sentences.
- *The first reading cannot be replayed at $0* — its extraction prompt no longer reproduces under
  today's reader (a cache miss, nothing sent); its "on no card" risks are shown through the flag
  path on the cleaned reading instead.
