---
id: 2026-11-13-screen-basket-baseline-first-reading
status: shipped
date: 2026-11-13
prs: [1060]
supersedes:
superseded-by:
---

# The $0 screen-basket baseline is built as pre-registered, and its first reading — 30 days on five cohorts, the only horizon the cached prices cover — shows the screen's admitted names BEHIND the names it rejected on four of five cohorts; one month on overlapping cohorts is noise-sized evidence, not a verdict on the screen

**WHAT.** `vinci/scoring/screen_baseline.py`, built to the pre-registration
`docs/records/2026-11-13-screen-basket-baseline-preregistered.md` (committed `a2e579db`, pushed
before the module existed). `python -m vinci.scoring.screen_baseline --repo . --cache <cache root>
[--as-of D]` prints one block per cohort; nothing is committed as an artifact.

**THE FIRST READING** (code `d4defa02`, scored 2026-11-13, prices held through 2026-10-26; price
return; each cohort on its own):

| cohort (run) | admitted / rejected | 30d control: admitted − rejected [95%] | 30d admitted − cap-band benchmark [95%] |
|---|---|---|---|
| 2026-07-29 (`-03`; `-01`, `-02` collapsed) | 331 / 1,381 | **+9.02%** [+6.77, +11.27] (N 329 / 1,375) | n/a — the run recorded no deciding cap (329 admitted named) |
| 2026-08-12 (`-01`) | 292 / 1,428 | −1.21% [−2.81, +0.38] (N 292 / 1,426) | −0.36% [−1.86, +1.13] (N 292) |
| 2026-08-14 (`-01`) | 281 / 1,434 | **−1.77%** [−3.51, −0.03] (N 280 / 1,432) | −0.41% [−2.06, +1.24] (N 280) |
| 2026-08-24 (`-01`) | 268 / 1,453 | **−5.56%** [−7.23, −3.89] (N 268 / 1,450) | **−5.40%** [−6.96, −3.83] (N 268) |
| 2026-09-22 (`-01`) | 289 / 1,381 | **−5.98%** [−8.13, −3.83] (N 288 / 1,377) | **−6.06%** [−8.07, −4.05] (N 288) |
| 2026-10-16 (`-01`) | 343 / 1,299 | not yet passed (exits 2026-11-18) | not yet passed |

The 90- and 180-day horizons print on no cohort: each exits after 2026-10-26, the last session the
cache holds (the 2026-07-29 cohort's 90 days exit on 2026-10-28). Per cohort the output also names
every name scored to its last trade (6 to 10 a cohort), with no bar at entry (0 to 2), and set apart
on a ≥1.9x step (1 to 6).

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

**WHAT IT COSTS / WHAT IS ACCEPTED.** Price return understates total return on both legs alike.
The 2026-07-29 cohort has no benchmark reading because its run recorded no deciding cap — never
inferred. A renamed ticker is read as a stopped one (its last bar under the old symbol) and is named
in that list. Bars are keyed by symbol, so a symbol reissued to another listing inside a window
would splice two companies' prices; the ≥1.9x step catches a large splice, not a small one. A split straddling two cache fetches is set apart, so a genuine ≥1.9x day is lost with
it. The 90- and 180-day readings need a cache that reaches further; no vendor pull was made.
