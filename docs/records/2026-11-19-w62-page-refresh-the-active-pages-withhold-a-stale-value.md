---
id:
status: shipped
date: 2026-11-19
prs: [1127]
supersedes:
superseded-by:
---

# W62's page refresh: 8 of the 10 refreshed active pages move ($0, `anchor-backfill`, no LLM). GOOGL's screen value is WITHHELD ("not priced": its CIQ multiple is the 2026-09-30 close, 42 days before the page's close). The 7 other moved pages keep their values, and their split states the cadence verdict (TJX's W61 "Stale multiple" notice no longer prints). NCNO and VITL are unchanged. BRBR is excluded (A's rebuild), and the 15 watch pages are left as committed.

**WHAT.**
- **Pages refreshed.** `anchor-backfill` re-derived the anchor on head code `65a8b863` (main after #1122) for 10 pages: EPAM, GOOGL, IT, LLY, NCNO, SMPL, TJX, VITL, VRRM and WERN.
  - That code carries W62 (#1122) and A's net-debt cash rule (#1126, `3586a864`).
  - `anchor-backfill` is the anchor-only $0 writer: EDGAR and the CIQ bridge, with no LLM and no re-assembly.
  - `frontend/dossiers` was then mirrored, byte-identical to each page.
- **GOOGL's value is withheld, as W62 rules.**
  - The value, its diluted twin and its EV/EBIT are withdrawn: they were $292.90, $290.25 and 28.2x.
  - Its split goes with them: W61's refusal of CIQ's denominator before, and a stale anchor carries no split.
  - Its main table reads "Screen value / share | not priced | the multiple is the 2026-09-30 close, 42 days before the page's close; a fresh CIQ export clears it". It gains the `multiple_stale` flag and its detail line, and its mid-cycle sentence says R1 WOULD price the median.
  - Unchanged: `applicable` (True), the operator's R3 tag, the machine's R4 read and the dated 22.8888x with the 17.4518x median beside it. The value stays withheld until the operator brings a fresh CIQ export; no workaround was attempted.
- **The 7 other moved pages keep every value.** These are EPAM, IT, LLY, SMPL, TJX, VRRM and WERN.
  - Their screen value, multiple, net debt and split figures are unchanged.
  - The split arithmetic's last line now states the anchor's cadence verdict in place of W61's flat clock: "not stale by its history's cadence", then the rule.
  - CIQ's history (IT, LLY, VRRM): stale past 30 days.
  - The ex-lease history: the next quarterly observation's due date. EPAM 2027-02-26, SMPL 2027-01-26, TJX 2026-12-29, WERN 2027-02-26.
  - On TJX the split's `stale_close` turns false and W61's "Stale multiple" notice no longer prints. Its 2026-08-28 close is 75 days old, but its next observation is not due until 2026-12-29.
- **NCNO and VITL are unchanged** and left byte-identical. NCNO is an R2 page whose anchor stops before the multiple leg; VITL is lease-refused and publishes no screen value.
- **A's net-debt cash rule (#1126) moves no value here.** On the 8 moved pages, `anchor.net_debt` and every value read from it are unchanged.
- **BRBR is EXCLUDED** (coordinator B, 2026-11-19). Its rebuild is A's: its FY26 10-K is filed, and the operator added its CIQ export on 2026-11-18. It still prices the median until that rebuild.
- **The watch pages are left as committed** (operator ruling, 2026-11-13): AMZN, BURL, CNXC, FUBO, MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V and WLK. Each takes W62 at its next build once active.

**WHY.**
- W62 (#1122, merged as `65a8b863`) put the cadence rule in code, and no committed page carried it. GOOGL's committed page therefore still priced $292.90 on a 42-day-old CIQ close, and TJX's still called its multiple stale while the anchor priced on it.
- The operator ordered this refresh on 2026-11-19 ("Yes to both"), replying to "Merge #1122 once green, then run its $0 refresh of the active pages?".

**HOW VERIFIED.**
- **Dry run first.** 10 processed: 8 CHANGED and 2 unchanged (NCNO, VITL). Every priced base moved +0%, and GOOGL's moved to none.
- **Every page diffed leaf by leaf against main `65a8b863`.**
  - On EPAM, IT, LLY, SMPL, VRRM and WERN, 6 leaves move: `anchor.computed_at`, the split's last arithmetic line, and one appended `layer_refreshes` entry (4 leaves).
  - TJX: those 6, plus `gap_split.stale_close` (true → false) and `gap_split.stale_line` (the notice → null).
  - GOOGL: 43 leaves.
    - The value, its diluted twin and `anchor_ev_ebit`.
    - `data_quality` and its new detail line.
    - `value_withheld`.
    - `midcycle_gap.read`.
    - The 31 leaves of its withdrawn `gap_split`.
    - `computed_at`.
    - The refresh entry (4 leaves).
  - 0 other leaves move. `applicable`, `recipe_hint`, `reason`, `multiple`, `net_debt`, `valuation_basis`, `ev_gap` and `qa_flags` move on none of the 8.
- **Each md moves only** in these places:
  - the header's "layers refreshed to" stamp;
  - the split's last arithmetic line (6 pages);
  - TJX's "Stale multiple" notice, removed;
  - GOOGL's screening block: the "not priced" row replacing the value and dilution rows, the refused split gone, the flag line, and the mid-cycle sentence;
  - the rendered refresh entry under "Record & reproduce".

  `anchor-backfill` re-renders each md from its JSON.
- **Each committed split rebuilds its published value.** `committed_gap_split`, the rebuild from the committed fields alone, raises on none of the 7. Its value at today's multiple equals the stored one within $0.0005 per share. Its other figures fall within $0.0012 per share and $0.008M; that is the rounding of the committed inputs, not something this refresh moved.
- **The full offline suite passed** (`bin/commit`) on the committed artifacts before the push.

**BOUNDARY.**
- **Roster:** `data/coverage_roster.jsonl` at `65a8b863`, the latest row per ticker: 11 active and 15 watch, 26 committed pages.
- **Code:** main `65a8b863`, 2026-11-19.
- **Inputs:**
  - the CIQ exports in the primary checkout as of 2026-11-19, read in place and never copied;
  - EDGAR companyfacts fetched 2026-11-19, cut at each page's price date (its reference date where it stores no close).
- **Count:**
  - Refreshed: 10 active pages (11 active less BRBR).
  - Moved: 8 pages. GOOGL's value is withheld; 7 keep every value.
  - Unchanged: 2 pages (NCNO, VITL).
  - Excluded: 1 page (BRBR).
  - Left as committed: 15 watch pages.
- **The split** is now on 7 pages (EPAM, IT, LLY, SMPL, TJX, VRRM, WERN), none of them stale; it was on 8 before (the same 7 plus GOOGL's refusal).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **GOOGL shows no screen value until a fresh CIQ export.** That is W62's intended outcome: a re-export moves CIQ's history to its export date.
- **BRBR still prices the median.** W50's current multiple is not on its page, and W62's corpus at `8ea51e99` found its 32-day CIQ close stale. Both rules reach it at A's rebuild, on its new CIQ export.
- **The 15 watch pages carry neither W62's verdict nor its row** until each is re-derived. The 11 carrying a multiple still price the median and say so in their own words (W50's record).
- **The known limitations of W62's record stand:** SMPL's 15-day ex-lease close against a moved price; `audit_r1`'s "incomplete anchor" wording; and the `headline_basis` date match (W63).
