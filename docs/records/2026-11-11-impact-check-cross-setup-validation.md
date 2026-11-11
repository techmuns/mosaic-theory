---
id:
status: shipped
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# The impact check: one command writes a fix PR's cross-setup validation from real committed data, base code against head code, at $0 — and the pre-spend check compares values and list members (RD-D4)

**WHAT.** `python -m vinci.impact run --base origin/main --head HEAD --out <outside the repo>`
writes the PR body's `## Cross-setup validation (deterministic)` section and a JSON beside it
(`vinci/impact/`, RUNBOOKS §o). Five parts, each measured with code the only variable:

1. **Fail first.** Head's changed test files run on base's `vinci/` and on head's, both in head's
   tree. A name the tests import that base lacks gets a placeholder that raises where it is used,
   so each node fails at its own line instead of the file failing to collect.
2. **Pages.** Every committed page built at $0 (`prespend.mechanical_build`, no LLM phase) by both
   codes from ONE set of inputs (head's committed data, one store snapshot, the HTTP cache served
   frozen, the CIQ exports hashed before and after), compared value by value with list members
   matched by identity (`vinci/impact/values.py`), with a census of every list family's population.
3. **Synthesis requests.** Each side's request captured from its own build, byte for byte, and the
   six frozen panel pages from their frozen inputs; the row-53 panel check is named owed or not.
4. **Rendered surface.** The committed JSON and the $0 page rendered by both codes, and
   `frontend/build.py` run by both.
5. **Downstream readers.** The changed modules' importers (static `ast` graph) and each offline
   consumer the diff reaches — the decision ledger, `run-monthly`'s scoring report, the monitor
   day, the theme desk, the screen (on `--run-screen`) — run by both codes, outputs diffed.

The section is stamped with base, head, date, the inputs and the PR's own diff identity
(`git patch-id --stable` over every path but docs/, planning/ and the root `.md` files).
**The re-sync rule:** a report stays valid while the patch-id is unchanged AND main touched none of
the PR's own paths since the stamped base (`python -m vinci.impact verify`); anything else is a
re-run.

**RD-D4 (TeamNostra).** `prespend.compare` now pairs every outermost Sourced field through the
same comparator: a list member both pages hold whose field reads worse is a regression (exit 1);
a member that left its list, and a field PRESENT on both whose value, source or note moved, are
listed in full, not a stop. The last line says what was compared and how much moved, never that
nothing was lost.

