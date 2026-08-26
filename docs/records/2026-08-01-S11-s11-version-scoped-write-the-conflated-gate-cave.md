---
id: S11
status: recorded
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S11. VERSION-SCOPED WRITE + THE CONFLATED-GATE CAVEAT — built 2026-08-01. ITEM 1 DROPPED.**

**ITEM 1 (the `migrated` third state) WAS DROPPED — its premise did not hold.** The brief said
"every dossier write adds schema-default keys, so a re-render diff is unreadable". MEASURED over
all 11 committed dossiers (model round-trip): **10 of 11 re-render clean; only FUBO moves, +28
keys** (23 `material: False`, 3 `filed: null`, `extraction_version: null`, `current_guide: null`)
— pure defaults, no value moves. **MVST re-renders CLEAN**: its 79 keys were applied and committed
by #284, so that is a PAST event, not a pending one. STATE.md:4045 already recorded exactly this
("Re-rendering all eleven dossiers from committed JSON moved one file, FUBO"). The "51" figure for
FUBO appears nowhere in the record; measured is 28. The claimed blocker on IT's cap therefore did
not exist. Operator confirmed and dropped the item.

**ITEM 3 — VERSION-SCOPED SERIALIZATION, and the reasoning is the deliverable.** #302 added
`RefPoint.vintage`; `write_record` used `model_dump_json` with no filtering, so the next write of
the 7 committed 1.3 records would emit **119 `"vintage": null` keys**. The decision, three ways:

- **A record below `VINTAGE_REQUIRED_FROM` must NOT write the key at all.**
- **NOT an `exclude_none` question.** That is VALUE-driven — it drops a field for being null. It
  would strip every null across all seven records, a far LARGER diff than the one it fixes, and it
  **cannot drop `excluded: False`**, a materialized default that is not None.
- **NOT a `migrated`-state question.** That is a diagnosis — a label saying stamp and structure
  disagree. It describes the damage after the fact; it does not stop the 119 keys.
- **It is version-scoped serialization**: write exactly the fields the record's OWN declared
  `schema_version` knows about. `vinci/dossier/extraction_version.py` already makes this argument
  about itself, normalising `""` and `None` to one state because *"unstamped" and "I did not look"
  are different states*. `"vintage": null` on a 1.3 record asserts WE LOOKED AND THERE IS NONE; the
  truth is THIS RECORD PREDATES THE QUESTION. Only the declared version separates them.

`REF_FIELDS_INTRODUCED_IN` declares **every** versioned reference field (role/leg/excluded/
excluded_reason at 1.3, vintage at 1.4) — declaring only the one that hurt would be the #302
hygiene-guard defect exactly, a mechanism asserting a generality it does not have. Applied at
**BOTH** write sites: `write_archived`'s docstring promises "same serialization as write_record",
which patching one site would have made false (D15).

**CORPUS RUN, NOT A SYNTHETIC — and it caught a defect the synthetic missed.** The parsed-dict
compare said all 7 records were identical. The BYTE-level pin said they were not: `json.dumps`
defaults to `ensure_ascii=True`, so the change would have re-escaped every `×`, `÷` and `−` across
all seven files. Fixed with `ensure_ascii=False`; the dict-level check would have shipped it.
**This is the operator's warning paying off in the same build it was issued in.** Drift 119 -> 0.

**ITEM 2 — THE CONFLATED-GATE CAVEAT, and it is TWO runs, not one.** The brief named `-01` at 412
rows; measured, **412 is `-02`** and `-01` carries **423**. Both runs carry `g3_and_distress`,
whose FAIL reason reads "rejected by the multiple floor OR a distress signal" — one key, two
decisions, so the rows record ROUTING, not the gate. Marking only `-01` would have left 412 rows
of the same defect unmarked.

`<run_id>.caveat.json` is a SEPARATE, ADDITIVE file — **the manifest stays write-once**, because
rewriting it would silently re-label every row already filed under that run, and a caveat found
AFTER a run is precisely what must not be smuggled into it. Each states rows_carrying_it, the
outcome split, and what those rows **CAN** be used for (the admitted/rejected routing outcome,
stage-reach counts, G1/G2 analysis) and **CANNOT** (any G3 hit rate or threshold calibration, any
multiple-floor-vs-distress attribution, comparison against a later run's `g3_multiple_floor`).

The affected runs are **DERIVED BY SCANNING** the rows, never listed: a hardcoded pair cannot
answer "is every affected run marked" about a run it does not contain. `-03` records the split
keys and is pinned to carry NO caveat — the file names a real defect, not a blanket disclaimer.

**MUTATIONS — seven, all RED.** Filter removed (below-gate record writes vintage); filter always
fires (1.4 record loses its vintage); `vintage` dropped from the map (an undeclared new field);
`ensure_ascii` back to default; only `-01` marked; a caveat stating the wrong population; the
scan returning nothing.

**REVIEW FINDING (#303) — THE MECHANISM COMMITTED ITS OWN DEFECT ONE LEVEL UP.** The first cut
version-scoped REFERENCES only, while its comment claimed the record was written with "exactly the
fields its OWN declared `schema_version` knows about". Re-writing the committed **schema-1.2**
archive record materialised **`"notes": []` on all three axes** — the exact class the mechanism
exists to stop, inside the fix for that class (D15, fourth instance).

**WHY THE CORPUS RUN MISSED IT, and this is the reusable lesson.** The pin walked
`scenarios/*.json` — **all seven at 1.3**. *A version-scoping check run against records that all
share one version cannot fail.* The only record below the gates lives in `scenarios/archive/`, and
`write_archived` — the second write site, changed in the same commit — had **zero test coverage**.
Fixed: `AXIS_FIELDS_INTRODUCED_IN` (notes at 1.3); the pin now walks the archive and ASSERTS it
stays below the gates, so if the archive is ever re-stamped the pin says version-scoping has lost
its only real exercise rather than passing silently. `ratified`/`ratified_by` are deliberately NOT
in the map — the 1.2 record already carries both, checked against the committed record.

Three more mutations, all RED: axis scoping removed; `notes` dropped from the map; `ratified`
wrongly added (OVER-scoping — the pin catches both directions).

**NOT FIXED, recorded (scope).** `runs_with_conflated_gate` reads an unaffected run's file in full
before concluding it is unaffected — fine at 3 runs, linear in run count. And **nothing forces a
caveat to be read**: `read_rows` returns rows with no signal that a caveat is filed against them.
The brief specified a separate additive file, not read-time enforcement, so that stays a follow-up
rather than an unasked scope expansion.
