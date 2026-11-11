---
status: recorded
date: 2026-11-10
prs: [950]
supersedes:
superseded-by:
---

# The machine proposal's vote rule, as a pre-registered design (design only, $0): today a build proposes only when every COMPLETED draw of five agrees, and that rule's chance of proposing sits between 10% and 90% for any name whose lean commits on 63% to 98% of draws, so a re-draw flips it. Three options for the operator, side by side: A keeps five draws under one rule that holds its meaning at any draw count (a one-sided binomial test that the lean is the majority read, which at five draws IS today's rule), with failed draws as dissent and the split sealed beside every proposal ($0 a build); B adds ten draws, 9 of 10 to propose (+$1.00 to +$1.50 a build, recommended); C, the operator's, adds sequential draws, hysteresis, a borderline outcome and a confirmation at log time, and its first two parts publish a wobbly name more often than today. The measurement is re-scoped to the independence of draws, which all three assume. DECIDED 2026-11-10 (operator: "decide as per the expert team"): Option A with C(iii)'s borderline outcome and C(iv)'s ten-draw confirmation at log-verdict, and the four-builds-a-page independence measurement at a $110 cap (§9). No code changes in this record

**THE ASK.** Operator, 2026-11-09, verbatim: **"start ... the other two fixes in the correct manner"**.
For this one the agreed manner (the coordinator's brief) is to fix the fragile BUY vote rule
separately from #930, as a pre-registered design. #930 merged as `f491d155`. This record is that
design. It changes no code: not the proposal, not the lean, not the draw count.

**THE SECOND ASK.** Operator, 2026-11-10, "yes" (relayed by the coordinator): add an **Option C**
beside A and B before choosing, at $0 and under the same discipline: sequential sampling,
hysteresis for names already proposed, three outcomes, and a confirmation at decision time (§5b);
C's cost from the measured tallies; and the measurement re-scoped to C's needs, centred on the
independence of draws (§7).

**THE DECISION.** Operator, 2026-11-10, verbatim: **"decide as per the expert team"** (relayed by the
coordinator, who made the choice under that delegation): **Option A + C(iii) + C(iv)**, with the
independence measurement at four builds a page, **cap $110**. The reasons, the sequence and what it
accepts are §9. The design's own recommendation (B with C(iii)) stays below as written; the
decision departs from it on cost per build, and §9 says how.

**THIS IS A DECISION-PATH CHANGE, FLAGGED.**
- CLAUDE.md: the proposal mapping is face-validity-frozen and never outcome-tuned.
- This design leaves the three-row mapping exactly as it is (bullish → the long leg, bearish → its
  twin, mixed → nothing). It changes the gate beside it, which `verdict.derive_proposal` calls
  "the REPRODUCIBILITY GATE, and it is deliberately OUTSIDE the mapping", and the draw count, which
  is an operator ruling of 2026-09-26 (`synthesis.SYNTHESIS_DRAWS`).
- Both are on the decision path. The implementing PR edits decision-line files, so the edit hook
  asks the operator, and it needs a real shown run before merge (CLAUDE.md).
- **Option C crosses two lines further, each the operator's to overrule in words (§5b):**
  - its sequential draws cross the 2026-09-26 ruling that N is fixed for every name;
  - its hysteresis makes the proposal depend on the previous page, not on the build alone, which
    is CLAUDE.md's "derived DETERMINISTICALLY from its committed evidence lean".

**HOW THE RULE IS CHOSEN: FACE VALIDITY ONLY, IN WRITING.**
- The rule is chosen by what it tests and by its error rates as functions of a name's lean rate
  p. It is never chosen by forward or historical returns, and never by which names it would
  propose or withhold.
- No candidate below was scored on any page's tally. Every table is a function of p alone.
- The only page figures in this record are the finding (§2), as #925, #931 and #935 already
  published them, and one $0 check that two of those arms sent the same request.
- **Disclosed order:** the operating-characteristic table (§4) was computed before the criteria
  (§3) were written. The criteria read p only, never a name, but they were not written blind to
  which candidates pass them. Two choices made after the table are named where they are made:
  - C2's anchor: the first draft's own 2/3 was replaced by the 2026-09-26 ruling's 0.60;
  - the counting convention, which changes the pass set by one N (§4).

## 1. Where the rule is (code at main `fd123ada`)

- **The draw count:** `vinci/dossier/synthesis.py:1667`, `SYNTHESIS_DRAWS = 5`. Its comment
  (1643–1666) records the 2026-09-26 ruling: five, "chosen on the error rates of the unanimity
  gate below and NOT on cost". It also states the ceiling: "unanimity is a weak detector of
  mildly-wobbly names at ANY practical N … Catching those needs a different RULE, not a bigger N."
  `vinci/dossier/assemble.py:1281` passes it (`draws=SYNTHESIS_DRAWS`).
- **The lean across draws:** `synthesis.synthesize` (1723–1872); the draw loop is 1795–1828.
  - Each draw that returns a complete tool call is "completed". Its `evidence_balance` goes
    through the one shared parser (`verdict.split_lean`), and its label is kept as
    `.strip().lower()` (1828). A label that does not parse is its own bucket (`""`), so it cannot
    join the majority.
  - A draw that raises (1803), or returns an incomplete call (1820), is not counted at all.
  - `tally = Counter(...)` over the completed draws (1848). The modal label is the most common
    one, ties broken by the earliest draw (1849). The page keeps the first draw carrying it (1850).
  - **The gate's input:** `unanimous=len(tally) == 1`, written only when `attempted > 1` (1855–1856).
    A split build adds a page flag (1865–1871).
- **The gate:** `vinci/dossier/verdict.py:115–156`, `derive_proposal`.
  - The mapping keys a label as `re.sub(r"\s+", "-", label.strip().lower())` (140).
  - After the mapping picks an action, line 151 (`if draws_unanimous is False:`) withholds it.
  - `None` (a single-draw artifact) is "not measured" and passes.
- **Where it is read and recorded:**
  - **The ledger,** which seals the proposal at log time:
    - `vinci/cli.py:1491–1494` reads the committed dossier's `draw_agreement.unanimous`;
    - `vinci/ledger/workflow.py:120–250` writes `machine_proposal` and `machine_lean`, the two
      fields of `vinci/schemas/ledger.py:205–206`. The tally is not sealed.
  - the markdown brief's proposal line: `vinci/dossier/render.py:3919–3922`;
  - the reproducibility line: `render.py:2870` and `frontend/views/shared/dossier.js:1470–1483`
    (the web prints no proposal, by the user decision recorded at `dossier.js:1540`);
  - **the panel rule's boundary test:** `vinci/evals/panel.py:157–167`, `_boundaries`. It
    hard-codes `total == 5`, and calls a proposal "on the boundary" at 4 or 5 committed of five;
  - the harness's mirror of production: `vinci/evals/compare.py:571–578`, `_proposal`;
  - the cost series, which copies the tally whole: `vinci/dossier/run_metrics.py:123`.
- **The record it reads:** `vinci/dossier/schemas.py:3048–3065`, `DrawAgreement` (`attempted`,
  `completed`, `labels`, `unanimous`).

## 2. The finding

- **LLY's proposal moves with the draws.** LLY's committed-lean draws, as the panel records give
  them:
  - #931: BASE bullish 5 → CAND bullish 4 / mixed 1, so the proposal went BUY → withheld
    (`docs/records/2026-11-09-fix4a-measured-on-the-panel.md` §4);
  - #935: BASE bullish 3 / mixed 2 → CAND bullish 5, so the proposal went none → BUY
    (`docs/records/2026-11-09-fix3b-measured-on-the-panel.md` §4).
  - **#931's CAND and #935's BASE sent the same request,** checked here at $0 rather than taken
    from the records:
    - LLY captured at `564baad8` with #931's six transforms, and at `622786a2` with #935's seven
      (the seventh, `current_buybacks`, is the identity at that ref);
    - the two are wire-equal, and both hash to `6515cd17c893`, #935's registered BASE pin.
    - So the 7 of 10 those two arms read are ten draws of one request.
  - At a 0.7 bullish rate, five of five occurs 16.8% of the time; at 0.8, 32.8%; at 0.95, 77.4%
    (so #925's 22.6% withhold at a 1-in-20 dissent rate).
- **Why it moves. It is what any count rule does, not an anomaly of LLY.**
  - A rule that proposes when x of N draws carry the lean publishes with probability
    q(p) = P(X ≥ k | N, p).
  - Two builds on identical input then disagree with probability 2q(1 − q). That is 0.5 at the
    rule's threshold (q = 0.5) and falls off on either side, as fast as the curve is steep.
  - Under five of five, q sits between 0.1 and 0.9 for every p from 0.631 to 0.979. That band holds
    nearly every name whose lean commits most of the time.
- **Found, not fixed (1): one completed draw passes the gate.**
  - The gate counts COMPLETED draws, and writes the tally whenever `attempted > 1`. So a five-draw
    build with four failed draws records `unanimous=True` and proposes.
    - The page prints "all 1 of 5 draws on this build returned the same lean".
    - The code's own comment says "ONE DRAW IS NOT AGREEMENT", but it guards attempted, not
      completed.
  - **No committed page is in that state.** 19 of the 27 pages at `fd123ada` carry a five-draw
    tally, every one 5 of 5 completed, and 8 carry none.
  - **It is reachable.** The 2026-09-01 regression the code describes returned an unusable tool call
    "perhaps half the time" (`synthesis.py:1805`).
- **Found, not fixed (2): two spellings of one lean are two buckets.**
  - The tally keys labels as `.strip().lower()` (`synthesis.py:1828`), while the mapping collapses
    whitespace to hyphens (`verdict.py:140`). So "Strongly bullish" and "strongly-bullish" are
    separate tally buckets, though both map to BUY. A build split only by spelling is non-unanimous
    today, and its proposal is withheld.
  - **Latent:** the 19 tallies on file hold three spellings only (`strongly-bullish`, `mixed`,
    `strongly-bearish`).
- Both are on the decision path, so they are fixed by R1 and R3 below, not here.

## 3. Face-validity criteria (read p only)

- **C1. The rule says what it tests, and the words hold at any N.** A rule that means one thing at
  five draws and another at ten has been tuned, not chosen.
- **C2 and C8: no worse than today at either end of the 2026-09-26 table.** That ruling's table
  (`synthesis.py:1646–1653`) names the two failure directions with reference rows of its own:
  - its 0.60 row, a wobbly name, where publishing is the error;
  - its 0.95 row, a solid name, where the 23% withhold is "a FALSE withhold, the price paid".
  - **C2:** a p = 0.60 name publishes no more often than today. Withholding stays the cheap side,
    by that ruling's own asymmetry (`synthesis.py:1655–1658`): a withheld proposal costs a hint,
    while a published noisy one feeds the anchoring risk STATE.md records.
  - **C8:** a p = 0.95 name is withheld no more often than today (22.6%).
  - These anchors predate this design. **Corrected before commit:** the first draft anchored C2 at
    p = 2/3, a value of its own. Under 2/3 only ten draws pass; under the ruling's 0.60, more do
    (§4). The ruling's rows replace the draft's own.
- **C3. The rule's unstable band narrows.** That band is the range of p where 0.1 ≤ q ≤ 0.9.
- **C4. N is fixed in advance and the same for every name** (`synthesis.py:1664–1666`). So a
  sequential rule (draw five, and add more only on a split) is out, however it is pre-registered.
  - Option C(i) is such a rule, and is set out at the operator's request (§5b). Choosing it
    overrules this criterion with the ruling it restates.
- **C5. A draw that fails, does not parse or carries no recognized lean counts against the
  lean.** The denominator is the draws ATTEMPTED.
- **C6. The split is shown beside every proposal and sealed with it,** so a reader can tell a 10/10
  BUY from a 9/10 one, and a 5-of-5 page from a 3-of-5 one.
- **C7. No committed page moves until it is rebuilt.** Every artifact on file decides as it does
  today.

## 4. The candidates, by their operating characteristics alone

Every number below is exact binomial arithmetic in p, with no page in it. q is the probability
that a build publishes when the modal committed lean has rate p.

**Two counting conventions, and the choice is disclosed, not hidden.**
- **Modal-only (the tables below):** q counts a publish of the modal lean only.
- **Either-label (the 2026-09-26 table's):** that table counts p^N + (1 − p)^N, a publish of
  either label. Its 0.60 row reads 8.8% where modal-only reads 7.8%.
  - The second term is a build where the other label clears the bar. It proposes only if that
    label is itself committed.
- **The second term at p = 0.60,** in points: 5/5 1.02; 7/7 0.16; 8/9 0.38; 9/10 0.17; 8/10 1.23;
  10/10 0.01; 15/20 0.16. It is not uniformly small: 8/10 carries 1.23.

**One family states what it tests at every N (C1):** "a one-sided exact binomial test rejects
'this lean is not the majority read' (p ≤ 1/2) at 5%". Equivalently, the one-sided 95%
Clopper–Pearson lower bound on the lean's share exceeds one half. Its k at each N is the least x
with P(X ≥ x | N, ½) ≤ 0.05:
- N = 5: k = 5 (0.031; four of five gives 0.188). **This is today's rule exactly.** Unanimity of
  five is this test, written in the only form it has at five draws.
- N = 7: k = 7 (0.008). N = 9: k = 8 (0.0195; seven of nine gives 0.090).
- N = 10: k = 9 (0.0107; eight of ten gives 0.0547).
- N = 12: k = 10. N = 20: k = 15 (0.0207).

**P(publish), modal-only q:**

| rule | k/N | p 0.6 | 0.7 | 0.8 | 0.85 | 0.9 | 0.95 | band (0.1 ≤ q ≤ 0.9) | q = 0.5 at |
|---|---|--:|--:|--:|--:|--:|--:|---|--:|
| today: the test at five draws (unanimity) | 5/5 | 0.078 | 0.168 | 0.328 | 0.444 | 0.590 | 0.774 | 0.631–0.979 (0.348) | 0.871 |
| the test at seven draws (unanimity) | 7/7 | 0.028 | 0.082 | 0.210 | 0.321 | 0.478 | 0.698 | 0.720–0.985 (0.265) | 0.906 |
| the test at nine draws | 8/9 | 0.071 | 0.196 | 0.436 | 0.599 | 0.775 | 0.929 | 0.632–0.939 (0.308) | 0.820 |
| **the test at ten draws** | **9/10** | **0.046** | **0.149** | **0.376** | **0.544** | **0.736** | **0.914** | **0.663–0.945 (0.282)** | **0.838** |
| 8 of 10 | 8/10 | 0.167 | 0.383 | 0.678 | 0.820 | 0.930 | 0.988 | 0.550–0.884 (0.334) | 0.741 |
| two five-draw runs both unanimous (= 10/10) | 10/10 | 0.006 | 0.028 | 0.107 | 0.197 | 0.349 | 0.599 | 0.794–0.990 (0.195) | 0.933 |
| the test at twenty draws | 15/20 | 0.126 | 0.416 | 0.804 | 0.933 | 0.989 | 1.000 | 0.585–0.834 (0.249) | 0.721 |

**Two builds of one input disagree, 2q(1 − q):**

| rule | p 0.6 | 0.7 | 0.8 | 0.85 | 0.9 | 0.95 |
|---|--:|--:|--:|--:|--:|--:|
| today, 5/5 | 0.143 | 0.280 | 0.441 | 0.494 | 0.484 | 0.350 |
| 7/7 | 0.054 | 0.151 | 0.331 | 0.436 | 0.499 | 0.421 |
| 8/9 | 0.131 | 0.315 | 0.492 | 0.480 | 0.349 | 0.132 |
| 9/10 | 0.088 | 0.254 | 0.469 | 0.496 | 0.389 | 0.157 |
| 8/10 | 0.279 | 0.473 | 0.437 | 0.295 | 0.131 | 0.023 |
| 10/10 | 0.012 | 0.055 | 0.192 | 0.316 | 0.454 | 0.481 |
| 15/20 | 0.220 | 0.486 | 0.315 | 0.126 | 0.022 | 0.001 |

**Which N pass both ends (C2 and C8), for the test at N from 6 to 30:**
- **modal-only:** N = 9 and N = 10, beside today's 5;
- **either-label:** N = 9, 10 and 12. At N = 12 (10 of 12), q(0.60) is 8.63%, against today's
  8.80%. Modal-only fails it, at 8.34% against 7.78%.
- **The convention changes the pass set by one N.** Ten narrows the band most in both sets: 0.282,
  against 0.290 at twelve and 0.308 at nine. So the recommendation does not ride on the
  convention.
- **The rest fail one end:**
  - at 6 and 7 draws the test is unanimity again, which withholds a solid name more often (C8);
  - at 8, 11, and every N from 13 to 30, it publishes a wobbly name more often (C2).

**Each candidate against the criteria:**
- **8 of 10** (the brief's example) is this test at α = 0.0547, not 0.05. It fails C2: a p = 0.60
  name publishes 16.7% of the time (17.9% either-label), against 7.8% (8.8%) today.
- **Agreement across two independent runs** (both five-draw builds unanimous) is unanimity of ten.
  It narrows the band most (0.195), but fails C8:
  - a p = 0.95 name publishes 59.9% of the time, and its builds disagree 48.1% of the time;
  - it makes the proposal rarer, not steadier, for exactly the names that commit.
- **The test at twenty draws** fails C2 (12.6%). A bigger N makes the test confident at a lower p.
  That is honest, but more permissive than the ruling's asymmetry allows.
- **The test at seven draws** fails C8 (69.8% published at p = 0.95, against 77.4%).
- **The test at nine draws (8 of 9)** passes C1–C8. Its band narrows to 0.308, and it publishes
  less than today only below p = 0.63.
- **The test at twelve draws (10 of 12)** passes only under the either-label convention. Its band
  is 0.290, and it costs two draws more than ten.
- **The test at ten draws (9 of 10)** passes C1–C8 under both conventions:
  - its band narrows furthest, to 0.282 (C3);
  - it publishes less than today at every p up to 0.74, a wider range than nine draws' 0.63;
  - a p = 0.60 name publishes 4.6% (7.8% today, 7.1% at nine draws);
  - C7: at five draws the same test decides every committed artifact as today.

**What it does NOT fix, said plainly:**
- A name sitting at the rule's threshold still flips on re-draw. At p = 0.8, two ten-draw builds
  disagree 46.9% of the time, against 44.1% for today's five-draw ones. No rule at an affordable N
  stops that.
- The gain is at the ends of the range:
  - a p = 0.95 name publishes 91.4% of the time (77.4% today), and its builds disagree 15.7% of the
    time (35.0% today);
  - a p = 0.60 name publishes 4.6% of the time (7.8% today).
- LLY's one request read 7 of 10 over two arms. A name like that sits in the band under every
  candidate. **For such a name, the split printed beside the proposal (R4) is the mitigation that
  works,** not the rule.

## 5. The proposal (for the operator's ruling; nothing is built)

- **R1. The gate is the binomial test.**
  - The mapping's action is proposed only if x, the modal committed lean's count among the N
    ATTEMPTED draws, has P(X ≥ x | N, ½) ≤ 0.05.
  - The gate's words: "a one-sided exact binomial test says this lean is the input's majority read,
    at 5%".
  - **The tally keys each label as the mapping does** (`verdict.py:140`'s collapse of whitespace
    to hyphens), through ONE shared helper. So the tally and the mapping cannot disagree about which
    lean a draw carries, which closes §2's second hole.
- **R2. N = 10** (`SYNTHESIS_DRAWS` 5 → 10), fixed for every name. k = 9.
- **R3. A failed, unparsed or unrecognized draw is dissent.** This closes §2's one-completed-draw
  hole by construction: 1 of 5 attempted fails the test.
- **R4. The split is shown beside every proposal, and sealed with it.**
  - The markdown proposal line and the ledger CLI print "BUY — 9 of 10 draws strongly-bullish,
    1 mixed (the 9-of-10 rule)". A withheld proposal prints its tally too, as it does today.
  - **The ledger row seals the tally** (attempted, the count per label, the rule) beside
    `machine_proposal` and `machine_lean`. That is a new optional `LedgerEntry` field and its write
    in `ledger/workflow.py`: an append-only addition, never a rewrite.
- **R5. The tally records its rule.** `DrawAgreement` gains `rule` (its name and parameters),
  `required` (k), `modal_count` and `passes`.
  - The gate reads `passes` where it is present, and `unanimous` where it is not.
  - Every committed artifact (five draws, completed = attempted on all 19) therefore decides as it
    does today (C7). A page moves only when it is rebuilt.
- **R6. Unchanged:** the three-row mapping; mixed proposes nothing; the LLM writes no verdict
  (`Synthesis` has no verdict field); no code path approaches execution.
- **The operator's choice is between three options (A and B here, C in §5b, side by side at the
  end of §5b):**
  - **Option A** is R1, R3, R4, R5 and R6 at N = 5, at $0 a build. It keeps every decision today's
    rule makes on a build whose draws all complete with one spelling per lean. It closes both holes
    and prints the split.
  - **Option B** adds R2, at the cost below.
  - **Recommended: B, with C(iii)'s three outcomes** (§5b). Ten narrows the band most of every N
    that passes both ends, under either convention (§4). Nine draws (8 of 9) is the cheaper
    alternative that also passes, at one draw fewer a build.

## 5b. Option C, the operator's (2026-11-10)

**THE ASK.** The operator asked for a third option beside A and B before choosing (2026-11-10,
"yes", relayed by the coordinator), under the same discipline: never chosen by returns, never by
which names it proposes. Every figure below is a function of p, except the cost line, which counts
the SHAPES of the 33 measured tallies, descriptively. Its four parts are C(i) to C(iv), so they do
not collide with the criteria C1–C8.

**C(i) — sequential sampling, by a stopping rule fixed in advance.**
- **The rule.** Draw five attempted draws; let m be the modal label's count, R3's dissent included.
  - The modal label is committed and m = 5: propose (R1 at five draws).
  - The modal label is committed and m is 3 or 4 (3/2 or 4/1): draw five more, and propose only if
    the same lean holds at least 9 of the 10 (R1 at ten).
  - Otherwise (a mixed modal label, or m ≤ 2): stop, with no proposal.
- **Its exact error rates**, for the lean at rate p: q_C(p) = p⁵ + 5p⁴(1 − p) · p⁵. The 3/2 branch
  adds nothing, because three of the first five plus five of five is eight, under nine.

  | | p 0.5 | 0.6 | 0.7 | 0.8 | 0.85 | 0.9 | 0.95 |
  |---|--:|--:|--:|--:|--:|--:|--:|
  | A (5/5), q | 0.031 | 0.078 | 0.168 | 0.328 | 0.444 | 0.590 | 0.774 |
  | B (9/10), q | 0.011 | 0.046 | 0.149 | 0.376 | 0.544 | 0.736 | 0.914 |
  | **C(i), q** | **0.036** | **0.098** | **0.229** | **0.462** | **0.617** | **0.784** | **0.931** |
  | C(i), two builds disagree, 2q(1 − q) | 0.070 | 0.177 | 0.353 | 0.497 | 0.472 | 0.338 | 0.128 |
  | C(i), expected draws, continuing on 4/1 or 3/2 | 7.34 | 8.02 | 8.34 | 8.07 | 7.65 | 7.00 | 6.13 |
  | C(i), expected draws, continuing on 4/1 only | 5.78 | 6.30 | 6.80 | 7.05 | 6.96 | 6.64 | 6.02 |

- **The expected-draws rows assume** that the dissenting draws carry no committed lean (mixed,
  failed or unparsed). If they carry the opposite lean, a 2/3 split continues too, on that lean's
  side, and expected draws rise.
- **At the reference rows:**
  - p = 0.60 publishes 9.8% (A 7.8%, B 4.6%); either-label 10.9% (A 8.8%);
  - p = 0.95 is withheld 6.9% of the time (A 22.6%, B 8.6%).
- **It fails C2 by construction.** C(i) publishes on every first five A publishes on (5/5), and
  adds a second chance at 4/1. So q_C ≥ q_A at every p: there is no p at which C(i) is the
  stricter. As a test of "p ≤ ½" its size is 3.6% (q_C at 0.5), still under 5%.
- **Continuing on 3/2 cannot propose.** Its publish rates are identical to continuing on 4/1 only.
  It buys a printed ten-draw split and nothing else, at 1.0 to 1.7 extra expected draws between
  p = 0.6 and 0.8. The record keeps the operator's continuation set as stated, and names the
  cheaper set with the same error rates.
- **It crosses the 2026-09-26 line.** `synthesis.py:1664–1666`: "N IS FIXED FOR EVERY NAME,
  DECIDED IN ADVANCE. Drawing again because the first answer is unwelcome is outcome-dependent
  sampling".
  - C(i) draws again on the TALLY, by a rule fixed in advance and applied identically to every
    name and either direction, never on whether an answer is welcome.
  - But it does make N depend on the first five draws, which that ruling's first sentence forbids.
  - Adopting C(i) is the operator overruling that sentence, in words, on the record.

**C(ii) — hysteresis for names already proposed.**
- **The rule.** A name WITHOUT an existing proposal needs the new bar, C(i). A name WITH one draws
  ten, and keeps the proposal only if the same lean holds at least 6 of the 10. Below that it is
  withdrawn, and the new bar applies to any other lean.
- **What "existing" means, and where it is read from.** There are two candidates:
  - **the committed page:** the proposal R1/R5 derive from the `dossier.json` on main that the
    rebuild replaces (its `draw_agreement` and `evidence_balance`). For an artifact from before R5
    that is today's rule's proposal, so C7 holds. Every page has one, it is committed and diffable,
    and it is an as-of artifact the build already knows;
  - **the ledger:** the latest sealed `machine_proposal` for the ticker (`schemas/ledger.py:205`).
    Only names whose verdict was logged carry one. So the machine's next proposal would depend on
    whether the human logged, a loop from the human's action back into the machine baseline the
    spread is decomposed against.
  - **If C(ii) is ruled, it reads the page.**
- **It changes a constitutional sentence, flagged.** CLAUDE.md says the proposal is "derived
  DETERMINISTICALLY from its committed evidence lean".
  - Under C(ii) it is deterministic given the build AND the previous page, no longer a function of
    the build alone.
  - Adopting C(ii) changes that sentence. That is the operator's ruling, and a CLAUDE.md edit this
    design does not make.
- **Interaction with R5.**
  - The keep test reads the new tally against the KEEP bar, so R5's record gains `kept_by` (new |
    hysteresis).
  - It is printed beside the split, for example "BUY, kept: 7 of 10 strongly-bullish (keep bar 6 of
    10; a new proposal needs 9)".
  - An artifact from before R5 carries no `passes`, and its existing proposal is today's rule's.
- **The flip rate it buys,** on repeated rebuilds of one unchanged input:
  - **The model:** a two-state chain in steady state. q is the new bar's publish rate and
    r = P(≥ 6 of 10) the keep rate; a rebuild flips with probability 2q(1 − r)/(q + 1 − r).

  | p | A | B | C(i) | C(i) + hysteresis | B + hysteresis |
  |---|--:|--:|--:|--:|--:|
  | 0.60 | 0.143 | 0.088 | 0.177 | 0.155 | 0.082 |
  | 0.70 | 0.280 | 0.254 | 0.353 | 0.181 | 0.150 |
  | 0.80 | 0.441 | 0.469 | 0.497 | 0.061 | 0.060 |
  | 0.95 | 0.350 | 0.157 | 0.128 | 0.000 | 0.000 |

- **What it costs in proposals.** This is the long-run share of rebuilds carrying a proposal,
  π = q/(q + 1 − r):
  - p = 0.60: C(i)+H 21.1%, B+H 11.2%, against A 7.8% and B 4.6%;
  - p = 0.70: 60.3% and 49.8%, against 16.8% and 14.9%.
  - Hysteresis keeps a wobbly name's lucky proposal: at p = 0.60 it survives a rebuild 63.3% of
    the time. **It fails C2 in the long run,** at 1.4 to 2.7 times today's rate at p = 0.60.
- **Expected draws:** a name with an existing proposal always draws ten. Under C(i)+H at p = 0.60,
  0.80 and 0.95: 8.44, 9.87 and 10.00.
- **What the steady state assumes:** an input unchanged between rebuilds. A rebuild usually follows
  a new filing or price, so a real name's p moves. The table bounds what hysteresis can buy; it
  does not predict any name.

**C(iii) — three outcomes.**
- **propose:** the bar (new, or keep under C(ii)) is met.
- **borderline:** the modal lean is committed and holds a majority of the attempted draws, but the
  bar is not met. At five draws that is 3 or 4 of 5; at ten, 6, 7 or 8 of 10. The split is printed,
  and there is no proposal.
  - Under C(i) a borderline first five continues, and ends borderline unless the second five reach
    nine. P(borderline under C(i)) at p = 0.6, 0.8 and 0.95: 0.452, 0.466 and 0.067.
- **none:** a mixed modal label, a committed lean at or under half, no read, or a failed synthesis.
- **Unchanged:** mixed still proposes nothing, and the LLM still writes no verdict (`Synthesis`
  has no verdict field).
- **In the ledger:**
  - `machine_proposal` stays None for both borderline and none, and the Disposition stays
    NO_PROPOSAL, as today;
  - the sealed tally (R4) gains `proposal_state` (proposed | borderline | none), so the two are
    told apart without a new Disposition.
- **The page already prints a split build** ("the draws DISAGREED — 3x …, 2x …"). Borderline names
  that state; it adds no display the human was not already shown.
- **It is separable.** C(iii) fails no criterion and costs $0, so it can sit on A or B as well as
  on C.

**C(iv) — a confirmation at decision time.**
- **Where it hooks in:** `vinci log-verdict` runs `_cmd_log_verdict` (`cli.py:1587`), which seals the
  proposal with `_sealed_proposal(cfg, ticker)` (`cli.py:1472`, called at 1627) before
  `log_verdict` writes the row (1628). Today the seal reads the committed `dossier.json` only,
  "never recomputed from live data (as-of discipline)".
- **What it would do:**
  - before sealing, rebuild the committed page's exact synthesis request (the replay harness already
    does this: `vinci.evals.replay.capture`, from the committed page and its transcripts);
  - draw ten, apply R1 at ten, and seal THAT proposal, with both tallies (the page's and the
    confirmation's) beside it.
  - The input is the committed page, never live data, so the as-of discipline holds.
- **The rules it needs:**
  - exactly one confirmation per log, recorded whether or not the verdict is then logged, so it
    cannot be re-run until it agrees;
  - its result stays sealed until the verdict is logged, as the proposal is today;
  - it needs the page's transcripts on the logging machine (CIQ, read only), and refuses without
    them.
- **Cost:** one uncached draw and nine cached ones.
  - $1.19 + 9 × $0.20 ≈ $2.99 at production's medians, and $1.36 + 9 × $0.30 ≈ $4.06 at the panel's;
  - so about **$3 to $4 a logged verdict**, and about 15 minutes (10 × ~93 s) before the log
    completes;
  - it is paid per logged verdict, not per build.
- **It is separable.** C(iv) fails no criterion; it can sit on A or B as well as on C.

**C(i)–C(iv): the expected added cost a build, from the 33 measured tallies.**
- **The population:** the 37 builds at `fd123ada`. 33 carry a five-draw tally; the 3 refused and 1
  failed record none.
- **The shapes**, as modal label × count of 5:
  - committed 5/5: 5; committed 4/1: 2; committed 3/2: 4;
  - mixed 5/0: 12; mixed 4/1: 6; mixed 3/2: 4.
- **Added cost, descriptive only, not a tuning input:**
  - **C(i), continuing on 4/1 or 3/2:** 6 of 33 builds continue, +0.91 draws a build, so **+$0.18
    to +$0.27 a build** at $0.196 (production's median cached draw) to $0.30 (the panel's);
  - **C(i), continuing on 4/1 only:** 2 of 33 continue, +0.30 draws, so +$0.06 to +$0.09;
  - **C(ii) adds ten draws for each proposed name.** The 5 committed 5/5 tallies would draw five
    more on their next build: +0.76 draws, so +$0.15 to +$0.23 a build;
  - **C(iv):** about $3 to $4 per logged verdict, on top;
  - for comparison, B is +$1.00 to +$1.50 a build.

**A, B and C side by side** (modal-only q; C(i) continuing on 4/1 or 3/2, as the operator
specified):

| | A | B | C(i) + C(iii) | C(i) + C(ii) + C(iii) |
|---|---|---|---|---|
| draws a build | 5 | 10 | 5, or 10 on a borderline first five (expected 6.1 to 8.3) | 10 for a proposed name |
| publishes at p = 0.60 (C2: at most 7.8%) | 7.8% | 4.6% | 9.8%, fails | 9.8% new, 21.1% long run, fails |
| withheld at p = 0.95 (C8: at most 22.6%) | 22.6% | 8.6% | 6.9% | ~0 once proposed |
| builds disagree, p = 0.80 / 0.95 | 0.441 / 0.350 | 0.469 / 0.157 | 0.497 / 0.128 | 0.061 / 0.000 |
| added cost a build | $0 | +$1.00 to +$1.50 | +$0.18 to +$0.27 | +$0.33 to +$0.50 |
| line it crosses | none | none | 2026-09-26's "N IS FIXED" | that, and CLAUDE.md's "deterministic from the committed lean" |

- C(iii) and C(iv) are left out of the table's differences: they fail no criterion, and either can
  be added to A or B.
- **Recommended: B, with C(iii)'s three outcomes; C(iv) if the operator wants a ten-draw read at
  decision time.**
  - C(i) fails C2 at every p, by construction.
  - C(ii) buys the largest drop in flips (0.061 at p = 0.8). It pays for it by holding wobbly
    names' proposals (21.1% at p = 0.6), which is the anchoring the 2026-09-26 asymmetry exists to
    avoid. It also crosses the determinism sentence.
  - That is this design's face-validity read. The choice is the operator's.

## 6. What each option costs on every paid build

- **Five more draws a build, each reading the prompt the first one cached:**
  - production's median cached draw is $0.20 (all 37 builds in `data/snapshots/assembly_runs/`;
    see BOUNDARY);
  - the panel's is $0.30 (#935's 48 cached draws).
  - So **+$1.00 to +$1.50 a build**, against a median build total of $3.33 (the same 37): **+30% to
    +45%**.
