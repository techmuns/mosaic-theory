---
status: open
date: 2026-11-10
prs: [967]
supersedes:
superseded-by:
---

# Fix request 2, order 4, the CIQ reader's live RA-D2 and RA-D4: the dividend per share is the dividend, not its growth rate, and every period guided on the latest date is kept, in time order. Built and STOPPED for the six-page panel check; no page refreshed

**WHAT.**
- **RA-D2** (`ciq_sheets._dividend_per_share`, read by `return_ratios` and `key_ratios`).
  - **The defect.** CIQ's Ratios sheet has no dividend level. Its four 'Dividend per Share' rows
    are growth rates, under 'Growth Over Prior Year' and the two-, three- and five-year CAGR
    heads, and the first was printed as "Dividend/sh". A growth cell at a marker printed
    "dividend: none" for a payer.
  - **On the exports on disk:** V read 0.19, 0.15, 0.13, 0.14 against dividends of 1.87, 2.15,
    2.44, 2.79; GOOGL read 0.38 and 0.05 against 0.83 and 0.86.
  - **The fix.** Both now read the Income Statement's 'Dividends per Share' level, for the same
    periods, matched by period kind and end. GOOGL's Income Statement heads FY24 'Reclassified'
    where its Ratios sheet does not, so header text alone would not match.
- **RA-D4** (`_guidance_reads`).
  - **The defect.** F12 asks for every period guided on the latest date. The read kept the
    leftmost column of that date (a strict `>`), so a second period guided the same day was
    dropped, and which one survived was column order. SMPL's FY 2026 guide (1,345.00 – 1,355.00),
    given with its FQ4 2026 guide on 2026-07-09, never reached the page.
  - **The fix.** The read carries the others (`_GuidanceRead.same_day`). The bridge string names
    them ("same day: … for FY 2027"), and the table gets a row per period, the metric's delivery
    record on its first.
  - **Time order, not columns.** The read's own period, the one the guide check takes, is the
    first in time order (FQ before FY), so reversing the columns changes nothing. The "most
    recent outcome" had the same column-order tie on one date and is broken the same way
    (`_newer`), found by the reversal pin.

**WHY.** Document 15, order 4: "a dividend growth rate printed as dividend per share; one period
per guidance date, chosen by column position". Done when: "each A case is a passing test; F12
keeps every period guided on the date, each labelled".

**HOW VERIFIED.**
- **Fail first.** `tests/test_dividend_level_and_same_day_guides.py` fails 12 of its 13 cases
  (every one of its 8 tests in at least one case) on #957's `vinci/` (this branch's base) and
  passes here. The one case that passes there is the unread twin in the column order whose
  leftmost period is already the first in time; its reversed twin is the one that fails. The real-export pins read V's, GOOGL's, NKE's,
  AMZN's and SMPL's exports as they stand; the twins run on CI.
