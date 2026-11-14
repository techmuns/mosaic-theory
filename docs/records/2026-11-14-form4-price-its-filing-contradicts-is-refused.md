---
id:
status: shipped
date: 2026-11-14
prs: [1069]
supersedes:
superseded-by:
---

# A Form 4 open-market price its own filing contradicts is refused, never priced: inside one filing, one code's prices spanning more than tenfold keep only a strict majority within that factor of their median, and with no majority none; a refused sale keeps its count and date, and the largest of its side reads UNKNOWN naming the filing — LLY's "largest sale $57664.29M" is gone

**WHAT.**
- **The defect** (Codex P2 on #1068; `docs/records/2026-11-14-rebuild-group-2-epam-lly-vitl.md`).
  - LLY's rebuild wrote "largest sale $57664.29M, 10% owner, 2025-11-14" into `catalyst_path.insider_activity`, and that line was in its synthesis request.
  - Lilly Endowment's Form 4 `0000316011-25-000073` (filed 2025-11-17) states four sales on 2025-11-14 at weighted averages of 1030.312, 1031414, 1032319 and 1033.155. Two dropped their decimal points: the filing's own footnotes give their ranges as $1,031.00–$1,031.99 and $1,032.00–$1,032.95.
  - `Form4Line.usd` multiplied every stated price, with no check (`vinci/dossier/mechanical.py`, `_form4_codes`).
- **The rule** (`_refuse_inconsistent_prices`, applied by `_form4_codes` to every ownership filing it reads, domestic and FPI alike). It reads the STRUCTURED prices only; the footnotes are free text and never parsed. For each open-market code (`P`, `S`) whose stated prices in one filing span more than `_FORM4_PRICE_SPAN` (10):
  - the lines within its square root (√10, either side) of the group's median are kept only if they are a strict majority, and every other line is refused. The kept lines therefore agree with each other within tenfold. A window of the full factor either side kept a one-digit shift (103.10 beside 10.30–10.32) that fired the trigger, and multiplied it (review round 0);
  - with no strict majority, every priced line of that code is refused.
  - A refused line keeps its shares, its date and its count, and carries its reason (`Form4Line.refused`). Its price is never multiplied (`usd` is None).
- **The line** (`compose_insider_line`):
  - a window total counts a refused price apart from an absent one ("N with a price refused");
  - the largest of a side reads "largest sale UNKNOWN — k of n sales in the 3y scanned carry a stated price this reader refuses (<the first one's reason, its filing named>)", never a priced line named "largest" in its place, because the refused shares traded at some price this reader cannot state.
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
- **The corpus, before any synthetic case:** all 5,601 Form 4 documents in the HTTP cache on 2026-11-14, with 1,856 filing-and-code groups carrying a stated price. 2 groups span more than tenfold, both the Endowment's on LLY:
  - `0001415889-25-005456` (2025-02-25): 878401 among fifteen sales at 877.311–891.874, refused alone;
  - `0000316011-25-000073`: 2–2, all four refused.
  - No other filing's line moves.
- **The real run.** LLY's insider line on the fixed code, at its page's reference date: "largest sale UNKNOWN — 5 of 729 sales in the 3y scanned carry a stated price this reader refuses (Form 4 0000316011-25-000073: its 4 'S' prices run $1,030.31 to $1,032,319.00, more than 10-fold apart, with no majority that agrees)". The 182-day counts are unchanged: sells 6, 5 insiders, $34.59M.
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

**BOUNDARY.**
- **Code:** main `0f5e3eb2` (cut), merged with `a7e5d0e4`, on branch `claude/form4-price-guard`.
- **Corpus:** the HTTP cache's ownership XMLs whose `documentType` is 4, read 2026-11-14; groups are one filing's `P` or `S` lines with a stated price above zero.
- **LLY's line:** `_insider_activity` at LLY's page reference date (2026-10-16), the SEC cache as on 2026-11-14.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A filing with one priced line of a code** has nothing to compare against, so a dropped decimal there is not caught. Neither is a filing whose every price is wrong by the same factor. The falsifier: a committed insider line whose largest trade exceeds the issuer's market value, or any priced line its own footnote range contradicts.
- **A legitimate filing spanning more than tenfold** (none in the 1,856 groups) would lose its prices to UNKNOWN. That fails toward silence, not toward a false number. The named shape (review round 0, left as a stated limit): one Form 4 selling two share classes at different prices (a Class A/Class B pair, or common beside preferred), because the groups are keyed by code, not by `securityTitle`.
- **Any refused line makes its side's largest UNKNOWN**, even one whose agreeing siblings bound it below a priced line. This is deliberate, stated in the code: the reader never names a largest it cannot rank.
- **No committed page carries the change** until it is rebuilt: LLY's page is main's, with its insider line UNKNOWN, and its paid rebuild follows on the operator's ruling.
