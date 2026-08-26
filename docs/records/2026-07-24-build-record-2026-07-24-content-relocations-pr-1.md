---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 CONTENT RELOCATIONS (PR 1 of the report re-structure).** Operator
audit found the tiers were ordered AND composed by where content was COMPUTED, not by the question
it answers. This pass fixes composition only (ordering is a separate PR). SHIPPED, both twins:
(1) **"Ownership & concentration" -> "Business quality"** — the section carried NO ownership; all
four facts are business MIX (segments revenue share, segment EBITDA, customers, geography). It is
now the architecture's business-quality section. (2) **Insider activity + short interest** — the
only real OWNERSHIP content, sat inside "The street - estimates & guidance"; relocated to a new
appendix section **"Ownership & positioning"** (same move the management-commentary pointer already
made), and the street subtitle dropped its stale "and positioning" promise. (3) **"What happened"
-> "What happened - and can it survive?"** — TITLE, not composition: the section carries survival
triage (net debt/EBITDA, FCF sign, going concern) beside the event, which is RIGHT (overshoot-vs-
terminal is the fund's question and survival is its discriminator) but the old title described only
the first half. (4) **Brief consensus reframed as CONTRAST** ("The street, for contrast") — on a
fund whose edge IS a variant view, listing the street's target as a peer of our own valuation rows
blurs the distinction being sold. DROPPED ON INSPECTION, with reasons: **consensus path anchors
stay put** — they are not stray street data, they are the COMPARISON BASELINE directly under the
price-implied table, and its "at the name's own multiple the implied level is consensus by
identity" footnote only checks against them; moving them would orphan the table. **EBITDA-basis
triangulation stays put** — moving it would orphan the "· leverage basis" half of its section title
and separate a decision-critical caveat from its substantiation. VERIFIED: a FACT-INVENTORY
baseline (1,030 labels across 11 committed dossiers) captured before the change and re-checked
after — **0 facts lost, 0 gained**; the only deltas are the intended renames. md re-rendered from
committed JSON (pure re-render: no LLM, no re-assembly, deterministic); frontend rebuilt; web twin
verified on the running preview (business-quality present, old name gone, rename live, appendix
positioning present, street-contrast live, insider no longer in the street). Two pins updated with
reasons rather than silenced (section-order pin, JS brief-strip pin). Gate: ruff + `mypy --strict`
clean · 1068 passed, re-run on the regenerated artifacts per the ARTIFACT-PASS RULE.
