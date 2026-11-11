---
status: open
date: 2026-11-11
prs: [983]
supersedes:
superseded-by:
---

# Fix request 2, RA-D4 split from #967: every period guided on the latest date is kept, in time order. Measured on its own panel before it ships

**WHAT.**
- **The split.** #967 held RA-D2 and RA-D4 together, and its panel check did not ship (#973). The
  operator, relayed by the coordinator on 2026-11-11, verbatim: **"go ahead with the correct steps
  as per experts"**. The steps: split #967 into RA-D2 and RA-D4 (this), measure each on its own,
  merge what passes, stop what fails. This PR carries RA-D4's half of #967's code, unchanged, plus
  the evals harness's `--ciq` plumbing and its own transform.
- **RA-D4** (`_guidance_reads`). F12 asks for every period guided on the latest date. The read kept
  the leftmost column of that date (a strict `>`), so a second period guided the same day was
  dropped, and which survived was column order: SMPL's FY 2026 guide (1,345.00 – 1,355.00), given
  with its FQ4 2026 guide on 2026-07-09, never reached the page. The read now carries the others
  (`_GuidanceRead.same_day`): the bridge names them ("same day: … for FY 2027"), and the table gets
  a row per period, the metric's delivery record on its first.
- **Time order, not columns.** The read's own period, the one the guide check takes, is the first
  in time order (FQ and FH before FY), so reversing the columns changes nothing. A tie keeps the
  EARLIER period (the operator's ruling, 2026-11-10). The "most recent outcome" breaks its own
  same-date tie the same way (`_newer`).

**WHY.** Document 15, order 4: "one period per guidance date, chosen by column position"; done
when "F12 keeps every period guided on the date, each labelled".

**HOW VERIFIED.**
- **Fail first.** `tests/test_same_day_guides.py` has 8 cases (5 tests). 7 fail on `origin/main`'s
  `vinci/` (`ed2c5f8f`). The one that passes is the unread-guide twin in the column order whose
  leftmost period is already the first in time; its reversed twin fails.
- **$0 compare.** `--base 173b4818 --cand a27072ec --transform same_day_guides` on the panel:
  CNXC +1,735, ROST +1,194 and SMPL +1,179 characters, in `user.facts` only. BURL, LLY and MCK are
  identical. The same at `2b9b766c` → `dd301e30`.
- **The panel.** Registration `5bc72d2b9c16a660`, no-worsening only, drawn once ($27.32 of $35)
  and scored at $0. No class metric worsens. The lean moved on MCK, whose request is
  byte-identical in both arms, and on SMPL; no proposal moved.
  `docs/records/2026-11-11-ra-d4-measured-on-the-panel.md` records it. The operator, 2026-11-11:
  "Merge, moves are explained".

**BOUNDARY.** The exports under the primary checkout's `data/manual/ciq/` on 2026-11-11: 36
folders. The panel is the frozen six (BURL, CNXC, LLY, MCK, ROST, SMPL). BURL's committed guidance
predates A-D8's block discovery, so no code rebuilds it: the transform leaves it as committed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- It changes what live pages print and what their synthesis requests carry once re-assembled, so it
  ships only if its own panel check passes (RUNBOOKS §n). No page is refreshed here.
- Five of the 27 committed pages' syntheses (at `1d6c7d9f`, counted by the Estimates→Guidance
  source_ref in `synthesis`) cite the guidance bridge (FUBO 2, MCK 3, NCNO 1, UBER 1, V 2): a $0
  refresh under a kept synthesis would leave those claims describing the old read, so pages wait for
  the panel's verdict and a re-assembly.
- **Found, not fixed (from #967's review):** an unread cell on the same date as a readable guide is
  not listed among the same-day periods.
- **Found, not fixed (this review):** when every cell on the latest date is unread (RA-D3's
  shape: SMPL's FQ1 2027 and FY 2027, both 'NA' on 2026-10-27, on the export RA-D3 read), the
  read names the first in time and carries no `same_day`, so the other unread period is not
  labelled. RA-D3's census (36 sheets, 2026-11-10) found 0 such columns, so no page moves today.
- **Extraction version** `2026-11-11.same-day-guides`; the drift pins are re-pinned.
