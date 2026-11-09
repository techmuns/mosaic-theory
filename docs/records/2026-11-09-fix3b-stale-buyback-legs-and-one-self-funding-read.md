---
status: shipped
date: 2026-11-09
prs: [930]
supersedes:
superseded-by:
---

# Fix 3b: the fact layer states no buyback leg more than a year old, and one self-funding read — eleven stale legs on nine pages are no longer stated, and the survival line's one-input FCF leg is deleted. $0; the paid measurement is proposed, not run

**THE BRIEF.** Coordinator, 2026-11-09: STATE row 54 item (1), the rest of the label fix after 3a.
- **(a)** Capital allocation's stale and pre-split per-share values: buyback and per-share figures
  from a stale period, or on a basis that predates a split, with no date or basis beside them.
- **(b)** The two self-funding reads that disagree. #923's record calls this "3b's item 7".
- **Rules:**
  - fact layer only: no prompt rule, and `gaps.py` (#927) untouched;
  - structured values, never rendered strings;
  - "a value that cannot be stated on its own current basis is stated with its date and basis,
    or deleted. Deletion is preferred over added words";
  - every defect found on the 28 frozen pages, counted with its boundary;
  - pins positive and negative, end to end on frozen pages, each failing first on main;
  - a transform `FIX_3B` plus the $0 compare;
  - the measurement proposed, not run.

## 1. What shipped, by brief item

| item | disposition | what |
|---|---|---|
| (a) stale buyback legs | **SHIPPED** | A leg whose period ends more than 366 days before the page's price date is not stated: the field is UNKNOWN, and its note names the tag and its period (`capital_allocation.CURRENT_DAYS`, `_current`, `buyback_legs`) |
| (a) pre-split per-share values | **SHIPPED by (a)'s rule**; no split rule | Both pre-split figures on the 28 pages are also more than a year old: NFLX's $221.88 (2011, before its 2015 and 2025 splits) and V's $65.98 (2014-10-01→2015-06-30, across its 2015 split). No figure kept is pre-split (§4) |
| (b) two self-funding reads | **SHIPPED** | The survival line's FCF leg is deleted. `_survival_capacity` takes no FCF sign; `quality.fcf_sign` and `primary_source.self_funding` are unchanged |
| `FIX_3B` transform | **SHIPPED** | `FIX_3B = ("survival_read", "current_buybacks")` in `vinci/evals/variants.py` |
| the $0 compare | **SHIPPED** | §3 |
| the measurement | **PROPOSED, not run** | §5 |

## 2. The two defects, as found

**(a) Stale legs.** `_pick(kind="flow")` takes a tag's latest period however old it is. A filer
that stopped using a tag keeps its last value forever, and only the `source_ref` carried the date.
- 47 of the 84 buyback fields on the 28 pages are PRESENT (28 pages × cash, share count, average
  price).
- 11 of the 47 end 671 to 5,422 days before their page's price date (`stock_info.as_of`):

  | page | field | value | period ends | days before the price date |
  |---|---|--:|---|--:|
  | AMZN | cash ($M) | 0.0 | 2024-12-31 | 671 |
  | AORT | cash ($M) | 5.588 | 2014-12-31 | 4,314 |
  | AORT | shares | 585,000 | 2014-12-31 | 4,314 |
  | BURL | average price | 52.30 | 2015-05-02 | 4,192 |
  | EPAM | average price | 283.69 | 2023-03-31 | 1,265 |
  | LLY | shares | 0 | 2021-06-30 | 1,951 |
  | MCK | shares | 13,900,000 | 2020-03-31 | 2,409 |
  | MCK | average price | 151.23 | 2020-09-30 | 2,226 |
  | NFLX | average price | 221.88 | 2011-12-31 | 5,422 |
  | V | average price | 65.98 | 2015-06-30 | 4,133 |
  | VITL | shares | 2,852,770 | 2019-04-30 | 2,666 |

- The other 36 end at most 361 days before. The closest is ROST's share count, at 361 days.
- **The line is 366 days, the block's own trailing year.** The impairment STALE rule beside it
  uses the same 366. On these pages it falls in a gap: 361 kept, 671 dropped. It was not tuned
  to the gap (CLAUDE.md: face validity, never outcomes).
- **Three PERIOD MISMATCH notes named a leg now unstated** (MCK, LLY and VITL cash, each against
  an old share count). Those clauses go. EPAM's cash-vs-shares mismatch (78 and 259 days before)
  stays.

**(b) Two reads.**
- **The survival line** (`quality.survival_capacity`, copied to `leverage_survival.survival`)
  closed on a one-input read of the EDGAR fiscal-year FCF sign: "FCF-positive → self-funding",
  "FCF-negative → burning cash (cash not derived)", or "FCF sign UNKNOWN — runway not
  assessable".
- **`primary_source.self_funding`** is the two-input read: latest-quarter OCF and CIQ's LTM FCF.
  Its own docstring says it "supersedes the committed one-input 'self-funding'".
- The web already printed only the two-input read when it was present
  (`frontend/views/shared/dossier.js`). The model was sent both.
- **All 28 pages carried both. On eight they gave opposite answers:**
  - "self-funding" against MIXED: AORT, EPAM, GOOGL, MVST;
  - "burning cash" against YES: WERN, WLK;
  - "runway not assessable" against YES: IT, LLY.
- **On five pages both reads say no self-funding:** AMZN, FUBO, ORKA, TECX, VITL ("burning cash"
  against MIXED). The other 15 agree YES.
- **The gold set shows the cost** (`tests/fixtures/synthesis_gold/`: 644 claims, one draw per
  page):
  - three units are coded CONFLICT where a coder or the adjudication names the two reads:
    WERN:bull_points:7, GOOGL:bull_points:5, EPAM:bull_points:2;
  - LLY:key_unknowns:5 spends a key unknown on the disagreement itself.
- **The leg is deleted, not reconciled.** The sign stays in `quality.fcf_sign`, and the
  self-funding question has one answer.

## 3. How verified ($0)

- **The pins:** `tests/test_fix3b_stale_and_conflicting.py`, 32 tests, end to end on the frozen
  pages through the captured request (`capture_calls`) or the rendered page
  (`render._capital_allocation`).
  - **(a), positive:** each of the 11 legs is PRESENT on the committed page. Under this code it is
    UNKNOWN, the note names the tag and its period, and the request carries no value there.
    NFLX's and V's rendered pages no longer print $221.88 and $65.98. AORT's refusal note says
    its legs are not current.
  - **(a), negative:** the other 36 legs keep value, source and status, ROST's 361-day share
    count included. EPAM's mismatch note stays. FUBO's "the cash leg is absent" stays.
  - **(b), positive:** on the eight pages the request's survival lines carry no answer, and the
    two-input read appears once.
  - **(b), negative:** on the 25 pages `survival_read` reaches, the line is the committed
    leverage leg byte for byte. Its source names no FCF sign, and `quality.fcf_sign` and
    `primary_source` are unchanged.
  - **(a), at its edge** (`tests/test_buyback_average.py`, review round 1): a leg ending 366 days
    before the price date is stated, 367 is not. The frozen pages sit at 361 and 671, so
    `CURRENT_DAYS` = 600 or `<` for `<=` passed every other pin; both now fail.
  - **The harness parse** is pinned by a round trip.
  - **The transform** is pinned as own-field only, idempotent, the identity at a ref without the
    rule, and refusing a page with no price date or a malformed source.
- **Fail first on main:** in a main-only clone at `138436c7`, 30 of the 32 fail. The two that pass
  are the corpus count (28 pages) and the pin that `survival_read` still hands a pre-3b builder its
  FCF sign, which main's builder takes by construction.
- **A guard the gate caught, narrowed to what it names.**
  - `tests/test_ev_gap_transform_idempotent.py::test_the_gap_reads_its_market_cap_from_the_comps_panel_structurally`
    asserts that `ev_gap_transform` reads no `stock_info`.
  - It sliced `refresh.py` from `def ev_gap_transform` to `def _base_leg`, the next function when
    it was written (`23d6a312`, 2026-08-03). 24 functions have since landed between the two, so
    the slice covered 25.
  - It went red on `capital_allocation_transform` reading the page's price date, which is not a
    cap. It now slices to the next top-level `def` and asserts it holds the whole body.
  - A `stock_info` read planted inside `ev_gap_transform` still turns it red (shown, then
    restored).
- **The transform** (`vinci/evals/variants.py`):
  - `current_buybacks` rebuilds the three fields through `capital_allocation.buyback_legs`, the
    builder's own body, from each field's own point;
  - `buyback_point` reads a point back from the field's source, or for a not-current leg from its
    note. That is the one string read, harness only;
  - `survival_read` (fix 3a's) now also writes the line's source, and passes the FCF sign only to
    a ref whose builder takes it.
  - **On the 28 pages at this commit:**
    - the round trip is exact on 28 of 28;
    - `current_buybacks` moves 9 pages, the 11 legs;
    - `survival_read` moves 25 and refuses 3, FUBO, ORKA and TECX, as it already did (no net
      leverage, so the line needs CIQ net debt the layer does not carry).
- **Builder against transform** (RUNBOOKS §n step 2). The builder is run on each page's own EDGAR
  companyfacts, cut at its price date (`facts_as_of`, the cut `assemble_mechanical` applies; a
  live SEC read, cached).
  - **27 of 28 pages agree both ways:** with the line lifted it reproduces the committed three
    fields, and at the line it writes exactly what `current_buybacks` writes.
  - **V does not reproduce.** Its committed cash covers 2025-10-01→2026-03-31, while EDGAR at its
    price date (2026-10-23) holds 2025-10-01→2026-06-30. The page was assembled 2026-10-26 at
    extraction version `2026-10-09.3`; why its block is older was not investigated (§4).
  - **On V the field 3b moves agrees anyway:** its average is the same UNKNOWN both ways, and its
    cash, current either way, is not moved by 3b.
- **The $0 compare** (main `138436c7` against this branch; FIX_3A on both arms; the frozen panel):
  - **With no transform** the two refs send identical requests on all six pages, and `compare`
    refuses. A fact-layer change does not reach a replay without its transform.
  - **With `FIX_3A`'s five transforms on both arms,** every page differs in USER only, with
    SYSTEM and the tool schema equal. The survival line's value and source move in its two places
    (−94 characters; LLY −120).
  - **Adding `current_buybacks`,** BURL, LLY and MCK move further, on exactly the buyback fields
    and the notes that named them:

    | page | survival | buybacks | USER change |
    |---|--:|--:|--:|
    | BURL | −94 | −346 (average) | −0.101% |
    | CNXC | −94 | 0 | −0.027% |
    | LLY | −120 | −299 (share count, cash's mismatch, the average's refusal reason) | −0.066% |
    | MCK | −94 | −659 (share count, average, cash's mismatch) | −0.161% |
    | ROST | −94 | 0 | −0.021% |
    | SMPL | −94 | 0 | −0.020% |

  - No other span moves. The CIQ root is the primary checkout's `data/manual/ciq`, read only.

## 4. Found, not fixed (out of scope)

- **Two negative legs read MIXED.** `primary_source.self_funding(False, False)` reads
  "self-funding: MIXED — latest-Q OCF < 0, LTM FCF < 0". That is AORT, FUBO, ORKA, TECX and
  VITL. Both legs agree, so "mixed" misdescribes them. But `tests/test_cross_check.py:55` pins
  that wording deliberately ("two negative legs AGREE as a cross-check while the line still reads
  MIXED"), so changing it is a decision for the owner of that read, not for this fix.
- **Acquisition consideration is the largest on record, however old** (`_pick(kind="largest")`).
  It is not a per-share figure, and the brief's (a) names buyback and per-share figures. The
  original 3b list asked for "largest since <year>" with the window stated. Left for the
  coordinator to scope.
- **A split inside the year** would leave a per-share figure on another basis that this rule
  keeps. No page carries one: NFLX's 10-for-1 split of November 2025 precedes every leg it
  keeps, which cover 2026. A rule for it is not built, because no real run can show it working
  (CLAUDE.md: do not build speculatively).
- **V's committed buyback cash is older than EDGAR at its price date** (§3): 2025-10-01→2026-03-31
  against 2025-10-01→2026-06-30. Its page was assembled 2026-10-26 at `2026-10-09.3`. The cause
  is not investigated here, and a rebuild re-reads it.
- **Review round 0 (`/code-review high`), not applied:**
  - a CURRENT share count of 0 reads "the share-count leg is absent" in the average's refusal note
    (a falsy-zero test, pre-existing; no frozen page has one);
  - `schemas.py`'s comment still calls the survival block "leverage + self-funding + nearest
    refinancing wall". It is a decision-line file, so the comment is left for its owner.
- **The refresh transform reads uncut companyfacts** (`refresh.capital_allocation_transform`),
  so a refreshed block can read a filing after the page's price date. This predates 3b. 3b only
  dates the legs against the page's own price date, and writes nothing where the page has none.

## 5. The measurement, proposed (not run)

**The panel barely sees 3b.**
- On panel v2 (BURL, CNXC, LLY, MCK, ROST, SMPL), (b) moves all six survival lines. The two reads
  conflict on LLY only. (a) moves BURL (average price), LLY (share count) and MCK (share count and
  average price).
- In #926's 60 draws (registration `cceba9d9`; BASE `e00db8cd`, CAND `e91490ae`), **3 units**
  repeat a value or label 3b deletes, all on LLY:
  - 1 BASE and 1 CAND unit say "runway not assessable";
  - 1 CAND unit cites the 2021 share-count window.
  - BURL's $52.30 and MCK's $151.23 and 13.9M are cited by no unit.
- M-LABEL, the only calibrated target, reads (b) through one family ("runway not derivable": 1
  unit in #926's 30 CAND draws). It reads nothing of (a).
- **So a paid run on the panel cannot show 3b's effect.** It would read the no-worsening checks.

**Proposed: one no-worsening run, registered before any draw.**

```
python -m vinci.evals budget-open --budget-ledger <notes>/ledger-fix3b.jsonl --cap 35 \
  --approval "<the operator's words>"
python -m vinci.evals register --base origin/main --cand <this PR's head> \
  --transform relabel_drawdown_shape --transform trailing_only_note --transform survival_read \
  --transform peer_gap_question --transform print_row_guide --transform current_buybacks \
  --no-worsening --ship-alpha 0.01 \
  --ciq-root /Users/work/Documents/GitHub/mosaic-theory/data/manual/ciq \
  --note "fix 3b: no target can fire on the panel (3 units in #926's 60 draws, all LLY); the run reads the no-worsening checks only" \
  --budget-ledger <notes>/ledger-fix3b.jsonl --out <notes>/registration-fix3b.json
python -m vinci.evals run-compare --registration <…> --budget-ledger <…> --out-dir <fresh> --paid
python -m vinci.evals score --out-dir <…> --registration <…> --budget-ledger <…>
```

- **Both arms carry `FIX_3A` and `current_buybacks`.**
  - The frozen pages predate #923, and `survival_read` reads each arm's own builder.
  - `current_buybacks` is the identity on main.
  - So the arms differ in 3b only.
- **Design:** panel v2, 5 draws per page per arm, 60 calls.
- **Cost:** #926 drew the same design for $30.72. This change moves the request by 0.020% to 0.161% of USER
  (§3), so ≈$31. **Cap proposed: $35.**
- **The alternative** is a target that can fire: register `--ticker` pages outside the panel
  where 3b moves the request and the gold shows the cost. Those are AORT, EPAM, GOOGL, WERN and
  WLK for (b), and NFLX and V for (a). The panel stays whole. That needs a metric with fresh gold
  first (RUNBOOKS §n step 7), the same position fix 4a's M-GAP is in.

## 6. Coupling with #927 (fix 4a)

- **`vinci/evals/variants.py`:** both PRs append a transform and a tuple. The second to merge
  takes main and carries its own lines.
- **STATE row 54:** both re-point one of its open items (#927 item 2, this PR item 1). The second
  to merge carries main's edit beside its own.
- **#927's gap registry names a leg this PR deletes.** `gaps._survival_gaps` types "the FCF sign
  behind the survival line's runway leg". After 3b the survival line has no runway leg, so that
  item's words describe a line that no longer exists, though its field (`quality.fcf_sign`)
  still does. Whichever merges second rewords it in that PR. This PR does not touch `gaps.py`
  (brief).

**BOUNDARY.**
- **Pages:** the 28 pages committed at the panel's freeze `bcda7ce3`
  (`git ls-tree bcda7ce3 data/dossiers/`), read through this PR's code at `d6e29ce5` (review round 1 adds a test only, and moves no count).
- **Fields:** the three buyback fields on each, with each leg's age in days from its period end
  to the page's `stock_info.as_of`. Self-funding: the survival line's text after its last " | ",
  against `primary_source.self_funding`'s word.
- **Draws:** #926's 60 draws (60 calls, registration `cceba9d9`), units by regex on the unit's
  JSON text: `runway not assessable`, `180d|180-day`, `52\.3\b`, `151\.23`, `13[.,]9 ?M`, on the
  pages they belong to.
- **Gold:** `tests/fixtures/synthesis_gold/` at this branch, coder A, coder B and adjudicated.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Does this select on form? (CLAUDE.md, before any new gate.)** No. The line reads one date,
  each leg's period end, against one other, the page's price date, the same way for every filer.
  It never reads what kind of disclosure a filing makes, its size or its wording. What it removes
  is a figure about a period more than a year gone, whatever the filer is.
- **A page loses figures it showed.** AMZN's $0 cash of 2024, AORT's 2014 legs, MCK's 2020
  share count and average, and LLY's 2021 zero now read as "no current figure", with their dates.
  That is the brief's rule: deletion over a caveat.
- **No page carries this until it is rebuilt** (row 41, as with 3a).
- **The run proposed in §5 cannot show the change works on the panel.** It can only show that
  nothing else worsened.
