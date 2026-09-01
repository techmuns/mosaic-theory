---
id:
status: recorded
date: 2026-08-31
prs: []
supersedes:
superseded-by:
---

# Four operator rulings on the between-print monitor — two of them overturn a decision already recorded

**WHAT.** The operator ruled on the four questions the between-print monitor plan
(`docs/records/2026-08-27-between-print-monitor-panels.md`) left open. Recorded here because two
change a decision this repo had already made and documented, and because a ruling that lives only
in chat is not a ruling anyone can find later.

1. **Runs are OPERATOR-TRIGGERED FROM THE FRONTEND, and automatic LATER.** Today every job is
   triggered from a shell. The ask is a control on the dashboard first, automation after.
2. **Wire in the outside data sources** — court dockets, data-centre policy trackers, model-price
   boards. Terms verified per source before any of them is connected.
3. **The machine EVALUATES a kill criterion and HIGHLIGHTS one that has fired; the human decides
   what to do about it.** Not merely the number beside the criterion, which is what the plan
   proposed — the firing status itself is machine output.
4. **R3 IS NOT DEFERRED.** The P/E-basis scenario recipe gets built, so a P/E-framed underwrite
   (GOOGL today) becomes a real scenario record with machine-readable legs.

**WHY.** Ruling 3 supersedes a documented design choice. `vinci/monitor.py:23` states that "the
freshness/trigger panel FLAGS; it never adjudicates a trigger as fired — the machine surfaces, the
human concludes", restated at `:549`. That is now narrowed, not abolished: **the machine may
evaluate a criterion that is DETERMINISTIC and pre-registered, and must not evaluate one that is a
judgment.** SMPL's *"Quest revenue growth ≤ 0% YoY for two consecutive quarters"* is arithmetic
against a stated threshold and is evaluable. GOOGL's Variant-1 kill — *"FY27 direct EBIT consensus
falls below ~$214.1bn BECAUSE recurring economics deteriorate, not because of a discrete
non-operating or legal event"* — carries a causal clause no arithmetic can settle, and stays text.
The line CLAUDE.md draws is preserved by that split: the machine proposes a firing STATUS, the
human decides the ACTION (exit / trim / hold / re-underwrite). Nothing here lets an LLM conclude.

Ruling 1 supersedes #493, which de-sanctioned cron on the finding that no automatic schedule had
ever been authorised. Automation returns, but in two steps and behind a human's click first.

**HOW VERIFIED.** Nothing is built by this record; it is the ruling and its consequences, written
before the work so the work can be checked against it. What was checked:

- `vinci/monitor.py:23` and `:549` — the non-adjudication claim is real, documented twice, and is
  what ruling 3 narrows.
- STATE §5.0 item 4 (megacap/FPI readiness) named the MC1–MC4 ruling as blocked on the operator;
  MC1 shipped in #531 and R3 is now ruled IN.
- The frontend is a STATIC site built by `frontend/build.py` and served from committed JSON. It
  has no backend and cannot start a job on its own — ruling 1 needs a trigger path that does not
  exist yet, and that is the first thing to design rather than assume.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED RISK — an evaluated kill criterion anchors the human.** A criterion the machine marks
  FIRED will be read as a decision even though the disposition is still the operator's; that is the
  same anchoring risk STATE already records for the machine-proposed verdict. Falsifier: if the
  operator's disposition never diverges from the machine's firing status once there are enough
  observations to tell, the highlight has become the decision and the split is nominal.
- **A DETERMINISTIC CRITERION IS A DIFFERENT OBJECT FROM A WRITTEN ONE.** Evaluating requires a
  criterion carry a metric, a comparator and a threshold as FIELDS. Today they are prose in
  `verdict.reunderwrite_triggers`. Either the prose is parsed — refused, that is the
  display-string-as-data class this repo has paid for three times — or criteria gain a structured
  form and the prose stays beside it. The second is the only honest route, and it is a schema
  change on the sealed ledger payload, which is why it is recorded before it is attempted.
- **MEASURED, 2026-08-31: 27 committed criteria across 8 scenario records.** A crude
  numeric-versus-causal classifier put 15 in reach and 12 without a stated threshold, but reading
  the 12 shows the classifier undercounts — *"OWYN net sales turn negative year-over-year in any
  quarter"*, *"two consecutive quarters of positive revenue growth AND positive operating cash
  flow"* and *"spot pulls to ~28-30"* are all arithmetic it failed to spot, while *"material
  reduction in net debt"* and *"margin recovery that survives the fiscal 2027 price increase"* are
  genuinely not. Roughly two-thirds are evaluable IN PRINCIPLE. The number is not the finding.
- **THE FINDING IS THAT NONE OF THEM IS STRUCTURED.** All 27 are prose in
  `verdict.reunderwrite_triggers`; not one carries a metric, comparator and threshold as fields.
  So evaluation cannot begin by reading what is committed — it needs criteria to gain a structured
  form written BESIDE the prose, never parsed out of it. Parsing is the display-string-as-data
  class this repo has paid for three times, and a regex over an analyst's sentence is the worst
  instance of it: a criterion that silently fails to parse reads exactly like one that has not
  fired.
- **AND THE CAUSAL CLAUSE LIVES SOMEWHERE ELSE.** Zero of the 27 scenario-record criteria carry
  one. GOOGL's Variant-1 kill — the *"because recurring economics deteriorate, not a discrete
  legal event"* case — sits in the LEDGER payload's kill text, which no scenario record holds.
  Any evaluator must therefore cover two homes with different shapes, and the ledger's is sealed.
- **RULING 1 IS AN INFRASTRUCTURE CHANGE, NOT A PANEL.** A static site cannot trigger a job.
  **SETTLED 2026-08-31: a small AUTHENTICATED ENDPOINT**, on the operator's reasoning that the
  frontend already sits behind login credentials, so the trigger inherits the fence the pages
  already have rather than introducing a second one. The `workflow_dispatch` alternative was not
  taken. Two properties this must keep, both from CLAUDE.md rather than from the choice itself:
  every secret stays in env / Actions secrets and never reaches the endpoint's code or logs, and
  **no path from it approaches execution** — it may start an assemble, a screen or a monitor day,
  and nothing that places an order.
- **WHICH RECORD HOLDS A STRUCTURED CRITERION — SETTLED 2026-08-31: THE SCENARIO RECORD ONLY.**
  Ledger-payload kill text (GOOGL's causal-clause Variant-1 kill among it) stays PROSE and is not
  evaluated. That keeps the sealed payload sealed — a schema change to an append-only record the
  spread is measured from is a far larger act than this work needs — and it draws the evaluable
  set at exactly the boundary ruling 3 already draws: deterministic criteria get structure, and a
  criterion whose firing turns on a causal clause stays a sentence a human reads.
  CONSEQUENCE, stated rather than discovered later: a name underwritten only through the ledger —
  GOOGL today, which has kill criteria but no scenario record until R3 lands — has NOTHING for the
  evaluator to read. The panel is therefore blank for it, and blank must not read as "nothing has
  fired".
