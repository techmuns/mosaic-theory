---
id: r3-reaches-the-create-path
status: open
date: 2026-09-01
prs: []
supersedes:
superseded-by:
---

# R3 reached the sanctioned create path, and GOOGL is the first record written through it

**WHAT.** R3's arithmetic shipped 2026-08-31. Nothing could CREATE an R3 record. Six code paths
read a module-level `AXES = ("revenue", "margin", "multiple")` and each broke a forward-P/E record
differently:

| consumer | what it did to an R3 record |
|---|---|
| `validate_legs` | refused it — 9 problems, 6 for axes it never reads |
| — its anchor lookup | compared a P/E turn to an own-history **EV/EBITDA** median: a false **+41%** deviation flag |
| `assumptions_from` | composed provenance over revenue/margin, dropping the analyst's own words |
| `record_legs_for_validation` | mapped provenance onto absent axes, left `eps` unmapped — supersede would refuse every R3 record |
| `frontend/build.py` card emitter | `KeyError: 'revenue'` |
| `render.py` md table + `uw-card.js` leg rows | printed `Revenue —` / `Op margin —` and no EPS row — every input EXCEPT the one that produced the value |

All six now take their axes from `scenarios.axes_for(recipe_id, multiple_basis)` — one definition,
no second copy to drift from it. Two supporting changes fall out:

- **`Anchor` carries a structured `basis`.** The metric was previously reachable only by parsing
  the display label `"EV/EBITDA trailing median"` — the display-string-as-data class. An anchor on
  a different multiple is now DROPPED rather than compared, which makes the check STRICTER: the
  leg becomes unanchored and must state its own derivation.
- **`AXIS_LEG_FIELD`** maps an axis to the leg key holding its number (`earnings`→`eps`,
  `horizon`→`years_to_terminal`). Passing R2's REAL axes surfaced that `horizon` had never been
  mapped — three committed R2 records refused on "horizon is required and absent" while carrying
  the number under its own name.

**WHY.** THE UNWIRED-CAPABILITY CLASS, FOURTH INSTANCE — built, pinned, and unreachable. It was
found by trying to use it on a real name, not by a test, and the `KeyError` was found by the real
frontend build after the reasoning "a consumer reading `revenue` would already have broken on the
arithmetic" had explicitly dismissed that risk. The card builder wants those fields for DISPLAY,
where a `None` renders harmlessly; the dismissal was wrong about which consumer would fail.

**GOOGL, R3, written 2026-09-01.** Reproducing the IC memo of 2026-08-17 to the cent:

| leg | EPS | × P/E | value/share | vs spot $345.90 (2026-08-14) |
|---|---|---|---|---|
| bear | 15.388 | 20.5 | $315.45 | −8.8% |
| base | 16.221 | 24.5 | $397.41 | +14.9% |
| bull | 16.649 | 26.0 | $432.87 | +25.1% |

Reward/risk **1.692x against the 2.0x bar → FAIL**; IRR **14.89% against the 15% floor → FAIL**;
gate FAIL. The memo states ~1.69x itself — the gate is the fund's standing bar applied to the
memo's own numbers, and the machine proposed nothing.

Two things that must not be conflated: this 1.69x is the **FUNDAMENTAL** asymmetry on the
~Aug-2027 horizon; the ledger row's ~1.21–1.25x is the **TRADE** asymmetry on its own clock.

No `RefPoint` references land on either axis, and that is correct: no committed statistic anchors
a forward P/E here. Provenance is the per-leg derivations naming the memo, and the card now SAYS
`no reference values — set by judgment` rather than rendering an empty block. Both axis methods
render **draft — unratified**; ratification is a review act the operator performs.

**HOW VERIFIED.** Real `scenario-create` run through the sanctioned path. Both previously-broken
cases demonstrated side by side — the false deviation flag, and the analyst's words replaced by a
"stated per leg" placeholder. The **eleven other underwrite cards and sixteen other dossier pages
byte-identical** after a full `refresh_dossier` sweep + `mirror_to_frontend()`; same for the eight
prior scenario records after extending `LEG_FIELDS_DROPPED_WHEN_NONE` — verified against the
corpus, not assumed. The operator re-tag shown to survive `preserve_operator_tag` against the
machine's own HEAD proposal, with both sides read from real committed values. Card preview
captured collapsed AND print-expanded, 0 `undefined`. Basis filter pinned across all seven
combinations, positive and negative.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Two pins changed, neither a weakening:

- `test_every_committed_record_predates_the_vintage_rule` asserted every record sits below schema
  1.4. That was a fact about the CORPUS, not the invariant — true only while nothing had crossed
  1.4. Renamed and rewritten to assert the RULE, with an inertness canary (a real committed record
  bumped to 1.5) proving the check can fire, since GOOGL carries zero references and would
  otherwise pass over an inert helper.
- The methodology print-fate scan pinned `!withRefs.length`; the degrade condition moved to
  `!axes.length` because an axis WITHOUT references is no longer nothing to show. The invariant —
  absent data yields `""`, never invented content — is unchanged.

ACCEPTED: `scenario-propose` still emits an R1-shaped template (hardcodes
`multiple_basis: "EV/EBITDA"` plus revenue/margin assumption stubs), both hand-corrected to write
this record. The VALIDATOR is recipe-aware; the PROPOSER is not. Falsifier: the next R3 name needs
the same two hand edits. Recorded as STATE §5.0 row 9 rather than fixed silently.
