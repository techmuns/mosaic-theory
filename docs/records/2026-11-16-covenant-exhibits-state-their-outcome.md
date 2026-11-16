---
id:
status: shipped
date: 2026-11-16
prs: [1084]
supersedes:
superseded-by:
---

# Each located covenant exhibit's outcome is now a structured field: the E5 loop writes `capital_structure.covenant_exhibit_outcomes`, one entry per exhibit at the branch that decides it, and both renderers print each unextracted exhibit's own cause from it. A page without the field, which is every committed page until its next paid re-assembly, keeps #1073's neutral line byte for byte (STATE row 63)

**WHAT.**
- *The field.* `vinci/dossier/schemas.py` gains `CovenantExhibitOutcome`. It holds `accession`,
  `filename`, `family`, `outcome` and `declared_title`, the heading E5 read, or None.
  `CapitalStructure` gains `covenant_exhibit_outcomes:
  Sourced[list[CovenantExhibitOutcome]] | None`. The field is registered in `DROP_WHEN_NONE`, so a
  page without it writes no key.
- *The loop.* `covenant_extract.extract_covenant_terms` returns the outcomes as a fifth element.
  There is one per exhibit `_core_agreement_exhibits` targets, in its order, written at the branch
  that decides it. The seven values are the loop's own branches, read off the code; the brief's
  list matched them exactly:
  - `cost_bound`: past `_MAX_EXHIBITS`, so never fetched;
  - `fetch_failed`: no text came back;
  - `not_debt_agreement`: the heading is not a debt contract;
  - `too_large`: over `_MAX_EXHIBIT_CHARS`;
  - `llm_error`: the call raised `LlmError`;
  - `no_terms_returned`: the call returned no term rows. No flag has ever recorded this case,
    and the exhibit still spends one of the cost bound's calls, as before;
  - `extracted`: the call returned rows.

  Nothing located (no pointer rows, or pointers with no accession) returns None, as the term rows
  do.
- *Assembly.* `assemble_one` attaches the outcomes after `synthesize`, beside the term rows. It
  attaches them whether or not any exhibit gave rows.
- *The model never reads the field.* `synthesis.NOT_SENT` excludes it from the facts dump. The
  replay harness (`evals/capture_child.pre_synthesis_mech`) and the confirmation
  (`confirmation.layer_as_synthesized`) clear it, as they clear the term rows.
- *The $0 pre-spend check.* `prespend.LLM_WRITTEN` gains the field. The check forecasts it
  PRESENT wherever an exhibit is located, and ABSENT otherwise.
