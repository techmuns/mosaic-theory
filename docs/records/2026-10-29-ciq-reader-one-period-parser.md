---
id: 2026-10-29-ciq-reader-one-period-parser
status: shipped
date: 2026-10-29
prs: [861]
supersedes:
superseded-by:
---

# The CIQ reader reads a period from its header once, names the export each bridged figure came from, reads every guided block and the listing's own rating, and refuses a Financials export whose name and statements disagree (audit A-D3, A-X2, A-D6, A-D8, A-D10, A-X1, A-D11, A-D14)

**WHAT.**
- **One period parser** (`ciq_sheets.header_period`, audit A-D3 and A-X2). Every Financials
  period header is read once into kind, fiscal quarter, end date and fiscal year. The labels,
  same-quarter matches and fiscal years all come from it.
  - CIQ's `FQ4/CQ2` quarters are quarters. Before, `_fin_short` and `_quarter_token` matched only a
    bare `Q4`, so they were labelled `FY26` and their year-on-year growth was dropped.
  - A quarter carries its fiscal year. A January filer's quarter ending Apr-30-2025 reads `Q1-26`,
    not `Q1-25`. A 4-4-5 quarter ending Apr-04-2026 still reads `Q1-26`, because an end date in a
    month's first half is named for the month before it.
  - A fiscal-year column keeps the calendar year of its end, as before. The nominal month only places
    a quarter: a 53-week year ending Jan-01 still reads as the year it ends in, which
    `statement_recon`'s same-label drop rule relies on. Read that way, a 52/53-week December filer's
    Q4 ending in early January takes the earlier year while its annual column takes the later one.
    No export in the corpus has such an end; this is recorded, not fixed.
  - `ciq_balance.header_period` reads through it, and so does `_short_period`. `_quarter_token` is
    gone.
- **A YoY reads only the prior fiscal year's quarter.** This was found while fixing A-D3; it is not
  an audit ID. `_quarterly_revenue_yoy` took the nearest earlier same-quarter column on the same
  basis. Where the prior year's quarter was reclassified, it reached two to four years back under a
  "YoY" label. Six exports read this way on main, five of them committed pages (AORT +50.7% against
  Q1 2022, CNXC, EPAM, PARR, WERN; HLF has no page). Reading FQ/CQ quarters would have added BRBR
  and BDX. A prior-year quarter on another basis now gives no YoY line, which is the function's own
  stated contract. The quarterly table's YoY row checks the fiscal year too.
- **Each bridged fact names its own export** (`CiqFact.workbooks`, `CiqFacts.stamp`, audit A-D6).
  The bridge used to stamp every fact with the quarterly workbook. Now:
  - D&A, OCF, capex and revenue name the ANNUAL export they are read from;
  - the balance-sheet facts name the quarterly one;
  - a net debt built from both names both.
  The anchor prints each input's own stamp. GOOGL's D&A and IT's FCF named the wrong file.
  `tests/fixtures/anchor_ciq_bridge.json` had baked the wrong stamp in; it is corrected, re-derived
  from the same workbooks with every value unchanged.
- **Guidance blocks are found by structure** (`_guidance_starts`, audit A-D8). A block is a label
  row over CIQ's `As Of Guidance` row. `_GUIDANCE_METRICS` is gone.
  - A label repeated under a second listing is read once, at its first block, as the label search
    did.
  - The revenue guide is still exactly the `Revenue` block.
  - A metric `_GUIDANCE_HIGHER_IS_DELIVERY` does not name shows its guide with no MET/MISSED
    record.
- **The recommendation is the listing's own** (`_listing_rating`, audit A-D10). It is read from
  Trends' non-periodic block headed with this ticker. The rating counts run only from that block's
  `Recommendation` row to the first non-category row. Where the section holds no block for the ticker,
  both lines say so and name the blocks it holds, never dropped unremarked (round 1). On the real
  run that case occurs on 0 of the 32 readable names.
