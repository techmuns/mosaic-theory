---
id: 
status: recorded
date: 2026-07-27
prs: [227]
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

25. **THE BROAD TWIN-PARITY PIN — 2026-07-27.** #227 fixed ONE instance of a class: the screening
   anchor reached the web page and was silently absent from the markdown twin, so the committed
   `dossier.md` and the "Full dossier MD" download were short a decision value. Its four pins
   cover that section only — and a per-section pin covers exactly the bug already paid for.
   `test_every_assembled_field_reaches_both_dossier_renderers` drives the check from the DATA
   instead: harvest every key the 11 committed dossiers carry across `mechanical` + `synthesis` +
   `anchor` (44 today), and require that a field named by `vinci/dossier/render.py` is named by
   `frontend/views/shared/dossier.js` and vice versa. Adding an assembled field now reddens the
   suite until BOTH surfaces acknowledge it.
   **MEASURED BEFORE IT WAS WRITTEN.** Two designs were tried and discarded on their false-positive
   rate: heading-text matching read 33 of 46 md headings as "missing" (the surfaces name sections
   differently and build many titles dynamically), and a top-level-key check was too coarse to see
   inside `mechanical`, where the bug lived. The field-level check reads **0 one-sided out of 44**.
   **VERIFIED BY BREAKING IT** — dropped `catalyst_calendar` from the md twin (red), `peer_comps`
   from the web twin (red), and finally re-introduced #227's own field,
   `anchor_base_value_per_share`, missing from the md twin: **caught**.
   **SCOPE, recorded honestly:** a COVERAGE floor, not a semantics check — it proves a field is
   named on both sides, never that both render it correctly or in the same tier. Semantics stay
   with the per-section pins. Bare-token matching means a name surviving only in a comment would
   pass; accepted, because parsing two languages' access idioms is the brittleness that made the
   card-key pin give up on alias reads. Deliberate asymmetry is expressible via `_TWIN_EXEMPT`
   (empty today) so it lands as an argument in a diff, not a silent gap.
   **ALSO LANDED (#228, after a main catch-up merge):** the wording correction for #227 — four
   write-ups had said the gap meant "every PDF omitted it". Wrong: both PDF scopes are
   `window.print()` on the web page, which always rendered the anchor; only the markdown was
   short. Behaviour unchanged; the overstatement is corrected in place, not edited away.
