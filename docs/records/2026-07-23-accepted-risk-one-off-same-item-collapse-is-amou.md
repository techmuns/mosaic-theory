---
id: 
status: accepted-risk
date: 2026-07-23
prs: [196]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ACCEPTED RISK — one-off same-item collapse is amount-blind (2026-07-23, PR #196 review).**
`_one_offs`' identical-item collapse keeps the FIRST of two mentions sharing a byte-identical
captured phrase (SMPL's OWYN integration expense, $3.9M quarter / $6.5M YTD, worded identically →
one row, the quarter). Adversarial review found it can't distinguish that same-item-two-scopes case
from two GENUINELY DIFFERENT charges worded byte-identically (differing only in amount, no scope or
qualifier text) — e.g. a constructed "$5.0M of transaction costs … $20.0M of transaction costs" →
`[5.0]`, the $20.0M silently dropped. SMPL's real text carries NO QTD/YTD scope words ("…in the
current year period" on both), so the two cases are structurally identical to the parser — no local
signal separates them, and "keep both" would re-introduce the SMPL duplicate the operator flagged.
Kept as-is (optimizes for the observed case). **Falsifier:** a real dossier whose one-off driver
omits a materially different, identically-worded charge → then add scope-word detection or a
keep-both-and-flag path. Not shipped: a machine guard (no sound local discriminator exists). Two
MINOR review findings fixed instead: the caveat collapse is now LOSSLESS on differing why/how
(per-claim render, both twins, pinned `test_caveat_group_block_is_lossless_when_why_or_how_differ`),
and the JS render twins (catalyst reword, EBITDA casing, collapse) gained the web-e2e pins they
lacked.