**WHY.** Operator, 2026-11-11: "we need to make sure the system verifies & validates fixes based on
data deterministically and its implication across the setup before being merged with main / so
the goal in short is to complete the fixes correctly in a faster manner". The streams built this
section by hand, per PR, with bespoke replays (#953's refresh pass, #976's EX-99.1 replay); the
check generalises them to one command with one stamp. RD-D4 is the same defect class one level
down: a gate that compared presence and said nothing was lost.

**HOW VERIFIED.** CORPUS FIRST: the command was run on real merged PRs, and the
section's claims were checked against what each PR's own body says.

- **#976** (base `c2a4d743`, head `2b9b766c`; 27 pages):
  - 0 of 146 guides move.
  - The 21 default-period flags land where #976 put them: BURL 1, EPAM 1, SMPL 13, VITL 1,
    VRRM 5.
  - The refusal notes reach the page's caveats on NFLX (+3) and VITL (+2), as #976 says, and on
    WERN (+2). WERN's sit on a release, 8-K `0000793074-26-000162`, that its committed page does
    not cite yet, so #976's replay of the cited exhibits could not see them.
  - Three exhibits lose their "no anchored pattern" flag: NFLX, VITL and WERN.
  - **No synthesis request moves (0 of 27).** That contradicts #976's body ("they reach the reader
    and the request"). The notes are page flags, and `synthesize` is sent
    `mech.model_dump(exclude=NOT_SENT)` (`synthesis.py:1781`), with `primary_source` excluded and
    no page flag in it.
  - The frozen panel is 0 of 6, and the row-53 check is not owed.
  - Fail first: 29 of 108 nodes in its 3 changed test files fail at base and pass at head. That
    includes 26 of `test_guidance_fix2_e2.py`'s 39 nodes, through a placeholder for
    `GUIDANCE_PERIOD_DEFAULT_PREFIX`, the one name base lacks.
- **#953** (base `586fdcfd`, head `7ec84833`; 27 pages):
  - The page a re-assembly would publish shows MCK's "Impairment headroom" going from
    **$12,950.0M** to **$15,214.0M, as at 2026-09-30**. The intangibles leg moves 1,678
    (`IntangibleAssetsNetExcludingGoodwill`, as at 2012-06-30) → 3,942
    (`FiniteLivedIntangibleAssetsNet`, as at 2026-09-30).
  - The headroom field is gained on all 27 pages; 488 field changes in all, 459 of them in the
    peer block.
  - **Unseen by #953's own check:** the facts its pages' NEXT requests carry move on 23 of 27,
    BURL, CNXC, MCK, ROST and SMPL among them, because the peer block and the intangibles leg are
    sent to the synthesis. #953 compared the frozen panel (0 of 6, as here), which re-uses the
    committed layer.
  - The section puts the panel question to the operator ("ASK THE OPERATOR"): the move is in the
    facts only, and §n names prompt text and the layer's words.
- **#977** (docs only): nothing built. The two code trees are byte-identical (0.2 s).
- **#955 and #954** (ledger, scoring, monitor) exercised the consumers. For #954:
  - the ledger listing differs by its one changed summary line ("… · 0 correction(s) …"), #954's
    own change;
  - `run-monthly`'s scoring report over the 7 committed ledger rows is identical (2,601 bytes);
  - the monitor day is identical (19,546 bytes).
  - #955's fail-first pin is found: `test_a_correction_is_tagged_as_its_decision_is_read` fails
    at base, `:497`.
- **The control** (#977's two refs, `--no-shortcut`, every page built twice from one code with no
  kept build, 54 builds): **0 of 27 pages move (0 field changes), 0 of 27 requests differ, 0 of
  27 renders differ, 0 frontend files differ, 0 responses differ between the sides** (605.2 s,
  0 live fetches). The comparison's noise floor is zero, measured after the fixes below.

**Defects the corpus found in the check itself**, each fixed behind a pin before any number above
was taken:
- **LibreOffice collision.** Two builds converting transcripts at once under LibreOffice's shared
  profile lost a call on one side. A page, its request and the row-53 verdict all moved on #955
  with no code change. Fix: each child gets its own profile
  (`test_every_libreoffice_conversion_runs_under_the_processs_own_profile`).
- **Clock in the assembly log.** The log's fetch time ("(+1.5s fetch)") and the page's assembly
  instant are normalised before comparison.
- **Shared store.** Three page sides failed with `database is locked` while sharing one store
  clone. Each build now gets its own clone, and a fingerprint names any build that writes its
  store (none did).
- **Failures kept in the build cache.** Those failures had been kept and then reused
  (`test_a_failed_build_is_never_reused`).
- **Control and cache.** The control shares one `vinci/` tree on both sides, so its builds would
  have been "kept" and compared with themselves. `--no-shortcut` now reuses no kept build.
- **Positional pairing.** Two drawdown filings of one accession were paired by position (review
  finding 2). They are keyed by `gap_date` now, with a two-field key as the fallback.

**RD-D4, corpus first:**
- The fix log's own evidence is pinned on frozen cuts of the real pages (`7120a4cd^` against
  `7120a4cd`). VITL's `anchor.anchor_base_value_per_share` 30.0469 → None, its `applicable` and
  its `priceable`, and UBER's `priceable`, all stop the pass now. EPAM's same-day rebuild stops on
  none (28 block leaves listed).
- On SMPL's real pair (its 2026-08-18 page against its 2026-11-04 $0 build): 75 of 112 Sourced
  fields change value and 2 list members leave the drawdown window, so value changes are listed,
  never a stop.
- Across the eight real pairs, a block leaf losing its value happens on every one (1–14 leaves),
  so only the three decision leaves stop.

