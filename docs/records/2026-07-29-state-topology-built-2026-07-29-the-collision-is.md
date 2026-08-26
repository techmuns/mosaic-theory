---
id: 
status: shipped
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**STATE TOPOLOGY — BUILT 2026-07-29. THE COLLISION IS FIXED BY NAMING, NOT RENUMBERING; AND TWO OF
THE FOUR RECORDED MARKDOWN DEFECTS TURNED OUT NOT TO EXIST.**
**(a) THE TWO SERIES.** Both keep their numbers — renumbering would invalidate every reference in
the build records, the merged PR bodies and `docs/audits/`, a larger correctness risk than the
ambiguity itself. Instead each now sits under its own heading (**SERIES A — ENGINEERING /
AUDIT-REMEDIATION**, **SERIES B — ANALYST / OPERATOR**, which restarts at 13), with the collision
stated where a reader enters the queue and the convention recorded: conversational numbering is
ALWAYS series A.
**(b) PRONOUNS — all three fixed** (4381, 5291, 5859): the operator's and the auditor's are
unstated, so they/them.
**(c) THE ORPHAN `**` — ONE WAS REAL, ONE WAS MY CHECKER LYING.** Queue item 24's trailing `).**`
was genuine and is closed. §7 item 19's flagged marker is ``*** NO GATE — new exposure`` INSIDE A
CODE SPAN, where `**` is not markup — it renders correctly, verified against GitHub's API. The
naive counter was wrong, not the document.
**(d) THE INDENTED TABLES — CORRECTED 2026-07-29: NEITHER WAS REAL, AND #250's EXPLANATION WAS
WRONG. THE ERROR WAS MINE, IN THE MEASUREMENT.** #250 recorded that a table indented inside an
ORDERED list item does not render while one inside a BULLET does. **FALSIFIED** by constructing 10
cases and settling them against the API: EVERY indented case renders — ordered, bullet, nested,
1-digit, 2-digit, with or without a preceding blank line, at indents 2/3/4. The ONLY non-rendering
case is a table at indent 0 inside a list item, which is not what either instance was.
**WHAT ACTUALLY HAPPENED: I FED THE RENDERER A TRUNCATED WINDOW.** The failing sample started 9
lines BELOW its `26. ` list marker, so its 4-space indentation parsed as a top-level INDENTED CODE
BLOCK rather than as list-item continuation. Re-rendered from the marker: it produces a real
`<table>`. The document was correct the whole time; the sample was not.
**CONSEQUENCE, and it is a correction to shipped work:** #250 rewrote a CORRECT table as `·` lines
on the strength of a false negative. **The table is RESTORED here.** (#248's item-22 truth table was
converted on the same measurement error; its `·` lines read fine and are left, but the record no
longer claims they fixed a defect.) So of the four markdown defects recorded across #248/#250,
**ONE was real** — queue item 24's orphan — and three were artifacts of my own checkers and sampling.
**THE INDENTED-TABLE CHECK IS NOT NEEDED, which is a stronger answer than "not shippable".** There
is no defect class to guard: indented tables render. The gap #250 recorded as open is closed by
measurement rather than by code.

**(e) WHAT SHIPPED.** SHIPPED:
`test_state_and_engineering_docs_have_no_orphan_bold` — per LIST ITEM (a blank-line block puts §1's
1,223 markers in one bucket, where an orphan is neither detectable nor locatable), with CODE SPANS
STRIPPED FIRST so it cannot fire on correct content. Mutation-verified BOTH ways: one added `**`
reds it; a `***` in a code span does not. **NO indented-table check — because there is nothing to
check** (see (d)): every indented table renders. #250 recorded this as an open gap; it is closed by
measurement, not by code.
**THE PATTERN WORTH KEEPING — and it now cuts both ways.** Of the four recorded markdown defects,
**ONE was real**; three were artifacts of my own checkers and my own sampling. Three times the
renderer corrected a heuristic; the fourth time **the renderer itself was wrong because I truncated
the sample**. So the rule shipped to docs/engineering.md is the renderer-as-authority rule PLUS its
corollary: an authority fed the wrong context is not an authority.

**ADDED TO THAT SLOT 2026-07-28 (2) — INDENTED TABLES DO NOT RENDER, and it is the SAME shape as
the orphan-`**` class: a markdown defect invisible to the author and only visible to the reader.**
A markdown table INDENTED inside a list item is NOT parsed as a table by GitHub — it renders as a
wall of literal `|` pipes inside the paragraph. **Verified against GitHub's own markdown API, not
inferred from CommonMark** (the spec would also reject an unindented table interrupting a
paragraph, and GitHub renders THAT one fine — so the spec is not the authority here; the renderer
is). #248 introduced one, in queue item 22's caveat truth table, and it was rewritten as `·` lines.
A parity scan finds **TWO MORE, PRE-EXISTING on main** (the `| field | register |` table and the
`| check | honest worst | VITL | … |` table, both indent=4). Left standing — not #248's — but they
belong to the topology PR alongside the two orphan `**`. **The check ships with it** and covers both
classes: odd `**` count, and any delimiter row at indent > 0.

**ADDED TO THAT SLOT 2026-07-28 — THE ORPHAN-`**` CLASS, AND ITS MACHINE CHECK.** #244's first cut
left a dangling `(queued …).**` fragment inside item 26: an unbalanced bold that renders the rest
of the item as literal asterisks, the same class that broke §7's THEME #2 and needed its own
fix-PR. Caught by counting `**` per list item, not by reading. A parity scan over both files finds
**two more, PRE-EXISTING on main**: queue item 24 (a trailing `).**` after its origin clause) and
§7 item 19. Left standing here deliberately — they are not this PR's — but the topology PR is
STATE.md-structural and is where they belong. **It also ships the check** (INVARIANT RULE): a test
that flags any list item or paragraph whose `**` count is odd, so the next one reddens CI instead
of shipping. Three instances of one class, all caught by eye and one only after review, is the
argument for the machine.

**THE DRIFT GUARD COUPLES RENDER CHANGES TO FLEET-WIDE ARTIFACT COMMITS — named once, 2026-07-28
(operator), CORRECT BY DESIGN, no action.** `test_screening_context_reaches_every_committed_dossier
_e2e` renders live from committed JSON and compares to disk, so ANY render change turns all 11
committed `dossier.md` red until they are re-rendered. That is the guard working — it is what stops
the committed record drifting from the renderer, which is #221's lesson. The consequence worth
stating plainly: **the artifact pass is now ROUTINE on every render change, not an event.** 26a's
PR carried it as a separate commit (no code in the artifact commit, per the repo rule), and every
render PR after it must budget the same step.
