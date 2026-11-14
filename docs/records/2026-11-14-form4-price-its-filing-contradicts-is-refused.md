---
id:
status: shipped
date: 2026-11-14
prs: [1069]
supersedes:
superseded-by:
---

# A Form 4 open-market price its own filing contradicts is refused, never priced: when one filing's prices of one code span more than fivefold, every one of them is refused, never chosen by a vote; a refused sale keeps its count and date, and the largest of its side reads UNKNOWN naming the filing — LLY's "largest sale $57664.29M" is gone

**WHAT.**
- **The defect** (Codex P2 on #1068; `docs/records/2026-11-14-rebuild-group-2-epam-lly-vitl.md`).
  - LLY's rebuild wrote "largest sale $57664.29M, 10% owner, 2025-11-14" into `catalyst_path.insider_activity`, and that line was in its synthesis request.
  - Lilly Endowment's Form 4 `0000316011-25-000073` (filed 2025-11-17) states four sales on 2025-11-14 at weighted averages of 1030.312, 1031414, 1032319 and 1033.155. Two dropped their decimal points: the filing's own footnotes give their ranges as $1,031.00–$1,031.99 and $1,032.00–$1,032.95.
  - `Form4Line.usd` multiplied every stated price, with no check (`vinci/dossier/mechanical.py`, `_form4_codes`).
- **The rule** (`_refuse_inconsistent_prices`, applied by `_form4_codes` to every ownership filing it reads, domestic and FPI alike). It reads the STRUCTURED prices only; the footnotes are free text and never parsed.
  - For each open-market code (`P`, `S`) whose stated prices in ONE filing span more than `_FORM4_PRICE_SPAN` (5), **every priced line of that code is refused**.
  - Never a vote: a majority can be the wrong half, and nothing in the filing says which half is right (#1069's review, round 1).
  - A refused line keeps its shares, its date and its count, and carries its reason (`Form4Line.refused`). Its price is never multiplied (`usd` is None).
  - **Why 5×:** a misplaced decimal point moves a price tenfold or more, so it always crosses 5×. On the cached corpus no legitimate group reaches it: the widest are 1.51× (UBER, a director's ten purchases over months) and 1.44× (WERN). 5× sits between, set by face validity before any outcome was read.
- **The line** (`compose_insider_line`):
  - a window total counts a refused price apart from an absent one ("N with a price refused");
  - the largest of a side reads "largest sale UNKNOWN — k of n sales in the 3y scanned carry a stated price this reader refuses (<reason, its filing named; 'first:' when several filings>)", never a priced line named "largest" in its place, because the refused shares traded at some price this reader cannot state.
  - With nothing refused, the line is byte for byte what it was.
- **A new extraction vintage**, `2026-11-14.form4-price-its-filing-contradicts-is-refused`, with `mechanical.py` re-pinned to it.

**WHY.**
- The coordinator ruled the #1068 finding "not DEFER": a false $57.7bn sale on a page carrying a BUY proposal breaks "fail loud, never fabricate".
- The operator ruled LLY's path on 2026-11-14, verbatim "Rebuild LLY after the fix (Recommended)": this fix, a $0 re-precheck, then one paid LLY build.
- **Why no store-close check.** The coordinator's brief allowed "inconsistent with the same filing's other prices, or with the store's close for that date". The store's bars are split-adjusted, while a Form 4 states its prices as filed. So a close is no arbiter for a filing made before a split: after a 10-for-1 split, every earlier price reads ten times the close. The filing-internal rule has no basis question, and it catches both observed cases.

**HOW VERIFIED.**
- **Fail first, on the real filings** (`tests/fixtures/form4_price_guard/LLY.json`: three Endowment filings' `index.json` and ownership XML exactly as EDGAR served them, decoded through production's `_form4_codes`). On main's code, 3 of the 5 first tests fail on behaviour, and the two negative pins pass on both. Review round 0's 3 tests make 8; the cross-setup run counts 6 of 8 failing at base and passing at head. The three that first failed:
  - the decoded prices are multiplied (`107019537.75 != None`);
  - the dropped decimal among fifteen is not refused (`[] == [878401.0]`);
  - the composed line prints "largest sale $57664.29M".
- **The negative pins:**
  - `0000316011-25-000079`, the same holder two days later: ten sales at $1,030–$1,040, $1,031.414 among them with its decimal point, all priced as stated;
  - a line with nothing refused reads as before.
- **The corpus, before any synthetic case:** all 5,601 Form 4 documents in the HTTP cache on 2026-11-14, with 1,856 filing-and-code groups carrying a stated price.
  - Groups over each threshold: 10 over 1.4×, and 2 over each of 1.6×, 2×, 3×, 5× and 10×.
  - The 2 are both the Endowment's on LLY: `0000316011-25-000073` (4 sales, 2 wrong) and `0001415889-25-005456` (15 sales, 1 wrong: 878401 among 877.311–891.874).
  - **The cost:** 19 sale prices are refused, 3 wrong and 16 correct. Of the 16, 14 are the 2025-02-25 filing's other lines, the whole-group rule's added cost; round 0 already refused `0000316011-25-000073`'s two.
  - No other filing's line moves.
- **The real run.** LLY's insider line on the round-1 code, at its page's reference date: "largest sale UNKNOWN — 19 of 729 sales in the 3y scanned carry a stated price this reader refuses (first: Form 4 0000316011-25-000073: its 4 'S' prices run $1,030.31 to $1,032,319.00, more than 5-fold apart, so none is used)". The 182-day counts are unchanged: sells 6, 5 insiders, $34.59M.
- **LLY's $0 precheck on the fixed code** (the 11-11 store, vendor calls blocked): exit 1 on the accepted `buyback_shares` only; 0 post-spend refusals; `insider_activity` newly present.
- **The gate** in a clean detached worktree at `706f7d20` (after review round 0, before `origin/main` `a7e5d0e4` was merged in):
  - ruff clean; `mypy --strict` clean on 219 files;
  - `pytest -m "not network"` 11,362 passed, 662 skipped, 11 xfailed, 0 failed;
  - the mirror is in sync.
  - The first attempt failed on exactly the extraction-version drift pin for `mechanical.py`; the vintage and re-pin cleared it.
- **The cross-setup section** (`python -m vinci.impact run`, head `f5a51b44`, base `a7e5d0e4`), in #1069's body:
  - 25 of 26 pages built; PARR's mislabelled quarterly export stops it.
  - **1 of 25 moves, on one field:** LLY's `insider_activity`.
  - LLY's synthesis request moves in FACTS only, and the frozen panel shows 0 of 6 differing, so it prints ASK THE OPERATOR for the row-53 panel question (a ruling, not a rule).
  - 0 of 26 committed pages re-render differently.

**REVIEW ROUND 1** (the independent review of `2019fcef`, relayed by the coordinator: "FIX FIRST"). It confirmed the corpus (2 of 1,856 groups refused, the next-widest legitimate span 1.51×, GOOG's two classes unaffected), the fixtures, the fail-first, the gates and the FACTS-only move. It found:
- **MEDIUM:** a vote keeps the wrong half when it is the larger. The filer's own error on 3 of 5 sales kept the three wrong prices, multiplied them into a $30,968.88M window total in the synthesis request, and refused the two right ones. FIXED: the whole group is refused (coordinator's call), pinned by `test_a_majority_of_wrong_prices_is_refused_never_kept`, red under round 0's vote.
- **LOW:** a tenfold shift on the filing's lowest line spans 9.99× and missed the tenfold trigger. FIXED: the 5× threshold, pinned by `test_a_tenfold_shift_on_the_filings_lowest_price_is_caught`, red at 10×.
- **LOW:** two behaviours were untested:
  - the window's "N with a price refused" clause, now pinned on the real filing's four sales dated into the window (red with the clause deleted);
  - a span floor, now pinned by UBER's real 1.51× filing kept (red at 1.4×).
- **The FACTS-only ruling:** the cross-setup section prints ASK THE OPERATOR, because LLY's request moves in FACTS only. The operator's batch 3 ruling ("Not needed; #953 is the test (Recommended)") and its 2026-11-13 confirmation ("Keep it, watch leans (Recommended)") apply, so no row-53 panel check is owed.

**BOUNDARY.**
- **Code:** main `0f5e3eb2` (cut), merged with `a7e5d0e4`, on branch `claude/form4-price-guard`.
- **Corpus:** the HTTP cache's ownership XMLs whose `documentType` is 4, read 2026-11-14; groups are one filing's `P` or `S` lines with a stated price above zero.
- **LLY's line:** `_insider_activity` at LLY's page reference date (2026-10-16), the SEC cache as on 2026-11-14.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A filing with one priced line of a code** has nothing to compare against, so a dropped decimal there is not caught. Neither is a filing whose every price is wrong by the same factor. And the whole-group rule refuses correct prices beside a wrong one: 16 on the cached corpus, 14 of them added by round 1. The falsifier: a committed insider line whose largest trade exceeds the issuer's market value, or any priced line its own footnote range contradicts.
- **A legitimate filing spanning more than fivefold** (none in the 1,856 groups; the widest is 1.51×) would lose its prices to UNKNOWN. That fails toward silence, not toward a false number. The named shape (review round 0, left as a stated limit): one Form 4 selling two share classes at different prices (a Class A/Class B pair, or common beside preferred), because the groups are keyed by code, not by `securityTitle`.
- **Any refused line makes its side's largest UNKNOWN**, even one whose agreeing siblings bound it below a priced line. This is deliberate, stated in the code: the reader never names a largest it cannot rank.
- **No committed page carries the change** until it is rebuilt: LLY's page is main's, with its insider line UNKNOWN, and its paid rebuild follows on the operator's ruling.
