---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# The load-bearing axis is a portfolio property — and one universal panel already assumes GOOGL's

**WHAT.** Two R3 records will carry **opposite load-bearing axes**: GOOGL's downside is entirely a
de-rate, WST's base upside is entirely earnings arrival. **That is a cross-position property visible
in neither record** — each is internally consistent and says nothing about the other. Surfaced
because monitoring follows the load-bearing axis, and **one panel in the universal tier has GOOGL's
archetype written into it as a universal claim.**

## The two archetypes

| | what breaks the call | source |
|---|---|---|
| **GOOGL** | **the MULTIPLE.** Bear EPS $15.388 exceeds today's NTM $13.28698, so *"the entire bear outcome is a de-rating"* | ratified multiple method, `scenarios/GOOGL.json` |
| **WST** | **EARNINGS ARRIVAL.** Over the matched 18 months price tracked earnings one-for-one — multiple −1.2%, consensus +24.2%, implied price +22.7% — so the multiple contributes nothing to base | `docs/records/2026-09-10-base-gets-its-own-mechanism.md` |

**A single archetype pack across both monitors the wrong line on one of them.** GOOGL needs watching
for multiple regime; WST for earnings arrival. Neither record can say this, because neither knows the
other exists.

## The concrete instance, quoted

`vinci/panels_universal.py::MULTIPLE_AND_PRICE`, tier **`universal`**, `changes_the_call`:

> *"for a quality megacap **the multiple IS the trade**: where bear EPS already exceeds today's NTM
> EPS, the entire downside is compression rather than earnings. A multiple travelling toward the bear
> case while earnings hold is the call breaking on **the only axis that can break it**."*

**That is GOOGL's condition, stated verbatim, in a panel that applies to every name.**
*"Where bear EPS already exceeds today's NTM EPS"* is precisely GOOGL's; *"the only axis that can
break it"* is a universal claim generalised from a single position.

**For WST it is false.** The axis that can break WST's call is earnings arrival, and a reader
following this panel would watch compression on a name whose multiple has been paid nothing for.

*The panel is not wrong to EXIST for WST — distance to the underwritten multiple is worth seeing
either way. It is wrong about what CHANGES THE CALL, which is the field the design made mandatory
precisely so a panel could not be decorative.*

## The mechanism for this already exists and is unused across the whole tier

`PanelSpec.config_schema` was added for exactly this — its docstring says universal panels vary by
*"config only"*, and that without the field that claim *"was an aspiration the type could not
express."*

**All seven universal panels carry `config_schema = {}`:**

| panel | tier | cadence | config_schema |
|---|---|---|---|
| the_call · kills · multiple_and_price · filing_watch · dilution · attribution · sources | universal | event–daily–weekly | **none, all seven** |

**And exactly one of the seven carries archetype-bound language: `multiple_and_price`** — measured,
not eyeballed (scan for *"only axis" / "the multiple IS" / "megacap" / "bear EPS"* across all seven
`changes_the_call` strings; one hit). **The panel that most needs per-name configuration is the only
one whose text is already name-specific.**

## Not fixed here, and why

**The fix is not purely mechanical**, so it is reported rather than applied: making
`changes_the_call` archetype-neutral requires naming the load-bearing axis per name, and *which* axis
is load-bearing is an analytical judgement read off each underwrite record — operator territory, not
a rewrite. **And it is not urgent: STATE row 5 records that NOTHING CONSUMES the panel registry yet**
— no emitter, no frontend grid — so no reader is being misdirected today. This is the same
pre-consumer window that let the truncation defects be fixed before anyone saw them.

**What a fix would look like**, so the ruling is cheap to make: `MULTIPLE_AND_PRICE.changes_the_call`
states the distance and its meaning WITHOUT claiming which axis binds; a `config_schema` key —
`load_bearing_axis: "multiple" | "earnings"`, read off the underwrite record's own reasoning — carries
the per-name half. That is one field and two sentences, and it makes the tier's own "config only"
claim true for the first time.

**BOUNDARY.** Population: the seven specs in `vinci.panels_universal.UNIVERSAL_SEVEN` at this commit,
all read through the module (not grepped). GOOGL figures from `scenarios/GOOGL.json` as ratified
2026-09-10; WST figures from the matched-18-month decomposition in
`docs/records/2026-09-10-base-gets-its-own-mechanism.md` (charting export, 2,506 clean daily
observations, `Trends` consensus 8.02 → 9.96). Measured 2026-09-10.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **WST IS NOT YET A POSITION** — its triplet is unset and its
underwrite has not run — so this is a property of one live record and one prospective one. It is
recorded now because it is cheapest to record before the second underwrite is written, not because
it binds today. **The cheap fix was checked and is not available**: the mechanical half (empty
`config_schema`) could ship alone, but a config key with no value to put in it is worse than the
gap — it would read as coverage. **Falsifier: a third R3 record whose load-bearing axis matches
neither** — at which point "two archetypes" is itself too coarse and the field needs to be a
statement rather than an enum.