- **Wall time:** +5 × ~93 s ≈ +8 minutes a build (#935: 92.8 s mean a call). At 93 s apart the
  draws stay inside the 5-minute cache lifetime the code measures start to start
  (`synthesis._CACHE_TTL_S`). A miss is flagged by `_cache_misses`, as today.
- **Nine draws instead:** +4 draws, +$0.80 to +$1.20 a build.
- **Option C**, from the 33 measured tallies (§5b): C(i) +$0.18 to +$0.27 a build (+$0.06 to
  +$0.09 continuing on 4/1 only); C(ii) +$0.15 to +$0.23 more; C(iv) about $3 to $4 per logged
  verdict.
- **The panel's measurement cost, once** (§7): about $97.4, cap $110 (three builds a page: about
  $73.1, cap $80).

## 7. The measurement, pre-registered on the six-page panel, re-scoped to INDEPENDENCE (RUNBOOKS §n, adapted)

- **Why independence.** Every table here assumes the draws on one input are independent, with one
  rate p per input: today's rule's in `synthesis.py`, and A's, B's and C's.
  - If draws on one input correlate, or p drifts between builds, the count over N draws is
    overdispersed. Then every rule flips more than its table says: **the binomial error rates are
    optimistic.**
  - That assumption is what a paid run can test. Which rule to choose, it cannot decide.
