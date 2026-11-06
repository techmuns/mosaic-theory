---
status: recorded
date: 2026-11-06
prs: []
supersedes:
superseded-by:
---

# Synthesis eval PR 2 (paid, $32.69 of $45 and $28.2223 of $35): #921 passes on its target page and does not worsen the panel; the baseline is a noise-floor reference only (a harness defect alphabetised the tool schema in both arms); the LLM judge does not reach its pre-registered bar

**THE APPROVAL.** Operator, 2026-11-06, verbatim: **"Approve both"**, answering the coordinator's
question "Approve the harness's paid steps: $45 for baseline plus #921 re-check, $35 for grader
calibration?". Two budget ledgers were opened with `python -m vinci.evals budget-open`, each
carrying those words and what they approved: (a) **$45**, PR 2 steps 1–2; (b) **$35**, step 3.
Ledgers, registrations, raw draws and judge outputs are kept OUTSIDE the repository, in this
session family's notes folder under `synthesis-eval-pr2/` (draws and requests can quote licensed
transcripts; the requests stay in the session scratch folder only). Neither cap was raised and no
other approval was opened.

**THE RESULT IN SEVEN LINES.**
- **#921 on NFLX, its target page (registered rule): SHIPS.** Every BASE draw framed the
  +2,800.0 row against its sign; no CAND draw did: M-SIGN 10 → 0 units (p_lower 0.004). Nothing else
  worsened beyond noise; the lean held.
- **#921 on the panel: blocked by the rule's letter, passed by its intent.** Its target never fires
  on the panel (0 → 0), as §6.1 anticipated; no class worsened beyond noise; LLY's lean moved
  bullish 5/5 → 4/1, which withholds its BUY, and is explained below as within noise.
- **The instruction echo #920 predicted is real:** CAND's NFLX prose carries #921's own words
  ("adds … to pre-tax income", "pre-tax income — a gain").
- **A harness defect reached all 70 draws, in BOTH arms:** the synthesis tool schema was sent with
  its fields alphabetised. The #921 comparison is internally fair; the step-1 baseline is NOT
  production's exact request and serves as a noise-floor reference only.
- **The noise floor is real:** on the three pages whose two requests were byte-identical, M-LABEL
  "improved" 37 → 27 units at p_lower 0.024 with no change at all.
- **The judge (v1, then v2 revised on DEV) does not reach §9's bar:** on the held-out TEST half, scored ONCE by the frozen v2, kappa (OK vs error) is **0.23** against the final labels (bar 0.6; the coders' own 0.75); it calls 8.9% of claims errors where the gold has 41.7%, and finds ABSENT figures but almost none of LABEL, SELECTIVE, PATH, BASIS or STALE. It is NOT trusted to gate any class.
- **Spend:** steps 1–2 $32.6905 of $45; step 3 $28.2223 of $35. No call failed.

## 1. What was registered, before any draw

| registration | sha256 | base → cand | pages | draws / condition | target | held out from the change |
|---|---|---|---|---|---|---|
| #921, panel | `7169261d4d7206047f521973258c6dea4d848ca9b75f331a195806e537dd01ff` | `dc5b8787` → `b109e26c` | BURL, CNXC, LLY, MCK, ROST, SMPL | 5 | M-SIGN | BURL, ROST |
| #921, target page | `ed155786e6d0b0863673899f1a3e872a00e7ac79f2b8c55e6194515630307ee8` | `dc5b8787` → `b109e26c` | NFLX | 5 | M-SIGN | none |

- **Scorer:** fingerprint `66f62b52830ef892cb6fb049d732648f7902ca6ba151cd79fcc083cc99d976c0`, the
  files at `74bd8431`. A later commit (`5a320a0d`) changed `compare.py`, so re-scoring these runs
  is done from `74bd8431` — `score` refuses any other scorer.
