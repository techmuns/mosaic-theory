---
id: 
status: shipped
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**CALL-SITE PARITY LANDED — AND EXTENDING IT FOUND THAT ASSEMBLY DROPS `ev_gap` (2026-08-03).**
`tests/test_consensus_parity.py` sat on an orphan branch, **never PR'd**, 33 commits behind. Read
before deciding: it still passes on current main, skips cleanly with no licensed CIQ, and **both
mutations redden** (a dropped cell; the estimate pair re-labelled as a count) — so it measures
rather than decorates. It closes the residual the CPB assembly-vs-refresh diff **structurally could
not reach**: CPB has no CIQ bundle, and no name can exercise both halves because the set with
bundles and the set with dossiers ARE THE SAME ELEVEN. *Structural is an argument, not a
measurement* — kept verbatim in the docstring.
**THE SKIP GUARD WAS THE FOURTH INSTANCE of the guard-that-cannot-fire pattern** (item 1's
completeness gate · the absence-reason guard · #310's no-op `getattr` · `test_consensus_rows` in
#318). `except Exception: pytest.skip` never fired — `files()` returns `[]` without raising — so
the file passed in CI only because a SECOND skip caught it downstream. **Working by accident is not
working**; conditioned on the file list, per the house convention.
**THE OPERATOR'S CHECK FOUND A LIVE DEFECT, AND IT THREATENS THE NEXT QUEUED TASK.** The test was
written when `consensus_levels` was the only field with two write paths; there are now three.
**`ev_gap` IS WRITTEN ONLY BY `refresh.ev_gap_transform` — ASSEMBLY NEVER SETS IT.** The field
defaults to None and no assembly path touches it, so **a fresh assembly writes `ev_gap: null` and
the page reverts to "MISSING REFRESH".** SMPL's re-assembly is NEXT in the queue and SMPL is one of
only three names carrying a decomposition, so re-assembling it today would silently drop the EV gap
the last two builds existed to produce. The render would be honest about it — that is what the
three-state design bought — but the number would be gone.
**~~PINNED AS THE ASYMMETRY IT IS~~ — THAT WAS A TOMBSTONE, NOT A GUARD (review of #324).** The
pin passed happily while a fresh assembly wrote `ev_gap: null` and would have reddened only once
somebody FIXED it. **A test that is green throughout the harm and red at the repair protects
nothing** — it offered the queued SMPL re-assembly exactly no cover from the event it described.
**CLOSED INSTEAD OF DOCUMENTED: assembly now applies `ev_gap_transform` to the freshly-built mech**,
so both write paths run the SAME builder and cannot disagree by construction. **RECOMPUTED, NEVER
CARRIED FORWARD** — copying the committed gap across an assembly would put one struck on old
cap/net-debt/consensus beside new ones, the frozen-beside-live defect.
**AND CI CAUGHT A THIRD LOCAL-GREEN DEFECT FROM THE LICENSED-EXPORT-ABSENT CLASS.** The new test
strips `ev_gap` (that is what assembly hands over), so with no bundle there is neither a workbook
to read `consensus_as_of` from NOR a prior stamp to carry forward — correct answer None, and the
vintage comparison went red in CI while passing here. **Split by what each half depends on:** the
RATIOS are struck from the stored mech and the committed record and are asserted EVERYWHERE
(mutation-verified in CI's own condition); the VINTAGES depend on the export and are asserted only
where it exists. Not a live concern — a real assembly cannot run without the bundle — which is why
it is conditioned rather than dropped.
**AND THE FIRST REPLACEMENT PIN WAS ALSO WRONG, caught by its own mutation:** it searched the
assembly source for the NAME `ev_gap_transform`, and deleting the two lines that apply it left the
`import` behind — **the pin passed on a build that had stopped calling it.** An import is not a
call. Now an AST check that the transform's result is ASSIGNED BACK TO `mech`, which also catches
the call-but-discard shape. Both mutations CAUGHT. The insider line's two paths are NAMED and deliberately NOT compared
— refresh's fetches ~110 filings from EDGAR, and a value comparison would turn an offline parity
test into a network one.
**SCOPE IS STATED IN THE DOCSTRING** so a green run is not read as covering the layer: values
compared for one field, asymmetry pinned for the second, omission named for the third.
Gate: ruff + `mypy --strict` clean · full suite green · CI-condition run: 2 passed, 5 skipped.
