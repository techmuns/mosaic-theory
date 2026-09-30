---
id: 2026-09-30-six-pages-onto-the-forward-multiples
status: shipped
date: 2026-09-30
prs: [663]
supersedes:
superseded-by:
---

# Six pages onto the forward multiples, and the normalized-EPS row changes basis mid-row

**WHAT.** ROST, TGT, NFLX, NKE, LLY and AMZN re-assembled onto #659/#660/#661 (`323f52b6`), one
name at a time, `1 done · 0 error(s)` each. Artifacts only. Every one of the six gains the four
forward-multiple rows; the fleet's forward coverage goes from 1 name (BURL) to 7.

**WHAT MOVED.** Measured against each name's own 2026-09-28 assembly, same 2026-09-22 as-of:

    name  lean                before -> after          draws before -> after      fwd
    ROST  strongly-bullish -> strongly-bullish         3/2 split -> 4/1 split      0 -> 4
    TGT   mixed            -> mixed                    5/5 unanimous -> unchanged  0 -> 4
    NFLX  strongly-bullish -> strongly-bullish         3/2 split -> 4/1 split      0 -> 4
    NKE   mixed            -> mixed                    4 of 5 COMPLETED -> 5 of 5  0 -> 4
    LLY   strongly-bullish -> strongly-bullish         5/5 unanimous -> unchanged  0 -> 4
    AMZN  strongly-bullish -> strongly-bullish         3/2 SPLIT -> 5/5 UNANIMOUS  0 -> 4

**NO LEAN CHANGED, on six names, re-drawn.** Worth stating because the immediately preceding
name did move: BURL went strongly-bullish → mixed on identical data (#662), and three of these six
were sitting 3/2, one draw from a flip. They held. That is one observation of the gate's variance,
not a rate.

**AMZN CROSSED THE GATE.** It was 3/2 split and is now 5/5, so its machine proposal is no longer
withheld — it is SEALED (available to `dossier --show-proposal`, absent from the page so it cannot
anchor). ROST and NFLX remain withheld at 4/1. The gate's whole purpose is that this is a property
of the build, not of the name.

**THE ROWS REACHED THE REASONING, NOT JUST THE LAYOUT.** AMZN's synthesis now argues a bear point
off them directly: *"NTM P/E is 26.73x vs peer median 16.92x and P/FY27E normalized EPS is 24.6x,
so the trailing 19.8x understates what the market pays on forward earnings"* — the exact failure
the BURL underwrite made, now caught inside the dossier.

## THE FINDING: `EPS (Normalized)` IS NOT ONE BASIS ACROSS ITS OWN ROW

Surfaced by putting the forward multiples on the decision surface, and **pre-existing** — the
committed pre-run pages carry byte-identical EPS rows, and re-deriving from the workbooks
reproduces them exactly, so this is CIQ's panel faithfully extracted, not a mis-mapping here.

In the LTM (actual) column normalized EPS strips one-offs and sits BELOW GAAP. In the estimate
columns it converges to the GAAP consensus. Measured across all seven names now carrying forward
multiples, `EPS (Normalized) ÷ EPS (GAAP, dil.)`:

    name  LTM (actual)    estimate columns
    AMZN  0.44            1.00, 0.99
    TGT   0.71            0.99, 1.01
    ROST  0.76            0.97, 1.00
    NFLX  0.63            1.00, 1.00
    LLY   0.93            1.04, 1.06
    BURL  0.80            1.03, 1.02
    NKE   (no LTM col)    1.01, 1.05

**6 of 6 LTM columns below 1.0 (0.44–0.93); 13 of 13 estimate columns at 0.97–1.06.** The row
changes basis at the actual/estimate boundary and says so nowhere.

**WHAT IT DOES AND DOES NOT BREAK.** It does NOT corrupt the forward multiples: each is price ÷ an
ESTIMATE-column EPS, and within the estimate columns the two bases agree to ≤6%. It DOES corrupt
any growth read ACROSS the boundary. AMZN is the extreme — LTM 5.44 → FY26E 12.87 reads as +137%,
and a large part of that is the basis moving from 0.44× GAAP to 1.00× GAAP, not earnings. The
`EPS (Normalized)` row is printed whole in the Financial-Summary appendix, so a reader — or the
synthesis — can take that difference for growth.

**A SECOND, SEPARATE ODDITY IN THE SAME COLUMN, and it is CIQ's own:** AMZN's FY26E net income
$140,097M EXCEEDS its FY26E EBIT $109,863M with no gain modeled in that column, while FY27E is
ordinary (NI $114,993M < EBIT $140,131M). Our extraction reproduces the workbook byte-for-byte.
Recorded as observed, not diagnosed — it is the likely cause of the FY26E EPS step, and settling
it needs the workbook's own basis notes, not more code.

**NOT FIXED HERE, DELIBERATELY.** Scope was a re-assembly. Naming the basis on the row, or dropping
the redundant normalized estimate rows (they differ from GAAP by ≤6% while the label promises a
distinction), is a render decision with its own measurement — opened in STATE §5.0 rather than
taken in an artifact pass.

**HOW VERIFIED.**

*The runs.* Six sequential `dossier --ticker`, each `1 done · 0 error(s)`, exit 0, 18:36–19:19 IST.
All four chains confirmed present on the tree before the first run.

*The gate.* ruff clean · `mypy --strict vinci` clean (154 files) · `pytest -m "not network"` exit 0
on the freshly-committed artifacts.

*The basis measurement* is re-derived from the CIQ workbooks through `financial_summary_annual`,
not read off the rendered tables, so it tests the extractor's output rather than the page's.

**BOUNDARY.** Measured 2026-09-30 off `323f52b6`. Six names re-assembled; the basis table covers
**seven** (the six plus BURL, already on this work) — every committed name that carries forward
multiples, which is the whole population of names with a CIQ estimates workbook loaded, not the
26-name fleet. Unit: fiscal-year columns of `financial_summary_annual`. NKE has no LTM column in
its export, so its actual-column ratio is absent rather than zero. All multiples struck on the
2026-09-22 close, 8 days before the build — every page carries `PRICE STALE AT ASSEMBLY`, as its
predecessor did, so the before/after comparison is like-for-like.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **Six syntheses are fully rewritten for names whose facts did not change.** Inherent to a full
  assembly. The leans did not move; the prose did.
- **`P/FY..E (normalized)` and `P/FY..E (GAAP)` are near-duplicates** (≤6% apart on all seven
  names) while the labels promise a real distinction. Shipped as-is; the alternative is a render
  change in an artifact pass.
- **AMZN's CIQ bundle lacks the Credit Health Panel** (10 files against 11 elsewhere) — pre-existing;
  its credit fields stay UNKNOWN rather than wrong.
- **Prices are 8 days stale on all six.** A `vinci refresh` would move every multiple; not run, so
  that the comparison against 2026-09-28 is like-for-like.
- **Nothing CI-validated** — the `gate` workflow has been failing on Actions billing since #652.
