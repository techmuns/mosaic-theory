---
id:
status: open
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# The fund has no between-print altitude, and a live position it cannot see — a panel registry and the plan to build it

**WHAT.** Two findings and a design, from reviewing an externally-drafted GOOGL monitoring plan
(`GOOGL_Monitoring_Plan_Plain_English.md`, 2026-08-17) against this repo.

**FINDING 1 — A LIVE POSITION IS INVISIBLE TO THE MACHINERY.** The accompanying IC memo records a
**$50,000 / 5.0% NAV GOOGL starter entered 2026-08-14 at ~$345**. This repo's ledger has no such
row. No verdict, no kill criteria under watch, no dossier — the same `pending_analyst` class of gap
closed for SMPL, re-occurring on a bigger position. GOOGL is a quality-book name by its own framing
(the memo's binding question — *what does today's price already assume, and is the runway longer
than that* — is the quality sleeve's page question), and it would be that book's FIRST position.

**FINDING 2 — THE MACHINERY IS STRONG AT UNDERWRITE-TIME AND ABSENT BETWEEN PRINTS.** `vinci/monitor.py`
is spread/position machinery (decision rows, closes, benchmark assignment), not indicator monitoring.
Nothing watches a thesis between earnings. SMPL's OWYN deterioration was caught by a re-assembly, not
by a monitor; its fourth kill criterion has no watcher. That gap — not GOOGL specifically — is why
this is worth building.

**THE DESIGN — PANELS ARE MODULES.** A monitor panel is a `PanelSpec` carrying `key`, `tier`,
`requires` (tags / R-file notes / feeds / uploads), `config_schema`, `render`, `cadence`, `caveat`.
A NAME declares which panels it runs and with what config, beside its sleeve. This is the shape
`DriverSpec` and the sleeve registry already use; it is not a new architecture.

Four tiers, and the middle one carries the leverage:

| tier | example | what varies per name |
|---|---|---|
| **universal** | the call · kills · multiple & price · filing watch · dilution · attribution · sources | config only |
| **cohort** | the race · capital conversion · backlog · cost of borrowing · segment margin | the metric pair, the note name, the segment |
| **theme** | data-centre policy · model pricing | nothing — attaches to the driver, not the ticker |
| **name** | dockets · patent cliff · distributor watch · freight cycle | justified individually, kept rare |

**COHORT MEANS A BUSINESS SHAPE, NOT A SECTOR LABEL.** Capital conversion is not a tech panel:
tractors commissioning is the same question as servers commissioning, so a trucking name reuses it
with a different R-file note name. Measured on the design: a second AI-infrastructure name reuses
**12 of 14** panels unchanged with **no new panel code**; a different sector still gets **7 of 7**
universal panels free.

**THE GATING RULE IS THE SAFETY PROPERTY.** `NOT IN THE SET` never renders (a payments name has no
data-centre panel, and no empty tile pretending otherwise). `IN THE SET BUT REFUSED` renders loudly
and names the requirement that failed. **These two must never look alike** — that is this repo's
absent-vs-broken class, and a panel grid is where it would recur most cheaply.

**WHY.** The external plan independently converged on this repo's three-tier portability split and
on all three of its own traps — silently stale tags, unstable R-file numbers, and an anchor that
drifts under a restatement — which are MC1, the resolve-by-name discipline, and the seal/refresh_log
pattern respectively. Convergence from an outside draft is evidence the split is real rather than
a house habit. Four corrections were applied to that plan and are recorded under WHAT IT COSTS.

**HOW VERIFIED.** Nothing is built; this record is the plan and its evidence. What was checked
against the repo rather than assumed:

- `vinci/monitor.py` read — spread/position machinery, no indicator altitude. The claim that we
  "already have monitoring" is false and was corrected before this record was written.
- `vinci/sleeves.py:41` — the quality book's vocabulary is `("BUY", "PASS")`, enforced at ledger
  write by `_require_verdict_in_sleeve`. A starter records as BUY in that book.
- `vinci/themes/schemas.py` — `DriverSpec` confirms the global-code / per-name-config shape the
  `PanelSpec` copies.
- `data/followed.json` — LLY/UBER/V quality, NFLX overshoot; no GOOGL. Ledger has no GOOGL row.
- LLY (#491) shipped **dossier-only, no scenario record and no ledger row**, which is the precedent
  path for a quality megacap and means R3 does not block recording the position.
- `AXES_BY_RECIPE` (`vinci/scenarios.py:963`) carries R1 and R2 only — **no P/E-basis recipe
  exists**, so the memo's `P/E × EPS` legs have no machine home yet.
- The design was measured, not eyeballed: the first draft ran 635 words of prose across 15 panels
  with **13 panels carrying zero visual encoding**, and its multiple panel encoded bar lengths that
  contradicted the distances they labelled. Rebuilt to 345 words, 0 panels without a visual.

**THE PLAN.**

| phase | build | depends on |
|---|---|---|
| **0** | **Record the position.** `followed.json` (quality) → CIQ package → assemble GOOGL (the LLY path) → ledger BUY row carrying the memo's kills + thesis, verdict written in the same operation | nothing |
| **1** | **MC1 — per-tag freshness assertions** + an onboarding tag-resolution pass, harnessed against two tickers from day one. Protects all 16 dossiers, not just this one | nothing |
| **2** | **`PanelSpec` + the registry**, with the gating rule pinned: not-in-set silent, in-set-refused loud | phase 1 |
| **3** | **The universal seven**, rendered on the monitor-day artifact | phase 2 |
| **4** | **The cohort five**, starting with the race (sealed anchor, weekly re-fetch, flag-never-overwrite) and capital conversion (R-file note resolved BY NAME) | phase 3 |
| **5** | **Theme panels** on the existing `ai-datacenter` driver — terms verified per source first, in writing | phase 2 |
| **6** | **R3 — a P/E-basis recipe**, so the memo's legs become a real scenario record and price gates arm | operator ruling |

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The external plan priced the forecast race as "blocked, needs vendor access". That is inverted
  for us.** The revision data is in the CIQ Estimates workbook we already ingest — but CIQ is
  manual-export-only by security rule, so "weekly" means **a weekly operator pull**. The cost is
  operator time, not licence money, and four panels go stale together when that pull is late.
- **The plan's "set up once, runs itself" conflicts with #493**, which de-sanctioned cron: the
  weekly and monthly jobs are operator-triggered. Everything here rides that same sanctioned entry
  point. Any always-on polling is a separate operator decision and is NOT assumed by this plan.
- **The plan never watched the multiple, and the memo says the multiple is the whole trade.** Bear
  EPS ($14.60) exceeds today's NTM EPS ($13.29), so the entire downside is compression from ~26x to
  22x. A multiple-distance panel is added here; it was absent from the source plan.
- **`OpenRouter` daily logging is dropped**, though the source plan kept it as a free extra. It
  fails that plan's own filter — *if this number moved a lot, would we change the size?* — and a
  feed no decision reads is the guard-that-cannot-fire class.
- **ACCEPTED RISK — a panel grid invites decoration.** Fifteen panels that each look important make
  none of them important. The face-validity guard is that every panel must state what would change
  the call; a panel that cannot answer that is decoration and should be cut, not shrunk.
- **ACCEPTED RISK — the memo is an EXTERNAL artifact on a basis this repo cannot yet represent.**
  Until R3 exists, GOOGL carries a ledger row and kill criteria but no machine-readable legs, so
  price gates and reward/risk-at-spot do not arm for it. Falsifier: if a second P/E-framed name
  arrives before R3 is built, the gap is structural rather than incidental and R3 stops being
  optional.
- **UNVERIFIED, carried as a claim and not a fact:** that ~47% of a named supplier's AI revenue
  sits with Google. It is a lead-source input and must be re-verified before any trade acts on it.
- **NOT MEASURED:** whether the cohort tiering holds beyond the six names the design was drawn
  against. The 12-of-14 reuse figure is a design claim, not an observation.
