---
id: 2026-10-19-net-debt-one-builder
status: recorded
date: 2026-10-19
prs: [749]
supersedes:
superseded-by:
---

# Net debt is read by ONE builder, every balance-sheet line at ONE date, for the screen and the anchor alike

**WHAT.** STATE §5.0 row 27 (1): "the screen's EDGAR snapshot (`client.compute_fundamental_snapshot`)
still nets cash only, and feeds `mechanical`'s forward-adjusted net debt". Operator, 2026-10-19:
"start row 27 (1) but first diagnose it deeply and a scalable expert solution across multiple
sectors and names". The diagnosis found the cash leg was the smaller defect. The fix is a builder,
`vinci/edgar/net_debt.py`, that both the snapshot and the anchor (`anchor._lease_inclusive_net_debt`)
now read.

**THE DIAGNOSIS.** Measured over the 1,694 universe names with cached companyfacts.
- **Two formulas for one quantity.** The snapshot and the anchor each built net debt by hand. They
  disagreed by ≥0.25x EBITDA on 121 names beyond the operating leases that separate them on
  purpose, and on the sign of net debt for 49.
- **Every leg was read at its OWN latest date. This is the largest defect, and the anchor shared it.**
  - 314 names had a long-term-debt leg older than their own balance sheet; 99 of them more than
    400 days old and worth ≥0.25x EBITDA.
  - A filer that moved its debt to a tag outside the two-alias list kept its last value under the
    old one. LUMN read $31.5bn from 2021 beside a 2026-06-30 balance sheet carrying $13.2bn.
    NSIT read $94M from 2015 against $1,469M today.
  - Filers that repaid debt still carried it: KLIC's 2012 notes, TECX's $15M from 2023 (CIQ shows
    no debt).
  - Current-debt legs: 251 names more than 400 days old.
- **The row's own item.** Short-term securities were not netted on 249 names, 70 of them by
  ≥0.25x EBITDA, mostly technology and health care.
- **Total + current double count** (the anchor already guarded it; the snapshot did not): 118
  names, 15 by ≥0.25x.
- **Finance leases missing from the snapshot**: 382 names, 45 by ≥0.25x (CZR $13.1bn).
- **Restricted cash in the fallback cash tag**: 104 names, none ≥0.25x. Measured on
  `RestrictedCashCurrent` only; immaterial, not changed.
- **Banks, lenders, insurers.** 279 financials. The snapshot produced a "net debt" for 145, which is
  not a leverage measure for them.

**THE DESIGN** (each rule measured on the corpus; the module doc carries the cases).
- **One date.** Debt, borrowings, cash and securities are face lines, read at the cash instant or
  not at all. Leases are often an annual note line (BRBR, TGT). They are read as the filer's own
  total at that date, else each part within 400 days of it, else as absent.
- **The debt line.**
  - The larger of the bare `LongTermDebt` tag and noncurrent + current (OC: $899M of maturing notes
    under `SeniorNotesCurrent`).
  - Beside a same-date current tag with no noncurrent tag, the bare tag IS the noncurrent line
    (AAL; 4 of 4 where a total settles it).
  - Short-term borrowings are added unless they are the current maturities tagged twice (ATEC,
    VGNT), the maturities inside the bare total (UBER), or inside the filer's own total (CSIQ).
  - The filer's current-debt total (`DebtCurrent`), where reported, sets them.
  - The debt-and-finance-lease family is read where no debt-only line exists (LUMN, TGT, BURL,
    PPC), with its finance leases not added again.
- **Two named bases.** LEVERAGE = borrowings + finance leases − cash − short-term investments; the
  snapshot's ratios read it, and so does the anchor wherever R1 prices #750's ex-lease history.
  EV = LEVERAGE + operating leases, the CIQ TEV ruler; the anchor reads it where rent is
  immaterial. Under ASC 842 EBITDA is post-rent, so a ratio over it leaves operating leases out. A
  bridge to CIQ's own multiple history keeps them, as CIQ's total debt does (PARR to the dollar).
- **Fail loud.**
  - A debt line absent at the date from a filer that used the standard tags before is REFUSED,
    never zero. Of 195 such names, about 110 still show debt elsewhere (another tag at the date, or
    material interest expense: AN pays $180M), so zero would invent net cash.
  - The under-capture witness now judges each unread instrument against what the reading can hold.
    It may sit inside long-term debt or the filer's current total, be a balance already read, or be
    the whole reading's total (NFLX `NotesPayable`). It may NOT sit inside one short-term borrowing
    line: CIQ counts MVST's subordinated notes beside its bank borrowings.
  - The filer's own total debt (`DebtLongtermAndShorttermCombinedAmount`) is an arbiter and a
    witness, never the line itself. MVST's $118.6M is its bank borrowings only; read as the line it
    would put MVST at +$8M against CIQ's +$65M. RYZ's $955M refuses a $2.6M reading.
