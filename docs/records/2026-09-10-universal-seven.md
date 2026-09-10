---
id:
status: open
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# Phase 3 — the universal seven, and the two defects the corpus found

**Phase:** 3 of the panel design (`docs/records/2026-08-27-between-print-monitor-panels.md`) ·
**Status:** built, preview pending operator ruling

## What this is

The seven panels every followed name runs — *the call · kills · multiple & price · filing watch ·
dilution · attribution · sources* — as `PanelSpec`s, plus the resolution that decides whether each
may render for a name and the grid that draws it. Everything reads COMMITTED artifacts only: the
per-ticker dossier, the latest monitor snapshot, the scenario record. No fetch, because a grid that
fetched would show a mark the repo cannot reproduce.

## The face-validity guard is now structural

The design carries an accepted risk — *"fifteen panels that each look important make none of them
important"* — and a guard against it: *"every panel must state what would change the call; a panel
that cannot answer that is decoration and should be cut, not shrunk."*

`PanelSpec.changes_the_call` is now a REQUIRED non-blank field. A guard enforced by reviewer
attention passes on a tired day; a decorative panel now cannot be constructed at all. All seven
answer it, and the answer renders in the MAIN BODY rather than an on-demand tier — it is decision
text, not provenance, and hiding it behind a disclosure triangle would make the guard unreadable at
the moment it matters.

Two of the seven answer it by saying they do NOT change the call, which is the honest answer and
was worth keeping: **the call** is the anchor every other number is read against, and
**attribution** says whether the call is being PAID — the fund's only evidence its discriminator
works.

## TWO DEFECTS THE LIVE CORPUS FOUND, AND A FIXTURE WOULD NOT HAVE

**1. Absent-vs-broken, committed by the phase that exists to separate them.** A scalar dossier fact
is `{value, source_ref, status, note}`. A COMPOSITE section — `primary_source.filing`,
`dilution_pipeline` — carries its content under its OWN keys with a `source_ref` and no `value` or
`status` at all. The first resolver required `value`, so **`sources` refused on 18 of 18 names
while every one of them carried a filing reference** — and refused with an EMPTY reason, which is a
blank tile wearing a label. Any fixture shaped like the scalar case would have passed.

Fixed: a composite section is present when it carries a `source_ref`. And a refusal may never reach
the reader without a reason — where the assembler recorded no note, the panel now says so rather
than passing silence on.

**2. A name is not a row.** SMPL carries TWO decision rows in the committed snapshot: one closed
(entered 2026-07-20 at $10.92) and one open (2026-08-04 at $11.33). The append-only ledger permits
this. The obvious way to index the snapshot — `{r["ticker"]: r for r in rows}` — keeps whichever
came last in LIST ORDER, so the panel would show an entry price and an excess from a position the
book no longer holds, with nothing anywhere saying it had chosen.

Fixed with `select_row`, and as a RULE rather than a preference: the live call is the open row,
because a closed row's call is already scored. With no open row the latest closed one shows, and its
own `closed` flag says so. With MORE THAN ONE open row it REFUSES by name — choosing would pick an
entry basis at random.

## The corpus result

66 ready · 60 refused across 18 names × 7 panels. Every refusal was verified true, not an
over-refusal:

| panel | refuses for | verified cause |
|---|---|---|
| **kills** | **18 of 18** | **zero scenario records carry a measured criterion — corpus-wide** |
| the call · attribution | 14 | only 4 decision rows exist in the snapshot |
| filing watch | 10 | 8 names are in the freshness list |
| multiple & price | 2 (FUBO, TECX) | EV/EBITDA is genuinely NM — a loss-making name has no multiple |
| dilution · sources | 0 | present for every name |

