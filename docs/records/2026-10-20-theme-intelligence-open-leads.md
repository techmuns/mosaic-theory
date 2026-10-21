---
id: 2026-10-20-theme-intelligence-open-leads
status: recorded
date: 2026-10-20
prs: [755]
supersedes:
superseded-by:
---

# Theme intelligence: the weekly run keeps the answers it paid for, the first Actions run starts, and four open leads close

**WHAT.** STATE §5.0 row 32 (8), the agent's items (h) and (i), and the operator's (c) and (d).
Operator, 2026-10-20: "complete all steps in correct order". The order:
1. **U31f, the paid cache.**
2. **The leads.** Each was measured on the 132 local registries before it was changed:
   - (i) the figure ledger reading a figure REFERENCE as a figure;
   - QA's content-hash check;
   - the desk's counter-evidence gate;
   - the desk's Articles follow-up.
3. **The first weekly run on Actions**, on the PR branch, so it also proves U31f.

The operator's rulings ((a), (f), (k), the prompt cache in (d)) and the paid options ((e), (g)) are
theirs and stay open. The stale test branch in (d) is deleted.

**THE FIXES.**
- **U31f — the weekly run keeps a failed run's paid answers.**
  - The combined `actions/cache` saves in its post-step only when the JOB succeeds. This job
    fails on purpose when the scan fails or QA does not pass, so a failed run's paid model output
    was thrown away and the retry paid again.
  - The workflow now restores with `actions/cache/restore` and saves with `actions/cache/save` in
    its own step: `always()`, right after the scan, skipped only when the scan never ran or wrote
    nothing.
  - The key carries the run AND the attempt. A cache key is written once, so a re-run of the
    same run must save under its own key.
- **(i) A figure reference is not a figure.**
  - `completeness._skip_number` reads a number that NAMES a figure, table, exhibit, chart,
    section, statute (§), appendix, slide or page as a reference. Only punctuation and a PDF's
    table debris may stand between the word and the number.
  - It runs after the unit test, so a number with a unit ("5 pp", "23%") is always a figure.
  - The decimal half of the 2026-10-11 lead ("2,358.5GVA" read as "2,358") was already fixed on
    2026-10-14, when `GVA` joined the ledger's units.
- **QA's "version content hashes recompute" hashes the content AS STORED.** `card_sha(v.content)`
  re-serialised the PARSED content through today's model, so a field the schema gained later,
  with its default, moved the hash of an intact version. The pilot's six were written before
  `s07_what_could_go_wrong.price_context` existed.
- **The desk's counter-evidence gate reads the stored verdict.** It used to be inferred by
  elimination: added only when a WATCH passed every other gate. It now reads `counter_verdict`,
  the F8 value the card and the weekly report already read (U53), whenever the verdict holds.
- **The Articles follow-up is the ONE partial-awaiting-full rule.**
  - `desk.week_articles` kept a third copy of `report.partial_ask` that never read unreadable
    pages.
  - It now asks what the rule asks:
    - "Check the unreadable pages", pointing to Uploads;
    - "Supply the full report";
    - or nothing.
  - Where nothing is asked, it says why: the channel was retired; only back-matter pages could not
    be read; or the channel is preview-only by decision.

**DOES THIS SELECT ON FORM?** No. Theme intelligence is research attention, off the decision path:
- the ledger change decides which numbers are figures;
- the QA change decides what counts as intact;
- the desk changes decide what a page names.

None ranks or gates a name.

**HOW VERIFIED** (the 132 local registries under the pilot worktree's
`data/theme_intelligence/v2/`, each read on a backup-API copy; the live pilot never opened for
writing).
- **(i)** 27,758 stored ledger figures. Main's current rule against this one, on the same stored
  sentences: the new rule drops exactly 4, all references.
  - "see Figure | | | ; | 23";
  - "section 165(c)";
  - "§39.169", a Texas statute;
  - "Penn World Table 10.0".
  Three were open (uncaptured) items, so the change closes three false open items and drops no
  real figure.
- **Hashes.** 1,011 stored versions:
  - the stored content reproduces the stored hash on 1,011;
  - main's re-serialisation reproduces it on 42.
  On the live pilot's 29 runs, the check failed 4 under main's method and 0 now.
- **The gate.** 16 latest versions carry a counter-evidence verdict. Main's desk showed the gate
  on 1 of them; it shows it on 16. No WATCH is left with every gate passing (which elimination
  could have explained): 0.
- **The follow-up.** 81 PARTIAL article rows.
  - On main, 62 agreed with the shared rule. 8 asked for "the full report" for a supplied document
    whose pages needed a visual check. 11 asked for one where only back matter was unreadable.
  - Now 81 of 81 agree.
  - The 11 rows say "Nothing to ask — only back-matter pages could not be read".
- **The live pilot alone** shows neither desk lead today: its 3 PARTIAL rows already agreed, and
  no thesis carries a verdict. The leads were real on the wider corpus, which is why it was
  measured.
