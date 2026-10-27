---
id:
status: shipped
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# A renamed line continues its record — an alias table keyed by CIK + share-class FIGI carries the old id's bars and incumbency to the new id — and the cohort pool reads a line as its issuer registers it

**WHAT.** Two follow-ups from item 21 (`docs/records/2026-10-27-screened-population-typing-and-incumbent-line.md`), both decided by the lane owner after #825 merged. **Built on main WITHOUT #828**: the operator held the foreign-filer exclusion on 2026-10-28. Every number below is on main's population, foreign filers included.

1. **A ticker rename no longer splits a record** (`vinci/resolver/aliases.py`,
   `EodClient.ticker_details` / `carry_forward` in `vinci/eod/client.py`, `build_universe`).
   - **The key.** The resolver keys a line `SEC-<cik>-<ticker>`, so a rename minted a new id with
     no history while the old id kept all of it. A rename is now confirmed on **CIK + Polygon's
     share-class FIGI**, which survives a ticker change. Two conditions must hold:
     - the old ticker's record, as of the day before the new ticker's first session, carries the
       same FIGI and CIK as the new line's record today;
     - the old ticker is absent from today's reference pull, and the two lines are the same share
       class.
   - **The table.** Each confirmed rename is written to `data/snapshots/share_class_aliases.jsonl`,
     an ACCUMULATE-ONLY table: rows are never dropped or rewritten.
   - **The carry.** The new id is given the old id's history before its first session. Polygon's
     own bars for the old ticker cover the plan's two years and win on any shared session. The
     store's older copies fill the rest, set beside a fresh bar and restated first if the source
     has since applied a split (L7's caution, `restatement_factor`). Every carried bar names its
     origin, `polygon-alias:<old id>`.
   - **Incumbency follows the alias.** The new id inherits the old id's place in the committed
     population.
   - **Nothing is re-keyed.** The ledger and the dossiers key on the old ids, which stay exactly
     as they were (lane owner's design).
2. **The cohort pool reads a line as its issuer registers it** (`scripts/build_cohort_pool.py`).
   - **The builder** now applies the universe's cover rule (`registered_line` → `excluded_class`)
     to lines the feed types `CS`.
   - **The committed pool is pruned** of the rows the rule excludes, as a separate artifact commit.

**WHY — MEASURED.**

- **Renames.** Across eight Polygon reference pulls (2026-07-13 → 10-17), **49 share classes
  changed ticker**; 13 have an id in the entity master; **10 touch a committed primary
  population**.
  - HLX → HOS (Helix → Hornbeck, first session 2026-09-02) and BRR → SVIA moved a population line
    between consecutive builds.
  - HOS was screened on "only 20d" (09-22) and "only 44d history" (10-16), and could not be
    evaluated.
  - None touched the decision ledger or a committed dossier.
  - Four OLD tickers were once in the ranked queue: ISSC, ODV, PSKY, BBBY. Their successors IA,
    OGG, SKYD and NXH later entered the population as new ids.
- **The pool.** The type gate admits whatever the feed types `CS`, and the feed types notes and
  preferred depositaries `CS`. Of the committed pool's 18,827 rows (seven runs), **318 rows on 57
  lines** are registered on their issuers' covers as debt (178 rows) or as preferred beside a
  common traded under another symbol (140 rows):
  - MCHPP, in 5 runs;
  - ACGLN;
  - T-Mobile's TMUSI / TMUSL / TMUSZ;
  - Xcel's XELLL;
  - Adamas's notes and preferreds;
  - the bank depositaries.

**A DEFECT THE REAL RUN FOUND BEFORE IT SHIPPED.** The first cut took the rename boundary from
Polygon's `list_date`. That field is the SHARE CLASS's listing:
- HOS reads 2026-09-02, the rename;
- SVIA reads 2025-12-08, the day the class listed as BRR, so the first cut read BRR "as of
  2025-12-07", before that ticker existed.

The boundary is now the first session the source serves under the new ticker. It is pinned with
a record carrying SVIA's shape.

**REAL RUN — the 2026-10-16 build, replayed on main's population.**
- **Inputs:** the 10-16 run's own cache and a copy of its own STORE (`vinci.db`), TTL ignored. The
  network was refused except for 49 live Polygon calls (ticker details and per-symbol bars) for
  the 14 rename candidates. The three lookups the original run never got (BMMX, CTY, TCXB) were
  replayed as failed, as in the baseline.
- **10 renames confirmed**, each FIGI-equal, with its first session under the new ticker:

  | old → new | first session |
  |---|---|
  | ISSC → IA | 2026-08-18 |
  | HLX → HOS | 2026-09-02 |
  | SCVL → SHOE | 2026-06-12 |
  | LC → HAPN | 2026-06-22 |
  | ODV → OGG | 2026-07-20 |
  | TOI → STLN | 2026-08-04 |
  | VSCO → VSXY | 2026-06-02 |
  | WGRX → MEDS | 2026-07-22 |
  | PSKY → SKYD | 2026-10-06 |
  | BRR → SVIA | 2026-09-22 |

- **4 candidates correctly refused:**
  - NHP beside its preferreds NHPAP / NHPBP;
  - BW beside its note BWNB;
  - NN beside its warrant NNAVW;
  - DMC, which L7 also lists as a rename of FDP: Polygon carries no share-class FIGI for DMC
    today, and with no key there is no rename (PLGO's shape).
- **The screen's own 52-week drawdown** (`compute_price_features`), bars held → after the carry.
  Every one was unevaluable before:

  | line | bars before → after | drawdown after |
  |---|---|---|
  | HOS | 32 → 1,287 | −38.5% |
  | IA | 43 → 1,287 | −37.5% |
  | SHOE | 88 → 1,287 | −36.3% |
  | HAPN | 83 → 1,287 | −33.1% |
  | OGG | 64 → 1,101 | −46.0% |
  | STLN | 51 → 1,233 | −9.8% |
  | VSXY | 96 → 1,287 | −14.8% |
  | MEDS | 51 → 405 | −78.6% |
  | SKYD | 9 → 301 | −60.4% |
  | SVIA | 19 → 306 | −65.4% |

  Whether each passes G1 is the screen's call at the next weekly.
- **Population:** 2,065 → 2,065, identical set, 0 caps moved. The rename changes HISTORY, not
  membership.
- **Pool prune**, measured on main's committed artifacts (unchanged by #828 either way):
  - **86 of 1,245 (run, industry) medians move**, through the same `vinci.cohort` functions the
    queue uses. Bituminous Coal, 07-29: −29.4% → −57.0%. Life Insurance, 07-29: −9.0% → +1.7%.
    Radiotelephone, 09-22: −24.5% → −17.4%.
  - **Ranks are unaffected** (cohort reads are context attached after ranking).
  - **47 of the 343 served names' cohort reads change**, and 2 calls flip ("own" → "unresolved"):
    JBGS and ORC. They show at the next queue re-render; the committed queue matches the
    pre-prune reads 343 of 343.

**HOW VERIFIED.**
- **`tests/test_rename_alias.py`, 14 pins.** Frozen REAL records (`tests/fixtures/rename_hlx_hos.json`):
  both Polygon records, both tickers' bars, and the HLX bars the 10-16 store held.
  - FIGI confirms; a different FIGI refuses; no FIGI refuses; only an inactive same-class sibling
    costs a call; the boundary is the first session, never `list_date` (SVIA's shape).
  - The table only grows.
  - The new id gets the old id's history: Polygon wins on a shared session, the old id is
    untouched, a second carry neither writes nor asks.
  - A held copy on an old split basis is restated (counterfactual 2:1).
  - A bar the old id holds after the rename is never carried (L7's reused-ticker mirror).
  - The screen can evaluate HOS after the carry.
  - The builder writes the alias and carries.
  - The heir of an incumbent keeps the slot (counterfactual sibling), and incumbency follows a
    chain of renames (A → B → C; review round 0).
- **`tests/test_cohort_pool_registered.py`, 2 pins.** The call site; end to end on the committed
  pool, none of the named failure lines remains and OBAI (a common the feed names like a bond)
  does.
- **Mutations: 10 of 10 red on the rename.** Incumbency not following; FIGI not compared; active
  siblings as candidates; share class ignored; the listing cut-off dropped; held copies winning;
  no restatement; carry every build; aliases never written; bars never carried.
- **No paid model call.**

**BOUNDARY.**
- **Rename counts:** Polygon `/v3/reference/tickers` pulls of 2026-07-13, 07-14, 08-08, 08-17,
  08-28, 08-31, 09-22 and 10-17. A class is one `(cik, share_class_figi)`; "touches a
  population" means one of its ids is in the committed primary snapshot of 2026-08-24 (#553),
  2026-09-22 or 2026-10-16.
- **Real run:** reference date 2026-10-16, primary band, main's population (2,065; #828 held, not included).
- **Pool prune:** the committed `cohort_pool.jsonl` at this branch's base. Every pooled line the
  feed types `CS` and NAMES preferred / depositary / pfd / notes / debentures / bonds (62 lines)
  was confirmed against its issuer's cover at each run's own date. Pooled lines with no such word
  were not cover-checked by the prune; the builder checks every `CS` line from now on.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A line Polygon gives no share-class FIGI is never aliased** (DMC, PLGO). Its record stays
   split.
2. **Each candidate costs about three Polygon calls the first time** (today's record, the old
   ticker's dated record, the new ticker's bars), and the old ticker's bars once more for the
   carry. 49 calls on the 10-16 replay. After that the alias is known and costs nothing.
3. **The carry runs once per rename.** A split the source applies to the old ticker AFTER the
   carry is caught only by the anchor restatement on the new id's own bars.
4. **The committed queue's cohort context is stale for 47 names until the next re-render.** A
   re-render needs the structural scan's EDGAR calls, so it is left to the weekly run.
5. **A line renamed TWICE carries only its last step's bars.** C gets B's bars, and B holds A's
   only if B was ever admitted (review round 0, deferred: no chain exists in the measured
   renames). Incumbency DOES follow the whole chain.
6. **Old ids in the ledger are not mirrored forward.** No ledger row is on a renamed line today.
   If one were, its scoring would stop at the rename (StaleExitError, #820). FALSIFIER: a ledger
   row whose id has a successor in the alias table.
