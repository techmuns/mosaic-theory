---
id: 
status: shipped
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**QUEUED BUILD → BUILT 2026-07-24 — CATALYST CALENDAR (brief drafted 2026-07-24; RATIFIED 2026-07-24 by the operator
WITH PLACEMENT B — see amended (d); mockups: standalone + in-situ on the live SMPL page, both
reviewed).** Origin: the operator's SMPL ten-claim audit,
claim #10 — catalysts exist only as scattered prose (cost-outs, Q4 margin inflection, the
two-quarter Quest test) with no dated surface and nothing watching the clock. Existing machinery
(verified, not recalled): `catalyst_path` is the STREET's estimates/guidance view, not an event
calendar; the underwrite record already carries `reunderwrite_triggers: list[str]` (undated
free-text). THE BRIEF:
(a) **Schema** — `CatalystCalendar` on the mechanical layer: rows `{event, expected_date,
date_basis: "stated"|"cadence-estimate", tests_what, source_ref}`; every date source-bound or the
row is UNKNOWN (fail-loud; never a guessed date). VERIFY-AT-BUILD: the filer's actual print
cadence from its own filing history.
(b) **Assembly (all ANCHORED/deterministic; no LLM phase)** — A: next expected print from the
filer's historical 8-K/10-Q cadence, labeled `cadence-estimate` (the EPAM ~2026-08-07 precedent);
B: guidance checkpoints — the committed FY guide (revised_guidance / guide fields) paired with the
print that will test it; C: dated forward events already extracted from 8-K bodies (`events`,
maturity dates). Supplying layers named per row.
(c) **Triggers gain deadlines** — OPTIONAL `deadline` on `reunderwrite_triggers` entries (schema
bump, additive-only; `verdict.rationale` untouched → SEAL-SAFE; legacy records round-trip).
The analyst dates their own falsifiers ("Quest stalls two more quarters" → ≈ the second print
out); the machine NEVER invents a trigger or a date.
(d) **Render — PLACEMENT B (amended at ratification, 2026-07-24)** — the dated rows table is the
CLOSING card of the Analysis tier: AFTER the synthesis/argument, BEFORE Sources (both twins) — the
buy-side memo close: the argument poses the crux, the calendar says when reality votes on it,
hand-off to the monitor. NOT on/after the street card (the original draft — rejected at review:
data-affinity placement read as consensus context, two sections before the argument it serves,
and mechanical tables never interleave INSIDE the argument). The Brief keeps one line in the crux
block ("Next catalyst: <event> ~<date> <basis-chip>"); exhibits cite via endnotes per the
standing rule.
(e) **Monitor** — the freshness panel flags a PASSED catalyst window ("window closed → re-read
due"): a FLAG, never a machine-priced delayed-catalyst scenario.
(f) **EXCLUDED BY CONSTITUTION** — no probabilities, no machine catalyst-weighting, no
direction: assembling dates is machine work; weighing them is the verdict's.
(g) **Pins** — per extractor a positive + negative pin on real committed shapes (a cadence
mis-estimate negative; a stated-date positive); an artifact-level conditional invariant (rows
present → each row dated-or-UNKNOWN + cited); JS twin parity.
Size: a #205-class PR. RATIFY (a)-(g) or amend before any build.
**→ DISCHARGED — BUILT same day** (PR #209; source D + the first dated trigger **#211** — opened
as #210, which GitHub auto-closed UNMERGED when its stacked base branch was deleted; identical
content merged as #211, corrected here by the 2026-07-27 queue-integrity pass; BUILD
RECORDS in §2). The brief stays as fossil; (b)'s source C shipped maturities-only and source D
(dated operating events) superseded the 8-K-events slice — dispositions in the build records.