- **Pins** (`tests/test_theme_intelligence_open_leads.py`, 10 for these fixes and 2 for the secret
  below, on committed fixtures through the real functions):
  - the four corpus sentences, and figures beside a reference that must stay, including words
    between a reference word and its number;
  - a stored version in the pilot's exact shape (no `price_context`), and a tampered version that
    must still fail;
  - the batch-B contested case through `desk.gates`, with its negative;
  - the preview-only unreadable case through `desk.week_articles`, and its back-matter variant;
  - a text lint of the workflow's cache steps, and the combined form main carried as its negative.
- **Mutation:** 16 mutants, all killed (13 for these fixes, 3 for the secret guards below).
- **Suite:** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved
  aside, 6,021 passed / 526 skipped.

**THE FIRST WEEKLY RUN ON ACTIONS — it FAILED on a malformed secret, and did not exercise U31f**
**(the second run below did).**
Started 2026-10-20 17:55 UTC on `fix/theme-intelligence-open-leads` (run 39470335127), with a
10-day window and at most 25 articles.
- **What happened.** The gate, the restore, QA, market context and the state-branch commit
  succeeded. The scan failed at its FIRST model call: `httpx2.LocalProtocolError: Illegal header
  value b'*** '`, raised as `anthropic.APIConnectionError: Connection error.`
  - The `ANTHROPIC_API_KEY` Actions secret carries trailing whitespace, which an HTTP header
    cannot carry.
  - The run's own environment dump shows it: `ANTHROPIC_API_KEY: *** ` with a space after the
    mask, where the other secrets show a bare `***`.
- **Cost: $0.** No request was sent.
- **U31f was not exercised.** No model answer was paid for, so no cache was written, and the save
  step was correctly skipped: its `hashFiles(...) != ''` condition held no files. The fix stays
  unproven until a run makes a paid call.
- **The state branch now exists.** `theme-intelligence-state`, root commit `3d577517`, holds this
  failed run's record and readout ("scan exit 1, qa failure"). That is the workflow's design: a
  broken week never looks like a quiet one. The next run imports it.
- **Why it went unnoticed since June.** `validate-keys` (re-run 2026-10-20, run 39472048588) reads
  any non-auth exception as "runner connectivity, NOT a key problem" and passed this key as a
  WARN. Both of its earlier runs failed on 2026-06-26, minutes after the secrets were created;
  their logs have expired.
- **Fixed here:**
  - `require_env` refuses a secret with leading or trailing whitespace, by name and before any
    request. The value is never printed. On this machine all four secrets are clean, so nothing
    local changes.
  - `validate_keys.py` FAILS a padded Anthropic or Polygon key before pinging it.
  - Pinned: a padded value refused by name, a clean one returned as it is, and the validator
    failing both padded keys without printing them. 3 mutants, all killed.
- **OPERATOR, to unblock (all three done 2026-10-21 — see the second run below):**
  1. Re-save the `ANTHROPIC_API_KEY` Actions secret without the trailing whitespace.
  2. Run `validate-keys`, which now fails a padded key.
  3. Run `theme-intelligence-weekly` again. Its first paid call is U31f's proof.

**THE SECOND WEEKLY RUN (2026-10-21) — the scan SUCCEEDED and U31f is PROVEN; the job is red on
one open figure, and Tiingo refuses the Actions key.** The operator re-saved `ANTHROPIC_API_KEY`
(2026-10-21 07:56 UTC); `validate-keys` passed every key (run 39565632511). The weekly run
39565710165 started 07:57 UTC on this branch at cea86303, with the same 10-day window and
25-article cap.
- **The scan.** Window 2026-10-12 to 2026-10-21; exit 0.
  - 7 articles analysed (5 full, 2 partial): J.P. Morgan 1, TrendForce 4, SemiAnalysis 2.
    Citi listed 20, none in the window. Morgan Stanley and Goldman Sachs are manual-first and
    blocked, so nothing was fetched from them.
  - 150 claims extracted and 150 verified. 10 theses created: 3 Research Now and 7 Watch.
  - **Cost $4.445**: 38 model calls, none cached; 355,606 input and 106,679 output tokens; no
    prompt-cache reads, because (d) is still off.
- **U31f is PROVEN, on exactly the case it was built for.**
  - The restore found no cache, as expected for a first paid run.
  - The save step ran on a job that went on to FAIL and wrote
    `theme-intelligence-llm-39565710165-1` (54,124 bytes).
  - The combined `actions/cache` main carried saves only on job success, so it would have thrown
    this run's $4.445 of answers away.
