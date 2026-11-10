---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# The machine proposal's vote rule, as a pre-registered design (design only, $0): today a build proposes only when every COMPLETED draw of five agrees, and that rule's chance of proposing sits between 10% and 90% for any name whose lean commits on 63% to 98% of draws, so a re-draw flips it. Proposed: one rule that keeps its meaning at any draw count (a one-sided binomial test that the lean is the majority read, which at five draws IS today's rule), failed and unparsed draws counted as dissent, the split printed and sealed beside every proposal, and ten draws (9 of 10 to propose) at about +$1.00 to +$1.50 a build. No code changes until the operator rules

**THE ASK.** Operator, 2026-11-09, verbatim: **"start ... the other two fixes in the correct manner"**.
For this one the agreed manner (the coordinator's brief) is to fix the fragile BUY vote rule
separately from #930, as a pre-registered design. #930 merged as `f491d155`. This record is that
design. It changes no code: not the proposal, not the lean, not the draw count.

**THIS IS A DECISION-PATH CHANGE, FLAGGED.**
- CLAUDE.md: the proposal mapping is face-validity-frozen and never outcome-tuned.
- This design leaves the three-row mapping exactly as it is (bullish → the long leg, bearish → its
  twin, mixed → nothing). It changes the gate beside it, which `verdict.derive_proposal` calls
  "the REPRODUCIBILITY GATE, and it is deliberately OUTSIDE the mapping", and the draw count, which
  is an operator ruling of 2026-09-26 (`synthesis.SYNTHESIS_DRAWS`).
- Both are on the decision path. The implementing PR edits decision-line files, so the edit hook
  asks the operator, and it needs a real shown run before merge (CLAUDE.md).

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
- **The operator's choice is two-part:**
  - **Option A** is R1, R3, R4, R5 and R6 at N = 5, at $0 a build. It keeps every decision today's
    rule makes on a build whose draws all complete with one spelling per lean. It closes both holes
    and prints the split.
  - **Option B** adds R2, at the cost below.
  - **Recommended: B.** Ten narrows the band most of every N that passes both ends, under either
    convention (§4). Nine draws (8 of 9) is the cheaper alternative that also passes, at one draw
    fewer a build.

## 6. What ten draws cost on every paid build

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
- **The panel's measurement cost, once** (§7): about $48.7, cap $55.

## 7. The measurement, pre-registered on the six-page panel (RUNBOOKS §n, adapted)

- **Why §n is adapted, not followed as written.** The change moves no request: the draws, not the
  prompt, are what change.
  - So `compare` would refuse (no page's request differs).
  - The class metrics cannot move, and are not read.
  - What can be measured is whether production-shaped ten-draw builds behave as §4's arithmetic
    assumes.
- **What it can and cannot decide.**
  - **It cannot choose or tune the rule.** k, N, α and the threshold are fixed by this record, and
    a different value needs a new record.
  - Six pages cannot measure a flip-rate difference as small as §4 predicts between 0.7 and 0.85
    (at most 0.03).
  - So the run checks two assumptions: that draws are independent, and that they rarely fail. It
    also reports what each rule does on each page.
- **It is Option B's.** Option A changes no decision on a build whose draws all complete, so its
  pins are its proof. If the operator rules nine draws instead of ten, the same design is
  registered at two builds of nine a page, at about $45.1.
- **Pages:** the frozen panel v2 (BURL, CNXC, LLY, MCK, ROST, SMPL; freeze `bcda7ce3`).
- **Request:** main's at registration, with every transform main's code then holds that re-reads a
  field from the ref's own code.
  - At `fd123ada` that is eight, in this order: `asof_cut` first, as its own docstring requires;
    then `FIX_3A`'s five, `gap_types` and `current_buybacks`.
  - Each page's request sha256 is captured at $0 and written into the registration before any draw.
- **Draws: two separate ten-draw builds per page, each shaped like production's.** That is 120
  calls, `claude-opus-4-8`.
  - Each build is its own run of ten draws, started more than five minutes after the previous
    build's last draw. So each opens on an uncached draw, as a production build does.
  - **Today's rule is read on each build's draws 1–5.** That is exactly a production five-draw
    build: one uncached draw, then four cached ones. So there are six production-shaped pairs per
    rule.
  - Draws 6–10 of each build are reported as their own blocks, marked "opens on a cached draw". They
    are never counted as a production build.
- **Registered outputs (counts, each with its boundary):**
  - per page: each build's tally, its first-five tally, and failed, unparsed and unrecognized draws;
  - each rule's proposal on each of its builds;
  - between-build disagreement under each rule: 6 ten-draw pairs and 6 five-draw pairs;
  - the independence check: the lean of the 12 uncached first draws against the 108 cached ones, by
    an exact test. It has little power and can catch only a gross difference, and it is reported as
    that.
- **Decision: no target, no-worsening only.**
  - **STOP** if more than 2 of the 120 draws fail, do not parse or carry no recognized lean (#935
    drew 60 of 60 complete).
    - Under R3 each such draw is dissent, so a rate f lowers every name's effective rate to
      p(1 − f), and §4's tables would overstate the rule.
    - Report it, and the operator rules.
  - **STOP** if the independence check rejects at 0.05. §4's arithmetic assumes independent draws,
    and so does today's ruling.
  - Otherwise the design stands as written. Every between-build disagreement under either rule is
    explained in writing, as §n's step 5 requires of a lean move.
- **Cost:**
  - per page, two uncached draws (≈ $1.36 each) and 18 cached ones (≈ $0.30 each) ≈ $8.12;
  - six pages ≈ **$48.7**, using #935's ledger means;
  - **proposed cap $55.**
- **One harness PR first ($0).** `python -m vinci.evals run`, the one-condition paid command, has
  three gaps at `fd123ada`:
  - **it defines no `--transform`.** `vinci/evals/__main__.py:204` reads
    `getattr(a, "transform", [])`, which is always `[]` for `run`, so it would draw the raw
    committed layer, not the registered request;
  - **it takes no `--ciq-root`.** `__main__.py:203` calls `panel_inputs(a.ticker)` at the default
    root, the same gap row 53 item (8) records for `score`, and on this machine it refuses;
  - **it takes no registration,** so the request pins above would go unchecked.
  - All three are needed before any draw.

## 8. Order, and what waits on whom

1. **The operator rules** on Option A or B, and on R1–R6 as written. Nothing is built before that.
2. **The harness PR** (§7's three gaps), $0.
3. **The operator approves** the measurement and its cap, in words written into a budget ledger.
4. **The run**, scored at $0 by applying both rules to the drawn labels, into a record.
5. **The implementing PR** (decision path; the edit hook asks the operator):
   - **R1–R5** in:
     - `synthesis.py`: the count, the tally's key and the record;
     - `verdict.py`: the gate;
     - `schemas.py` (`DrawAgreement`) and `schemas/ledger.py` (`LedgerEntry`);
     - `ledger/workflow.py`, `cli.py` and `render.py`;
     - the JS reproducibility line;
   - **the harness mirrors:**
     - `compare._proposal`;
     - the panel rule's `_boundaries`, which hard-codes five draws, so at ten it would read every
       rebuilt page as off the boundary;
     - `run_metrics` copies the tally whole and needs no change;
   - **pins, positive and negative:** §2's 1-of-5 build, a build split only by spelling, and the
     8-of-10 tally (withheld at α = 0.05);
   - **its real run** is step 4's draws replayed through the new gate at $0.
6. **Pages carry it** on each rebuild (row 41). No committed page moves before.

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
- **Panel cost:** #935's budget ledger, 60 calls (12 first draws, mean $1.359; 48 cached, mean
  $0.300; 92.8 s mean a call).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **This record: $0.** Nothing paid was run, and nothing in `vinci/` changed. The one capture (§2)
  sent nothing.
- **Accepted if Option B is ruled:**
  - **+30% to +45% on every paid build.** Falsifier: over the first ten ten-draw builds in the cost
    series (`data/snapshots/assembly_runs/`), the median synthesis cost is above $3.50 (today's $2.00
    median plus $1.50).
  - **More proposals on names that commit.** A p = 0.95 name publishes 91% of the time against 77%,
    and that is more exposure to the anchoring risk STATE.md records. That risk's own falsifier
    stands: the override rate collapsing toward ~0, or the human spread tracking the machine spread.
- **Not fixable by any rule here:** a name at the threshold flips on re-draw (§4). The printed and
  sealed split (R4) is what tells its reader so.
