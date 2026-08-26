---
id: D9
status: recorded
date: 2026-07-27
prs: [282]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: UNKNOWN — not recoverable from the header or git; do not read as fact
---

**D9. THE FALSE-UNKNOWN CLASS, THIRD INSTANCE** (review finding on #282, recorded at the operator's
direction). `DilutedOutstanding.is_zero_dilution` tested the increment alone, so a REFUSED pair
whose increment was a small negative — an inverted tagging error of −0.5 shares — answered **True**:
"the filer reports no dilution, checked" over a pair the module had just refused to use. Same shape
as the covenant line and as item 18's hardcoded UNKNOWN: **a derived answer that speaks for a result
which does not exist.** Now gated on `shares is None`. The generalisable tell is that the property
read one field of a NamedTuple whose OTHER field carries the refusal — a partial read of a
partially-valid record. Pinned by `test_zero_dilution_is_false_on_a_refused_result`.
