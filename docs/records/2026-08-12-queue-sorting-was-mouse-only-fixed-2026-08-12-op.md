---
id: 
status: shipped
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

### QUEUE SORTING WAS MOUSE-ONLY — FIXED (2026-08-12, operator-asked)

Surfaced by the operator's own inspector reporting the column header as **not keyboard-focusable**.
It was table-wide, not this column's: all 13 sortable headers were click handlers on bare `<th>`
elements with no `tabindex` and no button role, so the ranker **could not be sorted from the
keyboard at all** — and a `<th>` has no activation semantics either, so adding `tabindex` alone
would have produced a focusable element that still did nothing on Enter.

- **The control is now a real `<button>` inside a `<th>` carrying `aria-sort`** — the W3C
  sortable-column-header shape. A button brings focus, Enter/Space activation and "button"
  semantics natively, which is strictly more robust than re-implementing them with tabindex +
  keydown. `scope="col"` added; the ▲/▼ is `aria-hidden` because `aria-sort` already carries the
  same fact and a screen reader would otherwise read the glyph as text. CSS resets the button so
  this is a SEMANTICS change, not a visual one, plus a `:focus-visible` ring (mouse users see none).
- **Focus is restored after the re-render.** `renderHead()` replaces the whole row, destroying the
  button just activated — without this a keyboard sort drops the user to `<body>` and the next Tab
  restarts at the top of the page. Reachable but unusable is what makes "technically accessible"
  meaningless, so it is pinned (source-layer; focus is a live-DOM behaviour the node harness has no
  model for).
- **VERIFIED IN THE BROWSER:** 13 buttons, all `tabIndex 0`; Tab from the search box lands on the
  first header in two presses with a visible 2px focus ring; activating a header re-sorts, flips
  `aria-sort` `none → descending`, and leaves focus on that same header; exactly one column ever
  claims to be sorted.
- **ONE THING NOT PROVEN, stated rather than glossed:** the harness's synthesised Enter reaches the
  button (`keydown: ["Enter"]` observed) but Chrome does not derive the `click` from a CDP-injected
  key event (`click: 0`), so **native Enter/Space activation was not directly observed**. What was
  established instead: the element is a `<button type="button">`, and NOTHING on the page registers
  a keydown handler or calls `preventDefault` anywhere in the view, the app shell or `lib/ui.js`, so
  nothing suppresses the default activation. An explicit Enter handler was deliberately NOT added —
  it would double-fire alongside the native click in a real browser and toggle the sort straight
  back, which is a worse bug than the one being fixed.
- Four guards, each mutation-tested: reverting to a bare clickable `<th>`; dropping `aria-sort`;
  un-hiding the ▲/▼ from assistive tech; and removing the focus restore.
