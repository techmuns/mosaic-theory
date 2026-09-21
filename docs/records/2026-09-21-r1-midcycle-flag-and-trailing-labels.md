---
id:
status: open
date: 2026-09-21
prs: []
supersedes:
superseded-by:
---

# R1 now says when its mid-cycle assumption is stretched, and a trailing window stops calling itself a fiscal year

**WHAT.** Two changes to `vinci/dossier/anchor.py`, neither of which moves an anchor value.

1. **A mid-cycle flag.** R1 reverts the operating margin to its own history's median and re-rates
   it at the median multiple of the SAME history. When the last twelve months sit five or more
   points from that median, the anchor now carries `midcycle_gap`, and both renderers print one
   stored sentence under the screening table. The sentence states the two margins and their
   sources, offers both readings — structural (history misleads) and cyclical (reverting is right) —
   and never chooses between them. It does not touch `data_quality` or confidence: the data is
   right; it is the assumption that is stretched.
2. **Trailing-window labels.** companyfacts stamps each fact with the fiscal year of the FILING that
   carried it. Amazon's 10-Q carries a trailing-twelve-month cash-flow column, so its freshest
   ~365-day point (2025-07-01 → 2026-06-30, `fy=2026`) was labelled "latest FY2026 (not LTM)" —
   wrong twice, since FY2026 has not ended and a trailing window IS an LTM. Its D&A said "FY2026"
   the same way. Labels are now read from the point's own period and form.

**WHY.** Asked whether AMZN should be analysed on one lens, the answer leaned on R1's 5.3% median
margin against a 12.1% LTM. The anchor turned out to land at $245.46 against a $245.96 price — not
because it is right, but because a stale margin and a multiple earned on that same stale margin
offset. A number that coincides with the price for the wrong reason needs its assumption printed
beside it.

**HOW VERIFIED.** Every committed anchor recomputed through `compute_anchor`, old code and new, on
identical inputs: **no value moved on any of 22** (base value, EV/EBIT, margin, confidence, data
quality); **only AMZN's two labels changed.** The flag fires on 7 of 16 R1 anchors — AMZN +6.8,
GOOGL +6.8, LLY +19.9, NFLX +18.2, PARR +10.5 above; WLK −8.7, BRBR −5.7 below — and is silent on
the other nine. Preview rendered from committed JSON in both renderers, scanned for
`undefined`/`null`/`NaN`: none. Nine new pins, each red on the baseline; 12 mutations, 12 caught.

**THREE THINGS THE CORPUS CORRECTED BEFORE THIS SHIPPED.**
- **The two legs are different sources, and the first draft claimed otherwise.** The LTM is CIQ
  EBIT (excludes unusual items); R1's median is EDGAR GAAP operating income (includes them).
  Measured on the latest common fiscal year: median disagreement 1.2 points, but CNXC 15.5, WLK
  12.5, V 7.0, SMPL 5.8. The flag now REPORTS that same-year disagreement beside every gap — WLK's
  says "part of this gap may be basis, not business" — instead of assuming the legs agree.
- **LLY's median is already CIQ.** It tags no `OperatingIncomeLoss`, so R1 fell back to the
  committed panel; calling that median "EDGAR GAAP" would have stated a false provenance. The
  anchor passes which path it took as a structured flag, never parsed from the source string.
- **`direction` is a forbidden field name** (`test_dossier_schema_has_no_conclusion_field`). The
  field is `ltm_side`; the guard was not weakened.

**BOUNDARY.** 22 committed pages at `origin/main` 8f7bce7, EDGAR companyfacts as of 2026-09-21.
Threshold `MIDCYCLE_GAP_PTS = 5.0` (percentage points of operating margin, inclusive, decided on
the same 2-decimal rounding the flag stores); sources said to agree within `BASIS_AGREE_PTS = 2.0`.
Both set by face validity; neither read a forward return.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The committed pages do not carry the flag until their anchors
are recomputed — `anchor-backfill`, an artifact step, never bundled with this code. The one
string-parse of these labels (`audit_r1.py`, `"not LTM" in basis`) now correctly stops flagging
AMZN; it is pre-existing and left as it is.