- **Banks (60), lenders (61), insurers (63) by SIC: not applicable.** Applied on the screen record's
  two ratios and on `mechanical`'s route A. The test is SIC, not a deposits line: MTN's "deposits"
  are season-pass prepayments. Brokers and asset managers (62) and insurance brokers (64) keep the
  ratio.

**DOES THIS SELECT ON FORM?** No. No gate, rank or threshold reads these figures: `net_leverage` and
`net_debt_to_ocf` are page context and a dossier fallback, and the anchor bridges a multiple chosen
elsewhere. The refusals decide whether a figure is SHOWN, never how a name is judged. The SIC rule
keys on what the balance sheet IS, not on how it is disclosed.

**HOW VERIFIED.**
- **Against CIQ, the independent source.** CIQ's Total Debt − Total Cash & ST Investments, read
  2026-10-19 from this machine's workbooks, against the anchor's EV basis (old reading on main
  c4ebdc37 → new). Names where CIQ shares EDGAR's balance-sheet date:
  - **Within $15M of CIQ, 13 names:** BRBR (−8), BURL (0; was +136), EPAM, GOOGL, HLF (+3), NFLX
    (−15; was refused), PARR, PENG (0; was +3), ROST, SMPL, TJX, WERN (−1; was +8), WLK. This
    is the live-cache run. The pin (`test_the_anchor_reads_ciqs_net_debt_on_every_shared_date`)
    checks the 13 names in the frozen CIQ fixture, which has no TJX workbook date match and
    includes TGT, at a wider tolerance of max($15M, 1% of CIQ's total debt).
  - **Closer, not there:**
    - TGT −135 (was +1,019).
    - UBER +222 (was −1,775); the remainder is its finance leases. Its page's CIQ Net Debt
      ($4,744M) is a different CIQ field, which nets long-term securities: row 27 (2).
    - AMZN −8,544 (was −9,640): row 27 (2).
  - **Refused, as before:** FUBO and MVST under-captured; ORKA no debt line. **Newly refused:**
    TECX, whose phantom 2023 debt was the old reading.
- **Against the filers' own totals.** On the 94 names reporting `DebtLongtermAndShorttermCombinedAmount`
  at the date, the debt line read matches it (within 2%) on 63, against 45 before.
  - 24 that read wrong before are now refused.
  - 2 that read right before are not now: SCHL reads $75M against $80M, and GATX is refused
    (no standard debt line at the date; its $12,333M total is a witness, never the line).
  - 5 are off both before and after (BKSY, ITRI, MGNI within 3%; RITM and RZLV).
- **The corpus, old → new** (1,694 names):
  - 854 known → known, of which 163 moved ≥0.25x EBITDA. Largest: LUMN 29,636 → 11,330; NCLH
    1,334 → 14,817; NJR 408 → 3,669; TROX 2,732 → 3,036.
  - 22 sign flips, each checked: stale legs dropped (NSIT, VECO), securities netted (ENPH, NVAX),
    borrowings read (HOG).
  - 187 known → UNKNOWN (126 "no debt line on the balance sheet", the rest under-captured).
  - 20 UNKNOWN → known.
  - 253 now not applicable (SIC 60/61/63).
- **Pins** (`tests/test_net_debt_one_builder.py`, 44, on frozen real data):
  - the CIQ agreement above, on frozen CIQ scalars (`tests/fixtures/ciq_net_debt_one_builder.json`);
  - the moved names closer than before;
  - the page field (`compute_anchor`);
  - screen = anchor − operating leases to the dollar, on every committed fixture;
  - one pin per debt-line rule, on ten shape fixtures (`tests/fixtures/net_debt_shapes/`, from the
    cache via `scripts/build_companyfacts_fixture.py --net-debt-shapes`);
  - the witness, leases and their bound (FLR's 2019 leases not read), and the SIC rule on both
    consumers, with negatives;
  - an instrumented check that every tag the builder requests is frozen in the fixtures.
  - The committed companyfacts fixtures gained the builder's tags, merged at each fixture's own
    filing vintage: 120 tags, no existing tag changed (checked).
- **Existing pins updated, with reasons in place.**
  - The securities-leg tests point at the helpers' new module.
  - `test_net_debt_undercaptured_fails_loud` now names the convertible: the borrowings are read,
    so the convertible is what proves under-capture.
  - The double-count pin now expects MVST refused: its total stopped at 2025-12-31.
  - `ANCHORS_AWAITING_BACKFILL = {BURL, TGT, WERN}`.
- **Mutation.** 23 mutants, all killed: the one-date read, every debt-line rule, the double-tag
  and arbiter guards, the lease total and bound, the stale refusal, the three witness rules, both
  bases on both consumers, the ratio's reason, the SIC rule (both directions) on both consumers,
  and `READ_TAGS`.
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved aside.
  The local venv was aligned with CI first: `pdfplumber` (declared) installed, and `types-openpyxl`
  (undeclared) removed.

**BOUNDARY.**
- Corpus: the 2026-10-16 universe snapshot's 2,065 names, of which 1,694 have cached companyfacts
  (fetched 2026-08-06 to 2026-10-18).
- Committed fixtures at their own vintages.
- CIQ: this machine's workbooks, read 2026-10-19.
- Materiality: |Δ| over operating income + D&A, latest fiscal year, positive EBITDA only.
- Code measured on this branch over main c4ebdc37.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The committed pages are NOT changed here.**
  - BURL, TGT and WERN's anchor base values move +1.16%, +1.84% and +0.46%; the pin holds them in
    `ANCHORS_AWAITING_BACKFILL` for the artifact pass.
  - Fields the pin cannot see also move: AMZN's net debt (+1,096; base −0.04%), UBER's (7,565 →
    9,562), NFLX's (UNKNOWN → 7,512), TECX's (−208 → refused; the CIQ vendor fill takes it).
  - VRRM's route-A "net debt / FY26 adj-EBITDA" (985 → 980), and every page's EV-bridge
    `edgar_net_debt`.
  - The screen's candidate records change at the next weekly run.
- **Recall is traded for honesty.** 187 names lose a figure. Most are a debt line no longer on the
  balance sheet; some are genuinely debt-free (KLIC). A corroborated-zero rule (no debt tag at the
  date, no witness, no interest expense) could recover them, and the 202 that never tagged debt.
  It is a new inference and is NOT built here. Falsifier: a debt-free name refused here whose CIQ
  total debt is only leases.
- **Seen, not changed:**
  - **A bank inside a non-financial SIC.** WEX (7389) owns a bank; the $4,940M of securities now
    netted back its deposits. Its covenant leverage excludes the bank; the SIC rule does not reach
    it.
  - **The page's CIQ-primary "Net debt / EBITDA" is lease-inclusive over post-rent EBITDA.** That
    is CIQ's own construction, and it overstates leverage on lease-heavy names: BURL's 3.8x is
    mostly its $4bn of operating leases. A consistent row (CIQ net debt less its operating leases)
    is a page decision for the operator, not made here.
  - **Row 27 (2)'s debt-side gaps** (AMZN, UBER's long-term securities) are smaller but remain.

## REBASED ONTO #750 AND #751 (2026-10-20)

Operator, 2026-10-20: "the code is merged to main by the other session, check and rebase your code
to latest main and if there's any change we need to revert on our end?"

**WHAT #750 CHANGED THAT THIS TOUCHES.** R1 now prices lease-material names (rent ≥5% of EBITDA)
on the ex-lease history and bridges them with net debt EXCLUDING operating leases
(`docs/records/2026-10-19-r1-prices-on-one-lease-basis.md`). It did so by adding
`ex_operating_leases=` to `anchor._lease_inclusive_net_debt`, the function this PR rewrote.

**RESOLVED, NOTHING REVERTED.**
- #750's interface is kept as it merged: the `ex_operating_leases` option, its "operating leases X
  EXCLUDED" bridge wording, the public `lease_inclusive_net_debt` for the EV-bridge cross-check,
  and the vendor-fill refusal on the ex-lease path.
- Only the reading under it changed. The ex-lease bridge is the builder's LEVERAGE basis (#750's
  definition: operating leases out, finance leases in); the default is EV.