- **Why `b109e26c` is also main's baseline:** at $0, `compare --base b109e26c --cand 8a1fab7a`
  (main) is IDENTICAL on all seven pages, so #921's CAND draws are main's. `dc5b8787 → b109e26c`
  differs on CNXC, LLY, SMPL and NFLX (the material-figures section, +534 to +603 characters) and
  is byte-identical on BURL, MCK and ROST — which therefore yield A/A data (§4).
- **Targets, as pre-registered (§6.1, R6.1):** #921's form is measured on NFLX, where it fires; the
  panel must not worsen. The panel registration names M-SIGN as its target so the panel is read
  under the same rule; that it cannot improve there was known before the draw.

## 2. Spend, against the caps

| ledger | approved cap | spent | calls | detail |
|---|---:|---:|---:|---|
| (a) steps 1–2 | $45.00 | **$32.6905** | 70 | BURL $4.1444, CNXC $4.4562, LLY $6.2465, MCK $3.9189, ROST $3.8691, SMPL $4.9706 (panel $27.6057); NFLX $5.0848 |
| (b) step 3 | $35.00 | **$28.2223** | 35 | v1 on DEV, 14 pages, $11.0337; v2 on the DEV check, 7 pages, $5.8709; v2 on TEST, 14 pages, once, $11.3177 — $6.7777 unspent |

- Every call was served by `claude-opus-4-8`, stopped on `tool_use`, one HTTP attempt; draws 2–5 of
  each page and arm read the prompt cache; on BURL, MCK and ROST the CAND arm read BASE's cache
  (the requests were identical), which is why those arms cost less.
- **A third registration row in ledger (a)** names an out-dir with no draws: a re-draw of NFLX,
  started after the defect (§3) was found and stopped by the coordinator's ruling BEFORE its first
  call ($0). The registered NFLX run, which had completed 10/10, stands as the result; re-drawing a
  completed registered run is result-shopping, and nothing from the stopped run is scored.

## 3. The defect, and its reach

