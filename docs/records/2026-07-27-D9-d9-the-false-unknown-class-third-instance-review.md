---
id: D9
status: recorded
date: 2026-07-27
prs: [282]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D9. THE FALSE-UNKNOWN CLASS, THIRD INSTANCE** (review finding on #282, recorded at the operator's
direction). `DilutedOutstanding.is_zero_dilution` tested the increment alone, so a REFUSED pair
whose increment was a small negative — an inverted tagging error of −0.5 shares — answered **True**:
"the filer reports no dilution, checked" over a pair the module had just refused to use. Same shape
as the covenant line and as item 18's hardcoded UNKNOWN: **a derived answer that speaks for a result
which does not exist.** Now gated on `shares is None`. The generalisable tell is that the property
read one field of a NamedTuple whose OTHER field carries the refusal — a partial read of a
partially-valid record. Pinned by `test_zero_dilution_is_false_on_a_refused_result`.

*(scheduling superseded by D19.)* **D10. FUBO DOES NOT CLOSE FOR FREE — the selector is right and the SOURCE is missing** (the cheap
read, 2026-07-31). The tie-break fix does not touch `shares_out`: that path is
`_edgar_shares_outstanding` → `latest_instant(extract_points(facts, "shares"))`, a DIFFERENT
selector, and cover-page counts are **instants** — there is no quarter-vs-cumulative ambiguity to
break. The real cause is upstream of any selection: **EDGAR's companyfacts for CIK 0001484769 has
no `dei:EntityCommonStockSharesOutstanding` point after 2025-07-31**, while the same blob carries
us-gaap facts filed as recently as **2026-06-16**. The company kept filing; the dei fact stopped
appearing. So it still needs the queued 10-Q cover-page read — now evidenced on both sides, with
CIQ's 29.4M confirmed right and ours confirmed wrong. **The overlay cannot fix it either**: its
`basic_out` leg is that same stale fact.
