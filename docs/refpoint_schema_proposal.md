# RefPoint schema 1.3 — proposal: fields for what today travels as prose

> STATUS: PROPOSAL — nothing here is built. Diagnosis 2026-07-27 (operator-directed, this doc is
> its record); decision + build are separate steps. Per the no-speculative-build rule, the code
> change waits for an explicit go.

## What the diagnosis found

`RefPoint` is `{label, value, unit, source}` — four fields, three of them strings. Everything an
analyst wants to say about a reference beyond its number has exactly one place to go: prose inside
`label` (or, once, `unit`). Census of all 8 committed records (7 live + 1 archive), 132 references:

| meaning travelling as prose               | count | share |
|-------------------------------------------|------:|------:|
| statistic ROLE (median/percentile/trough…)|    50 |   38% |
| LEG anchored (bear/base/bull in the label)|    21 |   16% |
| unit outside any small vocabulary         |     7 |    5% |
| EXCLUSION / not-a-reference flags         |     5 |    4% |
| label > 80 chars (narrative, not a name)  |     4 |    3% |

Three compounding facts make this a defect rather than a style question:

1. **A production consumer already parses the prose.** `uw-card.js` (masthead `Method` cell):

   ```js
   const med = ref && (ref.references || []).find((p) => /median/i.test(p.label || ""));
   ```

   `find()` takes the FIRST label containing "median". On MVST that is the **peer** median (14.5x)
   of a set the analyst labelled *heterogeneous* — while the own-history median is labelled
   *"unusable, six closes over 1.3 years"*. On AORT it is 32.1x, whose own label warns it *"spans
   near-zero-earnings years"*. Both mastheads render a confident **"vs N× median"** built from a
   comparator the analyst explicitly disqualified in the very string the regex matched. This is
   the "parsers consume structured values, never rendered strings" bug class, live today — and it
   exists because the ROLE has no field to consume.

2. **The register linter cannot see these fields.** `lint_record` scans `method`, `reason`,
   `rationale`, triggers — not `references[].label`/`unit`. Running its own `lint_text` over the
   132 labels finds **26 violations of the existing register rule** (`DEAD REGIME`, `anchor`,
   `committed`, `own-history`, `band low`) sitting exactly where it never looks. The banned
   vocabulary did not disappear; it migrated into the unscanned fields.

3. **A real finding was mutilated to fit the shape.** The 2026-07-26 SMPL re-verification
   (`9afc554`) cut the base normal margin 15.5%→14%, and the honest consequence — two sealed
   entry-boundary stress cells that used to clear the fund's 2:1 bar now read ≈1.96 and ≈1.73,
   i.e. FAIL — had nowhere to live. Its prose went into a 380-char `label`, cell A into `value`,
   and cell B was smuggled into `unit`: `":1 (cell A at the re-set 14% normal; cell B ≈1.73)"`.
   It is also filed under `multiple` though it is a whole-record boundary finding. The analyst did
   the right thing with the wrong schema.

Render-side patches were tried first and rejected: a 100%-width table to tame the raggedness the
380-char label caused was reverted (it opened a 600–785px label→value gulf; the raggedness was ONE
bad row, not a layout problem). CSS cannot fix a schema gap.

## Proposal — schema 1.3, three additions, all following the `bear_basis` precedent

Schema 1.2 already solved this exact class once: bear-multiple provenance travelled as prose,
went wrong twice, and became an enumerated, validated, forward-required field (`bear_basis`,
`margin_basis`; `BASIS_REQUIRED_FROM = "1.2"`). 1.3 applies the same move to `RefPoint`.

### A. `RefPoint.role` — what statistic this is (fixes the 38% + the masthead bug)

```python
REF_ROLES = frozenset({
    "median", "mean", "percentile", "band_low", "band_high", "trough", "peak",
    "current", "reported", "consensus", "guidance", "peer_median", "peer", "analogue",
})
role: str | None = None            # None on legacy records; validated against REF_ROLES when set
```

`uw-card.js` then selects `role == "median"` (own-history) and NEVER `peer_median` — the masthead
bug becomes unrepresentable. The list is a starting vocabulary drawn from the 132 real labels;
extend deliberately, as `BEAR_BASES` is.

