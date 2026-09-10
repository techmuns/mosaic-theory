---
id:
status: open
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# Phase 5 precondition — the theme terms, verified per source, in writing

The plan makes this a **precondition**, not a deliverable: *"Theme panels on the existing
`ai-datacenter` driver — terms verified per source first, in writing."* This is that verification.
It was done before any panel code, and it changed what the phase can honestly ship.

## What a theme trigger actually carries

Every declared trigger on both thesis cards is `{trigger, deadline, basis}` — **prose, a date, and a
source**. There is no metric, no comparator, no threshold anywhere in either card.

So the theme panel **cannot put a number beside a theme falsifier**, which is what
`ThemeFalsifierRow`'s docstring reserves for it (*"Indicator MEASUREMENT … is deliberately NOT here
— that is the PanelSpec plan's job"*). Same finding as `kills` in phase 3, one altitude up: the
panel is correct, loud and empty until the operator arms measurable triggers. What the panel CAN add
is the `basis` — where each trigger would be checked — and whether that basis is reachable.

## The bases split in two, and only one kind is checkable here

**TIMING bases** claim that N print cycles land inside the deadline window. That is falsifiable
against real filing cadence, and it rots silently — a filer shifts its reporting date and a "one
full print cycle" window quietly stops containing one.

**EXTERNAL-SOURCE bases** — *"public price lists + customer disclosures"*, *"payer coverage
disclosures + the incumbents' direct-to-patient channel disclosures"* — name sources outside the
repo. They are recorded as **unverifiable from committed data**, not as verified.

## The timing check, run against live EDGAR (2026-09-10)

| card · trigger | deadline | result |
|---|---|---|
| `ai-value-migration` · first-confirming | 2026-12-15 | **8 of 9 inside**, 0 outside, **1 unverifiable** |
| `glp1-drug-value-chain` · first-confirming | 2026-11-30 | **1 of 2 inside**, 0 outside, **1 unverifiable** |

Nothing is falsified — **no named representative's next print lands outside its window**. MSFT
2026-10-29, GOOGL 10-30, AMZN 10-31, META 10-30, NOW 10-30, NVDA 11-19, VEEV 11-21, CRM 12-04; LLY
10-30. Every one comfortably inside.

**The two unverifiable names are the finding.** SAP and NVO file **no 10-K and no 10-Q** — both are
foreign private issuers on 20-F/6-K. So *"every named representative's next quarterly print lands
inside it"* and *"both incumbents report by mid-Nov 2026"* are **not satisfied for those names; they
are unchecked**, and the two are different states that must not render alike.

## Why they are unchecked: a sibling call site the FPI fix never reached

The monitor's freshness path pulls `forms=("8-K", "10-Q", "10-K")` (`vinci/cli.py:2077`). A foreign
private issuer therefore yields **no filings, no `next_expected_print`, and no unread-print flag** —
it is invisible to the between-print watcher entirely.

This is the *same* blindness `vinci/triage.py` already fixed one path over, and said so in writing:
*"6-K IS NOT OPTIONAL. The 8-K path is structurally blind to foreign private issuers: FVRR files
zero 8-Ks and 57 6-Ks."* `themes/exposure.py` pulls 20-F/40-F/6-K too. The monitor's freshness path
was never updated to match — a sibling call site, found only because a theme trigger happened to
name two FPIs.

**Not fixed here.** Changing which forms the monitor watches alters `unread_print` and
`next_expected_print` for every FPI in the book, which is a decision-path change deserving its own
PR and its own real-run verification, not a side effect of a theme panel. Recorded in STATE.md as an
operator row.

## What this licenses the panel to say

* A trigger's `basis` renders **beside** it, because a criterion nobody can check is not a criterion.
* A timing basis whose names all print inside the window is marked **checked**.
* A basis that names an **external source** is marked **unverifiable from committed data** — never
  blank, and never quietly "checked".
* A basis naming a filer the monitor cannot see is marked **unchecked, with the reason**.

## One more thing the verification found

**`ai-datacenter` — the driver this phase was pointed at — has no thesis card.** It carries a frozen
56-member basket and an economics roll-up, and **zero** declared mechanism, market mistake or
falsifiers. Verified across two vocabularies plus `git log --grep` and `git log -S` over
`data/themes/thesis/`.

That is not a reason to skip the phase; it is the phase's first real case. A driver the fund tracks
with capital-relevant machinery but no declared thesis is precisely **in the set but refused** — and
the design's whole safety property is that this looks nothing like a driver the panel does not apply
to. Silence there would hide it.
