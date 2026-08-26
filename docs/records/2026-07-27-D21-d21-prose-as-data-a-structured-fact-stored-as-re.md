---
id: D21
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D21. PROSE-AS-DATA — a structured fact stored as rendered text, so nothing can compare it.**
(named 2026-08-01, after the third instance in one week.)

**THE CLASS.** A value that is structurally a datum — a date, a count, a window length, a period —
is written into a human-readable STRING and never stored beside it as a field. The string renders
correctly, so nothing looks wrong; but every consumer that needs the datum must re-derive it by
parsing prose, and two consumers parsing the same prose is the divergent-parser bug this repo
already banned at the display layer (`$1,101.80M` read as `1`). **The tell: you can read the value
but you cannot compare it.**

**THE THREE INSTANCES, all correctly left unparsed:**
- **`spot_source`** — `"Polygon AORT close 2026-07-20 (live at underwrite)"`. The spot's DATE is in
  there; `ScenarioRecord.spot` is a bare float with no `spot_as_of`. Seven records, 7/7 carry a
  date in the string, 0/7 as a field.
- **`pe_pctile_vs_history.note`** — `"1254 P/E observations over 1825d; …"`. The window length and
  the observation COUNT are both structured facts (`_PE_WINDOW_DAYS`, `len(hist)`) that exist as
  variables at write time and reach the record only as prose. #305 left `span_days`/`observations`
  absent on the G3 inputs rather than parse them back out — correct, and it is why the row cannot
  say how deep the range was.
- **`RefPoint.source`** — 49 of 119 committed references carry a period token inside the source
  string; 70 carry none. #302 added `vintage` as a FIELD binding forward and refused to backfill by
  parsing the 49, because a parse would manufacture confidence about which token is the period.

**THE FIX SHAPE — EXTRACT AT WRITE TIME, STRUCTURED, REFUSE DISAGREEMENT.** The producer already
HAS the datum as a value (it is what it formatted the string from), so:
1. **Store the field beside the string, never instead of it** — the prose stays; readers get both.
2. **Populate it at WRITE time from the same variable that formatted the string** — never by a
   later re-parse. A re-parse is a second implementation of the formatter, running backwards.
3. **Refuse disagreement**: if both are present and the field contradicts the string, RAISE. That is
   what makes the pair self-checking rather than two facts that can drift.
4. **Bind forward, never backfill by parsing** (the `BASIS_REQUIRED_FROM` / `VINTAGE_REQUIRED_FROM`
   precedent). Historic strings whose datum is unrecoverable stay unstamped and SAY so.

**FOURTH INSTANCE, 2026-08-01 — INSIDE THE TABLE AN ANALYST READS (recorded, not fixed).**
`peer_comps.peer_grid`'s `tev_ebitda` is stored as a **STRING**. A numeric filter over the
grid (`isinstance(v, (int, float))`) returned **ZERO survivors** on SMPL's 10 peers — every
peer silently failed the positive-EBITDA test — and the near-conclusion was *"no peer set
exists for SMPL"*. With float coercion, **4 survive, median 8.25x.** Same class as the other
three, but worse placed: the earlier instances sat in provenance strings a consumer might
reasonably not parse. This one sits in a NUMERIC COLUMN of a comparison table, where every
consumer will do arithmetic on it. The producer had the float. Not fixed here — the fix is
the write side, and the peer grid is assembly output, so it rides a re-assembly.

**RECOGNITION RULE for the next one:** if a string in a record contains a number, a date, or a
period that any consumer would ever want to sort, filter, or compare on — it is prose-as-data, and
the field belongs beside it. **Do not ask whether the string is parseable; ask whether the producer
had the value.** It always did.
