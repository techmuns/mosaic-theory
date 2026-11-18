---
status: shipped
date: 2026-11-19
prs: [1126]
supersedes:
superseded-by:
---

# Net debt reads its cash at the filer's newest balance sheet, from the first cash alias that carries it, so the alias walk no longer serves a year-end balance sheet two quarters on; only where no alias carries it is the walk's cash read, within 180 days, and PennyMac's 2018 balance sheet is refused (STATE row 11 (b) CLOSED)

**WHAT.** `vinci.edgar.net_debt.net_debt` picks its cash line differently. Nothing else changes.
- **The cash is read at the filer's newest balance sheet.** That date is `balance_sheet_date`: the
  newest `Assets` instant in us-gaap or ifrs-full, of any unit, ending on or before the day it was
  filed.
- **The first alias that carries the date wins.** `_cash_at_newest` reads the first cash alias,
  in `CONCEPT_ALIASES["cash"]` order, that carries that instant in dollars. Every other line is
  read at that date, as before.
- **THE BACKSTOP.** Where no alias carries the newest balance sheet, the alias walk's latest cash
  is read, and only if it is at most `CASH_MAX_AGE_DAYS` (180, two quarters) behind. Older is
  refused as a past balance sheet, and the refusal names both dates. PennyMac's reads: "no cash
  line net debt reads (CONCEPT_ALIASES['cash']) is tagged at the filer's 2026-09-30 balance sheet,
  and the one read, CashAndCashEquivalentsAtCarryingValue, was last reported $60M at 2018-12-31,
  2830d before it — a past balance sheet, not read as current". It claims only the tags it
  checked: PennyMac tags `Cash` $161.5M at that instant (round 1, below).
- **The walk is unchanged.** `extract_points` and `_walk`, with their 200d sibling rule, are
  untouched for every other concept and reader.
- **Readers.** Net debt's readers move with it: the screen's snapshot and its `net_leverage` and
  `net_debt_to_ocf`, and the anchor's lease-inclusive net debt. `vinci/edgar/net_debt.py` is a
  watched extraction module, so it carries a new vintage,
  `2026-11-19.net-debt-reads-cash-at-the-newest-balance-sheet`, and is re-pinned.

Three nits deferred from the review of #1112 ride here:
- `filer_fiscal_year`'s docstring now says 20 of the 21 tie days are stray us-gaap tags. The 21st
  is Nano Dimension's own US GAAP 6-K of 2025-08-20, 0001410578-25-001862, with 425 us-gaap facts
  and none in ifrs-full.
- The #1112 record gets an appended `## Amendments` entry, because it is merged. Americas Gold &
  Silver's served +160.6M is the sign-flipped `ifrs-full:ProfitLossFromContinuingOperations`
  −160,576,000, not `ProfitLossAttributableToOwnersOfParent`.
- A combined figure withheld one IFRS year behind is worded for its pair: "so neither US GAAP
  figure of that year is current". It is pinned.

STATE row 11 also carries the stray tag's flipped sign as ACCEPTED RISK, with its falsifier.

**WHY. Option 1, a bound alone, found the real defect, and the defect is the alias walk.** #1096's
census found PennyMac Mortgage's net debt of $5,958M served PRESENT. Every line was read at
2018-12-31, because its cash aliases stop there, beside 10-Qs to 2026-09-30. Option 1 bounded the
walk's cash date at 180d behind the filer's newest balance sheet. On screen run 2026-10-16-01's
768 replayed rows, it refused Eastman, Olin, Andersons, APEI and Everforth at 181d.

None of those five is stale. Each tags `CashAndCashEquivalentsAtCarryingValue` only in its 10-K
and the restricted-cash total in every 10-Q. The walk keeps the first alias while a sibling leads
it by at most 200d (`SIBLING_LAG_DAYS`), which is right for choosing a series and wrong for a
balance-sheet date. So the walk oscillates:
- after Q1 (90d) and Q2 (181d) it keeps the year end, and net debt reads a balance sheet up to
  two quarters old;
- after Q3 (273d > 200d) it switches to the 10-Q alias, and is current;
- the next 10-K brings it back.

A bound on that date refuses a current filer every second quarter, so the coordinator ruled for
option 2: read the cash at the newest balance sheet from whichever alias carries it, and keep the
bound only for the case where none does. Eastman's pin shows both halves of the oscillation.