- **Why §n is adapted, not followed as written.** No option moves the request, so `compare` would
  refuse (no page's request differs). The class metrics cannot move, and are not read.
- **What it cannot do:**
  - it cannot choose or tune. k, N, α, C(i)'s continuation set and C(ii)'s keep bar are fixed by
    this record, and a different value needs a new record;
  - no option is chosen from which panel page proposes. The run may come before the choice, since
    it tests a property of the draws that A, B and C share.
- **Pages:** the frozen panel v2 (BURL, CNXC, LLY, MCK, ROST, SMPL; freeze `bcda7ce3`).
- **Request:** main's at registration, with every transform main's code then holds that re-reads a
  field from the ref's own code.
  - At `fd123ada` that is eight, in this order: `asof_cut` first, as its own docstring requires;
    then `FIX_3A`'s five, `gap_types` and `current_buybacks`.
  - Each page's request sha256 is captured at $0 and written into the registration before any draw.
- **Draws: four separate ten-draw builds per page, each shaped like production's.** That is 24
  builds and 240 calls, `claude-opus-4-8`.
  - Each build is its own run, started more than five minutes after the previous build's last draw,
    so each opens on an uncached draw, as a production build does.
  - Each build's first five is a production five-draw build: A's, and C(i)'s first stage. Its ten
    are B's, and C(i)'s whenever the first five continue.
- **The primary test, and the one falsifier: overdispersion of the per-build counts.**
  - **Per page:** p̂ is the share of its 40 draws that carry the page's pooled modal label, and x_k
    is that label's count in build k.
  - **The statistic:** Pearson's dispersion statistic, X² = Σ_k (x_k − 10p̂)² / (10p̂(1 − p̂)),
    summed over the pages with 0 < p̂ < 1. It is referred to χ² with 3 degrees of freedom per such
    page.
  - **Independence is falsified if X² exceeds the χ² upper 5% point.**
    - The binomial tables are then optimistic by about VIF = X²/df, the measured variance inflation.
      It is reported with the result.
    - A ten-draw count's variance is VIF times the binomial's, and an intra-build correlation ρ
      gives VIF = 1 + 9ρ.
  - **Its power,** by simulation:
    - **Assumption:** p = 0.7 on all six pages. This is an assumption, not any page's value.
    - **Setup:** 6,000 runs, seed 20261110, beta-binomial builds.
    - **Four builds a page:** a false alarm 5.1% of the time at no correlation; power 37% at
      ρ = 0.05 (VIF 1.45), 71% at ρ = 0.1 (VIF 1.9) and 96% at ρ = 0.2 (VIF 2.8).
    - **Three builds a page:** 5.4%, 30%, 58% and 89%.
- **Reported, not decided on:**
  - within-build serial dependence: a runs test on each build's sequence;
  - the 24 uncached first draws against the 216 cached ones, by an exact test;
  - failed, unparsed and unrecognized draws;
  - each build's outcome under A, B and C(i) (with C(iii)'s three outcomes), and the disagreement
    between builds under each: 6 pairs a page per rule.