- **What:** `capture_child.jsonable` normalised a request with `sort_keys=True`, and the paid path
  SENDS the captured request. So every one of the 70 draws sent the synthesis tool's schema with
  its fields alphabetised — `bear_points, bull_points, decisive_question, evidence_balance,
  key_unknowns, twin_reference_cases` instead of production's `bull_points, bear_points,
  twin_reference_cases, decisive_question, key_unknowns, evidence_balance`, and each point's
  `figures` before its `source_ref`. With a forced tool the model may fill fields in schema order,
  so the lean (`evidence_balance`) may have been written earlier than production writes it.
- **Why the guard passed it:** it compared captured and live requests as dicts, and dict equality
  ignores order.
- **Reach:** all 70 step-1/2 draws, BOTH arms equally. **The #921 comparison is internally fair**
  (the same reordering on both sides of every page). **The step-1 baseline is not production's
  exact request**, so it is a noise-floor reference only (§5), never a production estimate. The
  PR 1 byte-identity proofs are unaffected (they compare SYSTEM and USER as strings, by full
  sha256; the logs hold no tool schema).
- **Fixed:** `d262dce3` keeps key order (two tests that failed first); `5a320a0d` makes the guard
  and `compare`'s identity check read the request as SENT — its serialised bytes, order included
  (`Request.wire`), with a test that fails on the old order-blind comparison. Every later
  comparison draws its own BASE arm under the fixed harness, so the defect does not carry forward.

## 4. #921, by the registered rule

| metric | NFLX BASE → CAND (units) | p | panel BASE → CAND | p |
|---|---|---|---|---|
| **M-SIGN (target)** | **10 → 0** | **p_lower 0.004** | 0 → 0 | p_lower 1 |
| M-LABEL | 24 → 21 | p_upper 0.849 | 68 → 65 | p_upper 0.745 |
| M-ABSENT | 6 → 12 | p_upper 0.060 | 50 → 63 | p_upper 0.093 |
| M-PATH | 1 → 3 | p_upper 0.262 | 5 → 0 | p_upper 1 (p_lower 0.028) |
| M-ECHO (reported) | 7 → 12 | p_upper 0.103 | 52 → 49 | p_upper 0.685 |

- **NFLX — the score tool: SHIPS.** Per draw M-SIGN was 2, 2, 2, 2, 2 at BASE and 0, 0, 0, 0, 0 at
  CAND — the smallest p a 5 v 5 page can give. No other class metric worsened at p_upper ≤ 0.05
  (M-ABSENT nearest, 0.060). Leans: BASE mixed 4 / bullish 1, CAND mixed 5; no proposal either way.
- **Echo, CAND only on NFLX:** "adds to pre-tax income", "pre-tax income — a gain", "adds $M to
  pre-tax" — #921's instruction words, reaching the prose (#920 §10 predicted it for V1).
- **The panel — the score tool: BLOCKS,** on two reasons: (1) the target M-SIGN does not improve (it
  fired 0 times in 60 draws, as on the gold); (2) **LLY's lean moved**, bullish 5/5 (proposes BUY)
  → bullish 4 / mixed 1 (withheld). No class metric worsened at p_upper ≤ 0.05; the panel's
  committed-lean count did not move at p ≤ 0.05.
- **LLY, explained in writing as the rule requires.** LLY's request does differ (#921's line for
  its material row). Its three five-draw builds of record were bullish 15/15 (the logged 2026-10-29
  build and the committed 2026-11-03 build, each on its own page and code, and this BASE arm); CAND gave 4/5. If the one
  dissent among those 20 draws were equally likely anywhere, it would fall in CAND's five with
  probability 5/20 = 0.25: this n cannot attribute it to #921. In production a single dissent
  withholds LLY's BUY; that LLY sits one draw from it is the proposal-boundary property the panel
  rule chose it for.
- **Reading §6.1 whole:** the target improves beyond noise on the target page; the panel does not
  worsen beyond noise; the one lean move is within noise and explained. **#921 passes**, with its
  instruction echo named.
- **What n cannot show here:** whether #921 changes M-SIGN anywhere but NFLX (it never fires
  elsewhere on the panel or the gold); a lean effect smaller than four draws in five on one page;
  and anything about the alphabetised schema's own effect (both arms had it).

## 5. The noise floor, measured — the A/A pages (EXPLORATORY, not registered)

BURL, MCK and ROST sent byte-identical requests in both arms (same code path for them), so their
BASE-vs-CAND differences are noise by construction:

| metric | A/A pages BASE → CAND | p | pages #921 changed BASE → CAND | p |
|---|---|---|---|---|
| M-LABEL | 37 → 27 | **p_lower 0.024** | 31 → 38 | p_upper 0.055 |
| M-ABSENT | 35 → 44 | p_upper 0.147 | 15 → 19 | p_upper 0.278 |
| M-PATH | 3 → 0 | p_lower 0.111 | 2 → 0 | p_lower 0.250 |

- **An A/A "effect" at p 0.024.** With four class metrics read in two directions, a p below 0.05
  somewhere is expected now and then by chance alone — and the arms are also drawn in sequence
  (BASE then CAND, minutes apart), so drift is not excluded. Lean drift on identical requests:
  ROST bullish 2 → 1 of 5.
- **What it implies for the rule (a proposal, not an edit):** a single metric at p between 0.01 and
  0.05 is not, on its own, enough to ship or to block; either gate at α = 0.01 or pre-register a
  replication (a second five-draw pair) for results in that band. The coordinator decides.
- **The step-1 baseline — main's CAND arm, per page, as a noise-floor reference** (units over five
  draws; the request is main's with the alphabetised schema, §3): M-LABEL BURL 10, CNXC 12, LLY 13,
  MCK 10, ROST 7, SMPL 13 (65 in all); M-ABSENT 14, 12, 2, 22, 8, 5 (63); M-PATH 0; M-SIGN 0;
  leans BURL mixed 4 / bullish 1, CNXC mixed 5, LLY bullish 4 / mixed 1, MCK mixed 3 / bullish 2,
  ROST mixed 4 / bullish 1, SMPL mixed 3 / bearish 2; NFLX M-LABEL 21, M-ABSENT 12, M-PATH 3,
  M-SIGN 0, mixed 5.

## 6. The judge's calibration (step 3)

**Protocol (design record §9, fixed before any judge call):** the judge applies the frozen
`TAXONOMY.md` to one page's facts (the committed `dossier.json` at the gold's freeze, less its
synthesis, input manifest and price-store stamp) and that page's claims, one forced-tool call per
page, `claude-opus-4-8`; it may be revised on DEV only; it is then frozen and scored ONCE on TEST.
**Bar:** TEST kappa (OK vs error) ≥ 0.6 and within 0.15 of the coders' 0.76, AND, for any class it
is to gate, recall ≥ 0.5 on that class's material claims. Both halves of the bar, or no trust.

| version (commit) | half | claims | kappa vs final | vs coder A | vs coder B | judge error rate | gold error rate | cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| v1 (`a45ace8e`) | DEV, 14 pages | 330 | 0.19 | 0.26 | 0.19 | 11.5% | 46.1% | $11.0337 |
| v1 | the DEV check's 7 pages (from the run above) | 162 | 0.18 | 0.21 | 0.16 | 10.5% | 43.2% | — |
| v2 (`0ef8afd3`) | the DEV check, 7 pages | 162 | 0.27 | 0.27 | 0.27 | 10.5% | 43.2% | $5.8709 |
| **v2, frozen** | **TEST, 14 pages, once** | **314** | **0.23** | 0.26 | 0.21 | **8.9%** | **41.7%** | $11.3177 |

- **The revision (v1 → v2, DEV only).** v1 wrote about 1,200 output tokens per page for about 23
  claims — a skim. v2 makes the lookup the FIRST field of each verdict (every figure, date, period,
  direction and label the claim asserts, with the JSON path and value where the facts state it):
  output rose to about 4,000 tokens per page and kappa on the same seven pages from 0.18 to 0.27,
  but the error rate did not move. It looks the figures up, then judges them supported.
- **TEST, per class (v2, once):** recall = the gold class's claims the judge filed under it.

  | class | gold | judged | agree | recall | precision | material caught (any error) / same class |
  |---|---:|---:|---:|---:|---:|---|
  | ABSENT | 32 | 22 | 16 | 50% | 73% | 8/12 · **7/12** |
  | LABEL | 27 | 1 | 0 | 0% | 0% | 0/17 · 0/17 |
  | OVERREACH | 22 | 4 | 1 | 5% | 25% | 0/8 · 0/8 |
  | PATH | 12 | 0 | 0 | 0% | — | 1/6 · 0/6 |
  | SELECTIVE | 9 | 0 | 0 | 0% | — | 0/8 · 0/8 |
  | BASIS | 9 | 0 | 0 | 0% | — | 1/4 · 0/4 |
  | CONFLICT | 7 | 0 | 0 | 0% | — | 0/1 · 0/1 |
  | SIGN | 5 | 0 | 0 | 0% | — | 1/3 · 0/3 |
  | STALE | 5 | 0 | 0 | 0% | — | 1/2 · 0/2 |
  | PERIOD | 3 | 0 | 0 | 0% | — | 0/0 · 0/0 |

  On the 26 claims both the judge and the gold call errors, the class agrees on 17 and the
  materiality on 16. One TEST claim got no verdict (coded as an error, the conservative side).
- **The verdict by the bar: NOT MET.** kappa 0.23 is far below 0.6. ABSENT alone passes the class
  half (7/12 material, ≥ 0.5), but the bar is conjunctive, so **the judge gates nothing** — not
  ABSENT either. Its figures stand as information only.
- **What it tells us about the judge, plainly.** The classes it misses are the ones that need a
  claim held against a SECOND fact — a label against the series that contradicts it (LABEL), a
  subset against the whole (SELECTIVE), a path against its own reversals (PATH), a basis or a vintage
  against another (BASIS, STALE). One pass over ~150–250K tokens of facts with no reasoning room
  finds absent figures and not much else. The gold coders read flattened facts and could search
  them; this judge could not.
- **What n can and cannot show here:** 314 TEST claims make kappa 0.23 unambiguous against a 0.6
  bar; class figures rest on 3–32 claims and are indicative only (ABSENT's 7/12 has a wide
  interval). TEST has now been used ONCE; a v3 scored on it again would read it in-sample.
- **Recommendation — how the measurement proceeds:**
  1. **Gate on what passed:** M-LABEL as the one target (TEST P 22/32, R 22/27), the deterministic
     metrics as no-worsening proxies, the lean and proposal checks — exactly as R6 of the design
     record already said for the case where the judge fails.
  2. **Do not spend more on this judge design.** Re-prompting a one-pass judge moved kappa by 0.09.
  3. **If a judged class is needed** (SELECTIVE and OVERREACH, 33 of the 117 material errors, have
     no deterministic metric), the next design is a judge that can look things up: a per-claim
     call given the claim and only the fact blocks it cites or names (retrieved deterministically
     from the page), with room to reason — which needs the client to allow a non-forced tool or
     structured output, a client change. Calibrating it needs FRESH gold: TEST has been read once,
     so a v3 needs a new double-blind, adjudicated sample — for instance the claims of one panel
     draw per page per arm (about 380 claims), coded the way the diagnosis coded its 644. Cost to
     be estimated at its design; propose it then, not now.


## 7. Proposed, NOT run (each needs its own registration, approval and cap)

1. **A production-exact baseline:** main's panel, five draws per page, under the fixed harness.
   Measured today the six BASE arms (cache-cold) cost $15.3215 — **propose a cap of
   $20**. Optional: every comparison draws its own BASE arm, so this buys a reference, not a gate.
2. **Measuring fix 3a (#923):** $0 first — four more transforms in `variants.py` (the trailing
   EV/EBITDA note, the survival read, the peer-gap question, the catalyst print row), each calling
   #923's own code on the committed layer and each checked against a `vinci dossier precheck` build
   of a panel page; `compare` must then show all five label sites reaching the request. Then
   register `main → #923` on the panel, target **M-LABEL** (the one metric fit to be a target;
   baseline 65 units over 30 draws), five draws per arm. Both arms differ on most pages, so no
   cross-arm cache saving: about $30 expected — **propose a cap of $40**. Fix 3a's record names 27
   of the 28 corpus pages, so expect no held-out page.