- **A mislabelled Financials export is refused** (`CiqMislabelledError`, a `CiqAmbiguousError`;
  audit A-X1). The refusal fires when the filename's `_Annual`/`_Quarterly` token disagrees with
  the period type that ALL THREE statements state.
  - One statement disagreeing with the other two states nothing. This is AORT's recorded empty
    Income Statement, which read Annual.
  - A side sheet does not speak for the export. FUBO's annual export carries a Capital Structure
    Details sheet reading Quarterly.
  - A 'No Data Available' shell states nothing, and neither does an empty cell or a value other
    than annual/quarterly. `ciq.is_no_data_shell` is now the one reader of that sentinel;
    `ciq_sheets._no_data_available` calls it.
- **A lone export never answers for the other period type** (audit A-D11). It still answers when
  its period type is unread, which is the scope the 2026-10-11 record gave. The annual balance
  sheet's serial header prints as a date, not `[46203.0]`.
- **`read_sheets` releases each workbook** (deferred from #853): xlrd's map and openpyxl's zip.
- **Six extraction-version rows, one per output change** (audit A-D14; the Phase 1 id convention
  `<date>.<audit id>`, coordinator 2026-10-29): `2026-10-29.A-D14` names the 45 extraction-area
  commits since `2026-10-09.3` that appended no row; then `.A-D3`, `.A-D6`, `.A-D8`, `.A-D10` and
  `.A-X1`, the last of which is the stamp. Each row also sits in the web twin in
  `frontend/views/shared/dossier.js`, which `test_parity_pins` binds.
- **26b ships** as `tests/test_extraction_version_drift.py`.
  - It pins a hash of each module that can change a dossier: 48 of them, every module in
    vinci/dossier and vinci/edgar except seven excluded with a stated reason, plus
    vinci/verbatim.py and vinci/finra.py.
  - The hash reads code tokens only; comments, blank lines and docstrings do not count.
  - **The rule:** a moved, new or removed watched module is refused while the version table holds no
    row it did not hold when the pins were taken (`PINNED_TABLE`, a digest of the sorted row ids).
    Keying on the row SET, not the last row, is what lets parallel PRs merge in either order. A
    batch that adds its own row with its change never reds, whether it merges before or after
    another; this was simulated on the four sibling branches (#857–#860) in both orders, with no
    re-pin.
  - **Re-pinning is one command:** `python -m tests.test_extraction_version_drift --repin`
    (`WATCHED`, `PINNED_TABLE`, `PINNED_AT`). On a conflict in that file, take either side and
    re-run it.
  - **Merging the table itself:** each row is its own `(` … `),` block. A line-wise union fuses two
    rows into one element; the module's comment and the test's failure message both say so.

**WHY.** All eight are wrong values on committed pages, or the provenance of them. The audit's
classes: RC2, a period read by regex; RC4, kind from the filename; RC6, provenance; RC7, a
whitelist. A-D11's design note scoped the lone-export choice to an UNREAD period type, but the code
served one that read the other type.

**HOW VERIFIED.**
- **Failing first.** Every new pin was run against main `c51c286a` in a scratch worktree. All the
  defect pins fail there. The negative pins pass there:
  - AORT's and FUBO's shapes are not refused;
  - an unread lone export still answers;
  - December quarters, 4-4-5 quarters and fiscal-year labels are unchanged.
- **Mutation.** Each fix, and each review fix, was reverted in turn; every mutant turned the pins
  red (the list is in the PR).
- **#853's pins.** Its four B4 strict xfails (A-D3 ×2, A-D11, A-X1) are now passes with their
  markers removed. Eleven remain for later batches: A-D2 ×8, A-D4, A-D5 and the `.xlsx` currency
  pin.
- **Real run.** Every CIQ reader was run over the corpus with main's code and with this branch's,
  read only, and the reads were diffed. Results:
  - LLY and MCK are refused whole. LLY's Quarterly and MCK's Annual are each byte-identical to the
    other file of their pair.
  - On the other 32 names, every bridged fact's value, period, check, failure and scale outcome is
    identical; only the export each names moves.
  - Every multiple, band, net debt, EBITDA and FCF reader is unchanged.
  - What moved, of the 32: the recommendation on all 32 (24 changed, 8 newly shown); the rating
    counts on 24 (the industry's counts, and other listings', dropped); quarterly labels and YoY
    on 12; the trajectory's YoY line on 12 (6 FQ/CQ names gain one; AORT, CNXC, EPAM, HLF, PARR
    and WERN lose a two-to-four-year one); the balance-sheet posture label on 12; guidance on 10
    (14 blocks; with MCK's 3, the audit's 17 across 11).
- **The licensed tests.** The test files that read the workbooks were run against the same corpus
  on main and on this branch, from a scratch directory, so tests opening repo files by relative path
  fail identically on both.
  - 25 fail on this branch only. Every one is the A-X1 refusal of the `-ta` copy's LLY pair, met by
    tests that iterate every folder or are parametrised on LLY.
  - None fails only on main.
  - In the primary checkout, LLY's Drive re-export clears its cases. MCK's identical pair (on Drive
    too) will fail the folder-iterating tests until it is re-pulled.

**BOUNDARY.**
- "The corpus" means the 34 non-test ticker folders of `mosaic-theory-ta/data/manual/ciq` as read
  on 2026-10-29, with the one held test-pack folder there skipped.
- "Pages" means the 26 non-test committed `data/dossiers/*/dossier.json` at `c51c286a`.
- Readers were called at reference date 2026-10-29.
- "45 commits" means the commits touching vinci/dossier, vinci/edgar or vinci/ciq in
  `544af3ae..c51c286a`.
- "20 pages" means the committed pages whose `consensus_context.revision_history` prints a
  Recommendation (`c51c286a`).
- "Six exports" means those whose trajectory printed a "YoY" more than one year apart, on main
  `c51c286a`, over the corpus.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No page is re-assembled here.** The combined Phase 1 rebuild lands these on the pages. Until
  then the committed pages carry the old reads: 20 recommendations, 6 FY-labelled quarterly tables,
  GOOGL's and IT's stamps, LLY's 8 serials, and the stamps `2026-10-09.3` / `2026-08-16.1`.
- **LLY cannot be rebuilt until its re-export reaches the copy the assembler reads.** The re-export
  was made on 10-28/29; the `-ta` copy still holds the identical pair. MCK cannot be assembled until
  its Annual export is re-pulled (row 32 item (12)).
- **These are decision-path inputs.** The recommendation, rating counts, guidance, quarterly table
  and trajectory all enter the synthesis prompt, so a lean (and the machine proposal) may move at
  the rebuild. No anchor, R1 input or multiple moves on a readable name.
- **ACCEPTED: discovered guidance metrics carry no delivery direction until one is decided.** Those
  are same-store sales, EBT, net debt, maintenance capex, LT growth, CFPS and EPS excl. GW; they
  show a guide with no record. Deciding them is face-validity work, a follow-up. Falsifier: a
  reader takes a missing record for a missed one.
- **ACCEPTED: 26b reds a pure refactor of a watched module until it is re-pinned.** That is the
  spec's stated cost.
- **ACCEPTED RISK: the row-set rule loosens 26b, and its procedure is part of the rule**
  (coordinator review of #861, 2026-10-29).
  - **What it is:** once the version table holds a row the pins do not know, any further move of a
    watched module passes until the next `--repin`. After two batches each add a row, the pins
    reflect neither tree, and an unrelated refactor merged in that window goes unseen.
  - **The cheap fix is not available:** a strict pin (a move reds unless the pins are current) reds
    main whenever a batch merges on a CI run that predates another batch's merge. `gate` is
    required but not strict.
  - **The procedure:**
    - a PR that adds a version row runs `--repin` in its final commit, and again in the merge of
      main that lands it;
    - while the pins are stale, `test_stale_pins_are_said` warns in every CI log, naming the rows
      the pins do not know.
  - **Falsifier:** a watched-module change merged with no row while the pins were stale. It shows
    as a `--repin` that moves a module no row since the last re-pin names.
