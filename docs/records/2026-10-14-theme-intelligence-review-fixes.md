---
id: 2026-10-14-theme-intelligence-review-fixes
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the fifteen code-review findings, fixed

**WHAT.** Operator, 2026-10-14: "Apply these 15 code-review findings with the minimal edits." The
findings came from a max-effort review of PR #703: 13 finder angles, 36 candidates checked by
verifiers running the code, and a gap sweep. Each fix ships a regression test that fails without
it.

| # | Defect | Fix |
|---|---|---|
| 1 | The weekly workflow's `if: always()` commit pushed an EMPTY registry over the state branch when the restore failed (a branch exported by newer code). | The commit runs only when the restore step succeeded (`steps.restore.outcome == 'success'`). A failed SCAN is still committed. |
| 2 | `state pull` replaced the local registry before importing. A failed import, or a replay error other than a document error, left nothing that knew the unpushed upload. | The rebuild is all-or-nothing: on failure the local registry is restored from its backup and the pull refused, with nothing changed. Any replay failure is reported per document, and the document is kept as **pending** in the sync state; the next pull replays it. |
| 3 | A non-verbatim quote was re-anchored to a source sentence that says the opposite ("rose 9%" / "fell 9%"; a dropped "not"). | `verify.reverses`: a candidate sentence negated where the quote or statement is not, or stating the opposite direction, is never a re-anchor. |
| 4 | A figure was matched as a raw substring ('5' in '15%'); a multiple or basis-point figure passed with unit '%'; a name inside another word verified ("Meta" in "metadata", "AI" in "said"). | Whole figures, bounded by digits only (`_whole_figure`). An x / bp figure disagrees with a % unit. Mentions and sectors match whole words, allowing a plural and a glued footnote digit. |
| 5 | The card-number check pooled the model's own statement, so the line was checked against itself; an empty quote was span-verified. | The pool is the verbatim quote and value plus the claim's structured period, metric and scope, compared as magnitudes. A capitalised name with a one-digit version ("Era 3", "Opus 4.5") is excused, like a hyphenated name. `locate("")` is no span. |
| 6 | A sidecar `"llm_permitted": "false"` was read `bool("false")`, i.e. as permitted. | Read strictly: a JSON boolean or the words true/false. Anything else is refused, and the file is left in the inbox. |
| 7 | Re-analysis committed the retirement, then failed on deterministic triggers. | Each article's text is read and the order fixed BEFORE retiring. No per-document limit (the run budget bounds it, as a state replay). A passage re-anchored by an earlier run is kept, never a clash. A failure after retiring is `ReanalysisIncompleteError`, naming the run that finishes it (the same articles without `--retire`), never "refused". |
| 8 | Naive and aware publication instants were compared: one date-only stamp crashed every desk render. | Every instant is aware: the parser, the listing and declared dates, and a schema validator for records already stored (naive reads as UTC). |
| 9 | "A hold can never promote" raised on a legal SKIP → WATCH move under a hold, failing the scan. | The invariant is the one the rules enforce: a hold never yields RESEARCH NOW. |
| 10 | The push's tree check scanned the whole cloned branch, including the scheduled run's `readouts/`, so every laptop push was refused after the first Actions commit. | Only what a push writes — `registry/` — is checked. |
| 11 | A BLOCKED article record made the URL "KNOWN" for good. | A URL a scan already tried is KNOWN only when that try finished it. The article row decides only for URLs no scan has tried. |
| 12 | A same-key merge dropped the merged-in hypothesis's catalyst, strongest evidence, sectors, steps and its own risks. | Every role is folded in: catalyst, strongest, implications, sectors by name, earnings steps the kept chain lacks, risks tied to any merged hypothesis. |
| 13 | The resolution id hashed a subset of the record, so one name resolved two ways got one id with two payloads (StoreIntegrityError). | The id hashes every stored field but its time. |
| 14 | One unusable cached model answer failed the whole weekly scan. | That article is FAILED (said, checkpointed, its cache file named) and the scan goes on, PARTIAL. **Not re-asked:** the approved 2026-10-12 decision (an identical re-ask repeated the slip 4 of 4 times) stands. |
| 15 | A retired thesis was re-graded (new version, DOWNGRADED event) and counted as a live action in the weekly brief. | `reassess` never touches a retired thesis. The brief's Research Now / Watch / Skip counts and its ranking leave retired theses out, and say how many there were. The desk's This week lists them last, with no open-conditions badge. |

**WHY.** A wrong fact marked verified, data loss, and scans failing on one article: all three
break "fail loud, never fabricate".

**HOW VERIFIED.**
- **Corpus before synthetic**, old vs new `verify.py` over every local registry (147, read-only):
  - **Figure check:** 2,203 stored claims, **0 change**. The first draft of the boundary refused
    9 real claims ("$1.655 billion" in "US$1.655 billion", "707.5" in "707.5GVA"); the boundary
    now rejects only neighbouring digits.
  - **Mentions:** 450 checked; **2 change**, both glued page chrome ("Substackis"), correctly
    refused. A first draft also refused "COP2814" (a footnote marker glued to COP28); a trailing
    digit is now allowed.
  - **Sectors:** 153, **0 change**.
  - **Past re-anchors:** 130, **none reverses its quote**.
  - **Card lines:**
    - The first draft (verbatim evidence only) flagged 135 distinct lines; 84 of them used the
      claim's own period ("2027") or metric ("3-month").
    - With period, metric and scope pooled, version names excused and magnitudes compared, the
      **live pilot's 344 source-labelled lines on current versions get 0 new flags**.
    - Elsewhere (scratch and acceptance registries): 78 new issues, each a line printing a
      number its cited evidence does not carry, and 10 old ones gone.
- **A real run on the pilot, $0** (`run_reassess` of all 23 theses from stored evidence, no model,
  on a copy):
  - Old code re-graded the retired TH-BF20FBC464 (a new version: finding 15 on real data) and
    raised 7 card-line issues, 6 of them on that retired thesis.
  - New code leaves it alone and raises 1, the same one the old code raises.
  - No action changes otherwise.
  - The pilot registry's checksum is unchanged.
- **Mutants: 33 of 33 killed**, at least one per fix, each against its own regression test. Two
  survived the first pass because the tests could not see them — the version-name excuse (the
  quote also named it) and the `reassess` guard (nothing would have changed). Both tests were
  tightened; both are now killed.
- **The suite caught one regression:** `test_research_now_on_a_source_named_sector_with_no_ticker`.
  The card printed the statement's "−10%" for the verbatim "fell 10%", and once the statement
  left the pool the sign failed the check. The card check now compares magnitudes.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- "147 registries / 2,203 claims / 450 mentions / 153 sectors / 130 re-anchors / 551 versions":
  every `registry.db` under the `theme-intelligence` worktree's `data/theme_intelligence/`
  except backups, distinct by id, read 2026-10-14.
- "344 lines": the source-labelled card lines of the pilot registry's current versions.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of model spend.
- **Not done (outside the fifteen):**
  - the first-token family guard in the resolver;
  - the alias dedupe in `verify` ("Alphabet" / "Alphabet Inc.");
  - quarter-label stripping in the card check;
  - the replay re-paying when the registry context moved;
  - the remaining review findings in the scratchpad pool.
- **Steps are folded only where the kept chain lacks that step** (finding 12): two hypotheses'
  chains are not concatenated.