**HOW VERIFIED.**
- **The whole cache, today's blob, uncut.** Net debt runs on all 1,078 cached companyfacts; 961
  carry a dollar cash line. Main 5152d885 → this branch:
  - 946 of the 961 read cash at their newest balance sheet. The other 15 fall to the backstop: 2
    are read (90d), 13 refused (181d and more). 10 of the 13 were already UNKNOWN for another
    reason (no debt or cash line, or an under-capture witness) and now name the stale cash; the
    other 3 are the served → refused below;
  - **the value moves on 6**: Morningstar +$654.9M (543.9M → 1,198.8M, at 2026-03-31 not
    2025-12-31), Diebold +$183.6M, Perrigo +$62.3M, US Antimony +$27.1M, Papa John's +$7.5M,
    Fox Factory −$7.2M. Each reads the restricted-cash alias at its newest balance sheet;
  - **3 go served → refused**: PennyMac (2,830d), Jack in the Box (280d) and AdaptHealth (183d),
    none with an alias at its newest balance sheet;
  - **1 goes refused → served**: Phreesia, $14.2M at 2026-04-30. Its 2026-01-31 reading was
    refused by the under-capture witness, `LinesOfCreditCurrent` $84M beside $3M of long-term
    debt. At 2026-04-30 the $84.2M is read as borrowings, and the witness has nothing unread.
- **The whole cache at the run's cut (2026-10-16), main → this branch:**
  - 945 read cash at the newest balance sheet; 3 are read through the backstop and 13 refused;
  - the value moves on 13, the largest Morningstar +$654.9M, Eastman +$305.0M (4,221.0M →
    4,526.0M, at 2026-06-30 not 2025-12-31), Everforth +$277.0M and Olin +$192.0M;
  - 3 go served → refused: Jack in the Box, PennyMac, and BorgWarner, whose Q2 10-Q tags no cash
    line at 2026-06-30, so its year-end cash is 181d behind;
  - 1 goes refused → served: Phreesia.
- **Moves among refused readings** (round 1; the passes above counted served pairs only). A
  refusal re-dated while it stays UNKNOWN:
  - uncut: HIVE Digital's under-capture refusal, 2026-06-30 → 2026-09-30; Greenwich
    LifeSciences, 2025-12-31 → 2026-03-31, and Unusual Machines, 2026-03-31 → 2026-09-30, both
    under "no debt/cash";
  - at the cut: Greenwich LifeSciences and Unusual Machines (2026-03-31 → 2026-06-30).

  And the 13 backstop refusals at each cut name the stale cash; 10 of them were UNKNOWN on main
  for another reason.
- **Option 1 → this branch, at the cut:** 7 of option 1's 10 refusals are served: Eastman, Olin,
  Andersons, Everforth, APEI, Sunoco and Perrigo. Phreesia is also served, refused under option 1
  for its other reason. The 3 others stay refused.
- **The screen's own code on screen run 2026-10-16-01.** `vinci.facts.screen_replay.screen_inputs`
  replays each candidate row at its own price-date cut and close from the cached companyfacts:
  2,065 rows, 768 cached, 1,297 not read. Main → this branch, **20 of 768 names move**:
  - **record fields** (`net_leverage`, `net_debt_to_ocf`):
    - 16 values in 10 names stay PRESENT and move. Morningstar's net leverage goes 0.759 → 1.673
      and its net debt / OCF 0.922 → 2.033. The others are Everforth 2.933 → 3.738, APEI −1.236 →
      −2.113, Olin 5.048 → 5.412, Diebold 1.644 → 1.860, Andersons, Eastman, Fox Factory, Perrigo
      and Papa John's;
    - Phreesia's 2 go UNKNOWN → PRESENT (0.572, 0.180);
    - 6 names' 12 fields stay UNKNOWN, now naming the stale cash: PennyMac, Himax, National Steel,
      Badger Meter, Red Cat and Americas Gold & Silver;
    - **0 go PRESENT → UNKNOWN**;
  - snapshot-only, 3 names: SFBS, US Antimony and UMAC;
  - **no gate moves.** `vinci/screens/screen2.py` and `vinci/rank/` read no net-debt field. Their
    one reader is their writer, `screens/assemble.py`.
