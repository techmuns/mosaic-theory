---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier (2026-07-20, per the heading). The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **CITATION SYSTEM LIFTED TO lib/cites.js — THE THIRD NON-MODULARITY (2026-07-20,

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **ANSWER: nothing failed to propagate; it was NEVER shared.** `citeMark` / `withEndnotes` /
    `citePlaceholders` / `auditCitesInline` were ~25 PRIVATE lines inside `dossier.js` (which
    exports only `render` + `renderDossier`), so `uw-card.js` could not reach them. Its
    inline-only cites were DOCUMENTED and defensively correct — neither host that renders the card
    runs an endnote pass, so placeholders would have shown as literal `[?]` — but that was a
    workaround for a missing module, and it forced the inline form onto the MAIN BODY too.
    **Third instance of the same class** (after the label maps and the workflow-state vocab): one
    good implementation locked in one module ⇒ the next surface ships a lesser one.
  - **The convention is TWO-MODE, and only one of the three cites was actually wrong.** Main body
    → numbered endnotes; on-demand print-EXCLUDED `<details>` audit blocks → inline (an endnote
    there orphans an `[n]` in a printed Sources list, pointing at a marker the reader can't see).
    The card's `<details class="uw-inputs">` cites were therefore CORRECT; only the main-body Spot
    cite violated the rule.
  - **FIX (final form — the card OWNS its citations).** Machinery moved VERBATIM to
    `frontend/lib/cites.js`. The design then went through two iterations ON THE BRANCH:
    (1) a `cites` option on `uwCard` (default "inline"; the WERN host wrapped in
    `withEndnotes("U", …)`; the theme page kept inline) — REPLACED when the operator asked why the
    theme page's copy still showed the old layout: a knob a host can get wrong IS a rendering
    difference in waiting. (2) The knob is GONE — `uwCard` runs its OWN two scopes:
    `withEndnotes("U", body)` for the main body (its Sources list sits inside the card) and
    `withEndnotes("I", …)` INSIDE the Inputs `<details>` (marker + list share print fate —
    `details:not([open])` drops a collapsed block from the PDF, so an `[I n]` resolving into the
    card's outer list would orphan there). NO host runs a pass; the card renders identically on
    EVERY surface, current and future.
  - **GUARDS.** The pre-existing #9/#10 pin follows the machinery to the lib AND sweeps EVERY
    module that can import `citeMark`; #10 now states the REAL invariant (a citeMark inside a
    `<details>` is allowed IFF the block carries its own endnote scope) instead of the old blunt
    proxy (never inside `<details>`) — an operator-approved loosening. New pins: one home, ONE
    placeholder grammar frontend-wide, the card runs its own U scope + the Inputs block its own I
    scope, NO `cites` knob and no hand-rolled inline cite left in the card, and no host wraps the
    card in a pass of its own.
  - **Verified in the browser (all three surfaces, post-redesign)** — WERN: `[U1]` + Sources in
    the card, `[I1…I5]` + their list INSIDE the expanded `<details>`, exactly 2 Sources sections
    (U + I — no host double-wrap), 0 inline cites, 0 orphan `[?]`; THEME page now renders the
    SAME numbered card (`[U1]`, `[I1…I5]`, 0 orphans) — the operator's "why is the theme copy not
    updated?" is what forced iteration (2); VRRM per-tier numbering intact (Brief `[B1…]` 19
    sources). **The preview caught a real bug pre-commit**: the uw-card import silently no-op'd
    and the page threw "citeMark is not defined" — the PREVIEW RULE paid for itself.
  - **PROCESS DEFECT (recorded, mine):** a gate command piped pytest through `grep`, which
    discards the exit code, so a run reporting `1 failed` did not stop the commit. The commit was
    afterwards verified green in an ISOLATED clean checkout of HEAD (709 passed, exit 0) and the
    failure never reproduced in 4 further runs — cause unknown, NOT explained away. Gate commands
    must assert pytest's exit status, never a grepped summary line.
