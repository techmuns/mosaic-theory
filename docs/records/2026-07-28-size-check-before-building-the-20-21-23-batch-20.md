---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**SIZE CHECK BEFORE BUILDING THE 20+21+23 BATCH — 2026-07-28 (operator asked to be told BEFORE
rather than after). VERDICT: THE BATCH IS NOT ONE PR, AND ONE OF THE THREE IS MIS-SCOPED.**
· **ITEM 20 — SMALL, ~2 lines + a test. SHIP IT.** The claim VERIFIES against the real workbook:
SMPL's quarterly `P/LTM EPS` Close series literally ends `NM`, prior cell `15.89`. But THE AUDIT
MISPLACED THE DEFECT: `_multiples_close` is CORRECT — its docstring says "empty/NM → None" and it
does exactly that. The backward-fill is in the CONSUMER, `range_position` (`ciq_sheets.py:302,316`):
`pe = [v for _, v in _multiples_close(...) if v is not None]` FILTERS THE ABSENCE AWAY, then
`pe[-1]` takes the last survivor — the previous quarter. Backward-fill by a different route than the
audit described, which matters because a fix aimed at the READER would have changed nothing. Fix:
read the LATEST cell; print nothing (or UNKNOWN) when it is None.
· **ITEM 21 — MEDIUM, NOT the one-line routing change the audit implies.** The routing IS one line
(`ciq_sheets.py:1900`, `read_text(wb.path, wb.fmt)` → `read_sheets`). But
`_parse_business_relationships(raw)` consumes **TEXT**, while `read_sheets()` returns
`dict[str, list[list]]` — a different shape. **The parser rewrite for the sheet shape IS the item.**
Plus `Suppliers.xls` is a NEW consumer (never opened; carries the creditor group). Ship it, but as
its own PR with its own red (`Customers.xls` reads successfully), not as a third of a batch.
· **ITEM 23 — MIS-SCOPED. AS WRITTEN IT WOULD CHANGE NOTHING. DO NOT BUILD IT YET.** The extractor
ALREADY uses exactly one vintage: `1,351.8` is Trends "latest", and the acceleration read prints
the whole path (`1,334.2 (3m) → 1,335.1 (2m) → 1,333.9 (1m) → 1,351.8 (latest)`). The `1,334` is
NOT a second extraction — it is the ANALYST'S FROZEN RECORD REFERENCE, source-stamped "committed
dossier financial_summary (E cols = consensus)": what the dossier said when they underwrote,
CORRECTLY frozen at entry vintage. So "single vintage per build, stamped once" targets a mechanism
that is not the defect — the FOURTH instance of that pattern this week (P1's guard, item 18's
input, item 1's flat max, now this). The real issue is **an entry-vintage record value rendering
beside a fresh extraction value with nothing marking the difference**, which is ALREADY item 1's
clause: "entry-vintage values are exempt but must be LABELLED entry-vintage wherever they render
beside fresh values." **Recommendation: fold 23 into item 1's labelling clause and close it as a
duplicate, or re-spec it — operator's call. It is not a mechanical build.**
· **CONSEQUENCE FOR THE ARITHMETIC:** "one PR takes the original nine from 1 closed to 4 closed"
does not hold. Honest count: **20 closes P5** (small); **21 closes P6** (medium, own PR); **23 does
NOT close P8 as written**. The batch realistically takes the nine from 1 closed to **3 closed**,
across TWO PRs, with P8 returning to spec.
