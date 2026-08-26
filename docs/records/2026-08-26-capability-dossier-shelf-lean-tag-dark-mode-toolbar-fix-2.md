---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **DOSSIER-SHELF LEAN TAG + DARK-MODE TOOLBAR FIX (2026-07-20, feat/index-lean-tags; MERGED

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **WHAT IS SHOWN — the evidence LEAN, not the proposal.** The index card carries the
    synthesis's committed lean LABEL ("Mixed" / "Strongly bearish" / "Strongly bullish"). This is
    the same read the Brief already shows openly WITH its rationale; the machine's BUY/AVOID
    PROPOSAL remains sealed until the human logs (the 2026-07-13 pivot is untouched — no code
    path reveals `deriveProposal` earlier than before).
  - **TAG PRECEDENCE — the constitution in miniature (`cardTag`).** A LOGGED HUMAN VERDICT
    outranks the machine's lean: a decided name wears the coloured buy/avoid pill (the verdict OF
    RECORD — by then there is nothing left to anchor), an undecided name wears the neutral lean.
    **Colour on this shelf therefore means A HUMAN DECIDED, never that a model leaned.** Today
    VRRM alone reads a red AVOID beside ten muted leans. Pinned by
    `test_shelf_tag_prefers_the_logged_human_verdict` (inverting the dispatch would put a decision
    colour on an undecided name); `AVOID_TERMINAL → "AVOID"` is lossless and the pin asserts the
    two-verdict premise it depends on. Tags render INLINE on the ticker line (one-row cards).
  - **Rendered NEUTRAL by design, and pinned that way.** The lean maps 1:1 onto the proposal
    (`strongly-bearish → AVOID`), so the tag is ONE deterministic hop from a verdict. It uses no
    `.pill buy/avoid` vocabulary and no danger/live tint — a grid of directional COLOUR would let
    the eye triage the shelf before a fact is read. `test_lean_tag_is_label_only_and_never_
    directional` fails if colour or verdict vocabulary is ever introduced.
  - **⚠ EXTENDS THE RECORDED ANTI-ANCHORING RISK** (§the pivot's accepted risk) to a NEW surface:
    the lean now reaches the human BEFORE they open the dossier, where previously it appeared only
    beside its rationale. SAME FALSIFIER: if the override rate collapses toward ~0 or the human
    spread tracks the machine spread within noise, revisit — and this shelf tag is now the FIRST
    thing to remove, being the cheapest anchor to delete.
  - **No third lean parser.** build.py emits `synthesis.evidence_balance` VERBATIM into the
    dossier index (`reads`); the split stays with the ONE shared JS parser (`dossier.js
    splitLean`, mirroring `vinci/dossier/verdict.py`). A tombstone test fails the build if a
    lean regex ever appears in build.py. Absent/unparseable read → NO tag (never a fake "neutral").
  - **Dark-mode fix (operator-reported):** the dossier toolbar's inline styles set `background`
    but never `color`, so the UA's black `buttontext`/`fieldtext` leaked through — the "Open"
    label was invisible and the search box rendered stark white on the dark shelf. Both now carry
    `color:var(--ink)`/`background:var(--surface)`; measured contrast 7.19:1 in dark, 7.85:1 in
    light. Swept: these were the only two colour-less inline controls in the frontend.
  - Gate: ruff + `mypy --strict` clean; 705 passed (+3 pins). Build ×2 idempotent. Verified in the
    browser in BOTH themes: 11 cards tagged, card text is label-only ("AORT Mixed"), every tag
    resolves the muted ink in light and dark.
