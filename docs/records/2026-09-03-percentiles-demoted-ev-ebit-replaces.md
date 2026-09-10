---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# The P/E percentiles are demoted to context — retroactively — and EV/NTM EBIT replaces them

**BOUNDARY.** Source: operator's CIQ exports read 2026-09-03 through `CiqBundle`. Multiple series =
`Financials→Multiples` Close, settled quarters, n=38, current excluded. Consensus drift =
`Estimates→Trends`. USD. No raw CIQ committed. 24-month anchors are the settled quarter nearest
730 days before the current close.

## The ruling, and it reaches backwards

GOOGL's memo records `CURRENT-vs-HISTORY BASIS MATCH: LIMITED` — the current Estimates P/E is
explicitly **normalized NTM EPS**, the historical Financials row is labelled only **`P/NTM EPS`**, and
the workbook does not establish they share a denominator. Therefore *"the P/E quartiles are valuation
context, not load-bearing evidence."*

**That is structural to the workbook, so it applies to all four names — and retroactively to every
percentile computed in this thread.** WST's 37th/40th, WAT's 63rd/66th, MCK's 95th and BDX's 13th were
context all along. They were reported here as reference distributions with the LIMITED caveat
attached, but the caveat was carried as a footnote while the numbers did the work. **Demoted
explicitly: none of them may anchor a multiple leg.**

## What replaces them — EV/NTM EBIT, the GOOGL cross-check

EBIT is a **reported line**, not a proprietary normalized figure, so this basis does not carry the
LIMITED problem. Same sheet, same Close convention, same 38 settled quarters:

| | n | min | P25 | med | P75 | max | current | rank | 24m ago | 24m change |
|---|---|---|---|---|---|---|---|---|---|---|
| WST | 38 | 20.6 | 26.7 | 33.1 | 36.0 | 49.4 | 30.9 | 42% | 35.5 | **−13.0%** |
| WAT | 38 | 16.7 | 18.8 | 20.3 | 24.0 | 28.8 | 22.7 | 68% | 24.5 | −7.2% |
| MCK | 38 | 8.2 | 9.3 | 11.1 | 13.1 | 16.4 | 16.2 | **95%** | 12.6 | **+28.6%** |

**It corroborates rather than overturns.** Ranks agree closely with the demoted P/E ranks (WST 42 vs
37, WAT 68 vs 63, MCK 95 vs 95), so the earlier readings were not misleading — they were merely not
admissible as evidence. Now there is a basis that is.

**An earlier draft of this record carried a caveat that ran the wrong way** — that EV includes net
debt so leverage moves the multiple. **EV/EBIT is capital-structure-NEUTRAL, and that is precisely why
it is the right replacement.** A buyback lowers market cap and raises net debt by roughly the same
amount, whether funded by cash or debt, leaving EV substantially unchanged; only proceeds *leaving the
firm* leak, which a buyback does not do.

That makes MCK's reading a confirmation rather than a caveat. A −46% share count mechanically pushes
a P/E multiple **down** — which is why its trailing `P/LTM EPS` sits at the 46th percentile — while
the capital-structure-neutral `EV/NTM EBIT` sits at the **95th**. The neutral measure says the
re-rating is genuine, and the EPS-based measure is the one distorted by the buyback, not the other way
round. Both forward measures agree at the 95th.

## The within-series evidence, which survives the ruling

A change measured **inside one row** is internally consistent regardless of what the row's denominator
is — the basis question cancels. Over 24 months, against consensus that rose:

| | P/NTM EPS 24m | EV/NTM EBIT 24m | FY27E consensus 18m |
|---|---|---|---|
| **WST** | **−18.4%** | **−13.0%** | **+24.2%** |
| WAT | — | −7.2% | +5.9% |
| MCK | — | +28.6% | +7.9% |

**WST took the earnings and the multiple compressed.** Earnings arriving without a re-rating is direct
evidence against a theme premium, and it holds on the basis that survives the ruling. That is the
answer five comp bases could not produce.

### Anchor sensitivity — the 18-month window flips sign

