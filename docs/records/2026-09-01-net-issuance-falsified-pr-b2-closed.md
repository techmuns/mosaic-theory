---
id:
status: falsified
date: 2026-09-01
prs: []
supersedes:
superseded-by:
---

# Net issuance does not discriminate in this pool, and PR-B2 was already built

**Run 2026-08-12; recorded 2026-09-01.** Both findings sat unmerged on
`feat/dossier-evidence-line`, which became unmergeable after the 2026-08-25 STATE.md restructure.
**They are recorded now because main is currently stale in a misleading direction:**
`docs/records/2026-08-11-experiment-record-2026-08-11-price-state-falsifi.md` still lists net
issuance (Pontiff-Woodgate) as strong evidence worth building at queue level, and **PR-B2 as
approved next work**. A session reading main today would go build PR-B2. Both were tested and
closed three weeks ago.

## WHAT — net issuance is not a discriminator here

PR-B1 shipped net share issuance onto the queue on PUBLISHED evidence (Pontiff-Woodgate). Published
evidence is about a broad cross-section; **this pool is deep-drawdown small/mid caps**, and Phase A
had already shown transfer cannot be assumed. Tested before building more of it.

**Pre-registered:** issuance predicts LOWER forward sector-relative return ⇒ expected rho NEGATIVE.
Bar: ≥99th shuffle percentile AND same sign across four disjoint phase blocks.

| horizon | rho | t | shuffle pct | phase blocks |
|---:|---:|---:|---:|---|
| 30d | −0.0228 | −1.3 | 98% | MIXED |
| 60d | −0.0219 | −1.3 | 95% | MIXED |
| 120d | −0.0109 | −0.8 | 62% | MIXED |
| 180d | −0.0057 | −0.5 | 34% | MIXED |

**FAILS THE BAR AT EVERY HORIZON.** The sign is right — negative, as the literature predicts — but
no horizon clears the shuffle bar and every one is MIXED across phases.

**THE TERCILE MEANS LOOK LIKE THE OPPOSITE FINDING, AND THEY ARE A TAIL.** By mean, issuers beat
buybacks and the gap widens with horizon (+0.43 → +4.99 at 180d). The mean/median test settles it
at 180d:

| tercile | mean | median | up% | p90 | p10 |
|---|---:|---:|---:|---:|---:|
| T1 buyback | −8.94 | **−11.64** | 33 | +27.7 | −48.5 |
| T3 issuer | −3.95 | **−12.56** | 36 | +51.3 | −57.1 |

The typical issuer is **worse** (median −12.56 vs −11.64) and the up-rate is flat. The mean gap is
entirely a fatter tail in BOTH directions. Same shape as the turned-state cells: a mean carried by
lottery tickets over a flat median.

**THE NUMBER THAT MATTERS MOST IS IN NEITHER READING: EVERY TERCILE IS DEEPLY NEGATIVE.** At 180d
the BEST bucket is −3.95 against its own sector with a median of −12.56. The pool's problem is not
which slice you pick — **the whole pool bleeds against its own sector regardless of issuance.**
(That thread is picked up by `docs/records/2026-09-01-screen-gate-audit-g1-g2-g3.md`.)

## HOW VERIFIED

36 backdated months, 8.0k name-months, ex-sunk, outcome = forward return minus OWN SECTOR.
**Point-in-time on `ConceptPoint.filed`**: 29,161 observations had at least one not-yet-filed share
figure excluded. Uses `share_count_change` — the same helper the queue and the dilution demote
consume — so the test measures what actually ships. **1,209/1,209 tickers resolved, 0 EDGAR
failures.**

## CONSEQUENCES

1. The issuance leg stays **DISPLAY-ONLY and fenced**. This is the evidence that it must never be
   promoted; the AST fence added in PR-B1 is now **load-bearing rather than precautionary**.
2. It remains honest context for a human reading one name — a real, source-bound fact — but it is
   **not a discriminator and must not be described as one**.
3. **It removes the main argument for spending a lengthened weekly cron on insiders and short
   interest**: the same transfer assumption underwrites both, and it just failed for the one leg
   that was free to test.

## WHAT — PR-B2 is closed as unnecessary, not deferred

The approved plan's PR-B2: *"dossier 'What broke' section gains the same strip — one source-bound
`_fact("Evidence", …)` line in `_drawdown_idio_lines` + the JS twin in `drawdownIdio`."*

**Checked before building; the premise does not hold.** Every leg of the evidence strip is already
a first-class dossier fact, already rendered, already source-bound, in BOTH renderers:

| leg | Python | JS twin |
|---|---|---|
| Insider activity (Form 4) | `render.py:1650` | `views/shared/dossier.js:3901` |
| Short interest (FINRA) | `render.py:1654` | `views/shared/dossier.js:3903` |
| Share-count trend | `render.py:3535` | `views/shared/dossier.js:2730` |
| Own-history range position | `render.py:3792` (+ `:3259`) | `views/shared/dossier.js:3058` (+ `:1979`) |

*(Line numbers RE-CHECKED against main at recording time, 2026-09-01. The JS twin lives at `frontend/views/shared/dossier.js` — an earlier draft of this table cited a nonexistent `frontend/dossier.js` and 2026-08-12 line numbers that had drifted 34–136 lines; corrected in review. Line numbers drift — the anchors are the fact LABELS, which are stable.)*

And they are **populated, not merely wired** — **as of the 2026-08-12 run, across the 14 dossiers committed THEN** (main carries 17 as of 2026-09-01; the three added since were not re-counted and the ratios below must not be read as current): insider 14/14,
short interest 14/14, share-count trend 13/14, range position 13/14 (the two gaps are FUBO, sealed
at the time by its own `known_wrong.json`, and V).

So the specified change would print a **fifth** copy of facts that already have four homes, inside
a section about the drawdown, with **worse provenance** than the originals (a compact strip string
in place of per-fact `source_ref`s). That is precisely the duplication caught an hour earlier in
PR-B1, where the plan's "price tail" listed drawdown and the queue's `Depth (52w)` column already
carried it.

**The plan's own reasoning already said this**, and the sentence was read too quickly when the
phases were drafted: *"All built at dossier level. None surfaced at queue level, where triage
happens. That gap is the higher-ROI build."* The dossier never had the gap. PR-B1 closed the one
that existed. **PR-B2 is CLOSED as unnecessary — nothing unlocks it.**

## WHAT REMAINS OF PHASE B

The two legs PR-B1 stopped on, and the dossier work makes them cheaper than they looked: the
extractors exist and are proven on 14 names — `mechanical._insider_activity` (Form 4, P and S never
netted, `F` withholding excluded) and `vinci/finra.py` short interest. The open question was never
whether they work, only their **cost at 283-name scale on a weekly cron**: `_INSIDER_SCAN_DAYS` is
1095 and `_form4_codes` fetches per accession, so a cold cache is ~40–120 fetches × ~283 names, and
`data/cache` was already 2.8 GB against Actions' 10 GB ceiling. **A filing COUNT without direction
must not ship as a substitute** — most Form 4s are grants and withholdings, so an undirected count
would be the "heavy distribution" mistake again.

That is an operator budget decision, not an engineering one — **and finding (3) above weakened its
prior.**
