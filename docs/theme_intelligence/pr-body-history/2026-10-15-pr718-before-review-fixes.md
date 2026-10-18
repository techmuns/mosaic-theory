Operator, 2026-10-15, on the demo enrichment of J.P. Morgan's "Software Shock": "how do you know if Atlassian (TEAM), Twilio (TWLO) will be hurt or benefited?" Then: "do both options as one PR". The full account is in `docs/records/2026-10-15-theme-intelligence-enrichment-condition-and-basis.md`.

**This changes a rendered surface (the thesis page's "Companies the thesis implies" box, the card and its print), so the preview rule applies: preview below; stopping for approval.**

## What changes

**1. The condition.**
- Each proposal records the label of the card step it rests on.
- A step that is not a fact (the source's opinion, a forecast, our inference) makes the direction a condition. Such a proposal is shown under **"Exposed — the direction holds only if its step does"** as *"exposed — would be hurt IF this holds: “<the step's words>” (source opinion)"*. It never appears under "Could be hurt".
- Only a measured or externally verified step keeps "Could benefit / Could be hurt".
- The same reading appears on the thesis page, the card, its print and the markdown.
- Sets stored earlier read their step's label from the card version they rest on, and it is never guessed.

**2. The checkable basis.**
- The model must now state how the company earns from the exposed line, as `revenue_model` (one of eight values: subscription, usage-based, transaction fees, licences, product sales, advertising, services, other), plus the line itself as `revenue_line`. The prompt version is `ti-enrich-2`.
- The stated model is checked against the company's own latest annual report (10-K / 20-F / 40-F) filed on or before the as-of, read through the same SEC resolver and cache.
- The check reads only the filing's own revenue-source sentences ("We derive our revenues from …"). The result is IN_FILING, FILING_NAMES_OTHER, NOT_DESCRIBED or UNCHECKED, and the note lists every other way of earning the sentence names.
- The filing's sentence is shown on demand on the page and printed on the card.
- A registrant the identity check refused is never read.

**A design that was measured and refused:** searching the whole 10-K for each model's words. Across the 13 real filings of the demo's first proposals it "confirmed" nearly everything:
- Adobe matched 5 of 7 models;
- Salesforce's "per seat" hit was an attrition sentence.

The revenue-source sentence anchor found the filing's own statement for 10 of the 13 (none for AMD, Broadcom or Vertiv).

**Does this select on form?** The basis check does: it reads a disclosure. So NOT_DESCRIBED is about the filing's words, never the business. It removes, ranks and decides nothing, and no priority rule reads enrichment.

## Preview (real demo run, J.P. Morgan "Software Shock", as of 2026-02-09)

The thesis page box, as served (filing quotes collapsed):

![thesis page — as served](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-enrichment-basis/docs/theme_intelligence/enrichment-basis-2026-10-15/screenshots/thesis-hypotheses.png?raw=true)

The same box with "What its 10-K says" opened:

![thesis page — opened](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-enrichment-basis/docs/theme_intelligence/enrichment-basis-2026-10-15/screenshots/thesis-hypotheses-open.png?raw=true)

The card's enrichment section in its print state (the audit tier revealed):

![card — print](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence-enrichment-basis/docs/theme_intelligence/enrichment-basis-2026-10-15/screenshots/card-print-enrichment.png?raw=true)

## Real-run verification

The demo registry: one paid enrichment of 3 theses ($0.1195), then replays from the cache at $0. 16 proposals:
- **All 16 rest on a step that is not a fact** (10 model inference, 4 source opinion, 2 forecast), so all are conditions.
- **13 are IN_FILING.** Twilio's basis is usage-based, and its 10-K says *"Our revenue is primarily derived from usage-based fees …"*. That now sits beside "would be hurt IF agentic AI threatens SaaS domains (source opinion)". Intuit is IN_FILING for subscription "— and also transaction fees".
- **3 are NOT_DESCRIBED** (AMD, Broadcom, Micron).

Stored data: 109 distinct proposals, all in the pilot registry.
- 107 rest on a step that is not a fact (61 source opinion, 28 model inference, 18 forecast); 2 on a measured observation.
- **So the published desk changes when next published:** 107 of 109 proposals become conditions.
- Stored sets show no basis until enriched again, which is a paid call per thesis.

The real run caught a bug in this change before commit. The stated model was held in a variable named `model`, which overwrote the LLM model's name, so the set recorded "usage_based" as its model and the cost as UNKNOWN. It was renamed and pinned.

Checks:
- Pins: `tests/test_theme_intelligence_enrichment_basis.py`, 13 tests, with filing sentences verbatim from the real 10-Ks named in the file. The module cannot import on main, so all 13 fail there.
- One existing pin changed its words on purpose: Amazon rests on an inference step and is now a condition.
- Mutants: 20 of 20 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.
- Offline suite (`pytest -m "not network"`): **5,378 passed, 513 skipped, 37 deselected**. Record and STATE lints: 720 passed.

This branch is from main and is independent of #715, #716 and #717. All four edit STATE row 32 item (8), so the later merges resolve that one line.

## Disposition

| Item | Status | Note |
|---|---|---|
| 1. The condition (step label, "exposed … IF", never a bare direction on a non-fact step) | SHIPPED | all surfaces; older sets read the label from their card |
| 2. The checkable basis (stated revenue model, checked in the company's own annual report) | SHIPPED | revenue-source sentences only; whole-filing search measured and refused |
| Preview | SHIPPED | three states above; awaiting approval |
| Re-enriching the pilot so stored proposals carry a basis | SKIPPED | a paid call per thesis — the operator's call |

Accepted, stated in the record:
- The model vocabulary is ours, so other wording reads NOT_DESCRIBED.
- "Names" is not "mainly", so the note lists the other models a sentence names.
- Each proposal's first read costs one annual-report download, cached after that.
- `filing_text` duplicates the graph track's `html_to_text`, because of the package isolation rule.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

