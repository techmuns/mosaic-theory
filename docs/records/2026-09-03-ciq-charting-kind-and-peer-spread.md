---
id:
status: shipped
date: 2026-09-03
prs: [586]
supersedes:
superseded-by:
---

# Charting was an unregistered kind; the peer spread widens against instruments, not against containment

**BOUNDARY.** Source: operator's `WST_Peers_Charting` export, 2026-09-03, 2,512 pricing dates
2016-09-06…2026-09-02, 11 forward-P/E series (WST + 10 peers). Read through the new sanctioned
reader. No raw CIQ committed. Split dates 2022/2023/2024 are **chosen**; all three reported.
Spread is **(WST / peer median − 1) × 100**, and the reported change is in points **of that
percentage** — not P/E points.

## The format was unregistered, so it would have been dropped silently

`charting` was in none of `_WORKBOOK_KEYWORDS`, so `CiqBundle.from_files` hit `kind is None` and
`continue`d — a charting export vanished with no message. Now registered, with
`vinci/dossier/ciq_charting.py` reading it.

The documented scan rule (`notes` lines 72, 361: scan column 0 for `Pricing Date`/`Date`) **returns
nothing on this file** — its header is row 35 labelled **`Dates`**. The label set was wider than the
notes recorded. The reader scans for all three and **fails loud** naming the label set if none match,
rather than hardcoding row 35.

## The sentinel is detected by SHAPE, never by value

Pre-listing cells carry a repeated constant — `42.0` here, which is also a perfectly plausible
forward P/E, and that is what makes it dangerous. Three conditions, each earned by a case that broke
an earlier cut:

1. the run **repeats** (`n ≥ 2`) — a first cut flagged Agilent's single leading `22.34` as a sentinel;
2. the value **never recurs** after the run — true of all three real cases, and what separates a
   sentinel from a genuinely repeated price;
3. the column **varies** afterwards — so a flat series is never deleted.

**Corpus check:** the reader reproduces the hand-rolled pass exactly — **3,674 cells across exactly 3
series**, first-real dates **AVTR 2019-06-11, STVN 2021-08-10, FTRE 2023-08-07**, all matching their
listing events. Every drop is counted and printed; `report()` is never silent.

*Median absorbed the sentinel here — naive and clean medians agree — but that is robustness luck, not
design. A mean would have been corrupted. The drop is unconditional.*

## Peer-set drift, reported both ways

Live peers go **7 → 10** across the window (2016: 7, 2021: 8, 2023: 9, 2026: 10), so the median's
constituents change. Both sets are reported:

| | 2022 | 2023 | 2024 |
|---|---|---|---|
| drifting set (all live) | +15.5 | +25.8 | +19.3 |
| fixed 7 (full history only) | +12.5 | +21.7 | +15.7 |

**Drift inflates the widening by roughly a fifth but does not create it.** The operator's figures
reproduce exactly on the drifting set.

## The comp-set validity question — and it changes the answer

The set is mostly CROs, sequencing and instruments. Split by business:

| subset | 2022 | 2023 | 2024 |
|---|---|---|---|
| instruments (A, BRKR, RVTY, WAT) | **+15.7** | **+23.7** | **+18.0** |
| CRO / sequencing (FTRE, CRL, MEDP, ILMN) | −5.3 | +11.6 | +7.0 |
| containment (STVN, AVTR) | −43.4 | −29.9 | −9.5 |

**CORRECTED BEFORE MERGE — "almost entirely instruments" was wrong, and the subset is not a stable
basis.** The CRO/sequencing figure depends entirely on whether Illumina is in it:

| CRO subset | 2022 | 2023 | 2024 |
|---|---|---|---|
| CRO only (FTRE, CRL, MEDP) | **+11.1** | **+30.4** | **+28.7** |
| + Illumina (as tabled above) | −5.3 | +11.6 | +7.0 |
| CRL, MEDP, ILMN (no Fortrea) | −17.9 | −8.8 | −16.3 |

**One member changes the sign.** On the CRO-only reading the widening is *larger* than against
instruments on two of three splits, so it is broad-based against 8 of 10 peers with containment the
lone exception — not an instruments artifact. That a three-to-four-name subset flips sign on one
constituent is itself the result: **the subset decomposition is too thin to arbitrate.**

**The containment −43.4 is an artifact, not evidence of narrowing.** Before 2021-08 that subset is
**Avantor alone** — a leveraged post-IPO name on a low multiple — so the pre-period is a WST-vs-AVTR
comparison. Verified by composition dump: 2020-06 and 2021-06 carry only Avantor.

## The cleanest containment read

WST against **STVN alone**, its single truest business peer, from STVN's listing (n=1,272,
2021-08-10…2026-09-02):

| | pre | post | change |
|---|---|---|---|
| 2023 split | +10.7% | +13.1% | **+2.4** |
| 2024 split | +9.3% | +20.0% | **+10.7** |

Current spread **+34.2%** against a **+12.2%** median over the whole window.

**So WST HAS widened against its truest peer — but only clearly on the 2024 split, and only over five
years.** The pre-2021 containment comparison cannot be made from this file at all.

### And STVN is not a control group

**Stevanato's own forward P/E went 33.1 → 36.7 post-2023, +10.9%** (n=1,272, verified on this file).
Stevanato makes vials and syringes for injectables — **it is a GLP-1 containment beneficiary too**.
"WST vs STVN" measures one exposed name against another, so a spread that stays flat is consistent
with both re-rating together, and a spread that widens says which re-rated more, not whether either
re-rated on the driver.

**FIVE BASES, FOUR ANSWERS:** the point-in-time snapshot says expensive (+48% to peers), own history
says mid-range (37th percentile), the full-set spread says re-rated, the containment subset says
cheap (an Avantor artifact), and STVN says expensive. That is not measurement error — **WST has no
clean comparator.** Instruments and CROs are different businesses that de-rated on biotech funding;
the only true containment peer carries the same driver.

**THE COMP-SPREAD TEST CANNOT ANSWER THIS, AND THE RESPONSE IS TO STOP RATHER THAN FIND A SIXTH
BASIS.** The premium question is settled properly at step 10 — scenario legs, reward at spot, the
ratified 2:1 test — which is the fund's own discipline and the only version that feeds a memo. The
shortlist needs names worth the effort, and WST clears on materiality at 18% of net sales.

## What this does to the premium half

- **Own history: WST is at the 37th percentile** and stable across all three splits — no re-rating.
- **Versus instruments: widened materially** — but that is not WST's business.
- **Versus STVN: widened recently**, and today's +34.2% is well above its own +12.2% norm.

The bound flagged in the previous record is **partly closed, not closed**: the peer test now exists,
but its answer depends entirely on which peers, and the only genuine business comparison starts in
2021. **The premium half on WST is not settled by this file** — the honest statement is that WST has
not re-rated on its own history, has widened against a cluster that does something else, and sits at
an unusually wide premium to the one peer that does what it does.

## Caution on the detector — verified on ONE format

The sentinel rule is **leading-run-specific and verified against a single file**. If CIQ uses the same
constant for MID-SERIES gaps — a delisting/relisting, a reporting change, a coverage suspension — the
run is not leading and this misses it entirely. Recorded as **verified-on-one-format, not general**.
Extending to mid-series gaps needs a second export exhibiting one; guessing the shape from this file
would be the same over-generalisation the rule was built to avoid.

## Still owed

Ticker-not-name-prefix matching for comp sheets, and the Financials↔Estimates reconciliation as a
failing assert rather than a script — it ran clean by hand (all four at 0.00%) but is not a guard.
