---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# Ranked on earnings instead of revenue, WST and MCK swap places — and MCK's issuer says so itself

**WHAT.** The shortlist's materiality prong never said materiality **of what**. MCK entered on
**$15bn of quarterly GLP-1 revenue**, WST on **10% of sales**; on revenue MCK leads by 40%. On
earnings the order inverts, and not by estimate — **McKesson states the decoupling on its own
calls, in both directions.**

Both quarters end **30 June 2026**, so this is one window, not two.

## MCK — a revenue figure its own issuer says does not translate

`McKesson Corporation, Q4 2026 Earnings Call, May 07, 2026`, GLP-1 revenue **down** 4% sequentially:

> *"…volumes
> **had no impact on operating profit in the quarter**."*

`Q1 2027 Earnings Call, Aug 05, 2026`, GLP-1 revenue **up** 24% year-over-year — and the segment's
profit growth is attributed to everything else:

> *"Segment operating profit increased 19%… specialty
> distribution… health systems and strategic accounts…"*

**GLP-1 is not among the drivers named.** Down 4% moves nothing; up 24% is credited elsewhere.
Two quarters, opposite directions, same answer.

**And the company gives the structural reason:**

> *"revenues from branded pharmaceuticals reflect the WAC… **…compensated for the fair value…**."*

Fee-for-service, not a share of price. A $15bn revenue line at a WAC that can move without the fee
moving is exactly a figure that does not carry to earnings.

| MCK, Q1 FY2027 | |
|---|---|
| GLP-1 distribution revenue | **$15.0bn** (+24% YoY, +13% seq) |
| share of consolidated revenue ($105.4bn) | **14.2%** |
| share of North American Pharmaceutical revenue ($86.8bn) | 17.3% |
| consolidated GROSS margin ($3.7bn / $105.4bn) | **3.51%** |
| segment OPERATING margin ($894m / $86.8bn) | **1.03%** |

14.2% is the gross-profit share GLP-1 would carry **if it earned the company average**. It is an
upper bound that cannot bind: the fee structure puts branded distribution below the blend, and the
issuer's own statement puts the operating-profit sensitivity at nothing detectable.

## WST — a smaller revenue share sitting at the highest-margin point

`West Pharmaceutical Services, Inc., Q2 2026 Earnings Call, Jul 23, 2026`:

| WST, Q2 CY2026 | |
|---|---|
| revenue | **$872m** |
| gross margin | **37.7%** (+200 bps YoY) — ~$329m |
| adjusted operating margin | 22.6% (+230 bps) — ~$197m |
| HVP Components | **$424m = 48.6% of revenue**, +18.4% organic |
| GLP-1 (10% of total company sales) | ~$87m |

GLP-1 sits **inside** HVP Components, and the mix shift toward that line is stated to be what raises
company margin:

> *"…gross margin was 37.7% in the quarter, up 200 basis points…
> driven by better-than-expected sales… **positive mix shift to HVP Components**."*
> *"…HVP Components… **the incremental margins there are
> just quite nice**."*

If shifting mix toward HVP Components raises the 37.7% blend, HVP Components' margin **exceeds** the
blend. **So GLP-1's share of WST's gross profit is bounded BELOW by its 10% revenue share** — the
direction is disclosed even though the level is not.

## The ranking, and what it rests on

| | revenue exposure | earnings exposure |
|---|---|---|
| **MCK** | **14.2%** of consolidated revenue | ≤14.2% of gross profit as an upper bound that cannot bind; **operating-profit sensitivity stated as none** |
| **WST** | 10% of total company sales | **>10% of gross profit**, bounded below by the disclosed direction of the mix effect |

**The bounds cross.** WST's earnings exposure is bounded below at 10%; MCK's is bounded above at
14.2% by an assumption its issuer contradicts. Neither company discloses GLP-1 gross or operating
profit, so **this is a ranking with stated bounds, not a computed share** — and the ranking is the
question that was asked.

**This is a UNIT failure, and it completes the set.** BDX, WAT and WST each broke on **population**
— a figure quoted against a base it was not measured on. MCK's $15bn is correctly scoped and
correctly sourced; what it never stated is **which unit the materiality prong wants**, revenue
dollars or earnings dollars. Four names, four `BOUNDARY` fields, and between them the shortlist
failed on two of the four.

