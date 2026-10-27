---
id:
status: open
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# As-of invariance is pinned as properties: a read at date d is the same read however the filings and bars after d turn out

**WHAT.** `tests/test_as_of_properties.py`, test-only, plus one test dependency: `hypothesis>=6.100`
in the `dev` extra of `pyproject.toml`. The `gate` workflow installs `.[dev]`, so it installs
Hypothesis with no workflow change (`.github/workflows/gate.yml`, step "Install"). No production
file changes.

Six properties. Each names the contract line it pins:

| property | contract line | where |
|---|---|---|
| a snapshot read as of d equals the snapshot of the blob as it stood on d, however the rows filed after d are changed; the client's as-of path reads the same | "``as_of`` reads the facts as they stood on that date — every row FILED after it is dropped before anything is read" | `compute_fundamental_snapshot`, `EdgarClient.fundamental_snapshot` |
| a 10-K filed after d reporting a fiscal year one to four years ahead never moves what `behind_filer` judges | an annual is judged against "the filer's newest fiscal year" | `concepts.behind_filer` / `filer_fiscal_year`, through the snapshot |
| the cut blob is exactly the rows filed by d, in every namespace, with nothing empty left behind | "every row FILED after it removed, same shape"; "a unit, tag or namespace left with no row is dropped too" | `concepts.facts_as_of` |
| `close_as_of` answers what a store holding only the bars to d answers, and that answer is the latest close on or before d, or the refusal | "Latest close ON OR BEFORE ``reference_date``"; "this never reaches past ``reference_date``"; "if there is no bar on or before ``reference_date`` it raises" | `Store.close_as_of` |
| `relative_return` (G2's input) reads the same from the bars to d as from any bars after it | each series ends on "its latest bar at or before the reference date"; "BOTH LEGS END ON THE COMMON LAST BAR" | `relative_return` → `features.frontier` |
| `compute_price_features` reads a bar history in any order | "from a bar history (any order; sorted internally)" | `compute_price_features` |

The last one is the only permutation property and there is no monotonicity property, because no
other reader on these paths states one. It is not an as-of property (see below).

**HOW THE EXAMPLES ARE MADE.** Every example starts from a REAL committed blob and changes only
what was filed after d.

- *Facts.* The 61 companyfacts fixtures in `tests/fixtures/{companyfacts,annual_pairs,stale_annual,
  net_debt_shapes}/`. A row filed after d can be dropped, revalued (including 0, ±1e15),
  re-dated (period moved, duration kept), re-filed later, stripped of its filing date, moved to
  another of the blob's own tags in either namespace, or duplicated. In bulk, every later row can be
  dropped, scaled or shifted, or a 10-K filed after d can report fiscal years that have not
  happened yet. Tags come from the blob, never from `CONCEPT_ALIASES`. The re-tag session is
  changing the alias lists now, and the properties do not read them.
- *Cut dates.* Drawn on a filing day, the day before, the day after, or anywhere in the blob's
  filing history. A cut that leaves nothing filed after it is rejected.
- *The oracle.* The blob as it stood on d is built in the test, not by `facts_as_of`, and read
  with no cut. So one equality covers both halves: a later row that reaches a reader changes the
  left side, and a row filed by d that goes missing changes it too.
- *Bars.* The 24 committed series in `tests/fixtures/prices/` (23 names + IWM, 470 bars each,
  2024-12-02 → 2026-10-16). A bar after d can be dropped or repriced, and new bars can be added
  after d. The list handed over is out of order.
- *Bounded and deterministic.* Each property is parametrized over every blob or every name, at
  `max_examples=12` (4 for the permutation property), with `derandomize=True`, `database=None` and
  `deadline=None`, and the `too_slow` health check is off (drawing an example parses a real
  blob). CI reruns the same examples and cannot flake on timing. One draw over the whole corpus
  reached only 25 of the 61 blobs in 150 examples, which is why the run is per blob.
  Hypothesis writes `.hypothesis/constants/` anyway, and that directory ignores itself.

**HOW VERIFIED.**

1. *Green on main's code* (`56500bb1`): 240 cases pass (1 corpus check + 61 + 48 + 61 snapshot-side
   + 3 × 23 price-side), ~30 s serial on this machine.
