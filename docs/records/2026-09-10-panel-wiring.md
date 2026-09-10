---
id:
status: open
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# Phase 6 — the emitter and the renderer: the panels are on the frontend

**Status:** built · preview run, awaiting operator approval (PREVIEW RULE)

## What this closes

Phases 2–4 built the spec, the gating rule, the declarations and the computations, and **nothing
consumed any of it**: `cli.py` still said "panel routing (planned)" and no frontend file mentioned a
panel. This is the consumer.

* **Emitter** — `vinci/panels_emit.py` writes structured panel rows into the monitor-day artifact;
  `vinci monitor` calls it.
* **Renderer** — `frontend/views/shared/panels.js`, reached at `#/monitor-panels/<TICKER>` from a
  new "Monitor panels" nav entry. `frontend/build.py` already mirrored `data/monitor/*.json`, so it
  needed no change — which matters, because that file may not import `vinci`.

## One renderer, not two

The first cut of `panels_render.py` emitted **HTML from Python**. The frontend is a JS SPA reading
committed JSON, so that would have been the same design drawn twice in two languages — guaranteed to
drift, and the drift would be invisible until the two disagreed in front of a reader. The file is now
`vinci/panels_payload.py` and produces **structured values only**; the JS is the sole renderer, and
the approved preview design moved into it.

That is the house rule doing its job: display formatting is never load-bearing, so the renderer can
change how a figure reads without the artifact changing what it says.

## The gating rule had to survive serialization

The one thing that could quietly undo three phases is a `not_in_set` panel arriving in the JSON as a
row with a falsy state — a tile waiting to be drawn, when the rule is that those never draw.

**A `not_in_set` panel emits NO ROW AT ALL.** It is absent from the block, not present-and-falsy.
Every row in `panels[]` is a tile that renders: `ready` or `refused`, nothing else. A reader who has
never seen this code can rely on that from the JSON alone, and the e2e test asserts it over the real
committed artifact.

A **READY row with no value is demoted to a loud refusal** that says the requirement check and the
payload builder disagree. An empty ready tile is indistinguishable from a panel that does not apply,
which is the one thing the rule forbids.

## Corpus result

118 renderable rows over 15 names on the committed 2026-08-11 snapshot. GOOGL renders 4 ready / 6
refused; SMPL 6 ready / 1 refused. Values check against source exactly — SMPL's call is the **open**
row ($11.33, 2026-08-04), attribution −4.15pp / −0.24pp / −3.91pp.

## Three things the build found

**1. The range band excludes today's mark, on 16 of 18 names.** `len(series) == n_closes + 1` and the
extra point is the current mark; `low`/`high`/`median`/`percentile` are struck over the historical
window without it. That is why SMPL's current 5.56x sits *below* its own stated 6.11x low — a real
state, not a data error. Drawn as one undifferentiated line it reads as a glitch, and the tempting
fix — widening the band — would silently restate the percentile the whole panel turns on. The payload
now carries `range_excludes_current`, the sparkline draws the current point dashed and separate, and
the label says "excluding today's mark".

**2. The stylesheet tokens I reached for did not exist.** `--card`, `--bad`, `--bad-bg`, `--good`,
`--warn-bg` are not defined in this app; the real ones are `--surface`, `--danger*`, `--pos-text`,
`--warn*`. Because CSS falls back silently, READY tiles were rendering with a **fully transparent
background** and the refusal colours were frozen to one hard-coded palette — so dark mode would have
shipped wrong and nothing would have errored. Now on the real tokens, verified computed in both
themes: ready `#fff` / `rgb(18,23,31)`, refused `rgb(251,236,235)` / `rgb(42,25,23)`, the
refused-vs-ready distinction holding in each.

**3. A refusal was hiding data it had.** `kills` refuses on every name (no record carries a measured
criterion), and the refusal replaced the criteria prose entirely — leaving the reader with *less*
than the terminal view already gives them. The refusal now lists the criteria beneath its badge:
the badge says the NUMBERS are missing, the list says what they would have been about.

## Verification

Real run, in-browser, both themes and both disclosure states.

* 118 rows emitted; **0 carry `not_in_set`**; every refusal carries a reason; every tile states what
  would change the call (10 tiles → 10 blocks on GOOGL).
* No `undefined` / `NaN` / `[object` in the rendered grid — **including with every `<details>`
  force-open**, which is the #176 failure mode (a renderer that printed `undefined` three times
  inside a collapsed tier, invisible to the preview that approved it).
* No inline `Source:` caption under any exhibit; provenance resolves to each tile's own Sources tier,
  which force-opens in print under the existing T1 rule (`.pn-prov` is not `ds-bulk`, checked).
* SMPL's criterion text contains `<= 0%`; it survives as text, escaped in HTML, with no stray tags.

**A test failed on its first run and was right to.** It scanned payloads for `<` to prove the artifact
carries no markup — and caught SMPL's "growth <= 0% YoY", a mathematical operator in legitimate prose.
The assertion is now tag-shaped. That is the **third** substring false positive in this build, after
`RPO` matching inside "Corporate" and `ROU` matching inside "Group": a bare substring scan over human
text is nearly always too eager.

## Artifact

`data/monitor/2026-08-11.json` was regenerated **through `write_snapshot`**, so its superseded-day
guard ran rather than being bypassed (2026-08-11 is the front of the book; nothing sits on top). The
block is additive apart from `measured` / `stale_tags` defaults being re-emitted on freshness rows —
no existing value changed. Committed separately from the code, per the rule against bundling a code
change into an artifact commit.

## Not built

Cohort panels emit with **no note probe**, so `commissioning` and `segment_economics` refuse naming
the absent probe: the monitor run is offline by contract, and a filing fetch there would let the
browser show a mark the repo cannot reproduce. Wiring a probe into an online path is its own
decision. `cost_of_borrowing` needs no filing and resolves normally.
