---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

22. **AT-A-GLANCE v2 — the current-state block FOLDED INTO the masthead (2026-07-27).** The
   operator challenged the duplicate block, then challenged the first proposal against buy-side
   structure. Both challenges were right, and v1 was wrong in two STRUCTURAL ways:
   (a) it added a 6th stat cell — but `.uw-statband` is `repeat(5, 1fr)`, so the 6th does not
   wrap, it drops Method to a ragged one-cell second row; going to six shrinks every cell to
   ~173px while the 22px mono lead value alone needs ~150px, so the dominant number would wrap.
   (b) it mismatched WEIGHT TO FACT-CLASS: a **date** rendered at `.uw-stat-val`'s 16.5px mono
   carries a valuation number's authority, and a 13-word prose caption at 13.5px sat between the
   title and the numbers — the scan zone. **`.uw-mast-foot` (11.2px, ink-3) already existed for
   exactly this class of fact and the first proposal invented a new slot instead of using it.**
   SHIPPED (v2, zero CSS change to the band): holding label + status caption join the chip cluster
   beside the rating (11.2px caption, matching `.uw-stat-sub`); the 2:1 ceiling qualifies the
   Reward:risk cell in ITS sub-line; next-evidence + underwritten date go to the mast-foot; base
   normal margin is DROPPED (the legs table carries it); the separate block is deleted from both
   compositions — the masthead now carries it, so the card and the dossier agree by construction
   rather than by duplication. LESSON: propose placement only after reading the type scale — the
   component's contract is data, not taste.