- **The committed pages:** the impact run, in the PR body.
- **Pins: 14** in `tests/test_net_debt_cash_age.py`, on 11 frozen real filers
  (`tests/fixtures/cash_age/`, README there).
  - **Subset check.** Each subset reads as its full blob at main and at this branch: net debt and
    the balance-sheet date, uncut and cut at 2026-10-16 and 2009-11-30, 0 of 33 readings differing.
  - **Option 2's pins:**
    - Diebold read at 2026-09-30 today and at 2026-06-30 at the cut, under the restricted-cash
      alias;
    - Eastman at the cut, read at 2026-06-30 while the walk serves its year end, and after Q3 the
      walk switched;
    - Morningstar read at 2026-03-31;
    - Visa, where both aliases carry the newest ($12,938M and $19,118M) and the first is read.
  - **The backstop's:**
    - AdaptHealth, read at the cut (91d) and refused today (183d);
    - Jack in the Box, refused at 280d;
    - PennyMac, refused at 2,830d, including its committed run row through `screen_inputs`;
    - Himax and National Steel, whose IFRS balance sheets date the newest.
  - **The negatives:**
    - TAT Technologies, an annual filer whose year end is its newest balance sheet;
    - Roper's forward-dated `Assets`;
    - a net-debt shape with no `Assets`, which is not measured.
  - **Fail first.** On option 1's code the Diebold, Eastman, Morningstar and both PennyMac pins
    fail (5), the last two on the refusal's new words; AdaptHealth's passes there, as a backstop
    pin should. Against main, the impact run's fail-first stage has them (the PR body).
- **Mutants on `net_debt.py`, 5 killed of 5:**
  1. the walk's pick only, under the bound (option 1): killed by Diebold, Eastman and Morningstar;
  2. the aliases read in reverse order: killed by Visa. It survived until that fixture was cut,
     since no other fixture carries both aliases at its newest;
  3. no backstop: killed by PennyMac, Jack in the Box, AdaptHealth, Himax and National Steel;
  4. the backstop at a year: killed by Jack in the Box and AdaptHealth;
  5. the backstop at one quarter (89d): killed by AdaptHealth.

**ROUND 1 (2026-11-19): coordinator A's independent review of 1f3fadcb; Codex found nothing.**
No blocker. It reproduced every count above and re-derived Morningstar, Diebold and Phreesia.
- **Should-fix 1, FIXED:** the backstop refusal claimed an absence that is false. It now says no
  cash line net debt reads is tagged there (WHAT IT COSTS 3 has the other tags), and the PennyMac
  pins fail on the old words.
- **Should-fix 2, FIXED:** the restricted cash is measured (WHAT IT COSTS 1).
- **Nits:**
  - 3: the PR title says 0 RECORD fields go PRESENT → UNKNOWN. PennyMac's snapshot `net_debt`
    goes PRESENT → UNKNOWN in the same replay;
  - 4: the #1112 amendment lists all six ifrs-full lines;
  - 5 and 6 are FOUND NOT FIXED (WHAT IT COSTS 4);
  - 7: the PR body's fail-first count is corrected. With `balance_sheet_date` and `stale_cash`
    loaded into main's code, Visa, TAT and Roper pass. The real fail-firsts are 10 cash-age pins
    and the pair-wording pin;
  - 8: the moves among refused readings are named above.
- **What moves, e71ec3f8 → round 1:** only words. The 13 backstop refusals are reworded at each
  cut, and nothing else in any net-debt reading moves. In the replay of run 2026-10-16-01, 7
  names' notes are reworded (BMI, HIMX, PMT, RCAT, SFBS, SID, USAS), and no status changes.

**BOUNDARY.**
- **Cache:** the primary checkout's SEC cache, read directly, with no TTL and no network: 1,078
  companyfacts blobs, one per CIK, fetched 2026-06-17..2026-11-18. A cash-line filer is one with
  a dollar cash point (`net_debt` returns a reading), 961 at both cuts.
- **Code:** MAIN is 5152d885 (a detached worktree); OPTION 1 is 2ae8c7ed (the WIP bound merged
  with main); THIS BRANCH is its option-2 commit. Measured 2026-11-19.
- **Units:**
  - the cache passes: one filer's net debt (LEVERAGE and EV bases, date, cash tag, refusal);
  - the replay: one candidate row, or one field of one row;
  - "value moves": either base or the date differs while both sides serve.