- **QA 21 of 22, so the job is red.** One of 124 figures is open (`capture_not_verified`).
  - TrendForce A-373089a2ba59 b007 is a section heading: "… shipment growth expected to
    approach 36% in 2027".
  - It restates b009's "AI server shipments are projected to increase by nearly 36% YoY", which
    pass 1 captured and verified (C-c935d5c9c651cc).
  - Pass 1b named that claim, but `completeness.states_figure` refused the match. The words beside
    the figure are {approach, expected} in the heading and {increase, nearly, yoy} in the quote,
    with no shared word. A two-digit figure is not "precise" either.
  - Shown by running the function on the two stored sentences.
  - The rule is conservative on purpose: a shared small number is not identity, after the Citi
    transformer false match of 2026-10-11. Here it is a recall miss on a synonym.
  - **Not changed here.** Loosening it trades against that false match. Lead (l) is the agent's.
- **Market context: Tiingo refused every request from Actions.**
  - 43 requests across 32 tickers, every one `Non-retryable 403`. The panel fell back to the two
    years Polygon serves and said so on every row, as designed.
  - The local `TIINGO_API_KEY` gets 200 on the run's exact URL (AMD, 2021-10-01 to 2024-12-31:
    817 rows).
  - Tiingo also answers 403 for an invalid token (`{"detail":"Invalid token."}`), and the run's
    stored error text is cut at 120 characters, before Tiingo's detail.
  - So the Actions secret (saved 2026-10-16 09:03 UTC, never used on Actions before this run) most
    likely does not hold the working key. A refusal of the runner's address is not excluded.
  - `validate-keys` does not check Tiingo, which is why this surfaced only now.
- **Committed to `theme-intelligence-state`:** `bfdc5266` ("scan exit 0, qa failure, market
  success"), the registry plus both readouts.

**TIINGO, CLOSED THE SAME DAY — the key was re-saved and `validate-keys` now checks it.**
- **Operator:** re-saved `TIINGO_API_KEY` at 2026-10-21 08:42 UTC and asked for it to be
  validated.
- **`validate-keys` checks Tiingo** (`check_tiingo`), with the request the weekly run makes:
  daily prices, five years back.
  - An unset key is a WARN; the key is optional.
  - A padded key, or one Tiingo refuses, FAILS the run, and Tiingo's own reason is printed with
    the key masked. A truncated exception string had hidden that reason in the market step.
- **The invariant:** every secret any workflow reads must be passed to `validate-keys` AND read by
  its script.
  - On origin/main's own files, 5 workflows, the sweep finds exactly one: `TIINGO_API_KEY`.
  - On this branch it finds none.
- **Real runs:**
  - On this machine: the local key PASSes; a 40-character invalid key FAILs with "HTTP 403:
    Invalid token."; unset WARNs.
  - On Actions, run 39572152249 at 5efd19e6: Anthropic, Polygon, Tiingo and SEC all PASS, with
    "TIINGO_API_KEY: PASS — 200 from tiingo/daily/aapl/prices".
  - So the 2026-10-21 403s were the OLD key. Tiingo does not refuse the runner's address.
- **Pins:** 5 new tests, and the padded-key test now covers Tiingo.
  - A refused key with Tiingo's real 403 body, plus a hypothetical body echoing the key, which
    must be masked.
  - A working key, and an unset key that sends no request.
  - The validator's exit code.
  - The secrets guard on the repo's own files, with both of its halves as negatives.
- **Mutation:** 9 mutants, all killed.
- **Suite:** 6,026 passed / 526 skipped.
- **Not changed:** the market step still cuts a failed request's text at 120 characters. The
  five-year P/E on Actions shows at the next weekly run's market step, which is $0.

**(d) The stale test branch is deleted.** `theme-intelligence-state-test-20261011` held only
SYNTHETIC commits from 2026-10-11, with no PR. Tip `8d9d00a73fa025fc05974f91f870637f85503d7c`;
restore with `git push origin 8d9d00a73fa025fc05974f91f870637f85503d7c:refs/heads/theme-intelligence-state-test-20261011`.

**BOUNDARY.**
- **Code:** main 07665419.
- **Corpus:** the 132 registries present on this machine on 2026-10-20, of which the live pilot
  `pilot-2026-10-12` is one (13 articles, 38 versions); the rest are test and probe registries
  from 2026-10-10 to 2026-10-16.
- **Units:** counts of stored figures, versions, runs and rows.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The ledger change re-bills a completeness pass only for an article whose ledger it changes.**
  Four stored figures across the corpus; the first Actions run starts from an empty cache anyway.
- **The first state-branch commit comes from this PR's branch, not main.** It is a failed run's
  record, made by code that differs from main only by these fixes.
- **Still open, the operator's:**
  - (a) whether a qualitative sell-off is a dislocation;
  - (d) the article prompt cache;
  - (e) a second Gridlock draw (~$12);
  - (f) page 37's card;
  - (g) a paid re-enrichment;
  - (k) demand-driver names as exposures.
- **Still open, the agent's, awaiting a go:**
  - (l) a restated figure whose two sentences share no word beside it stays open and turns the
    week's QA red (the second run's one open figure).