- *The render.* `render._unextracted_line` and `dossier.js` `unextractedLineHtml` name, for each
  located accession the term rows do not cite, its targeted file and its cause:

  > 3 located agreement exhibit(s) not extracted this run: 0001193125-14-313404 ·
  > d772516dex101.htm — not sent: past the cost bound on exhibits per page; 0001193125-22-200058 ·
  > d393601dex101.htm — not sent: past the cost bound on exhibits per page; 0001193125-26-116001 ·
  > burl-ex10_39.htm — refused: not a debt agreement (its head declares no agreement)

  - A refusal names the heading E5 read, where it read one: NCNO's "(it declares itself “OFFICE
    LEASE”)". Where E5 read none, both readings print: "refused: no agreement title was read
    from its head; it was located as <family>", the pointer's family verbatim, or the first
    clause alone where the family is blank. The first draft said "(its head declares no
    agreement)", which the independent review showed false: VRRM's `vrrm-ex10_1.htm` heads
    itself "Amendment No. 4 to REVOLVING CREDIT Agreement".
  - An accession the field holds no outcome for reads "no outcome recorded". Neither renderer
    falls back to a QA-flag string.
  - With the field absent, both print #1073's neutral line. On the web that is the same bytes,
    the apostrophe unescaped as before.
  - *Where no exhibit gave term rows* (#1084 independent review, round 1). Both renderers used
    to print the stored covenant digest there, whatever the field held. LLY, ORKA, TECX and VITL
    each have one located exhibit, which E5 refused before any model call. Their digest reads
    "extraction failed: no covenant terms extracted from located exhibits", which is false for
    each. With the field, that path now prints the same line, naming each located exhibit's
    cause. Without the field, the digest prints as before.
- *Vintage.* `2026-11-16.covenant-exhibits-state-their-outcome`, with `assemble.py`,
  `covenant_extract.py`, `schemas.py` and `synthesis.py` re-pinned to it.

**WHY.** #1073 (`2026-11-14-covenant-unextracted-line-states-no-cause.md`) took the false cause
off the line, because no structured field recorded why an exhibit went unextracted: only `(E5)`
QA-flag strings did, and a parser may not read them. That record specified this field. Here is
one more reason a string is not enough, met while checking this PR. WLK's cost-bound flag reads
"Revolving Credit Facility·dex101.htm", and four of WLK's located accessions target a file named
`dex101.htm`. Three were extracted and one was past the bound, and the flag cannot say which.
The field names the accession.

*The synthesis prompt.* A new `None` field on `CapitalStructure` would have added
`"covenant_exhibit_outcomes": null` to every synthesis request. Measured on NFLX's capture, it is
one added line, against HEAD's code in a child process
(`test_capture_at_a_ref_runs_that_refs_code_and_matches_in_process` caught it). Row 53 measures
any prompt change on the panel first, so `NOT_SENT` keeps the request byte-identical. This
follows the precedent of `concentration.customers_listed`.

**HOW VERIFIED.**
- *Pins* (`tests/test_covenant_exhibit_outcomes.py`, 28 nodes):
  - *The loop.* One run of the real loop over BURL's committed pointer rows, stubbed only at
    fetch and model, drives each of the seven branches once. Each exhibit's outcome is its
    branch, with the pointer's family and the heading read.
  - *Located equals outcomes.* The outcomes, as a list, equal the targets: on that run, and over
    every committed page with pointer rows. A no-rows answer is `no_terms_returned`, never
    `extracted`. Nothing located writes no field.
  - *Assembly and the $0 check.* `assemble_one` attaches the field after `synthesize` (AST).
    The serializer writes it only when set. Both synthesis-input rebuilds clear it. The
    pre-spend forecast is PRESENT or ABSENT as above.
  - *The render, end to end on frozen JSON.* EPAM, NCNO, AMZN and BURL, through `render_markdown`
    and the production `renderDossier` in node: each unextracted accession reads its own cause,
    and the web line equals the Markdown's. The real loop's all-branch JSON puts all six
    non-extracted causes on both renderers. An accession the field omits reads "no outcome
    recorded". Without the field, the line is the neutral line, exactly.
  - *Code-review round 0.* Two exhibits under one accession each print that accession. The two
    label tables, Python and JS, hold exactly the schema's seven kinds.
  - *Independent review, round 1.*
    - TECX's committed page with its real-loop outcome (a frozen fixture, agreeing with its
      committed flag) prints the line on both renderers, not its stored digest.
    - The same page without the field prints the digest as before.
    - The field is out of the synthesis facts dump (`NOT_SENT`), on a page with it and one
      without. Removing that entry reds the pin, which before this nothing held.
    - The untitled refusal states both readings, end to end on VRRM's real outcome for
      `0000950170-25-072679 · vrrm-ex10_1.htm`, in VRRM's frozen block. Another accession's
      extracted exhibit has the same filename there. With an empty or blank family, the first
      clause prints alone. Both renderers give the same line, and the new constant is pinned on
      both.
- *Fail first.* Run with base code and head's `schemas.py` (so the file imports), 22 of the 28
  nodes fail. The 6 that pass are the precondition, the 4 neutral-line pins and the no-rows
  digest pin, which pin today's behaviour. A mutation that treats an absent field as an empty list reds those 4, and 11 of
  #1073's 15 nodes. #1073's other 4 nodes are preconditions, which read no renderer.
- *Frozen fixtures, written through the real loop.* `tests/fixtures/covenant_exhibit_outcomes/`
  holds the loop's output over the four pages:
  - each exhibit read from the EDGAR cache, cache only (a miss raises; nothing was fetched);
  - the model stubbed from the committed page's own term rows, so no model call.

  Every outcome agrees with that page's committed `(E5)` flags and term rows. The fixture README
  says how they were made.
- *Corpus run of the same probe:*
  - Over all 24 committed pages with pointer rows, it agrees with the committed record on 83 of
    91 located exhibits. Of the other 8, 5 are cache misses (MCK 4, WERN 1). The probe reads
    them as `fetch_failed`, which a paid build with network would not. The other 3 are FUBO's.
    Its 2026-08-18 page predates the identify-or-refuse gate, so today's code refuses what that
    build extracted.
  - On the 17 pages that print the line, it names 30 accessions: 23 `not_debt_agreement` and 7
    `cost_bound`, each agreeing with the committed flags.
- *Committed pages do not move.* All 26 committed pages went through the no-op refresh path
  (`refresh.refresh_fleet`), which re-renders each `dossier.md` and the frontend mirror. It
  reported 26 unchanged, 0 moved and 0 refused, and `git status` showed no change under `data/`
  or `frontend/`. Each committed `dossier.json` rendered through base and head `dossier.js` in
  node gave byte-identical HTML on 26 of 26.