**ADDED THE SAME DAY, on the coordinator's requirements and Codex's round 1 (#1000):**
- **Coverage leads.** Part 2 opens with "built N of M" and names every page not built, with why.
  A hand-built section of #970 built 17 of 27 pages: the other ten refused for want of bars, four
  of them panel pages.
- **The store gap is closed at $0.** The primary's `data/vinci.db` is stale by design, because
  every build refreshes a COPY. It priced 18 of the 27 pages and none of BURL, GOOGL, LLY, MCK,
  NFLX, ROST, TGT, TJX, UBER, V, MDY or SPY. `python -m vinci.impact store` copies it and fills
  every page's ticker and the benchmarks from the HTTP cache, with every socket refused, through
  production's `vinci refresh --aggs`. It priced 30 of 30 in 3.9 s. The cached bars came from one
  `refresh --aggs` of these 30 symbols at 09:31 that day, into a scratch copy, before the
  coordinator's rule against Polygon pulls without asking.
- **One-sided run noise.** A transcript that fails to convert on ONE side, on one input, is the
  machine. That side is re-built once, and set apart as noise if the failure persists. Each child
  already had a LibreOffice profile of its own, so this catches what that cannot.
- **Moves that reach no request.** Part 3 names the pages whose fields move while their request
  stays byte-identical. On #976 that is 7 of 7, with BURL's 1 and SMPL's 13 default-period flags
  among them, all in `primary_source`, which is NOT_SENT.
- **`--resume` keeps a side only while its inputs are unchanged** (Codex P1): every response it
  read must re-hash the same, and its page's CIQ exports must match the ones saved beside it.
- **#970** (base `2b9b766c`, head `03e6d660`, on the filled store): **built 27 of 27**, 0 of 27 move, 0 of 27 requests differ, 0 re-built for one-sided noise, 0 renders differ; fail first: 21 of 58 nodes fail at base and pass at head (762.1 s, 0 live fetches). The hand-built section had built 17 of 27.

**BOUNDARY.**
- **Pages:** the 27 `data/dossiers/*` at each run's head.
- **Inputs:**
  - one store, a `.backup` of eager-mendel's `data/vinci.db` with all 27 names and IWM, MDY, SPY
    refreshed by `--aggs` to the 2026-11-09 close;
  - the primary checkout's `data/cache`, served frozen;
  - the Drive CIQ folder, 285 exports on the 27 pages, hashed before and after, none moved.
- **Measured** 2026-11-11 between 09:50 and 12:00 IST.
- **Wall times** (6 workers):
  - #976, cold cache: 1,800.9 s, of which 4,038 SEC/Polygon responses were fetched live at the
    machine's 8/3-a-second SEC share. A page side's build had a median of 22.5 s and a maximum of
    1,616 s (a cold GOOGL).
  - #953, warm, 0 live fetches: 720.9 s; the control, warm, both sides built: 605.2 s.
  - A page side kept from an earlier run takes about 0 s; the 2-page #954 re-run fell from 183.7 s
    to 95.5 s.
  - A docs-only PR: 0.2 s.
- **Counts:** guide counts are the members of `mechanical.primary_source.releases[].guidance[]` on
  the $0 builds. #976's own 141 counted every EX-99.1 its committed pages cite, a different
  population, and 0 move in both.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A cold cache is the cost.** Every page a new store frontier has not seen fetches its filings
  once, on the machine's SEC share. After that, a run is mostly CPU, and main's side is built once
  per main commit (`~/.cache/vinci/impact-builds/`, outside every repo; it keeps request text, as
  the run folder does).
- **ACCEPTED, with falsifiers:**
  - The $0 page is the paid build minus its LLM phases. A change confined to the covenant,
    maturity or transcript-driver extraction does not show here; falsifier: a paid rebuild moving
    a field this check called unmoved.
  - The import graph is static. A dynamic import outside `vinci.quality` is invisible; falsifier:
    a consumer moving on a PR this check called "not reached".
  - The screen consumer runs only on `--run-screen`.
- **Corrections to merged PR bodies, measured here, nothing rewritten:**
  - #976's "the request" moves on NFLX and VITL: it does not.
  - #953's "every request stays byte-identical": it holds for the frozen replay only.
- **The CI check** that refuses a code PR body without this section, or with a stamp that no longer
  matches, is its own PR, opened after this one merges.
## Amendments

- **2026-11-11 — `status: open` → `shipped`** (the record-status sweep, `docs/records/2026-11-11-record-status-sweep.md`). This record's change merged to `main` as `fb568c7f` (#1000) on 2026-11-11. `prs:` was left empty at merge; the front matter stays as merged, so this entry names the PR.