### B. `RefPoint.leg` + `RefPoint.excluded` — who this anchors, and whether it counts

```python
leg: Literal["bear", "base", "bull"] | None = None   # None = frame-level context (most refs)
excluded: bool = False             # shown-but-not-used ("scale leader — NOT a reference for us")
excluded_reason: str | None = None # REQUIRED when excluded=True; refused when False
```

Renderers group/badge by `leg` and dim or sideline `excluded` rows — today the three excluded
references sit in the aligned numeric column with full authority. Validation mirrors the
margin/margin_basis pair: `excluded_reason` without `excluded` is refused ("a reason for an
exclusion that is not declared"), and vice versa.

### C. `AssumptionDerivation.notes` — a home for the SMPL-class finding

```python
class AxisNote(BaseModel, frozen=True):
    text: str                      # the finding, prose register = leg-reason register
    date: str                      # ISO — when recorded
    source: str | None = None      # provenance if the note carries numbers
notes: list[AxisNote] = Field(default_factory=list)
```

The boundary-cells narrative becomes a note; the two cells become two honest references
(`label="entry-boundary cell A"`, `value=1.96`, `unit=":1"`, `excluded=False, role=None`). No
sentence in `unit`, no 380-char label. (A record-level `notes` was considered; the SMPL finding
cites the multiple-axis cells, and axis-level keeps the note beside the numbers it interprets.
If a genuinely record-level finding appears later, that is a separate decision — not pre-built.)

### Enforcement (all forward-only, per the legacy rule)

- `ROLE_REQUIRED_FROM = "1.3"` gating in `_validate`, exactly like `BASIS_REQUIRED_FROM`:
  legacy records stay writable untouched; a 1.3 record with a leg-token or exclusion-token
  pattern in a `label` is REFUSED with the field to use ("the leg belongs in `leg=`, not the
  label"). The refusal regex lives next to the model, not in a consumer.
- `lint_record` extends to `references[].label` and `unit` (flag-only, as everywhere): the 26
  existing house-token hits become visible worklist items on legacy records, hard refusals on 1.3.
- `unit` joins a vocabulary check: the census found only `{%, x, $M, $/share, :1, years,
  % of revenue, count}` in legitimate use — start there, extend deliberately. A unit over ~15
  chars is refused outright (the smuggled-sentence case).
- `_schema.json` regenerates automatically on the first `write_record` (existing mechanism; the
  export is test-pinned).

### Migration of the 8 committed records

**By hand, not by parser.** 21 leg tags + 5 exclusion flags + 1 SMPL rewrite ≈ 27 rows across 8
files — an hour of operator work. A migration script that regex-parses labels into fields would
be the display-string-parsing bug enshrined as tooling; with N=27 the safe path is also the cheap
one. The linter extension produces the worklist (file, axis, index, token found); the operator
edits; the 1.3 validator confirms. Roles (the 50) may be back-filled lazily — `role` is optional
forever on legacy records, and only the median role is load-bearing today (uw-card falls back to
"no sub-line" when absent, which is honest).

### What this deliberately does NOT do

- No LLM anywhere; no outcome-derived vocabulary; verdict path untouched.
- No renderer parses labels afterwards — uw-card's `/median/i` is DELETED with the field's
  arrival, not kept as fallback (a fallback would preserve the bug behind the fix).
- Labels remain verbatim analyst text, printed as written. The fields do not rewrite them;
  they carry the machine-readable duplicate of what the label already says to a human.

## Open decisions for the operator

1. **Vocabulary of `REF_ROLES`** — the proposed list is drawn from the census; trim or extend?
2. **Is `peer_median` vs `median` the right split**, or should role be two fields
   (statistic × population)? Proposal says one field — two would be modelling ahead of need.
3. **SMPL rewrite touches a superseded-record's live sibling** — the archived 2026-07-21 copy
   keeps its malformed row (sealed, never edited); only live `SMPL.json` is fixed. Confirm.
4. **Timing** — 1.3 lands as one PR (model + gates + linter + uw-card fix + hand-migration +
   re-render), or model first and migration second? One PR proposed: the gates are only
   provable against migrated records (verify-by-real-run).