**The headline finding is the `kills` row.** The panel the entire design exists to enable has
nothing to measure anywhere in the corpus: the `scenario-criterion` write path shipped (#573) and
has never been exercised. The panel is correct, loud, and empty — and it will stay empty until a
criterion is armed on a real name. That is an operator action, not a code gap.

## Review fixes, and the design-sync gap they surfaced

Four findings applied. Three were small; the second is the one that matters for fidelity to the
approved plan.

**`config_schema` was missing, and the tier promises were therefore unfulfilled.** The design lists
`config_schema` as part of a panel, and stakes the whole portability claim on it — universal panels
vary by *"config only"*, cohort panels by *"the metric pair, the note name, the segment"*. Phase 2
declared `render` deferred out loud and dropped `config_schema` silently. The consequence was
concrete and contradicted this repo's own argument: `commissioning` hardcoded
`detail="property and equipment"` — **Alphabet's** heading — on the SHARED spec, so a WERN
commissioning panel would have probed for Alphabet's note and refused naming the wrong filer's
accounts. The module's docstring argues at length that a trucking name commissioning tractors asks
the same economic question under a different note name; the type could not express it.

Fixed: `Requirement.config_key` makes `detail` a DEFAULT that a name's config replaces, and
`PanelSpec.config_schema` declares what varies. The two are validated against each other — a key no
requirement reads is a silent no-op at every call site, and one no schema declares cannot be
supplied. An unset key REFUSES loudly rather than quietly probing the default, because silently
probing the default is exactly how one filer's note gets read as another's.

**The absence-clause guard keyed on a DISPLAY STRING.** `absent_means` was required when
`what != "segment"` — but `what` is the label printed in the message, not the thing that decides
which note is resolved. A caller passing a new `topic` and forgetting both keywords inherited the
segment clause AND had its note mislabelled "segment": wrong twice, silent about both. Observed: a
`goodwill` topic returned *"no report naming a segment — a single-segment filer discloses none"*. Now
keyed on the topic pattern. The guard caught an existing call in this repo's own test suite on its
first run.

**A blank clause passed the None-only check**, shipping a refusal that explained nothing — the
render branch `if absent_means else ""` encoded the hole rather than closing it. Now rejected.

**`detail` alone as the probe key** collapsed two requirements sharing a detail under different
kinds into ONE probe, so a panel could report READY with a disclosure never probed — invisible to
the mis-key guard, because the key it was handed was legitimate. Keys are now `<kind>:<detail>`.

**One bug this patch introduced and the tests caught:** the missing-config refusal was placed ABOVE
the `declared` check, so a panel that does not apply to a name reported REFUSED for want of a note
name it never needed — a loud tile for a question nobody asked, the gating rule inverted. Substance
is now decided before any form complaint, and that order is pinned.

**Methodology note.** A fast mutate/restore cycle left a `.pyc` newer than the restored source, and
Python trusted the cached bytecode from the mutated version — two tests reported failing against
correct code. The hazard cuts both ways: stale bytecode can make a mutation run report the wrong
verdict in either direction. Mutation runs here clear `__pycache__`.

Five mutations, all caught, each by the right test: key the guard on the label; let a blank clause
through; collapse the probe key; ignore per-name config; put the config refusal before the declared
check.

## What phase 4 inherits

The two cohort panels now REQUIRE a per-name `note_name`, and nothing supplies one yet — so both
refuse with "config is not set" until a name is onboarded. That is the correct state (loud, not
silent) and it is phase 4's first task: the cohort five, starting with the note name resolved per
filer rather than per repo.

## Verification

Real run on the committed corpus (above). Rendered numbers checked against source for SMPL: entry
$11.33 / 2026-08-04 (the OPEN row), multiple 5.6x at the 0th percentile of a 6.1–28.9x range over
35 closes, attribution −4.15pp / −0.24pp / −3.91pp — all exact. SMPL's multiple sits BELOW its own
range low, a real edge case the range bar handles.

Rendered-output scan: no `undefined` / `None` / `NaN`; no inline `Source:` caption under any exhibit
(house rule); 0 `not_in_set` tiles emitted; every refused tile carries its upstream reason; every
tile states what would change the call; all 9 disclosure tiers force-open in the print state.

Three mutations, all caught, each by exactly one test: key the snapshot by ticker; require a `value`
key; swallow the upstream note.

## Pending the operator

Per the PREVIEW RULE this is a render build: the preview is rendered from committed JSON in both the
collapsed and print-expanded states and STOPS here for approval. Not built pending that ruling: the
wiring into `emit_monitor` / the frontend decision log.
