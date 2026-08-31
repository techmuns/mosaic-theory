---
id:
status: shipped
date: 2026-08-31
prs: [531]
supersedes:
superseded-by:
---

# The one command that adds out-of-band names was the one the leak guard could not see

**WHAT.** `vinci refresh` never stamped `first_seen`, so every identity it INTRODUCED carried NULL
— QQQ, TSM and V in the committed entity master. `identities_first_seen_after` (the #442
failed-forward-run guard) filters on `first_seen > ?`, and **`NULL > date` is never true in SQL**,
so those identities were invisible to it. Fixed on both sides: `refresh` now stamps, and the guard
fails CLOSED on unknown provenance instead of trusting a field any writer can omit.

**WHY IT MATTERS — the #442 leak, re-opened through an unfilled field.** The guard exists because a
`run-weekly --end 2026-08-13` aborted after `build_universe` had upserted three securities, and the
backdated re-run at `--end 2026-08-12` then found them ALREADY IN THE STORE and admitted them to a
universe that could not have known them — a committed historical screen containing names from its
own future. `orchestrator.py:319` raises on exactly that. But a `vinci refresh X` followed by a
backdated run would sail through, because X has no `first_seen` to compare. **The one command whose
whole purpose is adding names OUTSIDE the cap band was the one command whose names the guard could
not see.** Same omission class as the SIC that #528 fixed on this same call — `build_universe`
passed `first_seen=reference_date`, this path passed nothing.

**HOW IT WAS FOUND.** Chasing an unrelated question about LLY's entity-master row. That row turned
out to be **completely correct** — verified field-by-field against a live resolve — but printing
`first_seen` beside each dossier's date showed three names with none at all, and one (`V`) that no
guard could ever see.

**THE FIX, THREE PARTS.**
1. **Source** — `_cmd_refresh` stamps `first_seen=date.today()`. `upsert_security` COALESCEs the
   field, so this only ever stamps a NEW row; an identity already in the store keeps the date it
   was really first seen, and a later refresh can never overwrite a true earlier date.
2. **Guard** — `identities_first_seen_after` now counts a NULL as "after". Unknown provenance
   cannot confirm the name was knowable at the reference date, so it fails CLOSED, the way
   `unknown_sic` excludes a name whose business type the universe cannot confirm.
3. **Data** — QQQ, TSM and V stamped from EVIDENCE, not a guess: the commit in which each identity
   first appears in the committed `securities.jsonl` (TSM 2026-06-19 `ea95072`; QQQ and V
   2026-08-13 `513b2a9`). That date can only be >= the truth, and later is the conservative
   direction for a fail-closed guard — it can over-exclude from a backdated run, never silently
   admit.

**THE BENCHMARK EXEMPTION IS LOAD-BEARING, not a convenience.** SPY/IWM/MDY and the sector ETFs are
`IDX-*` identities with no `first_seen` BY CONSTRUCTION (`benchmark_identity`), upserted by the
screen and the orchestrator themselves. A naive NULL-inclusive guard makes EVERY backdated run
raise on the rows it just wrote — failing closed on nothing real. Demonstrated: without the
exemption the guard returns `['IDX-IWM', 'IDX-SPY']` on a store containing only benchmarks.

**VERIFIED.** The artifact diff is `first_seen`-only — fields changed anywhere `['first_seen']`, 3
rows, PK set identical. Each pin demonstrated failing against the real pre-fix state: the artifact
pin names `['QQQ', 'TSM', 'V']` on the committed snapshot; the guard pin fails with the old SQL
restored; the exemption pin fails against a naive NULL-inclusive guard. ruff + `mypy --strict vinci`
clean; `pytest -m "not network"` 3376 passed, 0 failed, 144 network-skipped.

**INCIDENT → INVARIANT (shipped Y).** `tests/test_first_seen_provenance.py`:
`test_every_committed_identity_records_when_it_was_first_seen` (the artifact),
`test_an_identity_with_no_first_seen_fails_the_backdated_run_guard` (fail-closed),
`test_the_guard_never_fires_on_a_synthetic_benchmark` (the exemption),
`test_refresh_stamps_first_seen_on_an_identity_it_introduces` (the source, including that a later
refresh cannot overwrite a true earlier date).

**NOT DONE.** `first_seen` for LLY, NFLX and UBER reads 2026-08-24 — LATER than their own dossiers
(2026-08-21, 2026-08-10, 2026-08-07), because #527 re-introduced those identities and the store
genuinely learned them then. It is an honest record of this store's knowledge, not a fabrication,
and correcting it would mean inventing a date the record does not support. Left as-is, deliberately.