- **STOP:**
  - **X² over the 5% point:** report VIF; the operator rules on whether any option's tables stand;
  - **more than 4 of 240 draws fail, do not parse or carry no recognized lean:** under R3 each is
    dissent, so a rate f lowers every name's effective rate to p(1 − f).
- **Cost:**
  - per build, one uncached draw (≈ $1.36) and nine cached ones (≈ $0.30 each) ≈ $4.06;
  - 24 builds ≈ **$97.4**, using #935's ledger means; **proposed cap $110**;
  - **the cheaper version:** three builds a page, 18 builds ≈ $73.1, cap $80, at the lower power
    above.
- **One harness PR first ($0).** `python -m vinci.evals run`, the one-condition paid command, has
  three gaps at `fd123ada`:
  - **it defines no `--transform`.** `vinci/evals/__main__.py:204` reads
    `getattr(a, "transform", [])`, which is always `[]` for `run`, so it would draw the raw
    committed layer, not the registered request;
  - **it takes no `--ciq-root`.** `__main__.py:203` calls `panel_inputs(a.ticker)` at the default
    root, the same gap row 53 item (8) records for `score`, and on this machine it refuses;
  - **it takes no registration,** so the request pins above would go unchecked.
  - **One more need:** the run must record each build's start and the gap since the previous
    build's last draw, so the uncached-start condition is shown, not assumed.

