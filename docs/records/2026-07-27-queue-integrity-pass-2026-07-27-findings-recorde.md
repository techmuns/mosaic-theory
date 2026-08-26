---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**QUEUE-INTEGRITY PASS — 2026-07-27 (findings recorded, not silently fixed).** Every PR reference
inside this block was checked against the GitHub API: **#187, #194, #205, #209, #213, #215 verified
merged**; **#210 verified CLOSED-UNMERGED** — STATE credited it with the first dated trigger, but
GitHub auto-closed it when its stacked base branch was deleted and the identical content merged as
**#211**; the claim is corrected in the build record below. ("#10" is *claim* #10 of the ten-claim
audit, not a PR.) **No duplicate items; numbering sequential 1..15 after one deterministic
renumber.** No other unverifiable claim found in this block.

**BUILD**
**WHAT #253 ACTUALLY CLOSES — ZERO OF THE ELEVEN REMAINING HALVES. Stated precisely because the
operator asked for "1 of 3 stated rather than 3 of 3 assumed", and the honest answer is lower than
either.** Verified against the committed artifact, not against the item's own description:
· **P2 (guidance reads the wrong 8-K) — OPEN.** Item 1 clause (c) — guidance selected by MAX
  guidance date from the structured grid — is NOT in #253. SMPL's dossier still cites 8-K
  `0001702744-26-000010` (the April/Q2 guide); the July `…-26-000021` is still unused. Untouched.
· **P4 pt1 (spot is not the freshest available instance) — OPEN.** Clause (b), the
  freshest-available-instance contract, is NOT implemented. #253 ships a panel-SPREAD ceiling and a
  cap RECONCILIATION; neither selects a fresher close. Note P4's own evidence table used
  `cap ÷ shares = $10.28` as its CROSS-CHECK — so #253 implements the audit's DIAGNOSTIC and not
  its FIX.
· **P4 pt2 / clause (e) — PARTIAL.** The market cap now renders its own vintage on both twins. The
  instance clause (e) was WRITTEN FOR is still unlabelled: SMPL renders `consensus FY26E revenue
  base $1,334M` — the analyst's frozen reference — beside the live 1,351.8 with nothing
  distinguishing them. The cap is one frozen value; clause (e) governs all of them.
**SO #253 CLOSES NO AUDIT HALF.** What it DOES close is a defect the audit noted as C16 and never
raised to a P-item — live on **11 of 11 names**, worst on the ten SMPL is not. That is worth
shipping on its own merits and must not be counted against the thirteen.
**ITEM 1's CLAUSES STILL OPEN:** (a) trailing-fact recomputation · (b) freshest-available-instance
· (c) guidance-by-max-date · (d) the scheduler's max-age-of-contained-facts definition · (e) beyond
the market cap.
**BOUNDARY NOTE — VRRM SITS AT EXACTLY 45d AND PASSES**, because the ceiling is `>` not `>=`
(pinned). One day of ageing flips it. **A future VRRM failure is the guard working, not a
regression.**

**AFFECTED SURFACES, STATED PRECISELY (review of #255).** `render.py` renders NO own-history
exhibit at all — `own_history` appears zero times in it — so the markdown twin and the "Full
dossier MD" download were NEVER affected. The false stamp lived on the WEB PAGE and, because both
PDF scopes are `window.print()` on that page, in BOTH PDFs. The md's prose line carried the correct
EV/EBITDA as-of and `P/LTM EPS NM` throughout.
**AND #255 OPENED ONE CASE WHILE CLOSING ANOTHER — hardened in review.** Removing the shared
caption date moved a band with no `as_of` from carrying a WRONG date (bands[0]'s) to carrying NONE,
silently. Zero bands lack one today, so it is latent — but a dateless panel that says nothing is
item 22's prohibition, and the entire point of the fix was that a reader can tell which vintage a
panel is. Such a panel now reads `· undated`. Pinned and mutation-verified.

**THE NEW PIN WAS ITSELF THE DECAY CLASS — caught by the operator before merge, and it was worse
than suspected.** The first cut hardcoded literal dates (`"2026-07-17"`, `"2025-12-31"`, and AORT's)
against a LIVING artifact, so CNXC's queued re-assembly would have reddened it for a reason
unrelated to its claim — the TEST-LAYER rule's exact prohibition. And its "fixture still disagrees"
guard read `assert expect[0] != expect[1]`, comparing a HARDCODED TUPLE TO ITSELF: vacuously true,
never looking at the data. **Third instance of the vacuous-assertion class this week**, after 26a's
end-of-document slice and the `... or True` ruff caught.
REWRITTEN per #249's own rule: **relational** — each panel's expected date is read from its OWN band
in the committed JSON, so convergence is harmless — plus a **CONSTRUCTED companion** carrying the
DISAGREEING shape, which is what makes the bug possible and would vanish from the corpus the moment
both names re-assemble. **Verified by simulating the decay**: converging CNXC's panel dates to
2026-09-30 leaves the relational test PASSING; removing the per-panel date reds BOTH.
