---
id: 2026-10-15-theme-intelligence-state-sync-review-fixes
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the review of the O15-O18 change: three findings fixed

**WHAT.** A high-effort review of PR #712 (`docs/records/2026-10-15-theme-intelligence-state-sync-and-dates.md`)
reported three findings on it; operator, 2026-10-15: "fix all eight" (with five on PR #711).

| Finding | Fix |
|---|---|
| **The scan window and the look-ahead gate read different days.** The gate compared a publication instant's UTC day; discovery placed a candidate in the window by the publisher's LOCAL date. A US evening post (22:00 −04:00 on the window's last day) was admitted, refused by the gate as too new, recorded LOOKAHEAD — and next week's window no longer held it: never analysed. | Discovery reads a page's instant and a feed's `pubDate` as their UTC day (`utc_day`), the day the gate reads. And whatever a scan's gate refuses as too new (a listing card's date can be a day off the page's own instant) is QUEUED for the next run — said in a run warning — never dropped. |
| **A replay reused an answer built for another taxonomy.** Reuse checked the model and the prompt version only; a taxonomy change (new nodes or mechanisms) without a prompt-version bump reused an answer keyed to the old ones. | A reused answer must also fit the CURRENT tool: every value it gives a field the tool enumerates (taxonomy nodes, mechanisms, steps, kinds) is one the tool still offers (`extract._offered`); else the replay asks anew. |
| **A document one pull could not replay lost its answer ids.** They came only from the registry the pull replaces; a document kept pending is no longer in the next pull's. | The sync state keeps, beside each pending document, the extraction(s) it was given (`pending_answers`); the next pull's replay reads them, and they leave with the pending list. |

**WHY.** Two of the three lose or misread a document silently; the third pays twice for what
O15 set out to stop.

**HOW VERIFIED.**
- **Real data (copies; no model, no network):** the pilot replay of `docs/records/2026-10-15-theme-intelligence-state-sync-and-dates.md` run again with the taxonomy check — the same 8 of 9 documents replayed from the cache, $0 (the pilot's answers fit the current taxonomy). 275 distinct cached real HTML pages: 218 carry a publication instant (offsets 0 ×172, +08:00 ×30, +05:30 ×15, −04:00 ×1); **none** falls on another day in UTC, so the window change moves no real page today.
- **Pins:** 6 more in `tests/test_theme_intelligence_sync_findings.py` (16 in all): the window at
  both offsets, a feed date, a scan's too-new result queued and analysed next week, a pending
  document replayed from its answer, an answer with a node the taxonomy no longer has. All 6 fail on the change before these fixes (876a1135).
- **Mutants: 25 of 25 killed** (the 17 of O15-O18 and 8 for these fixes). One "survivor" on the
  first pass was a mutant that changed nothing (`{} or …`); corrected, it is killed. A
  never-reachable branch of the enum check (`anyOf`, which holds no enum) was removed rather than
  left untested.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.** Code: PR #712's branch, 2026-10-15. "275 pages": every cached HTML body under the
`theme-intelligence` worktree's `data/theme_intelligence/**/http_cache`, distinct by content.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- A listing card's date has no time zone and stays as listed; the queue above is what keeps a
  day's difference from losing a document.