- One #750 pin imported `anchor._sum_latest_tags`, which this PR retires. It now takes the
  operating leases from the builder, the same reading both bridges are built from, and its
  assertion ("the bridge drops the leases, only") is unchanged. All 48 of #750's lease-basis pins
  pass.
- This PR's BURL page pin read the live page's state. It now sets and removes the lease basis
  explicitly (#750's convention), pinning both bridges: EV $5,202.4M, and ex-lease = LEVERAGE,
  exactly $3,993M of operating leases less, printed as EXCLUDED.

**THE TWO CHANGES TOGETHER, MEASURED.** R1 with the frozen lease basis set, on the same inputs
(this branch's pages and fixtures), main's net-debt reading → the builder:
- TJX: ex-lease net debt −3,133 → −3,133, base $129.10 → $129.10. Identical; #750's own figure.
- BURL: 1,346 → 1,210, base $319.93 → $322.06 (+0.7%). Main still served its stale
  `LongTermDebt`; the builder reads its debt-and-finance-lease line.
- TGT: 11,100 → 9,946, base $155.94 → $158.47 (+1.6%), for the same reason.
- VITL, LLY: identical. UBER: 7,565 → 9,562 on the lease-inclusive basis, no base value either
  way.
- #750's "not covered" note on NFLX (CIQ's net debt not offered on the ex-lease path) no longer
  bites: NFLX's EDGAR net debt now reads (7,512), so no vendor fill is needed.

**ONE ARTIFACT PASS, NOT TWO.** Both PRs leave the committed pages for an artifact pass, and they
move the same retail anchors. The lease-basis refresh then the anchor backfill, run once after
this merges, lands BURL and TGT on their ex-lease values. The +1.16% / +1.84% above are the
no-lease-basis figures. STATE row 27 carries this as items (1) and (4) sharing one pass.

**VERIFIED.**
- Full suite on the rebased branch: 6,004 passed, 525 skipped.
- Mutation: 24 mutants, all killed. The two anchor-basis mutants now target the merged line: the
  ex-lease bridge reading EV, and the default reading LEVERAGE.

**BOUNDARY.** Rebased onto main 618f07e5 (#750 4bba300c, #751). Interaction measured on this
branch's committed pages and fixtures, 2026-10-20.

## CODE REVIEW FIXES (code review of #749, high, 2026-10-20)

Ten findings: seven fixed, one fixed differently, two not changed after measuring.
- **Fixed — `DebtCurrent` can carry the current finance leases.** They were added again as finance
  leases. Measured: 1 of the 12 names that read `DebtCurrent` beside current finance leases. GPK's
  $552M = $533M maturities + $12M borrowings + $7M current finance leases, now $7M lower ($5,599M →
  $5,592M net debt). Stripped only where the excess over maturities is exactly borrowings + those
  leases (WS-shaped totals keep their borrowings). Pinned on GPK, with the negative.
- **Fixed — the stale refusal named a $0 line.** KLIC's refusal cited "`DebtCurrent` $0M at
  2012-09-29". It now names the latest NONZERO standard tag: "`LongTermDebt` $109M at 2012-03-31",
  the balance the old reading carried.
- **Fixed — the witness parsed raw JSON**, a second parser of the same values. It reads through
  the builder's own dollar reader now. Doing so surfaced a real defect: **every leg must be read
  in USD.**
  - Cash and the lease fallback read any unit, while debt read dollars.
  - LPL (won) and HSAI (yuan) netted dollar debt against foreign figures: LPL read 3.26 trillion
    "dollars" of net debt.
  - Every leg now goes through one USD reader. LPL reads its dollar figures ($2,802M); HSAI its
    20-F convenience translation (−$576M); LAES moves $0.2M.
  - Pinned on every fixture: no read point is in another unit.
- **Fixed — the refusal kind was a string sentinel.** `NetDebt.nothing_to_read` now carries it,
  for the snapshot and the anchor alike.
- **Fixed — no glossary line** for "one builder / LEVERAGE basis / EV basis"; added to
  `docs/engineering.md` §House vocabulary.
- **Fixed — this record's CIQ list** did not match the pin's population (above).
- **Fixed differently — the sector rule lives at the consumers.** It stays there, because a
  snapshot-level rule would need SIC in a pure facts function and in every test fake. Instead a
  scan pins it: every `vinci/` function that calls `fundamental_snapshot` must call
  `not_applicable`, so a third consumer cannot forget it.
- **Not changed — the bare-tag-beside-current rule ignores the filer's total.**
  - An arbiter check was written and then removed, because it moves nothing.
  - Measured: no corpus name reports a total equal to the bare tag alone in this shape.
  - The 8 unsettled names have no total to consult.
  - Under "don't build speculatively" it waits for a real case.
- **Not changed — borrowings beside a bare total with no arbiter are still added.**
  - Measured: 11 non-financial names have this shape.
  - The one a total can settle (ETSY: $2,336M + $650M = its $2,986M) has them outside.
  - The others are separate revolver or note lines (AKR, GT, LW, CXT).
  - The inside case (CSIQ) is settled by its own total already.
- **Skipped — the builder runs once per consumer per page.** A few dozen tag lookups each,
  milliseconds. Not worth a cache.

**Corpus effect of the fixes** (1,694 names, old → new): 4 values move (GPK, LPL, HSAI, LAES) and
37 refusal notes are reworded (the nonzero stale tag). No other figure changes.

**Seen, not changed:** the builder has no bound on how OLD the balance sheet is. LPL's latest
us-gaap cash is 2009-12-31, because it moved to IFRS tags. Its net debt reads that date's balance
sheet, stamped with its 2010 filing date, as before this PR.

**Verified.** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved aside, 6,007 passed / 525 skipped. Mutation 30/30 killed, the six new mutants included: no finance-lease strip, a $0 stale line, legs in any unit, cash in any unit, `nothing_to_read` without the witness, and route A without the sector rule. Three shape fixtures were added (GPK, LPL, HSAI).

