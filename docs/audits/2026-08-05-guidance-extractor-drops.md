# The guidance extractor drops guided lines — measured across all eleven names

**2026-08-05. Report before fixing, as instructed. The fix is NOT what the brief anticipated.**

## The hypothesis in the brief is wrong

> *"If a metric-name allowlist explains it, it's dropping more than one thing on every name."*

**`gross margin` is already in the allowlist** — it is an alternative in both `_GUIDE_RANGE` and
`_METRIC_WORDS` (`vinci/edgar/release_parse.py`). Adding it would change nothing. The gap is the
**SHAPE of the statement**, not the metric vocabulary.

Three facts, each reproduced against the live parser:

| sentence (verbatim from the filing) | captured |
|---|---|
| `Net sales expected to range between $1.345 and $1.355 billion` | `net sales 1345.0–1355.0 $M` |
| `Gross margins expected to decline between 300 and 350 basis points year-over-year` | **NOTHING** |
| `Gross margins expected to decline approximately 375 basis points year-over-year` | **NOTHING** |

And the plural alone is fatal: `Gross margin expected to range between 30 and 32 percent` **matches**;
`Gross margins expected to range between 30 and 32 percent` **does not**. `_GUIDE_RANGE` has
`gross\s+margin` followed by `\s*`, which cannot consume the `s`.

## What the extractor actually accepts

A **two-sided LEVEL range**, in `$` or `%`, introduced by one of a small phrase set
(`outlook of`, `expected to range between`, `in the range of`, `between`, `of`), with a **singular**
metric name. Everything else falls through silently.

## The measurement — all eleven names, every release with an outlook section

Method: fetch each release's EX-99.1, locate the outlook window, split it into bullets/sentences,
and keep clauses carrying exactly one metric word plus a number. Compare against what `_guidance`
returned for the same release. Clauses that are plainly **reported actuals** ("versus", "compared
to", "up 16.6%") are separated out — the extractor is right to ignore those.

**17 genuine dropped guidance clauses. 17 correctly-ignored actuals.**

| metric | dropped |
|---|---|
| gross margin | 8 |
| revenue / net sales | 5 |
| adjusted EBITDA | 4 |

| name | dropped |
|---|---|
| SMPL | 8 |
| MVST | 6 |
| VITL | 2 |
| IT | 1 |

**Gross margin is NOT the only dropped kind.** Revenue and adjusted EBITDA are dropped from the
same releases, by the same gaps. AORT, EPAM, VRRM and BRBR's guidance-bearing releases came through
clean, so this is not universal — it tracks how each filer phrases the outlook.

### The dropped clauses, classified by shape

**1 · Percentage-CHANGE guides (6)** — a change, not a level. `_GUIDE_PCT` exists but requires the
literal phrase `growth rate`.
- SMPL 2026-01-08 `Net sales expected to range between -2% and +2% year-over-year`
- SMPL 2026-01-08 `Adjusted EBITDA expected to range between -4% and +1% year-over-year`
- SMPL 2025-07-10 `Net Sales expected to increase 8.5% to 9.5%`
- SMPL 2025-07-10 `Adjusted EBITDA expected to increase 4% to 5%`
- MVST ×2 `target revenue growth of 18% to 25% year over year`

**2 · Basis-point CHANGE guides (4)** — all SMPL, and the one the kill criteria depend on.
- 2026-07-09 `Gross margins expected to decline approximately 375 basis points year-over-year`
- 2026-04-09 `Gross margins expected to decline between 300 and 350 basis points`
- 2026-01-08 `Gross margins expected to decline between 100 and 150 basis points`
- 2025-07-10 `full year gross margin to decline by approximately 200 basis points`

**3 · One-sided guides (1)**
- VITL 2025-11-04 `increasing our Adjusted EBITDA guidance to at least $115 million`

**4 · Level ranges blocked by phrasing (2)**
- MVST `revenue guidance of $450 million to $475 million` — the word `guidance` is not in the
  introducer set, so the metric never reaches its number
- MVST `updating gross margin outlook for full year 2025 from 32% to a target range of 32% to 35%`

**5 · Qualitative prose (4)** — MVST's "targeting a resilient gross margin profile", IT's "increased
our Adjusted EBITDA and margin guidance", VITL's CFO quote. Refusing these is defensible; they state
no attributable number.

## Why the fix is bigger than a regex, and why it stops here

The brief says *"fix by deriving what's guided from the release text, not by adding `gross margin`
to a list"* — correct, and the measurement shows why it goes further than that.

**`GuidanceItem` models a LEVEL**: `low`, `high`, `unit`. Ten of the seventeen drops are **CHANGES**
— six percentage-change, four basis-point. Extending the regex to catch them without a basis field
would store SMPL's `decline between 300 and 350 basis points` as `low=300, high=350, unit="%"`,
because `_guide_unit("gross margin", …)` returns `%`.

**That is a gross margin of 300–350%.** A 100× magnitude error in a decision figure, stated
confidently — the exact class this parser has been fixed for twice already (Concentrix's billions
read as millions; BellRing's shared range binding a $2.4bn revenue figure to a ~$490M EBITDA line).
The module's own rule: *"a magnitude error in a decision figure is worse than an absent one."*

So a clean derivation **is** available, but it requires `GuidanceItem` to distinguish a **change**
from a **level** — a `basis` field plus `bps`/`%`-change units — and that ripples into four
consumers that today read `low`/`high` as a level: `_primary_source_digest`, the `scenario-propose`
evidence block, `guide_verification`, and the vintage marking. **Stopping here for that ruling**,
per the brief's own instruction, rather than shipping either a 100× error or a metric-list patch
that leaves ten of the seventeen still dropped.

## What this blocks

EPAM and IT are queued for re-assembly. **IT is one of the four names with a dropped guided line**
(2025-11-04, adjusted EBITDA), so it inherits the gap. SMPL's `375` remains absent from the record
whose kill criteria cite it — the number is verified real and correctly sourced (see the
2026-08-04 read), it simply never reaches the dossier.
