---
id: 
status: shipped
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**TWO FINDINGS FROM THE 26a BUILD — (1) NOW QUEUED AS ITEM 32, (2) FIXED 2026-07-28.**
(1) **THE BROAD TWIN-PARITY PIN DOES NOT COVER TOP-LEVEL FIELDS.**
`test_every_assembled_field_reaches_both_dossier_renderers` harvests keys from `mechanical`,
`synthesis` and `anchor` only — so `assembled_at`, `llm_model`, `sector`, `exchange` and (without
26a's own pin) `extraction_version` are outside it. Measured: extending it to the 17 top-level keys
would red on exactly ONE, **`midcycle`** (named in `render.py`, absent from `dossier.js`). That one
is **LATENT, not live** — `midcycle` is `null` on all 11 committed dossiers (absent on MVST), so
nothing is missing from the web today; but a dossier that ever carried it would render a section in
the markdown that the web twin and both PDFs omit, which is #227's exact shape. 26a therefore
ships its OWN explicit pin rather than widening the general one around an undiagnosed field.
QUEUE: widen the pin to top-level keys, after deciding whether `midcycle` is web-renderable or a
declared `twin_exempt` entry.
(2) **`.claude/launch.json`'s `frontend` entry used a RELATIVE `--directory frontend`** — so it
served whichever checkout the server process started in, in practice the PRIMARY repo, which is
another session's working tree. The first preview of 26a rendered the primary checkout's CNXC
(`assembled_at` 2026-07-23) and showed NO stamp, which reads exactly like "the feature does not
work". **FIXED 2026-07-28 (operator: fix, don't report — "trusted, that's an hour debugging working
code; the reverse case is a broken render previewing as fine because it's another session's
tree").** It was the ONLY relative entry of ten; every other already names its tree absolutely.
**GUARDED** (INVARIANT RULE): `test_every_preview_server_serves_an_absolute_directory` scans
`.claude/launch.json` and reds on any `--directory` that is not absolute.
