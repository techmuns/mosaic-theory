---
id:
status: open
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# Phase 2 — `PanelSpec` + registry, and the gating rule pinned

**Phase:** 2 of the panel design
(`docs/records/2026-08-27-between-print-monitor-panels.md`) · **Status:** built

## What this is

A monitor panel is now a declared object rather than a hand-written block: `PanelSpec` carries
`key`, `tier`, `title`, `requires`, `cadence` and `caveat`; `PanelRegistry` holds the panels this
repo can actually draw and answers, for one name, whether a panel may render. It fetches nothing,
computes nothing and renders nothing — it decides WHETHER, and says why not. That is the smallest
piece that can carry the safety property, which is the point: the property is testable before any
panel exists to test it with.

Two panels are registered, because two extractors exist: `commissioning` (#587) and
`segment_economics` (#578). Phases 3–5 add the universal seven, the cohort five and the theme set.

## DOES THIS SELECT ON FORM?

Answered in writing, as the standing rule on `DriverSpec` requires of every spec and every gate
built on one. Four gates have already failed this question.

**Set membership is SUBSTANCE. Requirements are FORM. They are separate arguments to `decide` and
neither is derived from the other.**

| | question | kind | when it fails |
|---|---|---|---|
| `declared` | does this name have this economic question? | **substance** | renders NOTHING |
| `requires` | can the disclosure deliver the number? | **form** | renders LOUDLY |

**The trap this build would have walked into** is defining membership BY the requirement — "this
filer indexes the note, so the panel applies." That inverts the rule and lets presentation decide
economics. It is not hypothetical: **WERN**, a trucking filer, indexes no report naming property
and equipment at all (live EDGAR, 2026-09-03), yet a trucking company commissioning tractors asks
the *same* economic question the commissioning panel asks. Gate on "has a property-named note" and
WERN is excluded for how it writes its accounts — the `machine_grade` failure one altitude down.

`test_not_in_set_renders_nothing_even_when_every_requirement_is_met` is that inversion as an
assertion: a name that has not declared the panel gets `not_in_set` **even with every requirement
satisfied**. Mutating `decide` to consult `have` when `declared` is false reddens it.

## The gating rule

> `NOT IN THE SET` never renders. `IN THE SET BUT REFUSED` renders loudly and names the
> requirement that failed. **These two must never look alike.**

Three states — `not_in_set`, `refused`, `ready` — as three *values*, not one falsy one, so a
caller cannot collapse them by accident: there is no single "no" to collapse onto. `renders` is
true for `refused`, so `if d.renders:` gets the loud behaviour by default and hiding a refusal
takes deliberate effort.

A fourth case is loud rather than silent: a name declaring a panel that is not registered raises.
A configuration bug rendering as a blank tile is how a grid lies.

## The panel never forms its own opinion about why

`requires` is not re-probed by a parallel regex. The extractors already distinguish four
refusals — no such report; the report carries no numbers; several match and choosing would file
the wrong table's figures; the columns do not line up — and a second opinion computed in the
panel would be a divergent parser of the same question, the class that already cost this repo a
false reconcile caveat. The upstream refusal is passed through **verbatim**.

## Refusals used as tests were OBSERVED, never invented

Live EDGAR, 2026-09-03, through the production entry points:

| name | panel | outcome |
|---|---|---|
| GOOGL | commissioning | READY (2 rows) |
| GOOGL | segment_economics | **REFUSED** — two `(Details)` reports match the economics refinement on the Q2 10-Q; ambiguous, not guessed |
| WERN, LLY | commissioning | **REFUSED** — no property-named report indexed |
| WERN, LLY, UBER, V, NFLX, SMPL | segment_economics | **REFUSED** — `(Details)` reports do not match the refinement |

Across all 17 dossier names the form probe answered **both** ways (PP&E note present for 5,
segment note for 8), so the requirement check is not vacuous in either direction.

**Note for phase 3+:** GOOGL's segment panel refuses on its *current* 10-Q. #578 was verified
against the FY2025 10-K, where one report matched; the Q2 filing carries both
`Revenues - Revenue by Segment (Details)` and `Information about Segments and Geographic Areas -
Revenue and Operating Income/Loss by Segment (Details)`. The extractor is behaving correctly by
refusing. Resolving which of the two is canonical is a segment-extractor question, not a panel one.

## Adjacent fix: a refusal that told the wrong note's story

`_pick_report` is shared by both routes. Its `what` was parameterised in #587 but its "why
nothing is here" clause was not — so a missing property note refused with *"a single-segment
filer discloses none, and that is an answer rather than a failure."* For segments that is true
and useful. For fixed assets it is **false**: every operating company holds them, so absence is a
presentation choice and the balances may sit under a note named for the asset itself.

Fixed by parameterising `absent_means` alongside `what`. In scope because this build renders that
text to a human, and the gating rule's whole safety property is that a refusal explains itself
correctly — a refusal carrying another domain's reasoning is worse than a bare one, because it is
believed. Pinned as the **claim**, not the wording: the replacement mentions single-segment filers
in order to deny the analogy, so a token scan would pass on the very message it rejects. The
sibling call site is pinned too, so a default that silently emptied would redden.

## The caveat channel

`PanelSpec.caveat` carries a standing qualification — not an error, a fact about what the number
is. The commissioning ratio needs one: it divides *all* not-yet-in-service assets by the
technical-infrastructure member alone, so "49.7%" without that sentence reads as a commissioning
rate and is not one. A panel whose number cannot be read correctly without a caveat, and which
has nowhere to put it, misleads exactly as that docstring did. The test pins the **channel**, not
the prose.

## Verification

Full offline suite green. Four mutations, all caught:

1. collapse `not_in_set` onto `refused` → 2 tests red
2. derive membership from requirements → 1 test red
3. paraphrase the extractor refusal instead of passing it through → 1 test red
4. revert the PP&E route to the segment absence story → 1 test red
