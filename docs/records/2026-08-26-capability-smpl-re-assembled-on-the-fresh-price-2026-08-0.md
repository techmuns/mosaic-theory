---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **SMPL re-assembled on the fresh price (2026-08-04) — and P2 is NOT closed in the synthesis.**

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **THE MARKING DID NOT CHANGE THE SYNTHESIS, BECAUSE IT MARKED A PATH THE MODEL WAS NOT
    READING.** `bear[1]` still asserts APRIL's guide in the present tense — *"Management guided FY26
    revenue to -10% to -7% YoY and adjusted EBITDA to -22% to -19% YoY"* — and **July's guide
    (1345–1355 / 220–225) is cited NOWHERE** in the new synthesis. The path is provable, not
    inferred: those percentages exist **only** in `drawdown_cause.revised_guidance`'s verbatim text
    (the structured `primary_source` guidance carries absolute `$M` ranges and **zero** occurrences
    of `-22`/`-19`), and `bear[1]`'s `source_ref` is that field's format — `EDGAR 8-K … Ex-99.1 —
    https://…` — not the digest's `8-K … EX-99.1`. Cause: `synthesis.py:979` dumps
    `mech.model_dump(exclude={"primary_source"})`, so `primary_source` is swapped for the **marked**
    digest while **`drawdown_cause` goes into the raw facts dump unmarked**, carrying April's
    numbers verbatim. #342 marked one of two paths. **This is the same defect #343 fixed in the
    `scenario-propose` template** (which also read `drawdown_cause.revised_guidance`), now shown to
    be live in the brief as well — the field is BY DESIGN the drawdown-moment guide
    (`mechanical.py:2470`), i.e. correctly historical but unlabelled as history. **NEEDS A RULING:**
    mark it via the shared `guidance_vintage_mark`, exclude it from the dump the way
    `primary_source` is, or tell the synthesis what the field means. Not built — the choice is not
    mine.
  - **SMPL LEFT `reconciled` IN THE FRESHNESS GATE, AND THE PIN FORBIDDING THAT RESTED ON A FALSE
    PREMISE.** `test_the_guards_fail_the_four_names_they_should_and_no_others_e2e` pinned
    `"SMPL" in reconciled` with the note *"a regression in price selection, not a data change to
    absorb"* — so it was checked against the selection code rather than absorbed. **There is no
    vintage alignment to regress:** `_stock_info` sets `price = feats.last` (the store's last close)
    and nothing aligns it to the comps export. The 2026-07-29 agreement was the store frontier
    happening to sit five days from the 2026-07-24 panel. Measured: spot `11.32` vs implied
    `909.4M / 88.46M = 10.2803` → **−9.18%**, outside the 2% tolerance; **the cap did not move, the
    market did**. Ordinary drift is a *rendering* obligation (clause (e)), not a failure. The pin
    was replaced by the invariant that is actually true: **`reconciled` must keep a live instance**
    (BRBR/CNXC/EPAM/VRRM), mirroring the existing `assert drifting`, so neither bucket can quietly
    stop being exercised. A per-name pin re-reds on every price refresh and teaches the reader to
    absorb it — the exact failure mode it warned against.
    - **CORRECTION (review of #343) — I CLAIMED THE PAGE DISCHARGES CLAUSE (e). IT DOES NOT.** The
      commit message and the first draft of this entry said *"the page discharges it — the snapshot
      dates both"*. The snapshot does print a date beside the cap, and **that date is the wrong
      panel's.** `render.py:2668` feeds `_brief_snapshot(cap_as_of=...)` from
      `valuation.implied_expectations.multiples_as_of` — the MULTIPLES panel — while the cap's own
      vintage lives only inside its `source_ref` (`… Market Capitalization Latest · as-of …`).
      **Wrong on 11 of 11 committed names.** Worst is **IT: labelled `2026-07-27` for a cap actually
      as-of `2026-06-25`** — a five-week-old cap presented as three days old, the label concealing
      precisely what it exists to disclose. SMPL: labelled `2026-07-21`, actually `2026-07-24`.
      This is **pre-existing, not introduced here**, but #343 makes it load-bearing: SMPL's cap-vs-
      spot divergence went from 0.3% (invisible) to 9.2%, and this label is the reader's only
      defence. **NOT FIXED HERE, and the reason is a rule, not reluctance:** there is no structured
      cap as-of anywhere in `stock_info` — the only copy is inside the `source_ref` string, so a fix
      by regex would be the second divergent parser of one display string, the bug class CLAUDE.md
      names by name. The extractor must expose the structured value first. Recorded as **O3**.
  - **Two new `qa_flags` are FALSE POSITIVES of the DIRECTIONAL-language check**, not a guardrail
    breach: `bull[7]` describes a director's open-market **buy** (an insider transaction) and
    `bear[10]` reports sell-side **conviction** / a 4-**Buy** split (analyst ratings). Both describe
    others' actions; neither is the machine concluding. Recorded, not suppressed.
  - **`llm_call.log` loses the `=== USAGE ===` block on every REFUSED attempt** — the log is written
    at `assemble.py:189`, inside the block that only runs after the refusal check at `:326`, so the
    two 19c/incomplete attempts above recorded no usage. Reported, not fixed (one-line move, but it
    is a code change outside this artifact pass).
  - *Verified:* full offline suite on the freshly-committed artifacts — 1875 passed, 3 skipped;
    ruff + `mypy --strict` clean (ARTIFACT-PASS RULE).
