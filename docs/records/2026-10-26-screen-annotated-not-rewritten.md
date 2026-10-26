---
id: 2026-10-26-screen-annotated-not-rewritten
status: shipped
date: 2026-10-26
prs: [799]
supersedes:
superseded-by:
---

# The 2026-10-16 screen is annotated, not rewritten: SFBS and IESC passed on a split the store took as a fall, and both queue surfaces now say so

**WHAT.** Operator ruling of 2026-10-26 on STATE.md §5.0 row 32 item (16): annotate the committed
2026-10-16 screen, do not rewrite it. Three pieces:

- **The ruling sits beside the run.** `data/snapshots/screen_runs/2026-10-16-01.annotations.json`
  holds, for each of SFBS and IESC:
  - the finding;
  - each gate's input as committed and on the repaired bars, as structured values (`value`,
    `passes`, the gate's `threshold`);
  - how the corrected values were measured, and the record that carries the full account.
  
  `vinci/screens/annotations.py` loads it and fails loud: a parse error, an unknown field, two
  annotations for one ticker in a run, or a `passes` that its own value and threshold contradict
  are all refused.
- **`ranked_queue.md`** marks an annotated name ⚠ in the table and lists every annotation on the
  queue's run after it, in rank order. A name below the table's cut is still listed.
  `write_queue_snapshots` loads the annotations for the queue's own screen date, so any re-write
  of this run's queue keeps them. A later run of the same ticker is never marked.
- **The app's Ranker** prints one line under the name: *"⚠ annotated 2026-10-26 — fails G1, G2 on
  the corrected data"*. The tooltip carries each gate's two values, the finding and the record.
  `frontend/build.py` mirrors the annotation files as `screen_annotations.json` (always written,
  even when empty). `frontend/lib/snapshots.js` attaches each to its row by `reference_date|ticker`
  against the row's own `screen_run_at` date.

The run's results, the candidate records and the queue's order are untouched. The committed
`ranked_queue.md` is re-rendered from the committed queue by the code above.

| | as committed | on the repaired bars |
|---|---|---|
| SFBS, band A, rank 5 | G1 −57.1% PASS · G2 −47.5% PASS | **G1 −14.5% FAIL · G2 +3.0% FAIL** |
| IESC, band A, rank 48 | G1 −68.7% PASS · G2 −51.2% PASS | G1 −38.3% PASS · **G2 −4.3% FAIL** |

**WHY.** Both names' only gap-down in the queue is dated 2026-08-06. That is the split itself: the
store took a 2:1 split as a price fall (`2026-10-26-split-restatement-and-total-return`, #796).
SFBS sits fifth in band A, so a reader working the queue from the top meets it early. Rewriting a
committed run would erase what the fund actually saw on 2026-10-16. Leaving it bare would let a
reader work a name the corrected data does not admit.

**HOW VERIFIED.**

- **On the committed files:**
  - re-rendering the committed queue (343 rows, table top 50) with the annotations is
    byte-identical to the committed `ranked_queue.md`;
  - without the annotations, the render is byte-identical to the file before this change (checked
    before any code moved);
  - `write_queue_snapshots`, on a temp config holding the queue and the annotation file, writes
    the same file.
- **In the app**, served from this branch (`http://localhost:8963/#/ranker`, 2026-10-26):
  - SFBS's row reads "SFBS ⚠" with *"⚠ annotated 2026-10-26 — fails G1, G2 on the corrected data"*;
  - IESC's reads *"… fails G2 on the corrected data"*;
  - QFIN, rank 1, carries no note;
  - the tooltip lists the gate values, the finding and the record.
  
  The first cut also printed the record path inline. It wrapped over several lines and made the row
  tall, so it moved into the tooltip.
- **`tests/test_screen_annotations.py`, 11 pins**, all on the committed files:
  - end to end against the committed Markdown;
  - only the two names marked;
  - unchanged without annotations;
  - listed below the table's cut;
  - another screen date not marked;
  - a contradicted PASS refused;
  - malformed and doubled files refused;
  - the app's mirror and keying;
  - the queue writer keeps the ruling;
  - a bad annotation file stops the writer before it replaces the JSONL.
- **Mutants: 10 of 10 killed**, among them the writer dropping the annotations, the section
  printing only names inside the cut, a screen date ignored, and the app's mirror emptied.
- **This change's own review** (`/code-review high --fix`) found 3 issues and fixed all 3:
  - the writer replaced `ranked_queue.jsonl` before the Markdown step could raise on a bad
    annotation file, leaving the pair disagreeing. Both are now composed first, and the new pin
    fails on the old order;
  - a dead helper;
  - a runtime import needed only for typing.

**BOUNDARY.**

- **The gate values** are #796's real recompute: the screen's own `build_price_record` and gates,
  reference 2026-10-16, IWM, `Screen2Thresholds()` defaults (G1 ≤ −30%, G2 ≤ −15%), on the
  repaired copy of the store #795 scored, 2026-10-26. They were copied into the file, not
  recomputed here.
- **Queue counts:** `data/snapshots/ranked_queue.jsonl` at `a675ba04`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The annotation is only as current as its file.** The next weekly screen produces a new run
  with no annotation, which is correct: it screens repaired bars. The 2026-10-16 file stays with
  its run.
- **Annotations are hand-authored decision data, like `data/followed.json`.** Nothing proposes
  them; an operator ruling does.