- **Cuts:** uncut, and cut at 2026-10-16. In the replay, each row is cut at its own price date
  (767 at 2026-10-16, 1 at 2026-10-15), with its own `last` close.
- **Replay population:** screen run 2026-10-16-01's 2,065 candidate rows. 768 are replayed; 1,297
  have no cached companyfacts and are not read.
- **Both aliases:** 712 of the 1,078 cached filers carry both cash aliases at their newest balance
  sheet, and 405 of those with different values (uncut).
- **Fixtures:** 11 filers, fetched 2026-06-27..2026-11-11 (the README has each).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The second alias includes restricted cash.** Where only
   `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` carries the newest balance
   sheet, net debt nets restricted cash. That is the alias list's own order, and the walk already
   served that alias whenever it led by more than 200d. A current balance sheet with restricted
   cash in it is preferred to a stale one without. **MEASURED (round 1):** restricted cash =
   alias 2 − alias 1 at the last date both carry, on the filers this branch serves through alias 2
   where main read alias 1.
   - **At the 2026-10-16 cut, 14 filers:** $0 to $15.0M, at most 2.2% of net debt. Diebold
     $15.0M (2.2% of its $687.3M), APEI $2.4M (1.8% of −$135.4M), Papa John's $2.4M (0.3%), and
     US Antimony $0.16M against −$3.2M. The other 10 are $0.
   - **Uncut, 7 filers:** 3 nonzero, Diebold $15.0M (1.9% of $791.2M), Papa John's $2.4M and
     US Antimony $0.16M; the other 4 are $0.

   It is real where alias 2 alone is read: Visa's two aliases differ by $6,180M at 2026-09-30, and
   the first is read there (pinned). Falsifier: a filer read through alias 2 whose restricted cash,
   so measured, is material against its net debt. None is today.
2. **The backstop's 180d is option 1's bound**, measured then on the walk's date: 571 at the
   newest, 4 at 90–91d, nothing from 92d to 181d. Under option 2 the backstop applies to 15
   filers today, 2 read at 90d and 13 refused at 181d or more. It is set by that gap and by the
   share count's precedent, never by outcomes.
3. **A filer whose newest balance sheet carries no cash alias is refused** once its last aliased
   cash is two quarters old. The common case is cash moved to a tag net debt does not read: on
   2026-11-19, 12 of the 13 filers the backstop refuses (uncut) tag cash at that exact instant
   under another tag. 8 use the disposal-group total
   (`...RestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations`; AdaptHealth's
   $80.7M), 6 `us-gaap:Cash` (PennyMac $161.5M, Jack in the Box $43.0M), 4
   `ifrs-full:CashAndCashEquivalents`, 2 `ifrs-full:Cash` and 1 `CashAndDueFromBanks`. Only
   CoinShares Bitcoin ETF carries none, and at the cut BorgWarner, whose Q2 10-Q tags `Assets` at
   2026-06-30 and no cash line at all. The refusal says only that no cash line net debt READS is
   tagged there. Reading those tags as aliases is a scope change, not made here: a possible
   follow-up, which would have to show each is the same line. Fail loud: CIQ can settle it at the
   depth stage.
4. **FOUND, NOT FIXED (round 1):**
   - **A walk cash dated after the newest balance sheet passes the backstop** with a negative age.
     `balance_sheet_date` skips a forward-dated `Assets` row, and the backstop does not skip a
     forward-dated cash. There are 0 cases at both cuts: no filer's walked cash is later than its
     newest balance sheet, and the walk picks none of the 12 forward-dated cash points the
     aliases carry. The right reading depends on the shape. A forward-dated context should be
     refused, while a cash instant on a date the filer tags no `Assets` is current. No real filer
     shows either, so a pin would choose on a synthetic shape. DEFERRED; an `abs(...)` mutant
     survives.
   - **`balance_sheet_date` accepts `Assets` from any form.** It is latent: all 961 newest
     instants come from a 10-Q (885 uncut, 868 at the cut), 10-K, 10-KT, 20-F, 40-F or 6-K.
5. **Not touched:** the 52 combined annual figures whose legs stop a year apart stay refused,
   pending the operator's reading (STATE row 11's owner column).
