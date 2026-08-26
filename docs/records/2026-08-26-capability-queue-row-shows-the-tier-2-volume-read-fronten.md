---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **Queue row shows the Tier-2 volume read** (`frontend/views/edge2/ranker.js`, PR #420) — `Score =

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **The label is rendered VERBATIM and the sort key is the structured `volumeOverlay`** — the
    display string is never re-parsed for its multiple. Consequence, accepted: within a band the
    order is arbitrary, because the overlay is a 4-step function. The clean fix is for the snapshot
    to emit `volume_spike` as a structured field beside the label; **not done here — the extractor
    boundary is out of this PR's scope, recorded in §5 as an operator to-do.**
  - **A 13th column overran the content area by 13px on a 1280px laptop** (`table.data th` is
    globally `white-space:nowrap`, so the table cannot shrink below its headers — no cell styling
    fixes it). Wrapped in the `overflow-x:auto` container `uw-card.js`/`dossier.js` already use for
    wide tables; measured 13px of page scroll before, 0 after, with the wrapper scrolling instead.
    Pinned — the next column added here cannot silently re-break the page.