## 8. Order, and what waits on whom (as decided, §9)

Each step is its own PR or run, and each STOPS for the operator's merge before the next.

1. **This record, updated with the decision.** No `vinci/` change.
2. **The harness PR ($0):** `vinci.evals run` gains `--transform`, `--ciq-root` and a registration,
   and records each build's start and the gap since the previous build's last draw (§7). Its pins
   fail first on main.
3. **The measurement (§7)**, registered before any draw, under ONE budget ledger opened as
   `budget-open --cap 110 --approval "decide as per the expert team (vote-rule independence
   measurement, $110 cap, coordinator 2026-11-10)"`.
   - It is drawn once and scored at $0.
   - Its record PR states whether independence is falsified.
   - **If it is falsified, everything STOPS before step 4,** and the operator rules with the
     measured VIF in hand.
4. **The implementing PR**, after the measurement (decision path; the edit hook asks the operator;
   a real shown run before merge):
   - **R1**, the binomial test, which at five draws decides as today's rule;
   - **R3**, failed, unparsed or unrecognized draws as dissent. This closes §2's first hole, a build
     with 1 of 5 completed reading as unanimous;
   - **R1's single spelling key** for the tally and the mapping, which closes §2's second hole;
   - **R4**, the split sealed in the ledger as an optional `LedgerEntry` field;
   - **R5**, the tally's rule record;
   - **C(iii)**, the borderline outcome, as `proposal_state`;
   - **C(iv)**, the ten-draw confirmation in `_sealed_proposal` on the `log-verdict` path;
   - **the harness mirrors** (`compare._proposal`; `panel._boundaries` needs no change at five draws);
   - **pins, positive and negative:**
     - the 1-of-5 build;
     - a build split only by spelling;
     - a borderline 4/1 and 3/2;
     - the confirmation sealed beside the page's tally;
     - one confirmation per log.
