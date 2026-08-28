---
id:
status: shipped
date: 2026-08-28
prs: []
supersedes:
superseded-by:
---

# The industry trajectory is a series again — four points, one basis

**WHAT.** Pools built for the three earlier trajectory runs (`2026-07-29-03`, `2026-08-12-01`,
`2026-08-14-01`), so the cohort series is measured on the WIDE basis throughout. 241 of 242 names
with a cohort now carry four trajectory points; before this, `_comparable_tail` truncated every one
of them to a single point rather than splice a narrow run onto a widened one (#509).

**NO CURRENT CALL MOVED**: `unresolved 96 · own 81 · cohort 65 · no-cohort 26`, identical before
and after, top-5 unchanged. The backfill adds history, not a re-judgement — the newest point was
already wide.

**THE RUN NAMED IN THE TRAJECTORY HAS NO UNIVERSE ROWS TO POOL.** `2026-07-29-02` and `-03` are
1,780 candidate rows each with not one `grain=universe` line: they re-evaluated that day's
candidates against the universe `-01` had already built. But `-03` is what the trajectory asks for
(it is the same-day run `run_for_stamp` resolves to), so pooling it means drawing members from the
run that did build the day's universe. **Checked, not assumed:** `-01` and `-03` carry
byte-identical `band`, `screen` and `stages` manifests, the same `reference_date`, and the same
`2026-01-30 → 2026-07-29` window. Every borrowed row records `universe_from`.

**THE FENCE PIN WAS TRUE BY ACCIDENT AND IS NOW TRUE BY CONSTRUCTION.**
`test_a_pooled_name_can_never_reach_the_queue` compared the pool against TODAY's queue with no
vintage in it — which held only while one run was pooled, and that run was the queue's own.
Backfilling put 10 names in both sets: ABAT, BBAR, BKKT, CAPR, CDZI, CLBK, CTGO, FLNC, ONON, WLK —
each out of band in July, grown into it since. **That is a name entering the universe, not a
measurement file leaking into selection.** ABAT: 0 candidate rows in `2026-07-29-03`, 1 in
`2026-08-24-01`.

Re-pinned per run, which is how the pool is keyed: no name may be peer AND candidate in the SAME
run — verified across all four (overlap 0/0/0/0) — plus a second pin that nothing pooled for the
queue's own run appears in the queue. The structural fence (`vinci.rank` may not import
`vinci.cohort`; `tickers` comes from the screened set) is unchanged and still the primary defence.

**VERIFIED.** Injecting a same-run peer/candidate into the live pool is CAUGHT; the ten legitimate
cross-run names are in the committed corpus and pass. `--run` refuses an unknown id rather than
falling back to the newest — 6 mutations caught, including the call-site case where `--run` is
accepted and silently ignored.

**FOUND IN PASSING, NOT FIXED (out of scope):** `netcache` resolves its cache directory relative to
the CWD, so running a script from `scripts/` writes a second 4.6MB SEC cache into `scripts/data/`.
Both pool and triage scripts now pin `sys.path` to this checkout for a related reason — a bare
`import vinci` under `scripts/` resolves through the venv's path config to a DIFFERENT worktree.
