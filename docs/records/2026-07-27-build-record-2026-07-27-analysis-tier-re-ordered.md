---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-27 ANALYSIS TIER RE-ORDERED BY DECISION QUESTION (PR 2b).** Closes the
report re-structure. The audit's root cause was that both tiers were composed and ordered by WHERE
CONTENT WAS COMPUTED, not by the question it answers; PR 1 fixed composition, this fixes order.
NEW ORDER (both twins, identical): what broke → business quality → the argument → catalyst calendar
→ valuation → peer comps → operating trajectory → the street → leverage & survival → analyst
caveats. The argument moves from LAST to 3rd and the calendar from last to 4th (on a
months-to-quarters book the dated path IS the trade); caveats move from 1st to last (doubt after
the claim it qualifies, and the Brief already carries the conditional warning strip).
**"## Mechanical layer" WRAPPER REMOVED**, and the analysis section heads promoted H3 → H2. The
operator asked what was structurally correct rather than convenient; the answer is that the wrapper
CLAIMED to encode the assemble-not-conclude line but did not: the argument and the caveats are both
machine-produced and both sat OUTSIDE it, so what it actually separated was structured facts from
prose — a format distinction wearing a provenance label. It enforced nothing (delete it and no
discipline weakens, unlike the no-verdict-field pin, the frozen proposal mapping or the peer/implied
fences), it duplicated more crudely what per-fact SOURCE-BINDING already does precisely, the three
tiers already carry decide/argue/prove, and the web twin never had it — so it was also a standing
asymmetry. It further BLOCKED the reorder: promoting the argument (an H2) above H3 siblings would
have orphaned every section after it. SCOPE — render-only, verified before building: the assembler
emits no headings, nothing in vinci/frontend/functions parses md headings, no test pinned the
wrapper, the `.md` is DOWNLOADED not rendered, and the PDF comes from the WEB DOM via window.print
(so the md re-level touches only the downloaded file). `dossier.json` is untouched: no schema
change, no re-assembly, no LLM. VERIFIED: fact-inventory invariant (1,030 labels) — 0 lost, 0
gained; the only 4 deltas are composite roll-up lines whose MEMBERS re-ordered with the sections
(member-set decomposition proves identical membership). Live web preview confirms the twin renders
the same 10 sections in the same order with the wrapper gone. INVARIANT:
`test_analysis_tier_reads_in_decision_order_e2e` pins the order in BOTH twins and asserts the
wrapper cannot return — mutation-tested. **REVIEW FIX (blocking):** the md half first READ
`dossier.md` off disk, making it an artifact-staleness check, not a RENDERER check — a `render.py`
reorder shipped fully green (reproduced). It now RE-RENDERS from committed JSON and compares back
to disk, so it guards renderer + freshness together; a per-dossier ≥8-section floor closes the
related hole that ordering a 1-element list is trivially true. Also fixed: five stale statements of
the OLD order (two in `render_markdown`'s docstring/banner, one above `analysisTier`, the
"PLACEMENT B — Analysis closer" framing in three places, and the now-false "the facts above stand
on their own" line in both twins). NOTE (fold behaviour, not data loss): `_dedupe_unknown_reasons`
anchors a folded UNKNOWN line at its FIRST member's position, so the forward-adjusted-leverage fold
moved from Leverage & survival to Valuation on 10 of 11 tickers — membership-identical, invisible
to a label inventory, but a reader in Leverage no longer sees that row. Mutation-tested (swapping two web sections reddens it
and names the offending order). The pre-existing minimal-fixture order pin was rewritten and now
documents why the calendar/street sections are legitimately absent from that fixture. Gate: ruff +
`mypy --strict` clean · 1074 passed.