5. **Pages carry R1, R3–R5 and C(iii)** on each rebuild (row 41). The confirmation runs at each
   logged verdict from the day step 4 merges.

## 9. The decision (2026-11-10)

**THE DELEGATION.** Operator, 2026-11-10, verbatim: **"decide as per the expert team"**. The
coordinator made the choice under that delegation and relayed it. The reasons below are the
coordinator's, recorded as given. Like the options, the choice reads the operating
characteristics and the cost, never returns and never which names propose.

**THE CHOICE: Option A + C(iii) + C(iv), the full independence measurement, cap $110.**
- **A** (R1, R3–R6 at five draws) adds $0 to every build. At five draws R1 decides as today's rule
  does, and R3 and the single spelling key close §2's two holes.
- **C(iii), the borderline outcome,** with the split printed, costs $0. It tells the human more than
  a withheld proposal that says only that it was withheld.
- **C(iv), the ten-draw confirmation inside `log-verdict`,** runs before the ledger row is written.
  - It puts B's accuracy (R1 at ten, 9 of 10) at the one moment a verdict is sealed. It costs about
    $3 to $4 per logged verdict, against B's +$1.00 to +$1.50 on every build, most of which no one
    acts on.
  - It also means the ledger's machine-baseline curve, which the BUY − AVOID spread is decomposed
    against, is sealed from ten-draw proposals.