**Measured properly with a ±6-week anchor sweep, the 18-month window is unusable and the 24-month one
is sound:**

| window | clean sweep range | sign flips? |
|---|---|---|
| 18 months | **−24.7% to +20.1%** | **yes** |
| 24 months | **−21.1% to −6.8%** | **no** |

By window length the instability is visible: 12m +6.2%, 15m +12.2%, **18m −1.2%**, 21m −18.3%,
24m −20.8%. It only settles from 21 months, because the Dec-24 → Mar-25 quarter drop (45.90 → 36.51)
puts an 18-month anchor on the cliff edge. **Quote the 24-month figure with its sweep range attached;
drop the 18-month one entirely** — a single number there is an artifact of where the anchor landed.

### Six revision-lag artifact days, and one of them nearly shipped

The daily series carries **6 days out of 2,512 where price moved and consensus had not yet been cut**,
so the ratio is briefly meaningless: 2020-03-16, 2022-10-27, **2024-07-25**, 2024-10-24, 2025-02-13,
2025-07-24 — **every one an earnings date**. Each is a single day more than 8% from both neighbours in
opposite directions.

A first pass at the 24-month sweep anchored on 2024-07-25 (37.04 → **35.57** → 41.25) and reported a
range of −21.1% to **+3.8%**, i.e. a sign flip that does not exist. Cleaned, the range is −21.1% to
−6.8% and holds. **This is a general hazard for any daily-multiple work and a further argument for the
quarterly settled basis**, whose quarter-end closes are far less likely to land on an earnings day.

## Momentum is not dispersion — state which leg it sets

**+24.2% is directional momentum, not a dispersion estimate.** Momentum-derived widths are widest at
the top of a revision cycle, which is exactly where WST sits. Two uses, and they assume opposite
things:

- **Bull leg from the drift** — extrapolates the revision trend forward.
- **Symmetric ±24.2%** — assumes the drift fully reverses.

Neither is neutral, and the underwrite must **say which and why**. The same figure for BDX (−21.0%)
would set a bear leg by extrapolation or a bull leg by reversal, which is the tell that direction is
an assumption and not a property of the number.

## BDX — a screen finding worth keeping

**BDX drops. Three names: WST, WAT, MCK.**

