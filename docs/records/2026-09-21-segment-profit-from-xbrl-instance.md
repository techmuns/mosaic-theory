---
id:
status: shipped
date: 2026-09-21
prs: [637]
supersedes:
superseded-by:
---

# Segment profit reaches every multi-segment page, read from the 10-K's own XBRL instance — the R-file route found it for one

**WHAT.** `vinci/edgar/segment_facts.py` reads each segment's profit, on the filer's OWN measure, from
the latest 10-K's XBRL instance, and assembly carries it as `concentration.segment_profit`: structured
rows (segment, member, profit, revenue from the identical context), the named measure, the
reconciliation to the filer's own totals, and one sentence both renderers print. A single-segment
filer carries nothing — the field is absent, the page draws no line, and no committed page grows a key.

**WHY.** Asked whether AMZN should be analysed like GOOGL or MSFT, the answer turned on where each
company's profit sits — and the machine could not say. MC2's extractor (`vinci/edgar/segments.py`,
#578) existed but was deliberately never wired, and measured on the ten multi-segment names in the
book it could not have been: its title-based pick of the SEC's RENDERED segment table found the right
table for ONE (GOOGL), refused six, and **silently returned the wrong table for three** — WERN's and
VRRM's COUNTRY revenue and WLK's reconciliation-to-pretax lines, each labelled as segment economics.
The rendered table is the filer's layout: segments as rows at some filers, as COLUMNS at others. The
instance is the structured source, where every figure carries its segment as a dimension.

**HOW VERIFIED.** Real run through `mechanical._segment_profit` on all 22 committed pages: **10
multi-segment, every one reconciling to the filer's own total; 12 single-segment; 0 refused.**

| filer | measure | segments sum | the filer's own total |
|---|---|--:|--:|
| AMZN | operating income | 79,975 | 79,975 consolidated |
| GOOGL | operating income | 145,799 | 129,039 consolidated (−16,760 reconciling items, as #578 pinned) |
| IT | gross profit (its "gross contribution") | 4,468.2 | 4,468.2 consolidated |
| EPAM | `epam:SegmentOperatingProfitLoss` | 855.1 | 855.1 segments total |
| AORT | gross profit | 284.2 | 284.2 consolidated |
| UBER | its segment Adjusted EBITDA | 11,438 | 11,438 segments total |
| WERN / WLK / VRRM | operating income | 23.1 / −1,513 / 415.9 | = segments total |
| PARR | operating income | 659.3 | 538.8 consolidated (corporate) |

Nine fixtures, each a real 10-K instance trimmed to the facts the rules read and proven, when frozen,
to read identically to the full filing. 14 pins; **13 mutations, 13 caught.**

**THE CORPUS CORRECTED THE DESIGN FOUR TIMES** before it shipped.
- **EPAM's segments are geographies** — tagged on the geographical axis beside the operating-segments
  qualifier. A business-axis-only rule read its revenue and never its profit.
- **"Any axis beside the qualifier" read TECX's five expense lines as five segments.** It itemises its
  ONE segment's costs on the income-statement-location axis. Only the geographical axis is accepted.
- **Seven single-segment filers tag their one segment** (ASU 2023-07) — LLY, NFLX, CNXC, NCNO, VITL,
  FUBO, TECX. Read as multi-segment, seven pages would have said their segment profit could not be
  found. One segment member or none is now a single-segment filer.
- **Alphabet states each segment twice** — income on {segment, operating-segments}, revenue on
  {segment}. The revenue fallback strips that qualifier on the BUSINESS axis only: on a geographical
  axis the bare context is revenue by customer location, a different number.

**BOUNDARY.** 22 committed pages at `origin/main` 8f7bce7; each page's latest 10-K as of 2026-09-21
(all FY2025). Unit: USD, converted to $M; a non-USD measure is refused. Fiscal year = the duration of
350–380 days ending at the instance's `dei:DocumentPeriodEndDate`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Two branches have **no live witness on the fleet** and are pinned
on real filings with a fact added at an existing value, never an invented magnitude: the measure order
(no filer tags both operating income and gross profit on its segments) and the consolidation guard
(eliminations carry revenue only, and the identical-context join already keeps them out). The page
carries the filer's ELEMENT name for a filer-defined measure, not its label — the label linkbase is
not read. Pages carry the field only once re-assembled; there is no backfill writer for concentration.

**REPORTED, NOT FIXED.** `vinci/edgar/segments.py::segment_rows` still silently returns the wrong table
for WERN, VRRM and WLK. It is unwired — only its own tests call it, and `_pick_report` is shared with
the commissioning route — so it harms nothing today; it should be deleted or its selection replaced,
separately.