- **Rejected:**
  - **B,** on cost per build. It is the design's own recommendation (§5), and the decision
    departs from it here;
  - **C(i),** more permissive than today at every p, so it fails C2 (§5b);
  - **C(ii),** which keeps lucky proposals (21.1% long run at p = 0.60) and breaks CLAUDE.md's
    "derived DETERMINISTICALLY from its committed evidence lean". With C(ii) out, no CLAUDE.md edit
    is needed.
- **The measurement at four builds a page** (240 draws, ≈ $97.4, cap $110), not three: a test too
  weak to catch correlation would only give false comfort.
  - At ρ = 0.1, four builds reach 71% simulated power, against 58% for three (§7).
  - The error rates of A, C(iii) and C(iv) all assume independent draws.

**What the decision leaves as it is, said plainly.**
- **The page's own proposal stays a five-draw one.** Under A its unstable band is today's, p from
  0.631 to 0.979 (§4). A rebuilt page's proposal flips on re-draw as often as it does today.
  - **What changes is what is sealed.** At log time C(iv)'s ten draws decide the proposal the
    ledger records, at B's error rates (§4: at p = 0.95, withheld 8.6% of the time against 22.6%).
- **The page and the seal can disagree.**
  - A page can read 5/5 and propose BUY, while its confirmation reads 8 of 10 and seals no proposal,
    or the reverse.
  - Both tallies are sealed (R4). The page's proposal is never the one recorded once a confirmation
    has run.
  - Either way the proposal stays sealed until the verdict is logged, as today, so the human decides
    without seeing the confirmation's answer.