Recorded as its own case, because it is the one the screen exists to catch: **the premium half was
satisfied and the materiality half never arrived.** BDX was cheap on every basis — 13th percentile,
−18% to peers — and its GLP-1 exposure was named in prose beside two names carrying figures. The
figure never came: its own transcripts give **agreement counts** (*"approximately 100 agreements
signed across novel and biosimilar GLP-1 programs"*) inside a segment that **declined 1%** then grew
5%. Meanwhile FY27 consensus was cut **16.82 → 13.29 (−21%)**, shares rose 27% and net debt 245%.

**The cheapness and the estimate collapse are one event.** A screen for materiality *without* premium
will always admit names that are cheap for reasons unrelated to the driver; the materiality prong is
what excludes them, and it only works if it requires a figure.

## Landed out of order

`#585` carried the 0.00% cross-source reconciliation, the split-date sensitivity and the MCK
mechanical check — and both `#586` and `#588` merged **on top of findings recorded in it** while it
sat open. The evidence was sound and nothing depended on the sequence, but the ledger now reads as
though the conclusions preceded their support. Noted so the order is not mistaken for provenance.
## Amendments

**2026-09-10 — the six artifact days were characterised wrongly three times. The DAY LIST is
right; the rule drawn from it was not.** Re-run against the same export through a symmetric
detector now shipped as `vinci.dossier.ciq_charting.find_spikes`.

- **"every one an earnings date" is WRONG and would encode a wrong rule.** **2020-03-16 is a false
  positive on cause**: all **9 series live that day fell more than 5%** (WST −10.7%, the peers −5.7%
  to −18.8%) — the COVID crash, market-wide, not a stale WST denominator. It is also not an earnings
  date. And the claim was never checkable from disk in the first place: the Key Developments export
  covers **2026 only** (179 of 196 year-mentions) and lists **no** 2020/2022/2024/2025 earnings date.
  It was inferred from the spike shape and written as if sourced. **SHAPE IS THE TELL, CAUSE IS THE
  PEER SET** — `Spike.market_wide` reports it, and `find_spikes` drops nothing, because dropping a
  day is a judgement about cause.
- **The detector must be SYMMETRIC or it misses a third of the class.** Four of the six are V's;
  **2024-10-24 (+13.1% / −10.4%) and 2025-07-24 (+14.2% / −8.0%) are inverted V's** — consensus cut
  first, price caught up after. Same lag, opposite order. Across all 11 series **45 spikes in 27,632
  cells**, of which **14 are inverted**: a V-only test silently returns 31.
- **The quoted triple for 2024-07-25 is wrong.** The body reads *"(37.04 → 35.57 → 41.25)"*.
  **37.04 is 2020-03-16's spike value**, transposed from the row above; the correct prior day is
  **40.58**, so the anchor's move in was −12.3%, not −4.0%.

**Unaffected:** the 24-month sweep range **−21.1% to −6.8%** and its conclusion that 24m holds while
18m flips, and the ruling that the **quarterly settled basis** is the one to use. Both stand — the
symmetric detector finds the same six WST days the original pass did.

**BOUNDARY.** Same export, same population: `WST_Peers_Charting`, Pane 1, 2,512 dates
(2016-09-06 → 2026-09-02) x 11 series, header row 35, 3,674 sentinel cells dropped. Spike test:
|move in| > 8% and |move out| > 8% with opposite signs. Peer test: >5% single-day move among series
carrying data that day. Measured 2026-09-10.

**2026-09-10 (second entry) — naming the class, because this is its second instance in eight days.**
*"Every one an earnings date"* was **inferred from the spike shape and written as though sourced.**
No date list was consulted; the only calendar on disk, WST's Key Developments export, covers 2026
alone (179 of 196 year-mentions) and lists no 2020, 2022, 2024 or 2025 earnings date, so the claim
was **unverifiable at the moment it was written**, not merely wrong.

**Same class as the fabricated PR number** (2026-09-03: work attributed to `#583`, which was a
different branch entirely). Both are a plausible detail generated to complete a sentence and then
stated with the confidence of a looked-up fact. Neither is a reasoning error — the surrounding
analysis was right both times — which is what makes the class hard to catch by reading. **The tell
is the SHAPE OF THE SENTENCE, not its content: a specific, checkable particular that no tool call in
the transcript produced.** CLAUDE.md already forbids asserting absence off one search; this is its
mirror — asserting PRESENCE off none.

**2026-09-10 (third entry) — the table is right and the sentence under it reads two windows as one.**
The columns are labelled **`P/NTM EPS 24m`** and **`FY27E consensus 18m`**; the sentence beneath them,
*"WST took the earnings and the multiple compressed,"* reads them as ONE co-movement. They are not.

Re-run at this record's own ±6-week sweep, the six artifact days dropped: **12m +6.2% · 15m +11.5% ·
18m −0.1% · 21m −18.3% · 24m −18.4%**, sweeps reproducing this record exactly (18m −24.7% to +20.1%,
24m −21.1% to −6.8%). **Over the MATCHED 18-month window — the only one both series support, because
`Trends` carries vintages no further — the multiple is ~FLAT and sign-unstable.** The compression is a
**21-month-and-longer** phenomenon. *(This record's 18m point reads −1.2%; −0.1% here is the same
measurement with the six revision-lag days removed.)*

**So the compression and the +24.2% revision are SEQUENTIAL, not simultaneous** — the multiple
compressed in the window 24-to-roughly-19 months ago, and over the most recent 18 months, during which
consensus rose 24.2%, it has been flat. **Each fact survives alone; the conjunction does not.**
What this record concluded from it — that earnings arrived without a re-rating, and that WST's premium
is not a theme premium — is UNAFFECTED: that argument needs the 24-month compression and the direction
of revisions, not a shared window. What changes is the reading of the CURRENT regime, and therefore
what an underwrite's legs may claim. See `docs/records/2026-09-10-base-gets-its-own-mechanism.md`.
