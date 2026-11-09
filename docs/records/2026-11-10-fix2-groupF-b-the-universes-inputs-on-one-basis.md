---
status: open
date: 2026-11-10
prs: [946]
supersedes:
superseded-by:
---

# Fix request 2, group F, the universe's inputs (RF-D8, RF-D4, RF-D9): "two and one-half" ADS reads 2.5, a filed share count with a split since its frames is replaced by Polygon's current issuer-wide count, and ADV is averaged over the market's sessions. The committed 2026-10-16 population holds 6 lines that leave the band on one basis

**WHAT.**
- **RF-D8, the ADS reader.**
  - The fault: "Each ADS represents two and one-half ordinary shares" read `known` 2, "one and a
    half" read 1, and "three and one-third" read 3. Nothing after the whole number said it ran on.
  - The fix: a mixed tail ("and one-half", "and a half", "and one-third") is part of the number,
    inside the same atomic match, and `_count` reads it as whole + fraction. An improper tail
    ("two and three-halves") is no count at all, never its whole part. "2 1/2" in digits is still
    refused, as before.
- **RF-D4, a market cap on two split bases.**
  - The fault: the close is today's (Polygon restates to the day of the read), and a filed EDGAR
    count is as of its frame, up to five quarters back. A name that split since was sized at the
    split factor: a $800M name read $400M and fell out of a $500M floor.
  - Why a frame cannot be adjusted: it does not say which day its count is from. SEC's frames API
    serves the fact that best aligns with the calendar quarter. So a split anywhere since the
    earliest frame could reach (a quarter before its quarter end) leaves the count's basis unknown.
  - The fix: such a line is sized on Polygon's issuer-wide count, `weighted_shares_outstanding`,
    which counts every class in the line's units. That is the same kind of count as the filed one
    it replaces. It is read AS OF THE BUILD'S REFERENCE DATE, so a back-dated build is never
    sized on a later count (review round 1, Codex P1 on #946).
  - **A split AFTER the reference date** (a back-dated build, the audit's own case) moves the close,
    which is restated to the day of the read, and not the filed count. Every frame predates it, so
    the count is put on the close's basis exactly, by that split's factor; a Polygon count is
    multiplied by it too. So the breadth read runs through the day of the read, not the reference
    date.
    - Where Polygon serves no count, the line is dropped as `split_basis_unresolved`.
    - Where neither reading of the filed count could put the line in the band, it is dropped
      `out_of_band`, naming both caps, without a request.
  - Every split in the window comes from ONE breadth read of Polygon's splits reference
    (`PolygonEodClient.splits_executed`: `execution_date.gte/lte`, pages followed).
  - Lines already sized on a Polygon count (depositary, multi-class, fallback) are unchanged.
- **RF-D9, ADV and the stale close.**
  - The fault: ADV was dollar volume over the days the NAME traded. A line trading 3 of 65 sessions
    read $4.0M against $0.18M and cleared the $3M floor. Its latest close was kept however old.
  - The fix: ADV is averaged over every market session in the lookback (the days the
    grouped-daily read returned bars), the audit's own fix. A session the name did not trade adds
    $0.
  - A close the name has not printed in the newest 10 sessions is no latest close. The line drops
    as `stale_price`, naming its last trade. Ten sessions is the SEC suspension limit the price
    scorecard uses (`GAP_SESSIONS`).

**WHY.** These are TeamNostra's fix request 2 (document 15): order 3 (RF-D8), and order 4's
prices (RF-D4, RF-D9). The universe is the validation population, so a mis-sized line enters or
leaves the population the spread accumulates against.
- **ADV: a refinement tried and reverted.** Averaged over all 64 sessions, ADV drops SWRD
  ($3.96M → $1.67M) and SVIA ($7.47M → $2.22M) from the committed population: they traded every
  session since their first, under these tickers. Starting the denominator at each name's first
  trade kept them. But Codex (round 1, P2) showed it also reads a long-listed line that resumed
  after a halt as new. Absence before a bar proves nothing. Polygon's `list_date` cannot tell
  either, since it is the share class's listing: SVIA's reads 2025-12-08, from before its rename
  (`resolver/aliases.py`). So the full window stands, and a line with under a lookback of trading
  history reads low until it has one.
- **The first RF-D4 fix used the per-class count, also revised before shipping.** It would have
  cut Tootsie Roll's cap 43% and Astronics' 16% by leaving out their unlisted classes. The
  universe sizes a single-listed-class issuer on its issuer-wide count, so the replacement is
  issuer-wide too.

**HOW VERIFIED.**
- **The defects, reproduced first** on `main` (`6fbbb4a2`) through the real `build_universe` and
  `latest_close_and_adv`, with the vendors faked at their clients:
  - RF-D4: $400M, "Polygon close x EDGAR dei:…", and dropped at a $500M floor. This branch reads
    $800M, "… weighted_shares_outstanding (CURRENT, ISSUER-WIDE - 2-for-1 on 2026-08-01 …)",
    admitted.
  - RF-D9: THIN, trading its 3 oldest sessions of 65, read ADV $4.00M with a close 62 sessions
    old. This branch reads $0.18M, with no close (`stale` 2026-07-15, 62 sessions).
  - RF-D8: on `main` 2.5 → 2, 1.5 → 1, 3⅓ → 3, and the title 2.5 → 2. This branch reads each
    whole.
- **Tests that fail first.**
  - `tests/test_ads_ratio.py`: 4 of the new pins fail on `main`, and all 54 pass here.
  - `tests/test_universe_one_basis.py`: 5 of 7 fail on `main`; the two negative pins pass on
    both.
- **The corpus.**
  - The 19 committed ADS covers (`tests/fixtures/ads_ratio_covers.json`) state no mixed number,
    and every one reads as before. No committed page or snapshot carries an ADS ratio, so no page
    moves.
- **RF-D9 on the committed 2026-10-16 population** (2,065 admitted lines), from the 65
  grouped-daily requests `latest_close_and_adv` makes for that date, fetched into a scratch cache
  on 2026-11-10:
  - 64 market sessions;
  - 2 admitted lines fall below the floor, SWRD and SVIA, both with under a lookback of trading
    under their tickers (27 and 19 sessions), and 0 are stale.
- **RF-D4 on the same population.**
  - **The splits read:** one breadth read of Polygon's splits reference for 2025-03-30 →
    2026-10-16 returned 2,624 splits across 2,169 tickers.
  - **The lines it touches:** 46 admitted lines carry one. 4 are already sized on a Polygon count;
    42 are on a filed count and are in band on at least one reading, so each costs one cached
    ticker-details request.
  - **On Polygon's issuer-wide count:** 41 of 42 resolve (LXP serves none, so it drops as
    `split_basis_unresolved`). 11 move by 10% or more, and **6 leave the band**:

    | Line | Split | Committed cap | Issuer-wide cap | |
    |---|---|---:|---:|---|
    | IESC | 2-for-1 on 2026-08-24 | $5,020M | $10,684M | above the $10B ceiling |
    | FUBO | 1-for-12 on 2026-03-24 | $2,739M | $242M | below the $300M floor |
    | BYND | 1-for-30 on 2026-08-14 | $3,533M | $125M | below |
    | GOSS | 1-for-80 on 2026-09-11 | $4,287M | $54M | below |
    | GRML | 1-for-50 on 2026-08-24 | $727M | $82M | below |
    | PMI | 1-for-50 on 2026-08-03 | $959M | $30M | below |

    Moving by more than 10% but staying in band: SFBS $2,152M → $4,304M, ASST $1,813M → $3,067M,
    SHAZ $499M → $952M, TJGC $488M → $322M and ABTC $626M → $551M.
  - **The 11 moves have two causes.**
    - Four of the five moves that stay in band are filed counts from the other side of the split.
    - ASST's is not. Its per-class count reads $1,822M, so its EDGAR frame held one class only,
      and the issuer-wide count moves it the other way. That is a policy-consistent read of an
      inconsistency the frames already had.
- **The code review (round 0) caught two breakages before the PR opened, both now fixed and
  pinned.**
  - The two new drop stages were missing from `DROP_STAGES`, so any build with retention (the
    weekly one) raised on its first stale or unresolved line.
  - `tests/test_retention.py`'s stage allowlist was not updated.
  - It also moved split-row parsing to the line that reads it, so a bad row for a ticker the build
    never sizes cannot abort it.
- **Codex review round 1 on #946: two findings, both fixed behind tests red on the PR head
  (`e37b188a`).**
  - P1: a back-dated build sized a past close on today's count. A split after the reference date
    is now applied to the count, and Polygon's count is read as of the reference date.
  - P2: the first-trade ADV denominator. Reverted to every market session.
  - The pins: `test_a_split_after_the_reference_date_moves_the_filed_count_onto_the_closes_basis`
    ($400M on the head, $800M after), `test_the_current_count_is_read_as_of_the_reference_date`, and
    `test_a_line_that_trades_only_its_newest_sessions_is_averaged_over_the_window` ($4.0M on the
    head, $0.18M after).
  - The 42 counts tabled above were read undated (2026-11-10). The six split factors that leave the
    band (2× to 80×) are far beyond the drift between the two dates.
- ruff and `mypy --strict vinci` are clean, and the full offline suite passes (`bin/commit`).

**BOUNDARY.**
- **Population:** `data/snapshots/universe_snapshot.jsonl` at `6fbbb4a2`. Its as_of is
  2026-10-16, with 2,065 lines in the primary band ($300M–$10B, ADV floor $3M). Tickers come from
  `data/snapshots/securities.jsonl`.
- **Grouped-daily:** 2026-07-18 → 2026-10-16, read 2026-11-10 with `adjusted=true`.
- **Splits:** Polygon `/v3/reference/splits`, `execution_date` from 2025-03-30 (the earliest frame
  `CY2025Q2I`'s quarter end less 92 days) to 2026-10-16, read 2026-11-10.
- **Caps:** each line's 2026-10-16 close × Polygon's `weighted_shares_outstanding`, read
  2026-11-10. So the "issuer-wide cap" is today's count against the 10-16 close. Share counts
  drift with buybacks and issuance, which is why moves under 10% are not tallied.
- **ADS corpus:** the 19 names in `tests/fixtures/ads_ratio_covers.json`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The weekly build makes one ticker-details request per filed-count line with a split in the
  window that is in band on either reading.** That is 42 on the 10-16 population, about 9 minutes
  at the plan's ~5 requests a minute, each cached a day. Lines dropped on the filed reading but in
  band on the other also ask, and they are not counted here, because counting them needs every
  frame. Plus 3 pages of the breadth read.
- **Polygon's current count can itself lag a split.** Where it does, the line is mis-sized as
  before. This is the same residual as RF-D1's both-feeds-late case: a vendor that has not caught
  up. A count that resolves to nothing drops loudly.
- **A line with less than a lookback of trading history reads low** for its first quarter: a new
  listing, or a rename the alias tables do not record. SWRD and SVIA leave the committed population
  at the next weekly build for this reason. Falsifier of "seasoning is the right error": a name
  so dropped that then clears the floor on the full window within one build.
- **The dashboard's universe funnel** (`frontend/lib/snapshots.js` `getUniverseStats`) lists a
  fixed set of gates. `stale_price` and `split_basis_unresolved` are not among them, so after the
  next weekly build its rows will not add up to `considered`. It is a render change, which under
  the PREVIEW RULE needs a preview and approval first, so it is left as a follow-up.
- **The committed population is not rebuilt here.** The 6 lines above stay in
  `universe_snapshot.jsonl` until the next weekly build, which the operator runs (STATE §5.0 row 31:
  CI cannot run it under the current Polygon plan).
  - No dossier page reads the universe's cap. That is "not found" under `universe_snapshot`,
    `latest_universe` and `record_universe` in `vinci/dossier/`; a page's cap is
    `mechanical.stock_info`, FUBO's included. So no page moves.
  - The readers that move at that build: the screen (`screens/run.py`), the ranked queue's
    displayed cap (`rank/ranker.py`) and the theme size factors.