- **$0 compare.** `return_ratios`, `key_ratios`, `guidance_bridge`, `guidance_bridge_rows` and
  `revenue_guide_lohi` were dumped at #957's code and this branch on the 36 folders on disk.

  | Reader | Folders moved | Pages among them |
  |---|--:|---|
  | `return_ratios` (the dividend row) | 14 in value, 36 in citation | 11 in value: CNXC, GOOGL, LLY, MCK, NKE, ROST, TGT, TJX, V, WERN, WLK |
  | `guidance_bridge` and its rows | 21 each | 16: AMZN, BURL, CNXC, EPAM, FUBO, IT, NCNO, NFLX, NKE, PARR, ROST, SMPL, TJX, UBER, V, WLK |
  | `key_ratios` | 0 in value, 22 in citation ("dividend: none" names the Income Statement) | — |
  | `revenue_guide_lohi` (the guide check's input) | 0 | — |
  | "most recent outcome" | 0 | — |

**BOUNDARY.**
- The exports under the primary checkout's `data/manual/ciq/` on 2026-11-10: 36 folders, the
  current exports, not the ones each page was built from.
- A committed page moves only when re-read.
- Synthesis citations: the 27 committed `dossier.json` at `9da0d096`.

**WHAT IT COSTS / WHAT IS ACCEPTED — THE STOP.**
- Both fields are in the mechanical layer the synthesis reads (`return_ratios`,
  `guidance_bridge`), so a page re-assembled on this code sends a different request. RUNBOOKS §n
  applies, so this PR is built and not refreshed.
- **The panel** is `vinci.evals panel`, the frozen six: BURL, CNXC, LLY, MCK, ROST and SMPL.
  Every one moves:
  - the dividend row: CNXC, LLY, MCK, ROST;
  - the guidance: BURL, CNXC, ROST, SMPL.
- **Proposed** (the operator's call; nothing drawn):
  1. **$0.** Ship a transform in `vinci/evals/variants.py` that re-reads the two fields from the
     ref's own code on the page's own export (`--ciq-root`, read only; the identity at main).
     Then run `compare --base <#957's head> --cand <this branch> --transform <it>`.
  2. **Paid.** A no-worsening run, the panel whole, 5 draws an arm, as #941's ran ($27.50 of a
     $35 cap). Cap proposed: **$35**.
- **Citations.** Five committed syntheses cite the guidance bridge (FUBO 2, MCK 3, NCNO 1, UBER 1,
  V 2), and none cite the ratios table. A $0 refresh of the guidance field under a kept synthesis
  would leave those claims describing the old read, so the pages wait for the panel's verdict and
  a re-assembly. No page is refreshed here.
- **Stacked on #957.** It edits `_guidance_reads` after RA-D3, so it merges after #957. Its
  extraction-version row follows #957's.
- **Found, not fixed.** An unread cell on the same date as a readable guide is not listed among
  the same-day periods. RA-D3 names an unread cell only when it is the newest date.
- **Review round 0 (`/code-review high --fix`).** Six findings were fixed, each behind a test that
  failed first:
  - A Ratios column the Income Statement does not state, or states twice, now reads "—" and says
    nothing of a dividend, never "none".
  - An unread guide's same-date tie is broken by time order.
  - Half-year labels (FH1, FH2; 70 header cells on disk) sort in time order.
  - The point/range display has one helper.
  - `tests/test_dossier.py`'s return-ratios fixture carries the Income Statement the row now
    reads.

  A second pass fixed one more, behind a test that failed first: the bridge string printed
  '(stale — Nd old)' after the same-day list, where it read as the last period's age alone. It
  now follows the date, as before this PR, and the list follows it.

  Two were left open. The table's row order under the renderer's past-year move is a render-layer
  change outside this diff. The same-day unread guide is as above.
- **An operator question the review raised.** When two periods guided on one date both resolve,
  the "most recent outcome" takes the EARLIER in time order. That is what the leftmost column gave
  on every export on disk, so no read moves. The later one is arguably the more recent outcome:
  UBER's Revenue reads FQ1 2020 MET while FQ2 2020, guided the same day, MISSED, and 15 reads on
  disk would change. This PR keeps today's reads; flipping the order is one line in `_newer`.
- **Extraction version** `2026-11-10.dividend-level-and-same-day-guides`; the drift pins are
  re-pinned.

**Review round 0b (after the squash).**
- The dividend row and "dividend: none" cite the Income Statement they are read from (`source_ref`,
  CLAUDE.md "source-bind everything"): `return_ratios`' citation moves on all 36 folders and
  `key_ratios`' on the 22 non-payers, values unchanged.
- The stale age reads before the same-day list.
- **For the operator before the panel:** MCK's LTM dividend prints 1.64 beside FY26's 3.17. CIQ's
  own LTM 'Dividends per Share' sums two quarters, because the quarterly export's Sep-30-2026 cell
  reads 'NA'. The row reads CIQ's figure as stated; checking a per-share LTM against its quarters
  would be a new rule.

## The operator's rulings, and the panel's $0 step (2026-11-10)

The operator, relayed by the coordinator, verbatim: **"yes to all, merge them one at a time"**.
- **The tie-break:** keep the EARLIER period, today's read. Nothing is changed.
- **MCK:** the LTM dividend is printed as CIQ states it, with a note (`_ltm_dividend_note`).
  - The note names each of the four quarters ending at the LTM column that carries no figure,
    and the sum of those stated. It never says what CIQ summed.
  - MCK's note, on its export as it stands: "Dividend/sh LTM to 2026-09-30 (1.64) is CIQ's own
    LTM figure, printed as stated; of the four quarters ending then, the quarterly export's
    'Dividends per Share' reads 'NA' for the quarter to 2026-09-30, and the 3 it states sum
    2.46". CIQ's 1.64 equals two of its 0.82 quarters.
  - It fires on 1 of the 36 folders on disk (MCK).
- **The panel check:** APPROVED, cap $35.
- **The $0 transform** (`vinci/evals/variants.py`, `dividend_and_same_day_guides`, `RA_D2_D4`).
  - It re-reads the four fields from the page's own CIQ folder. The harness hands it over as
    `--ciq` / `Context.ciq`, through `replay.capture_at` and `compare.compare_requests`, which
    records each file's sha256.
  - Each field is written only where the re-read, with the change's additions taken out, equals
    the committed field. Otherwise it is left as committed.
  - On the panel it writes every field on every page except BURL's guidance. BURL's export is the
    page's own (`758eae1432`, as stamped), but its bridge predates A-D8's block discovery, so no
    code at #957 rebuilds it. BURL's guidance is therefore NOT covered.
- **`compare --base 873fbe45 --cand <this branch> --transform dividend_and_same_day_guides`.**
  Every panel page's request differs; SYSTEM is equal, and only `user.facts` moves:

  | Page | Facts characters |
  |---|--:|
  | BURL | +104 |
  | CNXC | +1,798 |
  | LLY | +63 |
  | MCK | +290 |
  | ROST | +1,256 |
  | SMPL | +1,283 |
