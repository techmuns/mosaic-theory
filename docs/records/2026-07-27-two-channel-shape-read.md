---
id:
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: docs/records/2026-07-27-two-channel-shape-read.md
date-source: the filename's own date prefix, which the document's heading repeats — not inferred
---

# TWO-CHANNEL SHAPE-READ — 2026-07-27

Read-only catalog of every PR from **#194 through #222** (the highest merged PR at run time),
built because ~20 PRs ran outside the advisory thread and an unmapped codebase must not meet a
live verdict (the Aug-5 EPAM print). **No code was changed by this pass** — it writes this
catalog and STATE additions only.

Scope baseline: `5cca9c6c6` (2026-07-22, the commit before #194 merged) → `origin/main`.
**29 PRs in scope: 18 this thread · 11 other channel.**

## 1. SEAL SWEEP — the necessary part

Three independent checks, all **CLEAN**:

1. **Current state, all 7 records.** `seal.check_all` → no violations. AORT/IT/MVST/NCNO/SMPL/WERN
   sealed and intact; EPAM legitimately unsealed (`pending_analyst`).
2. **Sealed base-text immutability across the whole scope.** For every record, `base_text` at the
   baseline is **byte-identical** to `base_text` now. Growth occurred only through dated amendment
   tags: SMPL 0 → 3, IT unchanged at 2, all others 0.
3. **Ledger append-only across the whole scope.** 4 → 5 rows; **0 dropped, 0 mutated**; the single
   addition is `C-SMPL-screen2-20260706`, the authorized close row.

**No sealed surface was modified anywhere in scope outside the amendment mechanism.**

## 2. CATALOG

| PR | title | state | files | what it did | channel |
|---|---|---|---|---|---|
| #194 | EX-99.1: find the release (SGML TYPE) AND read the reason  | merged 2026-07-22 | 26 — STATE.md, data/dossiers, frontend/dossiers, tests… | EX-99.1 release finder reads SGML TYPE and the stated reason — parser hardening. | **this thread** |
| #195 | The gap card, made informative: no fabricated amounts, rea | merged 2026-07-22 | 42 — STATE.md, data/dossiers, frontend/dossiers, tests… | Gap card made informative: no fabricated amounts, real direct drivers. | **this thread** |
| #196 | Gap-card quality pass: fiscal-year period · one-off same-i | merged 2026-07-23 | 35 — STATE.md, data/dossiers, frontend/dossiers, frontend/views… | Gap-card quality pass — fiscal-year period, one-off same-item collapse, one 8-K rendered once. | other channel |
| #197 | What-broke event study: annotated daily chart + event ledg | merged 2026-07-23 | 56 — STATE.md, data/dossiers, frontend/dossiers, frontend/views… | What-broke event study — annotated daily chart + event ledger with true 1-day moves. | other channel |
| #198 | fix(extractors): SMPL audit triage — guidance anchor, LTM  | merged 2026-07-23 | 6 — STATE.md, tests, vinci/dossier | SMPL audit triage — guidance anchor, LTM mis-period, extractor fixes. | **this thread** |
| #199 | data(SMPL): step-2 re-assembly on #198 fixes — guidance +  | **closed-unmerged**  | 7 — STATE.md, data/dossiers, frontend/dossiers, scenarios | SMPL step-2 re-assembly on #198 — superseded by #203, closed unmerged. | **this thread** |
| #200 | Benchmark cap-band pin (ranker screen-time cap) + MVST re- | merged 2026-07-23 | 4 — STATE.md, tests, vinci/dossier | Benchmark cap-band pin (ranker screen-time cap) + MVST re-screen diagnosis. | other channel |
| #201 | fix(dossier): claim-#7 P/LTM basis caveat — sign-keyed on  | merged 2026-07-23 | 3 — STATE.md, tests, vinci/dossier | claim-#7 P/LTM basis caveat, sign-keyed on structured LTM GAAP EPS. | **this thread** |
| #202 | What-broke chart: one shared true-1-day-move rule (pre-win | merged 2026-07-24 | 3 — STATE.md, frontend/views, tests | What-broke chart — one shared true-1-day-move rule (pre-window detection). | other channel |
| #203 | data(SMPL): combined re-assembly — all three audit fixes i | merged 2026-07-24 | 7 — STATE.md, data/dossiers, frontend/dossiers, scenarios | SMPL combined re-assembly — all three audit fixes in the committed artifact. | **this thread** |
| #204 | docs(process): existence-check protocol + coin-time vocabu | merged 2026-07-24 | 3 — CLAUDE.md, STATE.md, docs/engineering.md | Existence-check protocol + coin-time vocabulary translation + house glossary. | **this thread** |
| #205 | feat(d3): hybrid bull/bear ordering — bull leads its crux- | merged 2026-07-24 | 5 — STATE.md, docs/engineering.md, frontend/views, tests… | D3 hybrid bull/bear ordering — bull leads its crux-linked twin (119-draw evidence). | **this thread** |
| #206 | fix(crux): remove the key_unknowns[:2] teaser — question + | merged 2026-07-24 | 4 — STATE.md, frontend/views, tests, vinci/dossier | Crux: remove the key_unknowns[:2] teaser (weather ~7% survival) — display honesty. | **this thread** |
| #207 | data: re-render all 11 md — hybrid bull/bear ordering + cr | merged 2026-07-24 | 22 — data/dossiers, frontend/dossiers | Re-render all 11 md — hybrid ordering + crux count-pointer into committed artifacts. | **this thread** |
| #208 | test(claim-7): artifact-level P/LTM caveat pin + catalyst- | merged 2026-07-24 | 2 — STATE.md, tests | Artifact-level P/LTM caveat pin + catalyst-calendar brief queued. | **this thread** |
| #209 | feat(catalyst): the catalyst calendar — dated events + wha | merged 2026-07-24 | 11 — STATE.md, frontend/views, scenarios, tests… | The catalyst calendar — dated events + what each tests, placement B (ratified). | **this thread** |
| #210 | feat(catalyst): source D — dated operating events (month-g | **closed-unmerged**  | 5 — STATE.md, scenarios, tests, vinci/dossier | Source D (month-granular dated operating events) — auto-closed on base-branch delete. | **this thread** |
| #211 | feat(catalyst): source D — dated operating events + SMPL's | merged 2026-07-24 | 5 — STATE.md, scenarios, tests, vinci/dossier | Source D + SMPL's first dated trigger — the #210 content, merged. | **this thread** |
| #212 | C3 data: SMPL input-staleness disposition — close row, sea | merged 2026-07-24 | 13 — STATE.md, data/dossiers, data/snapshots, frontend/dossiers… | SMPL input-staleness disposition — close row, sealed amendment, watch transition. | **this thread** |
| #213 | feat(freshness): assembly-freshness gate — CIQ valuation p | merged 2026-07-24 | 3 — STATE.md, tests, vinci/dossier | Assembly-freshness gate — CIQ valuation panel vs latest earnings print. | **this thread** |
| #214 | Two clocks (valuation vs trade horizon) + recipe capabilit | **closed-unmerged**  | 4 — STATE.md, scenarios, tests, vinci/scenarios.py | Two clocks (valuation vs trade horizon) + recipe capability registry — CLOSED UNBUILT. | other channel |
| #215 | docs(state): report re-design diagnosis — four proposals,  | merged 2026-07-26 | 1 — STATE.md | Report re-design diagnosis — four proposals, zero built; operator capacity parameters recorded. | other channel |
| #216 | fix(frontend): catalyst calendar reached the PDF but not t | merged 2026-07-27 | 6 — STATE.md, frontend/build.py, frontend/scenarios, frontend/views… | Catalyst calendar reached the PDF but not the web (card key drift) — datedTriggers never emitted. | other channel |
| #217 | C2 data: SMPL Q3 re-verification — base normal 15.5% → 14% | merged 2026-07-26 | 5 — STATE.md, data/dossiers, frontend/dossiers, frontend/scenarios… | SMPL Q3 re-verification — base normal 15.5%→14%, amend-at-watch. | **this thread** |
| #218 | feat(honesty): close-aware card headers + audit discharge- | merged 2026-07-27 | 12 — .gitignore, STATE.md, docs/audits, docs/ic… | Close-aware card headers + audit discharge-reading + IC memo archive + queue integrity. | **this thread** |
| #219 | refactor(dossier): content relocations — every fact under  | merged 2026-07-27 | 26 — STATE.md, data/dossiers, frontend/dossiers, frontend/views… | Dossier content relocations — every fact under the question it answers. | other channel |
| #220 | refactor(render): extract the analysis tier into helpers m | merged 2026-07-27 | 2 — STATE.md, vinci/dossier | Extract the analysis tier into helpers mirroring the md tier. | other channel |
| #221 | refactor(dossier): order the analysis tier by decision que | merged 2026-07-27 | 26 — STATE.md, data/dossiers, frontend/dossiers, frontend/views… | Order the analysis tier by decision question, not by data source. | other channel |
| #222 | feat(dossier): surface the assumption methodology + re-ord | merged 2026-07-27 | 17 — STATE.md, data/dossiers, frontend/dossiers, frontend/views… | Surface the assumption methodology + re-order the Brief. | other channel |

### Exception to the one-line rule — the OPERATOR CAPACITY PARAMETERS (#215, verbatim)

This channel had never seen these. Quoted exactly as recorded in STATE:

> **OPERATOR PARAMETERS (ratified 2026-07-24): participation 10% of ADV · build window
> 2 days · 10–20 positions · AUM $1M today, growing with results.** So a position is **$50–100k**,
> and the capacity ceiling (ADV × 10% × 2d) clears it by **14× on the THINNEST name and 486× on
> the deepest** (MVST $6.9M ADV → $1.38M ceiling; IT $243M ADV → $48.6M). A $100k position builds
> in **0.004–0.145 days** cohort-wide. A capacity block would print "0.0 days" for every name —
> the SAME failure mode as the horizon ratio: a second constant that discriminates nothing.
> **TRIGGER TO REVISIT — derived from the operator's own parameters, not a guess:** capacity binds
> when `AUM > N × ADV × 0.2`, i.e. **~$14M AUM** (MVST at 10 positions), then AORT $38M, SMPL/VRRM
> ~$71–73M, and only ~$400M+ for IT/EPAM. At 20 positions every threshold doubles ($28M / $77M /
> ~$142M). **So: build the capacity block when AUM approaches ~$14M, or sooner if a genuinely
> illiquid candidate (ADV < ~$5M) reaches the finalist stage — whichever comes first.** The split
> to preserve when it IS built: **capacity is a FACT** (ADV × participation × days — mechanical,
> fence-safe); **a proposed WEIGHT is a JUDGEMENT** (conviction × correlation × theme slot) and
> would be the machine concluding — expect the fences to apply, and treat it as an operator ruling
> rather than a build. At 10–20 positions with a two-person team, sizing is a conversation.

**What they now govern:** position sizing is **not built and must not be** at this AUM; the
capacity block has a numeric build trigger (~$14M AUM, or any finalist with ADV < ~$5M); and when
built, the fact/judgement split above is binding.

## 3. CONVENTIONS DELTA — the advisory catch-up sheet

Rules added in scope that this channel had not recorded, quoted verbatim with source:

- **XBRL impairment-tag overlap (#196-era pull, STATE):** *"XBRL IMPAIRMENT-TAG-OVERLAP RULE — one
  tag family per adjustment, never summed across families."* Summing `GoodwillImpairmentLoss` +
  `GoodwillAndIntangibleAssetImpairment` + `ImpairmentOfIntangibleAssetsExcludingGoodwill` +
  `AssetImpairmentCharges` double-counts because the middle tag is a SUPERSET of the two around
  it (KHC summed to $27.9B). **Directly governs the SMPL clean-margin work in #217.**
- **Benchmark flip on re-assembly (#200):** *"KNOWN-ISSUE (recorded 2026-07-23, INVARIANT RULE) —
  re-assembly can flip a cap-band benchmark."* Re-assembling IT flipped MDY→IWM, cascading to
  `stock_performance`, the idio comparison and the What-broke chart. Mitigation: a single-field
  surgical patch when only a derived field needs updating.
- **Basis labels (STATE §, pre-scope but enforced in scope):** *"Rule adopted: every margin cell
  carries its basis label; `bear_basis` gains `margin_basis`."* Now machine-enforced
  (`margin_basis` validator + `_require_bear_basis`).
- **Card-key contract (#216):** every `card.verdict.<key>` the JS reads must be a key `build.py`
  emits, and no snake_case survives on the card side. Scoped to the verdict block; the `ledger`
  sibling is explicitly excluded.
- **Position sizing (#215):** *"POSITION SIZING DOES NOT BIND AT THIS AUM — do not build it yet."*
- **PR #214 closed unbuilt:** the two-clocks/recipe-registry proposal was closed; the conceptual
  finding ("how long we HOLD vs how long the valuation takes to resolve") was kept.

## 4. QUEUE RECONCILIATION

Queue at the 2026-07-23 read-only check: **50 numbered items** → now **66**. **Nothing was pruned
without disposition — zero items vanished.** The queue GREW; every named item is located below.

| item | disposition |
|---|---|
| IR-document ingestion | LIVE — queue #30 (IR-DOCUMENT INGESTION TIER) |
| Unit-boundary audit | LIVE — queue #20, priority raised (operator's FIFTH instance) |
| Perimeter watcher | LIVE — queue #31 (reads footnotes AND releases, not 8-K only) |
| Entity-structure gate | LIVE — queue #32 (NCI / multi-class / Up-C before per-share math) |
| Form-4 classifier | LIVE — recorded as an unbuilt landmine (CIQ transaction-type mapping) |
| Staleness banners | LIVE — queue #34 |
| Interim-FCF engine option | LIVE — queue #36 (R2 sensitivity, printed per record) |
| **Basis-truthfulness check** | **DONE — graduated to an enforced rule**, not a queue item: `margin_basis` validator + `_require_bear_basis` in `vinci/scenarios.py` |
| Band span-stamps | LIVE — queue #5 (NCNO + AORT, one byte-preserving pass) |
| Render-completeness check | LIVE — queue #27 (from #185's dropped survival detail) |
| Export snapshots | LIVE — queue #38 (dated + sha-stamped vendor-export snapshots) |
| CIQ escalations ×2 | LIVE — #1 the A7 vendor-FCF gap ($193.8M); #2 VITL TEV/LTM EBITDA (queue #16) |
| Review pack format | LIVE — queue #40 (analogue sections rebuild-or-remove under the pack format) |
| Mirror-sync CI | LIVE — queue #24 |
| **tests-write-to-tmp** | **⚠ FLAGGED — no STATE record in this window at all.** Absent from the 2026-07-23 queue too, so it did not vanish *during* the scope; it has never been a numbered item here. De-facto adopted in practice (23 test files use `tmp_path`), but the convention is unwritten. |
| STATE split | LIVE — queue #22 (§5 build records → a fossils/decisions file) |

## 5. CHANNEL ATTRIBUTION SUMMARY

`Co-Authored-By` is a reliable channel signal across the whole scope: **Claude Fable 5 = this
advisory thread (18 PRs)**, **Claude Opus 5 = the other channel (11 PRs)**. No PR in
scope was unattributable.

The other channel owns the render/report surface (#196, #197, #202, #219–#222 — the dossier
re-ordering line) and the diagnosis work (#214, #215); this thread owns the extractor/record/
governance line. **#216 is the one true cross-channel collision**: it fixed a web-render bug in the
catalyst calendar this thread had built in #209/#211, four days later, found by looking at the
rendered page.