- *Preview (PREVIEW rule).* Six real pages with the probe's outcomes attached, BURL, NFLX, NCNO,
  AMZN, WLK and EPAM, plus the all-branch BURL. Each was shot collapsed (the on-demand tier shows
  its summary only, before and after alike) and force-open. BURL was also printed through the
  "Full dossier" scope (`ds-print-full`, the print CSS opening every `<details>`): 26 pages both
  sides, the line on page 24, only its words changed. The images are in the coordinator's notes
  folder, not in the repo. **Approved 2026-11-16** by the operator, relayed by the coordinator:
  "approve the covenant wording", covering the seven-row wording table in #1084's body as shown.
  The `(E5)` backfill stays unbuilt.
  - *Round 1.* The independent review found the untitled refusal's label false. The operator
    ruled on 2026-11-16: "State both readings (Recommended)". The review also asked for the
    no-rows path. The preview adds LLY, ORKA, TECX and VITL, and VRRM's new line, each collapsed
    and force-open. That preview is with the operator.

  The wording, as approved and then ruled:

  | outcome | printed |
  |---|---|
  | `cost_bound` | not sent: past the cost bound on exhibits per page |
  | `fetch_failed` | could not be fetched |
  | `not_debt_agreement`, a title read | refused: not a debt agreement (it declares itself “TITLE”) |
  | `not_debt_agreement`, no title read | refused: no agreement title was read from its head; it was located as FAMILY (the first clause alone with no family) |
  | `too_large` | too large for single-pass extraction; extract by hand |
  | `llm_error` | the extraction call failed (LLM error) |
  | `no_terms_returned` | read, and the model returned no terms |
  | (no outcome for an accession) | no outcome recorded |

**BOUNDARY.**
- Every corpus count is at main `b64be6f1` (2026-11-16), over the 26 committed
  `data/dossiers/*/dossier.json`.
- 24 of those pages have pointer rows, with 91 located exhibits: one targeted exhibit per located
  pointer accession, none shared.
- 17 pages print the line, naming 30 accessions.
- The probe's 91 outcomes are 49 `extracted`, 30 `not_debt_agreement`, 7 `cost_bound` and 5
  `fetch_failed`, all 5 of them cache misses.
- The cache is the operator's EDGAR cache at `data/cache/sec` in the primary checkout, read on
  2026-11-16.
- Fail-first counts are over the 28 nodes of the new file and the 15 of
  `tests/test_covenant_unextracted_reason.py`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *No committed page carries the field.* Each gains it at its next paid re-assembly, with no
  separate spend. Until then the 17 pages that print the line keep the neutral one. LLY, ORKA,
  TECX and VITL keep their stored digest, whose "extraction failed" is false for each. A $0
  backfill from the `(E5)` strings
  was not built, because parsers do not read QA flags. WLK's filename-only cost-bound flags show
  the strings cannot always be mapped back to an accession.
- *The digest the synthesis reads is unchanged.* On a page whose exhibits gave no term rows,
  `assemble.covenant_fail_reason` still writes "no covenant terms extracted from located
  exhibits" into the digest, and the synthesis reads that digest. Changing it would change the
  synthesis prompt, which row 53 measures on the panel first, so it is not changed here. TECX's
  committed synthesis repeats "(extraction failed)" in its own prose. The page no longer prints
  the digest once it carries the field, but that prose stays until the synthesis is fed a true
  cause.
- *Found, not fixed: E5 misreads some debt headings.* `agreement_title` returns None on real
  debt-contract heads, so E5 refuses them as "no agreement at all":
  - VRRM's `0000950170-25-072679 · vrrm-ex10_1.htm`, whose head reads "Amendment No. 4 to
    REVOLVING CREDIT Agreement" (checked on the cached text by the independent review);
  - CNXC's third and fourth amendments to a receivables financing agreement.

  On the 17 printed lines, 17 of the 23 refusals carry no heading read. This recall defect in
  the E5 gate is its own PR, after #1084.
- *The confirmation reuse key moves.* `confirmation.inputs_sha256` hashes the layer's full
  dump, so on every page it now hashes one more `null` key. No confirmation record
  (`data/snapshots/proposal_confirmations.jsonl`) exists in either checkout (checked 2026-11-16),
  so no recorded confirmation loses its reuse.
- *Falsifier.* A re-assembled page whose line names a cause its `covenant_exhibit_outcomes` does
  not hold. Or a page with the field on which a located exhibit has no outcome:
  `test_every_committed_page_gets_one_outcome_per_located_exhibit` re-derives this over the
  committed pointer rows.