- **What it costs: about $3 to $4 and ~15 minutes per logged verdict** (§5b C(iv)). It refuses to
  seal without the page's transcripts on the logging machine.

**BOUNDARY.**
- **Code sites:** main `fd123ada`, line numbers as of that commit. `synthesis.py`, `verdict.py`,
  `render.py`, `schemas.py`, `assemble.py`, `compare.py`, `panel.py` and `run_metrics.py` are
  unchanged since `6fbbb4a2`.
- **The 27 pages:** `data/dossiers/*/dossier.json` at `fd123ada`, after AORT's retirement (#942).
  - 19 carry a `draw_agreement`, all attempted 5 and completed 5; 8 carry none.
  - Their tallies hold the labels `strongly-bullish`, `mixed` and `strongly-bearish` only.
- **LLY's tallies:** the committed-lean labels of the draws in #931's and #935's records, five per
  arm, as those records count them.
  - **The request check:** `replay.capture_at` for LLY at `564baad8` (six transforms) and
    `622786a2` (seven), from the frozen panel's inputs (the primary checkout's `data/manual/ciq`,
    read only). Both are wire-equal and hash to `6515cd17c893`. The re-capture equals #935's
    registered BASE request.
- **The tables:** exact binomial tails, P(X ≥ k | N, p) = Σ_{i≥k} C(N,i) pⁱ(1−p)^(N−i). The band
  ends and the q = 0.5 points are solved by bisection to three decimals. The pass sets scan N = 6
  to 30 at p = 0.60 and 0.95 under both conventions. No draw enters them.
- **Production cost:**
  - **population:** all 37 records in the 37 files of `data/snapshots/assembly_runs/` at
    `fd123ada` (2026-10-26 → 2026-11-05, all `claude-opus-4-8`). Each has five successful
    synthesis calls (`assemble_dossier_framing`), priced by `vinci.graph.llm.cost_usd`;
  - **outcomes:** 33 written, 3 refused, 1 failed. A refused re-roll is paid for too, so all 37
    count;
  - **the medians:** synthesis $2.00 a build, first draw $1.19, later draw $0.20, build total $3.33;
  - **the 33 written alone:** $1.99, $1.18, $0.19 and $3.30.
- **Option C's arithmetic:** exact, from the same tails.
  - **The flip model:** the steady state of a two-state chain under an unchanged input.
  - **The tally shapes:** the `synthesis.draws` labels of the 37 assembly-run records at
    `fd123ada`. 33 carry one; the 3 refused and 1 failed carry none.
  - **The cached-draw price** for C's cost: the median of their 148 cached draws, $0.196.
- **The power simulation:** pure Python, seed 20261110, 6,000 runs per cell, beta-binomial builds
  at p = 0.7 on all six pages (an assumption, not any page's value). The χ² upper 5% point is
  taken by the Wilson–Hilferty approximation.
- **Panel cost:** #935's budget ledger, 60 calls (12 first draws, mean $1.359; 48 cached, mean
  $0.300; 92.8 s mean a call).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Accepted with the decision (§9):**
  - **The page's proposal keeps today's five-draw instability.** Only the sealed proposal is a
    ten-draw one. Falsifier: the first ten logged verdicts after step 4 show a page proposal and a
    sealed proposal disagreeing more often than §4's tables predict at the confirmations' own
    tallies. That would mean the two reads are not of one input.
  - **About $3 to $4 per logged verdict.** Falsifier: the cost series records a confirmation above
    $4.06, the panel-priced ten-draw build.
- **This record: $0.** Nothing paid was run, and nothing in `vinci/` changed. The one capture (§2)
  sent nothing.
- **Accepted if Option B is ruled:**
  - **+30% to +45% on every paid build.** Falsifier: over the first ten ten-draw builds in the cost
    series (`data/snapshots/assembly_runs/`), the median synthesis cost is above $3.50 (today's $2.00
    median plus $1.50).
  - **More proposals on names that commit.** A p = 0.95 name publishes 91% of the time against 77%,
    and that is more exposure to the anchoring risk STATE.md records. That risk's own falsifier
    stands: the override rate collapsing toward ~0, or the human spread tracking the machine spread.
- **Accepted if Option C(i) or C(ii) is ruled:**
  - **A wobbly name publishes more often than today:** at p = 0.60, 9.8% under C(i) and 21.1% in the
    long run with C(ii), against 7.8%. That is the anchoring exposure C2 exists to bound.
  - Its falsifier is the anchoring risk's own, as STATE.md records it: the override rate collapsing
    toward ~0, or the human spread tracking the machine spread.
- **Not fixable by any rule here:** a name at the threshold flips on re-draw (§4). The printed and
  sealed split (R4) is what tells its reader so.
