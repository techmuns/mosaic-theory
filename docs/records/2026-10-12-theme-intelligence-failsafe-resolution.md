---
id: 2026-10-12-theme-intelligence-failsafe-resolution
status: recorded
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — a review finding is resolved by a relabel only when it is about the label alone; Nomura's s07.2 finding returns to unresolved

**WHAT.**
- **The defect, raised by the operator:** `report._resolved_by_relabel` retired a REVIEW_PARTIAL
  finding whenever its words named the line's former fact label, even when the same finding also
  objected to content.
- **The fix:** the finding is now read FAIL-SAFE (`report.finding_scope`).
  - **label_only:** every clause is about the label, or affirms support with no hedge. Only these
    are resolved by the relabel.
  - **mixed:** it names the label AND objects to content, e.g. "support only parts", "not in the
    cited span", "overstates", "missing". It stays unresolved.
  - **ambiguous:** some clause is neither about the label nor a plain affirmation. It stays
    unresolved.
- **Nothing is edited either way.** The reviewer's words stay whole on the line (resolved or not),
  and the original finding stands in its run.
- **This corrects one claim of `2026-10-12-theme-intelligence-final-corrections.md`**, whose body
  stands as written: that record said Nomura's Review Required went from 5 lines to 3, with two
  findings resolved.
  - **s07.2** — its complete finding also says *"The cited observations … support only parts"* — is
    MIXED and returns to UNRESOLVED.
  - **s07.3** — its complete finding objects to the label and otherwise affirms the cited figures
    ("are cited observations; the inference is not measured") — is label-only and stays resolved.
  - **Net effect:** the Nomura card reads Review required · 4 lines, 1 earlier finding resolved. The
    weekly summary counts 8 current-card findings, not 7.

**WHY.** A relabel answers only an objection to the label. Retiring a finding that also objects to
content hides an open problem behind a fix to a different one. Under doubt the finding stays open,
which is the safe direction.

**HOW VERIFIED.**
- **Real data:** the two Nomura findings read whole from the pilot registry (read-only): s07.2
  `mixed`, s07.3 `label_only`. The re-rendered preview shows s07.2 under UNRESOLVED REVIEW with its
  full wording, and s07.3 as resolved history.
- **Unchanged checks:** 0 broken links, integrity all pass, QA 22/22.
- **Tests** in `tests/test_theme_intelligence_final_corrections.py`:
  - 4 new end-to-end cases. A label-only finding is resolved. A mixed ("support only parts"), a
    mixed ("not in the cited span") and an ambiguous finding all stay unresolved. In each case the
    whole wording is kept on the line and the original finding is unedited in its run.
  - 10 cases of the finding reader.
- **Mutants:** 5 of 5 killed — the old name-only rule, content objections ignored, an unreadable
  clause passing, a hedged affirmation counting, mixed counted as label-only.
- **Gate:** ruff, `mypy --strict` and the offline suite (results in the PR).

**BOUNDARY.** "Nomura's findings": the two REVIEW_PARTIAL issues on `TH-2FFD9B58A8` lines s07.2 and
s07.3 recorded by the run `R-20261012T102530Z-article` (v1), read 2026-10-12. "8 current-card
findings": the weekly report `R-20261012T133511Z-scan` on
`data/theme_intelligence/v2/pilot-preview2-2026-10-12/`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call, no article re-run, no record edited.
- **The reader is lexical, so it errs toward OPEN.** A purely label-related finding worded in a way
  it does not recognise stays unresolved and remains on the card for the human. That is the
  intended failure mode; the opposite one was the defect.