2. *Each property is red under a mutant that reads one post-cut fact.* Thirteen mutants, each
   applied to one production file in this worktree, run against the property tests it targets with
   `-x`, then restored byte-for-byte and checked with `git diff --quiet`. Harness kept outside the
   repo.

   | mutant | file | snapshot | later 10-K | cut blob |
   |---|---|---|---|---|
   | M1 the newest fiscal year read off the whole blob, before the cut | `edgar/client.py` | **red** | **red** | green |
   | M2 net debt read off the whole blob | `edgar/client.py` | **red** | **red** | green |
   | M3 ONE leg (diluted EPS) read off the whole blob | `edgar/client.py` | **red** | **red** | green |
   | M4 the cut admits rows filed the day after | `edgar/concepts.py` | **red** | **red** | **red** |
   | M5 the cut drops rows filed ON the cut day | `edgar/concepts.py` | **red** | **red** | **red** |
   | M6 the cut skips the dei namespace | `edgar/concepts.py` | **red** | green | **red** |
   | M7 the cut on the period end, not the filing date | `edgar/concepts.py` | **red** | **red** | **red** |
   | M8 the cut leaves empty units behind | `edgar/concepts.py` | **red** | green | **red** |
   | M9 the client drops `as_of` | `edgar/client.py` | **red** | green | green |

   | mutant | file | `close_as_of` | `relative_return` | any order |
   |---|---|---|---|---|
   | M10 `close_as_of` reads one day past its date | `store/store.py` | **red** | green | green |
   | M11 `close_as_of` reaches FORWARD when nothing is on or before | `store/store.py` | **red** | green | green |
   | M12 `frontier` ignores the reference date | `eod/features.py` | green | **red** | green |
   | M13 `compute_price_features` stops sorting | `eod/features.py` | green | green | **red** |

   13 of 13 killed, and every property is red under at least one. A green cell is a mutant outside
   that property's reach. The cut-blob property cannot see a reader handed the uncut blob (M1–M3,
   M9), which is why the snapshot property exists. The snapshot property caught M6 only through a
   later row moved into dei, which hides that tag's us-gaap rows (`points_for_tag` takes the first
   namespace present). The cut-blob property sees every later dei row, on the 29 blobs that carry
   dei.

   *M1 on real data, shrunk by Hypothesis to `annual_pairs/AMZN` as of 2010-01-29* (the day its
   FY2009 10-K was filed). The snapshot reads EBITDA $1,507M, dated 2010-01-29. With the fiscal year
   taken off the whole blob, FY2009 is "6025d behind the filer's newest fiscal year
   (DepreciationDepletionAndAmortization to 2026-06-30)" and EBITDA is UNKNOWN. That is the class
   #821's `behind_filer` opened: a later filing moving what is judged stale.

**SEEN, NOT FIXED — both on the screen's price side, outside this lane.**

- **`compute_price_features` is not an as-of read.** It takes `latest = bars[-1]`, whatever
  `reference_date` is. The screen hands it `store.get_price_history(...)`, every stored bar
  (`screens/run.py:137`). A `vinci screen --ref <past>` replay on a store refreshed since that date
  reads G1's drawdown off a later bar. Measured on the committed AMZN bars at reference 2025-12-31:
  given every bar, `last` reads $250.00 dated 2026-10-16, PRESENT, and the drawdown −12.95%; given
  the bars to the date, $230.82 dated 2025-12-31 and −10.74%. The dossier's maintenance route already
  truncates prices before this call (2026-10-26 record). The screen route does not. The
  fundamentals half of the same replay gap is already recorded
  (`docs/records/2026-10-26-fundamental-snapshot-as-of.md`, "No caller passes it yet").
- **G3's split refusal reads restatements filed after the reference date.** `pe_current_and_percentile`
  runs `share_basis_change` over every annual EPS point in its window, whatever its filing date.
  NFLX as of 2025-06-30: given every point, the percentile is refused (the 10-for-1 restatement filed
  2026-01-23). Given only the points filed by then, it reads 0.748. The current P/E is 6.75 either
  way: a split-adjusted price over the pre-split $19.83. The refusal is the more correct read here,
  because the stored bars carry the later split basis too. A G3 replay needs prices on the basis of
  their date, which no EPS cut can supply. Not pinned, since no contract states an as-of read.

**BOUNDARY.** Corpus: 61 companyfacts fixtures (30 `companyfacts`, 8 `annual_pairs`, 10
`stale_annual`, 13 `net_debt_shapes`; the 13 carry balance-sheet lines only, so the fiscal-year
property runs on 48) and 24 price series of 470 bars, all as committed at `56500bb1`. Examples:
12 per blob or name per property (4 for the permutation property), so 2,684 examples in 240 test
cases per run.
AMZN and NFLX probes: the committed fixtures at `56500bb1`, measured 2026-10-27. Mutation counts:
13 mutants, run 2026-10-27 on `56500bb1`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **~30 s on a ~17 min serial suite.**
- **The examples change when Hypothesis does.** `derandomize` fixes them per Hypothesis version, and
  the gate installs the newest. A property that holds only for most examples could then go red on a
  version bump. Each property here is meant to hold for every example. A red after a bump is a
  real counterexample, to be read, never retried.
- **The properties pin the wiring, not the readers.** If `facts_as_of` returns the right blob, every
  reader downstream is cut by construction, which is the #801 design. What a property catches is
  a reader handed something other than the cut blob, or a cut that is wrong.
