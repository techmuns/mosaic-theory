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
