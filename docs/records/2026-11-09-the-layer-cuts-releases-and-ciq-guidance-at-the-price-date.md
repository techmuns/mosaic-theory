---
status: open
date: 2026-11-09
prs: []
supersedes:
superseded-by:
---

# STATE row 57: the fact layer cuts its releases and CIQ's guidance at the page's price date where it builds them, and states what it leaves out. The release half was already cut at fetch (#884) but silently; CIQ's half was not cut at all. A guide CIQ dates after the price date now withholds the whole guidance read, because CIQ overwrites each period's guide. $0: 1 of 28 frozen pages moves (ORKA, 4 fields); the panel's six requests are byte-identical, so the paid run is proposed on ORKA alone

**WHAT.**
- **One cut rule.** `vinci.edgar.asof.within_cut`: an input dated on or before the page's price
  date is read, and one dated after it is not. Every cut goes through it:
  - the EDGAR view (`AsOfEdgar`);
  - CIQ's guidance walk (`ciq_sheets._guidance_reads`);
  - the release list (`gaps.releases_by_cut`);
  - the gap test's two cuts (`gaps.releases_read`, `gaps._ciq`). These are #927's own cuts,
    reused, not rewritten.
- **Releases.** Since #884 (2026-11-03) an assembly reads EDGAR as it stood on the price date, so
  no release filed after it is fetched (`tests/test_asof_cut.py` already pinned this). The cut was
  silent, though: nothing named the results 8-Ks it left out.
  - `_primary_source` now lists those 8-Ks from the index as it stands now (`AsOfEdgar.uncut`).
    It reads the filing list only and never fetches an exhibit.
  - It writes them to `primary_source.releases_after_price_date`: filed date, `8-K <accession>`
    and item codes.
  - A caller holding an uncut client (the refresh's `basis_triangulation_transform`) meets those
    8-Ks in its own list. It skips them there and names them the same way.
- **CIQ's Guidance sheet.** No reader cut it.
  - **A guide dated after the price date withholds the whole read.** The bridge, its rows and the
    revenue guide the check reads all read UNKNOWN (`GUIDANCE_NOT_AT_CUT`). The gap test then has
    no second read (§3).
  - **An actual dated after the price date** (CIQ's "Actual/Latest Date", which no reader read
    before) leaves only the delivery record. The sheet is still read.
  - Every cell the cut leaves out goes to `catalyst_path.guidance_after_price_date`: metric,
    period, guide or actual, the cell verbatim, its date, and its address on the sheet
    (`source_ref`: row and column).
  - The synthesis never receives that field (`synthesis.NOT_SENT`).
- **The caveat.** `mechanical.after_price_date_flags` writes one human caveat per kind of input
  left out. It names each input and the JSON field that keeps it.
- **The refresh paths** that rebuild the release lines from today's CIQ export now read it at the
  page's own price date: `_rebuild_release_lines` and `basis_triangulation_transform`.
- **The harness.** `variants.asof_cut` (`ASOF_CUT`) cuts a committed layer by the same rule, for
  the $0 measurement and any paid one. It refuses wherever it cannot write what a builder at the
  cut would.
- **The extraction version** `2026-11-09.asof-cut` is declared (both twins), and the drift pins
  are re-pinned. The seven watched modules this change moves re-pinned, and no other.

**WHY.**
- The coordinator's review of #927 (F12) found ORKA's committed page holding a release filed
  2026-10-26 beside its 2026-10-23 price date. Every reader but the gap test read that release
  uncut.
- **What was believed before:** that the layer does not cut its releases (STATE row 57, as
  written). **That is true only of pages built before #884.** ORKA's page was assembled
  2026-10-26, eight days before #884 merged. On main, an assembly fetches no release filed after
  the price date, but it said nothing about the ones it skipped.
- CIQ's half was a real, live gap. The probe of the 28 frozen pages' own exports found two that
  carry Guidance cells dated after their page's price date (§2).

## 1. Why a guide after the cut withholds the whole read

CIQ keeps ONE guide per period, its latest. A guide revised after the price date has overwritten
the one that stood on it.
- **LLY's export** (on disk 2026-11-09): FY 2026's EPS guide is 35.00–36.00, dated 2026-10-29. The
  FY 2026 guides given before that date are gone.
- **Cutting that cell alone** at a 2026-10-16 price date (the LLY assembly harness) leaves FY
  2025's guide of 2025-10-30 as the row's "latest". On 2026-10-16 that was false.
- **Nothing on the sheet** tells a guide first given after the cut (UBER's FQ4 2026, 2026-11-04)
  from one that was revised. The sheet's other rows were checked: As-Of Guidance, Consensus,
  "Days before actual", and Actual/Latest with its date.

The options, and why the first ships:

| option | what a reader sees | why not |
|---|---|---|
| **withhold the whole read (shipped)** | bridge, rows and revenue guide UNKNOWN, saying why; the gap test has no second read | loses the guides on the same sheet that no later cell touches |
| cut cell by cell | the newest guide left, as "latest" | false on LLY: FY 2025's guide shown as the latest at 2026-10-16 |
| withhold only the affected metric's row | the other rows read | the gap test reads a missing row as "CIQ records none" and can reach "the company's normal practice" (`gaps._guide_gap` ladder rung 3). Avoiding that would patch a reader, which the brief rules out |

**An actual is exact to cut.** CIQ dates each period's one actual. So an outcome reported after the
price date leaves the record, and the guide above it is still read.

## 2. Measured at $0

### 2a. The 28 pages committed at the panel's freeze (`bcda7ce3`), through `variants.asof_cut`

- **Population:** 126 releases and 209 CIQ guidance rows.
- **Releases:** 1 release on 1 page is filed after its page's price date: ORKA's
  `8-K 0001213900-26-112281 EX-99.1`, filed 2026-10-26, price date 2026-10-23.
- **CIQ rows:** 0 of 209 are dated after their page's price date.
- **27 pages are left exactly as committed** (pinned per page).
- **ORKA moves in 4 fields.** Each value below is old → new. The page's price date is 2026-10-23.

| field | old | new |
|---|---|---|
| `primary_source.releases` | 4 releases, the newest filed 2026-10-26 | 3: filed 2026-08-10, 2026-04-30, 2026-04-27 |
| `primary_source.releases_after_price_date` | absent | `8-K 0001213900-26-112281 EX-99.1`, filed 2026-10-26 |
| `primary_source.current_guide.note` | "no guide in any of the 4 parsed release(s)" | "… of the 3 parsed release(s)" |
| `valuation.adjusted_eps.note` | "…the newest EX-99.1 release, 8-K 0001213900-26-112281 EX-99.1 (filed 2026-10-26), states no annual adjusted-EPS guide the parser reads" | "…8-K 0001213900-26-086933 EX-99.1 (filed 2026-08-10)…" |

- **No other field cites the dropped release**, which the transform checks.
- **The dropped release carries no parsed content** (no guide, reconciliation, one-off or event
  impact). So the triangulation, the guide check, the EBITDA reconciliation and the digest's
  release blocks cannot move. The transform refuses a release that does carry content.
- **The brief's three readers on ORKA:**
  - `adjusted_eps` and `current_guide` re-derive (above);
  - **the guidance bridge**: ORKA has no CIQ Guidance sheet, so it has no bridge.

### 2b. The synthesis request, compared at $0

- **How:** the frozen panel inputs, the CIQ root read-only from the primary checkout.
  - base: `origin/main` `622786a2`, through `replay.capture_at`;
  - cand: this tree in-process, through `replay.capture`;
  - draws=1.
- **The six panel pages:** byte-identical in every arm. That holds bare, with `asof_cut`, and with
  `FIX_3A`+`FIX_4A` at base against `ASOF_CUT`+`FIX_3A`+`FIX_4A` at cand.
- **Request sizes, base = cand** (total characters, bare / with 3a+4a): BURL 453,328 / 454,386,
  CNXC 365,910 / 366,839, LLY 648,169 / 649,734, MCK 484,601 / 486,456, ROST 459,748 / 461,376,
  SMPL 478,288 / 479,811.
- **So the harness cannot register this change on the panel.** RUNBOOKS §n: compare "refuses when
  no page's request differs".
- **ORKA, bare:** identical. The new schema fields reach no request: `NOT_SENT` excludes the CIQ
  one, and the release one sits inside the excluded `primary_source`.
- **ORKA, with `asof_cut`:** one USER line moves, the `adjusted_eps` note above. Its length is
  unchanged, so the total stays 222,591 → 222,591 characters and the digest is unchanged.
- **ORKA with `FIX_3A`:** refused by `survival_read` ("the net leverage is not present, so the
  survival line needs the CIQ net debt, which the layer does not carry"). That refusal predates
  this change.

### 2c. The builder at the cut, on real CIQ exports

**Source.** The primary checkout's `data/manual/ciq`, read-only, 2026-11-09. Each of the 28 frozen
pages is cut at its committed price date. 25 pages have a Guidance sheet on disk; AORT has no
export, and ORKA and TECX have no Guidance sheet.

- **23 of 25: the cut moves nothing.** On 18 of those, the export rebuilds the committed rows
  exactly.
- **2 of 25 hold cells dated after their page's price date.** Both exports are newer than their
  page.
  - **UBER** (price date 2026-10-23), 4 cells: the FQ4 2026 EPS Normalized guide 0.95–0.99 and
    EBITDA guide 3,130–3,230, and the FQ3 2026 actuals 0.88 and 2,963. All four are dated
    2026-11-04.
  - **NCNO** (price date 2026-08-17), 7 cells: 5 guides (Revenue FQ3/FY 2027, EBIT FQ3/FY 2027,
    FCF FY 2027) and 2 actuals (Revenue and EBIT FQ2 2027). All are dated 2026-08-25.
  - On both, the read is now UNKNOWN. Uncut, main would read the 2026-11-04 and 2026-08-25 guides
    as the latest.
- **The actuals rule, checked on UBER with one edit** (its two FQ4 guides removed):
  - today's export, cut at 2026-10-23, rebuilds the committed page's seven rows exactly; only
    CIQ's block order differs;
  - main reads EPS Normalized 3/3 with "FQ3 2026 MET", from results not yet out on the price date.
    The committed page reads 2/2.
- **Actuals on the 25 sheets:** 3,782 resolved periods (a guide and an actual). 0 have an undated
  actual, and 4 have an actual dated after the page's price date (UBER 2, NCNO 2).
- **LLY at the assembly harness's 2026-10-16 price date:** 5 cells are dated after it.
  - EPS Normalized FY 2026 guide (2026-10-29);
  - DPS FQ3 2026 actual (2026-10-29);
  - DPS FQ4 2026 guide (2026-10-26);
  - Revenue FY 2026 guide (2026-10-29);
  - Effective Tax Rate FY 2026 guide (2026-10-29).
  - Main's assembly reads 5 rows dated after the price date.
- **LLY at its own page's 2026-11-02 price date:** nothing is dated after it, and the rows equal
  the committed page's.

## 3. Pins

- **`tests/test_asof_cut.py`, through the whole assembly on LLY's real inputs.** Each fails on main
  `622786a2` by assertion, run there with this branch's test files.
  - **The 2026-10-29 results 8-K** (0000059478-26-000104) is named once, in a human caveat and in
    `releases_after_price_date` with items 2.02 and 9.01. None of it is fetched. *On main:* "assert
    0 == 1"; no caveat names it.
  - **LLY's own Guidance sheet** (cut-down fixture): no guidance reader takes the five cells, the
    bridge and rows read UNKNOWN, the caveat names each cell, and the synthesis facts carry none of
    them. *On main:* `('EPS Normalized', '2026-10-29')` plus 4 more rows dated after the price
    date.
- **`tests/test_layer_asof_cut.py`:**
  - the rule's boundary, where the price date itself is read;
  - the release cut on ORKA's four releases, cut on the day of the last (all kept) and the day
    before (that one leaves);
  - an undated release refused;
  - UBER's sheet: withheld at 2026-11-03, read at 2026-11-04 (the boundary), and the actuals rule
    with the page rebuilt;
  - LLY's sheet at its page's own price date, the page rebuilt;
  - the transform on the 28 pages: 27 identity, and ORKA's four fields exact, idempotent,
    nothing else moved;
  - ORKA's synthesis request free of the accession;
  - the transform's refusals: a late CIQ row, a late release with content, a late release cited
    elsewhere, an undated release;
  - its identity on code with no cut;
  - `NOT_SENT`;
  - the caveat: each input named, a guide versus an actual alone, partitioned as a human caveat;
  - the refresh reading CIQ at the page's price date.
- **More pins in `tests/test_asof_cut.py`:**
  - two stand-ins beside LLY's real 8-K (one carrying only 5.02 after the price date, one results
    8-K before it): only results 8-Ks after the price date are named, and the one before is read;
  - a view that lists filings made after the cut (the refresh's uncut client, played by a
    subclass): the 2026-10-29 8-K is still never fetched, and named once;
  - an uncut client reads the same ten 8-Ks as the cut view (review round 0, below).
- **The gap test's own pins** (`tests/test_gap_test.py`: ORKA and the SMPL edit) pass unchanged
  through the shared rule.
- **The fixture.** `tests/fixtures/ciq_guidance_asof_cut.json` holds UBER's (129 cells) and LLY's
  (435 cells) Guidance sheets, each named with its sha256 and cut by nulling (rows, then columns,
  then cells), keeping a null only when every pinned reading is unchanged. The cutter is in the
  session family's notes folder: `row57-asof-cut/cut_guidance_fixture.py`. These are CIQ-derived
  facts under the 2026-11-04 rulings (#891 fixtures; published-data conditions).

**DOES THIS SELECT ON FORM?** No. Every cut selects on a date the source states: the 8-K's filing
date, CIQ's Guidance Date, CIQ's Actual/Latest Date. It never selects on what kind of disclosure
the input is. What the withholding does select on is CIQ's storage form, one guide per period.
That is a property of the vendor, not of the company, and the caveat says so.

## 3a. Review round 0 (`/code-review high --fix`) and mutation

**What the review fixed.** The review ran in a fork and applied three fixes, each with a pin. Its
written report did not come back, so these are read from the edits it made.

| # | finding | disposition |
|---|---|---|
| R1 | `_primary_source` took the ten newest 8-Ks and then cut. An uncut client's 8-Ks filed after the cut took slots the cut view gives to earlier ones, so the refresh's rebuild read nine where the assembly reads ten | FIXED: `_events_by_cut` splits before the window; pin `test_an_uncut_client_reads_the_same_ten_8ks_as_the_cut_view` |
| R2 | `asof_cut` raised a bare ValueError on a CIQ row date that does not parse | FIXED: it raises TransformError; pin `test_the_transform_refuses_a_ciq_row_whose_date_does_not_parse` |
| R3 | `asof_cut`'s citation check matched the release's full source_ref only, so a field citing the 8-K by accession alone (dashed or not) passed | FIXED: matches by accession; pin `test_the_transform_refuses_a_late_release_cited_by_accession_alone` |
| R4 | a test name over the line limit | FIXED (renamed) |
| R6 | (found by the suite's guard, `test_extraction_version_drift`) seven watched modules moved with no extraction-version row | FIXED: row `2026-11-09.asof-cut` in `extraction_version.py` and `frontend/views/shared/dossier.js`; `--repin` moved exactly those seven |
| R5 | (found by the suite's guard, `test_footnote_every_figure`) the CIQ audit entries published CIQ-derived values with no source ref | FIXED: each entry carries its cell's sheet, row and column; the UBER pin reads each value back from that address |

**Mutation.** The mutants were run one at a time on this tree, against
`tests/test_layer_asof_cut.py`, `tests/test_asof_cut.py` and `tests/test_gap_test.py`, with `-x`.

- **First run, before round 0: 21 of 27 killed.** The six survivors:
  - the revenue guide read uncut;
  - the release list's own cut removed;
  - the transform's guide-line proof skipped;
  - the after-cut listing's date filter;
  - the after-cut listing's item-code filter;
  - the EDGAR view left uncut, which the release list's own cut masked.
- **One survivor exposed a vacuous pin.** The guide-check assertion looked for "91,000", but the
  line prints "91000.0". It now asserts the exact line.
- **Each survivor now has a pin.** The view mutant is caught through the 10-Q filed with LLY's
  8-K, which no reader may fetch.
- **Second run, after round 0: 31 of 31 killed.** That is the 27, with the window mutant
  re-pointed at `_events_by_cut`, plus four on round 0's fixes:
  - the window split keeping every 8-K;
  - the citation check by full source_ref only;
  - an unparseable CIQ date escaping;
  - the window split naming a non-results 8-K. This one survived first, and the leaky-client pin
    now carries a 5.02-only stand-in.

## 4. The paid measurement — PROPOSED, not run

Row 53's rule: every change that moves the synthesis request is measured before it ships, on the
operator's approval and cap.
- **The panel cannot be registered.** Its six requests are byte-identical (§2b), and the harness
  refuses identical requests rather than compare one prompt with itself.
- **The one page whose request moves is ORKA**, outside the panel and frozen in the panel file.
  - Its arms differ by one note string of equal length.
  - No target can fire, so the registration is no-worsening only.
- **Recommendation: no paid run.** The change is a point-in-time correction. On the frozen pages it
  reaches one request by one note, and on the panel it reaches none, so the draws would measure
  noise. If the operator wants row 53 applied literally, the design is below.

```
python -m vinci.evals budget-open --budget-ledger <notes>/ledger-row57.jsonl --cap 5 \
  --approval "<the operator's words>"
python -m vinci.evals register --base origin/main --cand <this PR's head> --ticker ORKA \
  --transform asof_cut --no-worsening \
  --ciq-root /Users/mac/Documents/GitHub/mosaic-theory/data/manual/ciq \
  --note "row 57: ORKA's adjusted_eps note names the 08-10 release, not the 10-26 one; no other byte moves; the panel's six requests are identical, so none is drawn" \
  --budget-ledger <notes>/ledger-row57.jsonl --out <notes>/registration-row57.json
python -m vinci.evals run-compare --registration <…> --budget-ledger <…> --out-dir <fresh> --paid
python -m vinci.evals score --out-dir <…> --registration <…> --budget-ledger <…>
```

- **Design:** ORKA, 5 draws per arm, **10 calls**.
- **Cost estimate:** **≈ $3.70**. This is a linear fit of #926's per-page ledger (10 calls per
  page, $4.55 at CNXC's 366,839 characters to $6.23 at LLY's 649,734), which holds to within $0.30
  on the other four panel pages, applied to ORKA's 222,591 characters.
- **Cap proposed: $5.**
- **Arms:** bare, without `FIX_3A`, because `survival_read` refuses ORKA (§2b).

**BOUNDARY.**
- **Pages:** the 28 committed at `bcda7ce3` (the panel's `freeze_ref`); the panel is v2.
- **Code:** this branch's tree, against `origin/main` at `622786a2`.
- **Counts:**
  - releases: `primary_source.releases` entries;
  - CIQ rows: `catalyst_path.guidance_bridge_rows` entries;
  - a "field that moves": a top-level field of `primary_source` or `valuation` whose value
    differs.
- **CIQ exports:** the primary checkout's `data/manual/ciq`, read-only, 2026-11-09. They are not
  the pages' own on 7 of 25: BURL, IT, NCNO, PARR, TGT, UBER, WLK.
- **Request sizes:** SYSTEM + the tool schema's JSON + USER characters, draws=1, the frozen
  transcripts.
- **Key Developments, below:** operating-driver rows whose source is CIQ Key Developments, dated
  by their period field.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A page built from an export newer than its price date loses all its CIQ guidance.** That
  includes the guides no later cell touched, and UBER's and NCNO's would read UNKNOWN today.
  - Accepted as fail-loud: the alternative prints a guide the market had not seen, or a stale one
    as the latest.
  - The remedy is an export dated by the price date, or a build at a later price date.
  - **Falsified as the right default** if an operator-supplied CIQ field shows which period cells
    are first guides. Per-metric withholding (§1) would then be safe.
- **One bit reaches the synthesis.** `GUIDANCE_NOT_AT_CUT` tells the model that the export holds
  guidance dated after the price date, but no value, date or count. Accepted: the read must say
  why it is UNKNOWN.
- **Found, not fixed (the brief's scope is releases and guide rows):**
  - **CIQ Key Developments** (`ciq_sheets.key_developments`, the operating drivers' A3 rows) are
    read uncut. On the 28 frozen pages, 0 of 1,139 KD rows post-date their page. On the on-disk
    exports, 6 of 1,066 do (NCNO 5, UBER 1).
  - **The other CIQ estimates reads** (revision events, consensus, the horizon and acceleration
    reads) were not probed.
  - **ORKA's committed page** keeps its late release until it is rebuilt (row 35 already asks for
    that re-assembly).
- **Refresh paths beyond the two named** read committed values, so they inherit whatever the page
  was built with.
