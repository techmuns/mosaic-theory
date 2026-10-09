---
id:
status: shipped
date: 2026-10-09
prs: [697]
supersedes:
superseded-by:
---

# The machine proposes R4 — the three ratified conditions read off the page, AMZN and UBER the only names they select, and a committed recipe still wins

**WHAT.** The build now proposes `R4_forward_ev_ebit` when the operator's three ratified conditions
all hold (`vinci/dossier/recipe_proposal.py`):

| condition | the machine reads | ruled 2026-10-09 |
|---|---|---|
| 1. NTM EBIT > 0 | CIQ's NTM TEV/EBIT (`forward_consensus.current_multiples`) | present and positive |
| 2. R1 cannot anchor | R1's own `applicable`, and `financial_summary.ebitda_basis.divergent` | declines, OR the EBITDA basis is divergent |
| 3. R3 cannot price it cleanly | `forward_consensus.pe_eps_basis.fiscal_years`, and `quality.nonoperating_quarters` | FY P/E struck on GAAP EPS AND ≥2 of the trailing four quarters material |

**How it behaves:**
- **It fails closed.** A condition whose input is missing is UNKNOWN, and an UNKNOWN proposes
  nothing.
- **Only the recipe and its reason change.** The reason names each condition with the value it
  was read from. R1's computed values and its `applicable` bit stay.
- **Both writers apply it:**
  - the assembler, before `_write` keeps the committed recipe;
  - `anchor-backfill`, before `preserve_operator_tag`.

**THE STRUCTURED COUNT.** Condition 3 needed a number that existed only inside a sentence. The
non-operating read computed "3 of the trailing four quarters carry a material block" and wrote it
only into prose. It now also emits `quality.nonoperating_quarters`
`{material, window, window_end, source_ref}`. The window, the per-quarter arithmetic and the
materiality test are now one set of module-level helpers (`_nonop_common`, `_nonop_arms`,
`_nonop_material`), read by the prose and the count alike. The field is absent until built, and
version row `2026-10-09.2` names it, with its JS twin.

**WHY.**
- The next step in the ruled build order (STATE row 10). Operator instruction, 2026-10-09: "start
  the machine proposal".
- The three machine definitions were ruled the same day, as recommended: R1 declines or the EBITDA
  basis is divergent; at least 2 of 4 quarters material; and the proposal lands in the recipe hint,
  with the operator's tags winning.

**A CORRECTION, MADE BEFORE BUILDING.**
- **What I had said.** The first question to the operator stated that UBER's machine `R2_NEEDED`
  would become R4 at its next build.
- **Why it was wrong.** `preserve_operator_tag` records no provenance and keeps ANY committed
  recipe. `R2_NEEDED` is the machine's on UBER, NCNO and MVST and the operator's on AORT and VITL
  (#671), so the rule cannot tell them apart.
- **The ruling, re-asked with the facts.** Keep the rule. The R4 proposal shows on AMZN and UBER as
  "this build proposes R4", never written over a committed recipe, and the operator re-tags both.

**HOW VERIFIED.**
- **The prose did not move.** The non-operating sentence was computed for all 26 pages with main's
  code and with this branch's, from the same cached EDGAR facts. It is byte-identical on 26 of 26.
  Every count matches its sentence (3/4 ↔ "3 of the trailing four", 0/4 ↔ "no material item",
  1/4 ↔ a single named quarter). Where the prose is UNKNOWN (BURL, LLY, NCNO, NKE, TECX) the count
  is absent, never invented.
- **The rule on all 26 pages,** with the count from the new extractor: it proposes R4 for **AMZN
  and UBER and no other name**, the ratified table. Each refusal is the right one:
  - GOOGL: the FY P/E is struck on normalized EPS;
  - AORT: GAAP-struck, but 0 of 4 quarters are material;
  - VRRM: R1 anchors;
  - FUBO, ORKA, TECX: no NTM multiple, so UNKNOWN.
- **Assembly's write step on real copies** of AMZN and UBER, with R1 computed fresh from EDGAR:
  - the fresh proposal is R4;
  - the written recipe stays R3 on AMZN and `R2_NEEDED` on UBER;
  - the caveat reads "This build's own read proposes R4_forward_ev_ebit … This build's own reason:
    EV/NTM EBIT (R4) — all three ratified conditions hold: …".

  A page with no committed recipe was written R4.
  - *My first demo printed AMZN's OLD caveat* ("proposes R1"). It started from the committed
    page's caveat list, where a real build starts empty. Re-run with the build's own caveats, it
    names R4.
- **`vinci anchor-backfill --tickers AMZN,UBER`,** run for real on copies carrying the count, with
  live EDGAR: "PRESERVED committed recipe_hint 'R3_forward_pe' (machine proposed
  'R4_forward_ev_ebit')", the same for UBER, and both pages left byte-identical.
- **Tests** (`tests/test_r4_machine_proposal.py`, 14). The count is derived through the real
  extractor from each name's committed companyfacts fixture. They pin:
  - the count and the prose as one read, on every name with a fixture;
  - the ruled selection (AMZN and UBER only);
  - each condition failing on the real page that fails it;
  - fail-closed on a missing input, including every committed page as it stands, so the rollout is
    inert until the count lands;
  - both sides of the 2-of-4 ruling;
  - condition 2's two routes, each alone;
  - R1's own `applicable` bit;
  - only the recipe and reason change;
  - the recipe id equal to the engine's;
  - assembly keeping a committed recipe with the R4 caveat, and a new page taking R4;
  - both writers' wiring;
  - the field absent until built.
- **Mutation.** Thirteen mutants, all killed. One survived the first run and is now pinned:
  dropping condition 2's "declines" route went unnoticed, because UBER also qualifies through its
  divergent EBITDA basis.

  | mutant | tests failing |
  |---|---|
  | condition 1 inverted | 5 |
  | the count drops the revenue arm | 4 |
  | condition 2 drops the divergence route | 3 |
  | condition 3 ignores the EPS basis | 2 |
  | an UNKNOWN counts as met | 2 |
  | condition 3 threshold 1 | 1 |
  | condition 3 threshold 3 | 1 |
  | the proposal flips `applicable` | 1 |
  | the assembler never proposes | 1 |
  | `anchor-backfill` never proposes | 1 |
  | the count reads a 3-quarter window | 1 |
  | null written when absent | 1 |
  | condition 2 drops the declines route | 1 (survived until the two-routes pin) |

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @ee692651.
- **Counts:** live EDGAR companyfacts via the cache, measured 2026-10-09; the tests use the
  committed fixtures.
- **"Selects":** all three conditions met.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The proposal is inert on today's pages.** No committed page carries `nonoperating_quarters`,
  so condition 3 is UNKNOWN everywhere until a re-assembly computes the count, or a pass lands it.
  The operator's AMZN and UBER re-tags do not wait on that.
- **Condition 1 reads a TEV multiple's sign.** A name whose TEV is negative (net cash above market
  cap) would invert it. No committed name is in that state.
- **The machine still cannot tell a hand tag from its own** (`preserve_operator_tag`). The operator
  ruled to keep that rule; recording provenance is its own build if ever wanted.
- **Next:** the operator's re-tags, AMZN R3 → R4 and UBER `R2_NEEDED` → R4. The first R4 record
  follows.
