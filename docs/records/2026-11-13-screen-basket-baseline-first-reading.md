---
id: 2026-11-13-screen-basket-baseline-first-reading
status: shipped
date: 2026-11-13
prs: [1060]
supersedes:
superseded-by:
---

# The $0 screen-basket baseline is built as pre-registered, and its first reading — 30 days on five cohorts, the only horizon the cached prices cover — shows the screen's admitted names BEHIND the names it rejected on four of five cohorts (by more than the interval on two); one month on overlapping cohorts is noise-sized evidence, not a verdict on the screen

**WHAT.** `vinci/scoring/screen_baseline.py`, built to the pre-registration
`docs/records/2026-11-13-screen-basket-baseline-preregistered.md` (committed `a2e579db`, pushed
before the module existed). `python -m vinci.scoring.screen_baseline --repo . --cache <cache root>
[--as-of D]` prints one block per cohort; nothing is committed as an artifact.

**THE FIRST READING** (code at this PR's head, scored 2026-11-13, prices held through
2026-10-26, price return, each cohort on its own), under the split rule AS AMENDED (the
pre-registration's `## Amendments`, pr-feedback round 2), with the rule as first registered beside
it:

| cohort (run) | admitted / rejected | 30d control: admitted − rejected [95%] | 30d admitted − cap-band benchmark [95%] | as first registered: control · benchmark |
|---|---|---|---|---|
| 2026-07-29 (`-03`; `-01`, `-02` collapsed) | 331 / 1,381 | **+9.00%** [+6.70, +11.29] (N 330 / 1,379) | n/a — the run recorded no deciding cap (329 admitted named) | +9.02% · n/a |
| 2026-08-12 (`-01`) | 292 / 1,428 | −1.12% [−2.72, +0.48] (N 292 / 1,428) | −0.36% [−1.86, +1.13] (N 292) | −1.21% · −0.36% |
| 2026-08-14 (`-01`) | 281 / 1,434 | −1.73% [−3.48, +0.01] (N 280 / 1,433) | −0.41% [−2.06, +1.24] (N 280) | −1.77% · −0.41% |
| 2026-08-24 (`-01`) | 268 / 1,453 | **−5.47%** [−7.14, −3.79] (N 268 / 1,452) | **−5.40%** [−6.96, −3.83] (N 268) | −5.56% · −5.40% |
| 2026-09-22 (`-01`) | 289 / 1,381 | **−6.42%** [−8.64, −4.19] (N 289 / 1,380) | **−6.34%** [−8.41, −4.26] (N 289) | −5.98% · −6.06% |
| 2026-10-16 (`-01`) | 343 / 1,299 | not yet passed (exits 2026-11-18) | not yet passed | — |

Under the amended rule one name of the five cohorts is set apart (TDUP, 2026-07-29, a step across
two fetch batches), where the first rule set 15 apart (6 + 2 + 1 + 2 + 4 name-cohorts, TDUP among them; the review
counted 16 set-aside steps, since one name can step more than once). No sign changes. The largest move is 2026-09-22's control, −5.98% → −6.42%. On 2026-08-14
the control's interval now reaches zero, so the cohorts that trail by more than the interval are
two (08-24, 09-22), where they were three. The 2026-10-16 cohort prints its run's two committed
annotations (SFBS, IESC: "would not be a candidate" on split-spliced bars) beside it, display only.

The 90- and 180-day horizons print on no cohort: each exits after 2026-10-26, the last session the
cache holds (the 2026-07-29 cohort's 90 days exit on 2026-10-28). Per cohort the output also names
every name scored to its last trade (6 to 10 a cohort) and with no bar at entry (0 to 2).

**HOW TO READ IT — and how not to.** Five cohorts entered between 2026-07-30 and 2026-09-23 share
calendar time, so they are not five independent tests; the record forbids pooling them for exactly
that reason. Each interval is a cross-sectional one, around a single month in which every name in
a cohort sat in the same market. What the readings can say: on the 30-day horizon, in these months,
the screen's admitted names did not beat the names it rejected, and three of the five cohorts
trailed them by more than their intervals. What they cannot say: whether the screen selects at the
horizon it is built for (the de-rating twin resolves in months; the ledger's horizon is 180 days).
**Nothing here is read back into a gate** (the outcome fence, and retention's own rule).

**HOW VERIFIED.**
- **One name worked by hand, independent of the module** — the cache key computed and the
  response read by hand: AAON (2026-08-12 cohort; deciding cap $7.028B → MDY): entry close 87.67 on
  2026-08-13, exit close 79.795 on 2026-09-11 (the last session on or before 2026-09-12): −8.9825%;
  MDY 714.6 → 678.68: −5.0266%; excess −3.9560%. The module's mark: −8.9825%, −3.9560%.
- **Round 2 (the coordinator's independent review): 12 more mutants killed.** They cover the
  benchmark entered at the run's own close, an earlier same-date run's rows kept, a no-entry name
  imputed from the run date or scored at 0%, the truncation note dropped, the benchmark line before
  the control, the latest add read, the shallow-clone refusal, the annotations, and three on the
  batch rule. Five of the round's pins fail on the round-1 head (the batch rule ×3, the
  shallow-clone refusal, the annotations). The review's own hand-check matched the module to four
  decimals on CPB and BMI (2026-09-22) and BBBY (2026-07-29, stopped 08-14).
- **Mutation: 13 of 13 killed** (each a one-line mutant of the module, run against
  `tests/test_screen_baseline.py` in a copy of the tree): the latest run of a date, the commit's
  bytes not the working file's, a horizon bounded by the prices held, a stopped name scored not
  dropped, the split step, the cap-band benchmark, not-assessed kept out of the rejected leg, a cache
  gap never read across, the admission gate required, the entry on the NEXT session, the interval's
  z, Welch's two legs, and the benchmark read to the name's last trade. Three survived the first
  pass (the commit's bytes, Welch, the benchmark's exit) and were killed by tightened fixtures.
- **Read-only, $0:** the primary checkout's `data/cache/polygon` held 1,563 files before and after
  the run; every fetch raises (`_CacheOnly`).
- **The fence:** `tests/test_outcome_import_fences.py` names the module in the outcome layer and pins
  that an import of it from a screen module is seen.

**BOUNDARY.** Cohorts: the 8 `.jsonl` run files in `data/snapshots/screen_runs/` at `01ab6923`, each
added in one commit and never changed since, on 6 reference dates. "admitted / rejected": candidate-
grain rows of the cohort's run, admitted = `admitted` gate PASS, rejected = not admitted and outcome
FAIL. N: the names priced at entry and at exit and not set apart. Prices: the cached Polygon
grouped-daily responses (`adjusted=true`) for weekdays from 2026-07-29, contiguous through
2026-10-26 (2026-10-27 is the first weekday the cache lacks). Intervals: 95%, normal approximation
(the control by Welch's standard error).

**A SPEC DEVIATION, stated.** The benchmark band is assigned on the cap that decided the name's
membership (`deciding_cap`, Polygon close × shares at the run's reference date), where the ledger
assigns it on the cap at entry (`BenchmarkAssignment.cap_at_entry_usd`, entry price × shares). The
run stores no share count apart from the cap, so the entry cap would need the cap rescaled by the
entry close over a reference-date close the cap may not have used. A name moves band only if its
cap crosses $4B (or $25B) between the reference date and the next session.

**A SHALLOW CLONE IS REFUSED** (`git rev-parse --is-shallow-repository`): its one commit would read
as the commit that added every run file.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Price return understates total return on both legs alike.
The 2026-07-29 cohort has no benchmark reading because its run recorded no deciding cap — never
inferred. A renamed ticker is read as a stopped one (its last bar under the old symbol) and is named
in that list. Bars are keyed by symbol, so a symbol reissued to another listing inside a window
would splice two companies' prices; the ≥1.9x step catches a large splice, not a small one. A ≥1.9x step across two fetch batches is set apart, so a genuine one-day move of that size
across a batch boundary is lost with it (TDUP, once, on this reading). The 90- and 180-day readings need a cache that reaches further; no vendor pull was made.
