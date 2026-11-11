---
id: 2026-11-11-fund-pe-rule-split-adjusted-eps
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# The fund's P/E rule puts EPS filed before a filer-stated split on the current share basis, instead of refusing the range — the screen's G3, the dossiers' P/E range and the desk

**WHAT.** Operator, 2026-11-11, asked how splits should be handled: **"Split-adjust EPS, fund rule"**
— "standard practice: divide pre-split EPS by the split ratio in the fund's shared P/E rule. The
screen uses it too, so it's a decision-path change in its own PR, with a shown real run before
merge". DECISION PATH: `pe_current_and_percentile` feeds the overshoot screen's G3 ("a multiple at
the name's own floor"), the dossier pages' P/E range (`vinci/dossier/mechanical.py`) and the
theme desk.

- **`assemble.split_restatement`, new.** It returns the ONE split the filings state: the factor
  `share_basis_change` reads (two or more restated annual periods agreeing on it, never a
  magnitude alone, never a restatement that crosses zero), its direction, and the first filing
  on the new basis.
  - It returns None for no change, for two changes in one window, and for two same-size splits
    whose restating filings are more than a year apart. HLF's 2011 and 2018 2-for-1s both read
    ×2.0, and agreement alone would have grouped them.
  - `share_basis_change`'s output is unchanged: the same detection, factored into
    `_restatement_factors` / `_latest_agreeing_group`.
- **`_pe_pair_per_reported_share`.**
  - **Adjusted:** when the window holds one split stated by filings known by the date, and the
    EPS in use is on the new basis, every annual EPS filed before the restating filing is
    multiplied by the filer's factor (÷ for a forward split, × for a reverse). The percentile
    note says so.
  - **Still refused (`G3_SPLIT_BASIS`):** two basis changes, a split the filings known by the date
    do not yet state, and an EPS in use still on the old basis.
- **The desk (`theme_intelligence/market.py`).** `basis_breaks` takes the filer's factor
  (`explained`), and a break within 5% of it is the split already adjusted for. Until now the
  desk refused AMZN and GOOGL on their ×20 EPS restatements and ×20 cover-page share jumps. A
  break of another size still refuses. NVIDIA's 2024 split, which the fund's two-period rule does
  not read, stays refused.

**WHY.** Until now the rule refused a range through a split, holding that "the periods the filer
never restated have no published current-basis figure and deriving one would be fabrication".
The operator ruled for the standard practice instead. The factor is the filer's own, read from
its restated comparatives. Refusing cost the screen a G3 reading on every split name, and the
desk a five-year percentile on AMZN and GOOGL (11 rows on 2026-11-10).

**HOW VERIFIED.**
- **Pins, failing on main's code first** (run against an origin/main worktree):
  - NFLX on its real filings now reads **0.11**, near the bottom of its range, as a consistent
    basis puts it. The unadjusted range once published 0.909. The note names the filer's
    ~10.02x and its 2026-01-23 10-K.
  - The window-edge 2:1 is adjusted through the EPS reach-back; its exact expected value is
    computed from the bars. Unadjusted, it would more than triple.
  - PEGA on its real filings is built, with the filer's ~1.996x named.
- **Negative pins:**
  - a split the filings known by the date do not state is refused (valued 2023-01-31, restated
    2023-02-15);
  - two splits in one window are refused;
  - two same-size splits are two, not one;
  - a reverse split scales older EPS up;
  - on the desk, a ×3 share-count move of another size still refuses.
- **The desk on AMZN's real filings** (EPS and cover-page share counts, `desk_points`): the
  premise is the ×20 the filer stated (restated 2023-02-03), seen as `eps` and `shares` breaks;
  it now holds a five-year percentile.
- **REAL RUN, the decision surface.** These are the six names the 2026-10-16 screen refused at
  G3 for a split (`data/snapshots/screen_runs/2026-10-16-01.jsonl`), every one of which passed
  G1 and G2.
  - Read at that reference date, the screen's way: SEC companyfacts cut at the price frontier,
    annual diluted EPS, `pe_current_and_percentile`.
  - Prices are Polygon's recent bars plus Tiingo's older closes, joined and checked over their
    overlap. This is the screen's split-adjusted basis, but not its store, which ends 2026-07-02.

| Name | Split (filer's factor, restating filing) | Screen 2026-10-16 | Unadjusted range | Split-adjusted | G3 (≤ 0.25) |
|---|---|---|---|---|---|
| PEGA | ~2.00× forward, 2026-02-10 | refused | 0.119 | 0.119 | PASS |
| MFA | ~3.99× reverse, 2022-09-27 | refused | 0.147 | 0.233 | PASS |
| CIM | ~2.98× reverse, 2025-02-19 | refused | 0.001 | 0.250 | PASS, exactly at the threshold |
| PATK | ~1.50× forward, 2025-02-20 | refused | 0.678 | 0.484 | FAIL |
| MUX | ~10.2×, 2023-03-14 | refused | 0.652 | not held: 420 P/E points < 450 | NOT_EVALUATED (short history) |
| IVR | ~10.0×, 2023-02-21 | refused | 0.002 | not held: 417 points < 450 | NOT_EVALUATED (short history) |

  - **Under this rule, PEGA, MFA and CIM would have passed all three gates on 2026-10-16.**
  - Re-run after the code review's three correctness fixes (a lone older-split period in the
    window, splits restated by consecutive 10-Ks, a revision dating the split late): the six
    readings are unchanged.
  - CIM's unadjusted range (0.001) overstated how cheap it was. PATK's (0.678) overstated how
    dear.

- **The suite:** see the PR.

**BOUNDARY.**
- The real run is at reference date 2026-10-16 over the six names the screen refused for a
  split, with prices from Polygon and Tiingo rather than the screen's store. Each percentile is
  over five years of daily closes to that date.
- The fixtures are as committed (`tests/fixtures/companyfacts/`, `tests/fixtures/split_basis/`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **Nothing on the decision surface moves until it is re-run.**
  - The ranked queue changes only at the next weekly screen, which runs locally and cannot run in
    CI (STATE §5.0 row 31). On that data PEGA, MFA and CIM would enter. MFA and CIM are mortgage
    REITs, where a P/E range is a weaker read.
  - The committed AMZN, GOOGL and NFLX dossier pages keep the old refusal until each is
    re-assembled.
  - The desk shows AMZN and GOOGL on five years at its next market run.
- **Accepted.** An annual period the filer never restated is put on the current basis by the
  filer's factor for another period. The same split rescales every per-share figure
  identically, which is what the factor states. A split the filer has not yet restated (between
  the split and the next 10-K) still runs unadjusted where the fund's check cannot read it. That
  is unchanged; the desk's cover-page check still catches it.
- **Accepted (review findings not fixed here):**
  - The desk works out the split itself rather than reading the factor the rule applied; a
    structured return is a wider change. Where the two disagree, the rule refuses, so it fails
    safe.
  - A break is matched to the split by size, not date.
  - The split scan runs more than once per name.