3. **The judge, if it is to gate more than ABSENT:** see §6's recommendation.

**BOUNDARY.** Draws: 70, `claude-opus-4-8`, 2026-11-06 between ledger (a)'s opening (21:11 +05:30) and the first score (23:02 +05:30), five per page per arm,
sent with the alphabetised tool schema (§3). Units: prose units of `units.draw_units` with at least
one hit, per draw. Scorer: `74bd8431` (fingerprint above). Pages: the frozen panel v2 plus NFLX,
inputs checked by blob and transcript sha256 against `vinci/evals/synthesis_panel.json`. Spend:
production's `cost_usd` at `LLM_PRICE_PER_MTOK` (`claude-opus-4-8` $5/$25 per Mtok; cache write
1.25×, read 0.1×), summed from the two ledgers. Judge: 35 calls, one per page (that page's gold claims together), the gold pages read at `bcda7ce3`; DEV = AMZN … NFLX (330 claims), the DEV check = AMZN, BRBR, CNXC, FUBO, IT, MCK, NCNO (every second DEV page alphabetically from AMZN; 162 claims), TEST = NKE … WLK (314 claims), kappa on OK vs error with a missing verdict coded as an error.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $32.6905 + $28.2223 of the two approvals. Accepted, with
its falsifier: the baseline's alphabetised schema — falsified if a production-exact re-draw (§7.1)
moves a metric's per-draw mean outside the A/A spread measured here.
