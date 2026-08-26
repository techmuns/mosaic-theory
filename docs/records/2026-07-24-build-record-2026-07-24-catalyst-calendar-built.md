---
id: 
status: shipped
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 CATALYST CALENDAR BUILT (branch `feat/catalyst-calendar`; the brief
RATIFIED same day with PLACEMENT B — brief text + amendment ride PR #208's STATE change; mockups:
standalone + in-situ, operator-reviewed).** SHIPPED per the ratified (a)–(g):
(a) `CatalystRow {event, expected_date, date_basis stated|cadence-estimate, tests_what,
source_ref}` + `CatalystCalendar {rows, qa_flags}`; `MechanicalLayer.catalyst_calendar`
optional-with-default (old JSON round-trips). `DatedTrigger {trigger, deadline, basis}` on the
VERDICT block (`Verdict.dated_triggers`, additive — legacy records round-trip; rationale untouched
→ seal-safe; `scenarios/_schema.json` regenerated, the schema-sync pin enforced it).
(b) `_next_print_estimate` — median inter-print gap over the filer's OWN 2.02-8-K history (≥4
prints, gap sane-banded 60–120d, rolled past the reference; face-validity constants, never
outcome-tuned); REFUSES on thin/irregular history → loud qa_flag, no row. `_catalyst_calendar`
assembles A (cadence row; B enriches it with the committed revised-guidance checkpoint when
present) + C (in-horizon ≤730d stated maturities from the capital-structure panel); attached in
`assemble_mechanical`, misses ride the QA channel. REAL RUN: SMPL → next print 2026-10-08
(median 91d over 36 real results 8-Ks; the mockup's hand-estimate "~late Oct" confirmed) + the
guide checkpoint; MVST → print 2026-08-11 + FOUR stated wall dates incl. the decisive $41.7M
convertible 2027-01-31.
(c) render PLACEMENT B, both twins: the calendar closes the Analysis (after the argument, before
Sources/appendix) — `render.py _catalyst_calendar_lines` + `dossier.js catalystCalendar`; the
Brief crux gains ONE Next-catalyst line (earliest entry) — `_brief_lines` + `cruxInner`. Dated
triggers are read from the VERDICT (a mid-build bug caught by checking the field's landed home:
the first draft read record-level and the smoke masked it by fabricating the field — fixed both
twins, re-verified with correct nesting). Constitution footer on the card; endnote cites.
(d) monitor: `FreshnessRow.passed_trigger_deadlines` — an analyst deadline on/before the run date
flags "… PASSED → re-underwrite due" (window-closed FLAG; whether the trigger FIRED stays the
human's read — the standing no-adjudication pin still passes); future dated triggers join the
display list "(by YYYY-MM-DD)"; the decision-log panel renders passed flags loudest.
Gate: ruff · mypy --strict (110) · **1061 offline passed** (+6 pins: cadence positive/negative,
assembly rows + fail-loud, placement-B render e2e on committed-SMPL-with-injected-fixtures
(negative: pre-build JSON renders NO section, NO crux line), node py==JS twin parity, monitor
passed/future/unparseable). ARTIFACT NOTE: calendars land in committed dossiers at each name's
NEXT re-assembly (the field is mechanical DATA — a re-render alone cannot create it); dated
triggers appear when the analyst records them (machine never invents either).