## What this does NOT do

It does not gate MCK out. A distributor with 17% of segment revenue in a category is exposed to that
category's **volume** even where the fee per unit is fixed, and the Jan-2027 WAC reset is a live
question about that fee. **What it does is move the burden**: MCK's case can no longer rest on
$15bn, because $15bn is the number its issuer has twice declined to connect to profit. It has to
rest on the fee economics, and those are not disclosed.

**BOUNDARY.** Source: operator's CIQ exports, `manual/ciq/`, read 2026-09-10 via
`vinci.dossier.ciq.read_text`. MCK figures from the Q1 FY2027 call (quarter ended 2026-06-30) with
the sequential-decline quote from the Q4 FY2026 call (quarter ended 2026-03-31); segment = North
American Pharmaceutical. WST figures from the Q2 CY2026 call (quarter ended 2026-06-30); the 10%
GLP-1 share is the Q1 CY2026 call's figure, stated there as *"consistent with the previous quarter"*
and not restated in Q2. USD, reported basis, non-GAAP where the company reports non-GAAP (WST's
operating margin is adjusted; its gross margin is not). No raw CIQ committed.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The WST lower bound uses the DIRECTION of a mix effect, not a
disclosed segment margin — West does not publish HVP Components' own margin, so ">10%" is sound and
"how much more" is unknown. MCK's *"no impact on operating profit"* is a statement about **one
quarter's sequential move**, not a general zero-sensitivity claim; it is corroborated by the Q1 FY27
attribution and by the 1.03% segment margin, and it is used here as directional evidence, not as a
measured elasticity. **Falsifier: either company disclosing GLP-1 gross or operating profit**, at
which point this ranking is replaced by arithmetic.

## Amendments

**2026-11-13 — REDACTION: 12 spans cut to “…”**, under the operator's ruling of 2026-11-12, verbatim
"Cut all 21 + guard (Recommended)", whose option read: "One $0 PR. Each run is cut to 12 words or
fewer. Each record gets a dated redaction amendment naming count, position and hash only, as #1036
did. A local-only test scans every tracked file against the transcripts on disk, and skips in CI
where they are absent."

CLAUDE.md's rule, since 2026-11-10: no public field quotes more than 12 consecutive transcript
words, and this repo is public. This record was written before the rule, and 6 of its quotations
shared more consecutive words with the call they cite. Each is cut in place to 12 words or fewer,
keeping the words that carry the figure or the claim this record relies on; nothing else in it
moved, and nothing was reworded. Each run is named below by the line it starts on and the line(s)
its cut spans sit on, in the record as merged; by its length and the words kept; by the call it
shares them with and where it starts in that call; and by the sha256 of its words: never by the
words. A word is counted as the guard counts it
(`tests/test_tracked_files_hold_no_transcript_run.py`): split at whitespace, every dash form and a
slash, lower-cased, edge punctuation off, apostrophes folded. The hash is of those words joined by
single spaces, its first 16 hex digits. Git history keeps the old text, as the operator accepted; no
history is rewritten.

| run starts on line | cut on line(s) | words → kept | call | starts at word | run sha256 |
|---|---|---|---|---|---|
| 21 | 23 | 26 → 12 | `McKesson Corporation, Q4 2026 Earnings Call, May 07, 2026` | 3,105 | `a1a111ccaf919173` |
| 29 | 29–31 | 27 → 12 | `McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` | 3,156 | `948f5eb4141526d2` |
| 38 | 38–40 | 40 → 12 | `McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` | 3,041 | `9c6c385ee53f1c28` |
| 72 | 72 | 16 → 11 | `West Pharmaceutical Services, Inc., Q2 2026 Earnings Call, Jul 23, 2026` | 1,977 | `66ae5b4b482af204` |
| 72 | 72–73 | 16 → 12 | `West Pharmaceutical Services, Inc., Q2 2026 Earnings Call, Jul 23, 2026` | 1,999 | `8998e5cb6d798e99` |
| 74 | 74 | 17 → 10 | `West Pharmaceutical Services, Inc., Q2 2026 Earnings Call, Jul 23, 2026` | 4,924 | `cc04553ccaf7ccfe` |
