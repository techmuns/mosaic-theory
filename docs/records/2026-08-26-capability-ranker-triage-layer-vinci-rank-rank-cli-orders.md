---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **Ranker / triage layer** (`vinci/rank`, `rank` CLI) — **orders** the ~307 candidates into a

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Coverage caveat (an upstream data gap, NOT a ranker defect):** the ranking is **most reliable
    for names with a *confirmed* at-floor multiple, weaker for the ~51% without one** —
    multiple-percentile is present for only ~49% (P/E only; **EV/EBITDA pctile never populated** →
    that axis is UNKNOWN/0-credit, flagged, for the rest); **market_cap is 100% UNKNOWN** so
    tradeability rests on ADV alone; **events are 100% EOD `earnings_gap_down`** (no 8-K/guidance
    text — so drawdown-character is one axis, and Tier-2 reads *current* volume, not volume-at-the-
    gap). All handled fail-loud (UNKNOWN → 0-credit + flagged, never imputed) — correct behaviour; the
    fix is upstream coverage (§4), recorded not chased.
  - **Tier-3 DETERMINISTIC structural-disqualifier channel** (`vinci/rank/structural.py`, `rank
    --structural` flag) — **DEMOTE-ONLY, source-bound, off by default (network).** Reads the **free**
    EDGAR 8-K full text (item codes + body) + the EDGAR-XBRL shares series already used for market
    cap, and flags TERMINAL/STRUCTURAL signals only: **restatement/non-reliance (Item 4.02)**,
    **going-concern / substantial-doubt** (filing text), **delisting/deficiency (Item 3.01)**,
    **auditor resignation/dismissal (Item 4.01 + resign/dismiss verb)**, and a **dilution death-spiral**
    (shares ↑ ≥50% into a ≤−50% TRAILING drawdown — the *already-computed* historical drawdown, never
    a forward return). A fired flag **caps `priority_score` at 0.05 via `min()` (can only LOWER) and
    sorts the name to the queue bottom** — **there is NO promote path**; default is `UNCLASSIFIED`
    (`None`) → **zero effect, never fabricated**. Every flag is **source-bound** (accession + item +
    date, or the two share datapoints) so the human verifies. This completes the Tier-3 slot that was
    `UNCLASSIFIED` because 8-K text was never wired; it is **separate** from the LLM cause-annotation
    channel (which can boost mean-revert) — *this* one can only sink. **Its only job is triage hygiene
    — stop wasting CIQ deep-pull on structurally-dead names; NOT a return predictor.** *Verified by a
    real run: `rank --structural --no-write` over the committed 301-candidate snapshot → **50 sunk**
    (23 dilution-spiral / 10 auditor-exit / 7 restatement / 5 going-concern / 5 delisting; was 54
    before the post-review auditor-precision fix below), each traced to a specific 8-K
    (accession+item+date) or XBRL share series; **deterministic** (a warm re-scan reproduces the same
    set). Read the primary filing for the non-trivial cases: RGC dilution = **13.0M → 494.5M** shares;
    TLRY/EOSE/ZBIO going-concern + MVST/BBAI restatement language confirmed in the cited 8-K.*
    **Honest precision caveat — by design, not a defect:** the signals fire on structural **FORM**
    (item code + verb / language / share-count delta), which has a residual false-positive surface —
    e.g. **MBLY's "dilution" is Intel's Class-B→A distribution**, not new issuance. (The auditor leg
    also over-fired on routine changes — FUBO's merger-driven KPMG dismissal, a clean Big-4 switch —
    and was tightened post-review to require auditor-proximity + cause; PODD still fires, **correctly**,
    on its disclosed material weakness.) That is exactly why the channel is **demote-to-verify, never
    auto-kill**: it sinks a name for a human verification glance with the source attached; **the
    machine sinks + cites, the
    human concludes** (CLAUDE.md). Tests: each signal fires + is source-bound, dilution needs BOTH
    legs, default-`None` never fabricated, severity ordering, the explicit **no-promote-path** test
    (flagged score ≤ unflagged across strong+weak setups, sunk ≤ the 0.05 cap), sink-below-a-clean-name
    in the queue, no-flag leaves score/sort untouched; the AST no-forward-returns guard extended to
    assert `structural.py` is in scope. ruff + `mypy --strict` clean.
    - **Hardened post-code-review (pre-push audit).** (1) **Whole-scan resilience:** `scan_structural`
      now wraps each candidate in a per-name `except Exception` (mirrors `assemble_cohort`) — one bad
      EDGAR response or corrupt cache file (`JSONDecodeError`/`TypeError`/`IndexError` the per-extractor
      helpers didn't catch) skips that name, never aborts the 301-name pass; regression-tested.
      (2) **Auditor signal no longer over-fires:** `_AUDITOR_EXIT` was matching any `resign`/`dismiss`
      anywhere in the body → it wrongly DEMOTED good names (a routine Big-4 upgrade, a co-filed 5.02
      director resignation). A wrong demote is a silent miss at the funnel top, which demote-only does
      NOT protect against. Replaced with auditor-PROXIMITY: a resignation near an auditor token fires
      (auditor-initiated), a dismissal fires ONLY with an affirmative cause marker
      (disagreement/material-weakness) so an upgrade ("dismissed X, engaged Y, no disagreements")
      stays unflagged; tested (Big-4 upgrade + director resignation do NOT fire; resignation +
      dismissal-for-cause do). **KNOWN LIMITATION, recorded not fixed (#3):** going-concern body text
      is read only for `_BODY_ITEMS` {2.02,4.01,8.01,4.02}, so going-concern disclosed under
      2.04/1.01 is missed — a **safe-direction MISS** (under-demote → the name still reaches the
      dossier, which reads its 8-Ks and surfaces the distress), consistent with the recall-favoring
      funnel. Fix only if it bites in real use. ruff + `mypy --strict` clean; 178 suite green.
