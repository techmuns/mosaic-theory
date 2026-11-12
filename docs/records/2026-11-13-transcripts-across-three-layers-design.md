---
id: 2026-11-13-transcripts-across-three-layers-design
status: open
date: 2026-11-13
prs: []
supersedes:
superseded-by:
---

# Transcripts across the three layers: the raw calls stay private, the wiki gets a code-built Q&A index and transcript facts in the fact layer, and the intelligence layer gets a per-exchange summary checked against both. A design, not built (operator: "go ahead", 2026-11-13)

**WHAT.** This is a design for after fix request 2. Nothing in it is built.

**The operator's goal, verbatim (2026-11-13):** "a self-improving setup with raw data, deterministic wiki, and intelligence layer".

**What the operator needs from a call, verbatim:** "We don't need transcript word to work, we need the synthesis of each question & answrr given to the question or the overall transcript gist / key items."

**How the operator's three terms map onto this repo.** None of them appears in the repo's docs. The searches were "deterministic wiki", "wiki", "intelligence layer", "self-improving", "raw data layer", "three layers" and "knowledge base", over `docs/`, `STATE.md`, `CLAUDE.md` and `vinci/`, plus `git log --grep` on main `047f4c6b`. So this record maps them:

| Layer | What it is in this repo |
|---|---|
| **Raw data** | The licensed CIQ exports on the operator's Drive, the SEC and Polygon originals kept write-once by sha256 in R2, and the operator's private evidence spool. |
| **Deterministic wiki** | Code-built facts, each with its `source_ref`: the fact layer (`vinci/facts`, point-in-time) and the code-built half of each page's `dossier.json`. |
| **Intelligence** | The synthesis (an LLM), then the machine proposal (`vinci/dossier/verdict.py`, plain code), then the human verdict of record. |

**The design, one layer at a time:**

1. **Raw: the calls stay private.**
   - The full transcripts stay in the CIQ folder and in the evidence spool, which the ingest Mac uploads to the private bucket.
   - A call is addressed by its file's sha256.
   - A call's facts are knowable from the call's date, never from a period end, because CIQ is not point-in-time (CLAUDE.md, PUBLISHED DATA).
2. **Wiki: code only. No LLM output enters it.**
   - **(a) A Q&A index per call.** Each exchange holds:
     - the question's paragraphs and the answer's paragraphs, as paragraph ranges;
     - the asker and the asker's firm, and the answerer and the answerer's title, all from CIQ's speaker blocks (`vinci/dossier/driver_extract.py::_speaker`);
     - the figures and guidance numbers code reads from those paragraphs (`driver_extract.check_fact`, the same reader the driver rows use);
     - the hashes.

     The index publishes no transcript words.
   - **(b) Transcript facts join the fact layer.** Today they live only inside each page's `dossier.json`. Each would become a row carrying its `source_ref` (the file's sha256 and the paragraph) and its knowable date, so every page and the screen read one copy.
3. **Intelligence: a summary in our own words, for each exchange and for the call.**
   - Each exchange gets a summary, and the call gets a list of its key items: guidance changes, new disclosures, and shifts in tone.
   - Each claim cites an exchange's locator.
   - Every figure in a claim is checked against the wiki by the figure trace (#1023; #1040 in review).
   - The 12-word rule is held at build by #1036's guard. It catches a "summary" that is really a near-copy, which is the model's failure, not ours: LLY's and VITL's syntheses copied 14 and 13 words.
   - Each summary records the model and the prompt that wrote it, so it can be rebuilt raw → wiki → intelligence.
   - A summary is never an input to the wiki.
4. **Self-improving, inside the guardrails: measured evals only, never forward returns** (CLAUDE.md, "Never tune on forward returns"). The transcript layer gets deterministic rates, each stated with its boundary:
   - the share of summary figures that trace to the wiki;
   - the guard's hits;
   - exchanges summarised over exchanges indexed.

   A prompt change ships only after the pre-registered panel check (STATE §5.0 row 53).
5. **The 12-word cap stays** (CLAUDE.md, Security & secrets). It limits only what is published. The model reads the raw words at build time, inside the synthesis request, which is never committed.

**WHY.**
- **Why the wiki stays code-only.** An LLM summary written into the wiki would make the wiki non-deterministic, and every layer above would then build on unchecked text. Keeping the summary in the intelligence layer, cited and figure-checked, keeps the line CLAUDE.md draws: the machine assembles and cites, and the LLM never free-concludes.
- **Why transcript facts belong in the fact layer.** It is the one point-in-time copy every page reads (STATE row 44). Facts held only in each page's JSON are copies that can drift.
- **What expert tools do.** AlphaSense's Smart Summaries and FactSet's Transcript Assistant summarise each call (highlights, analyst questions, guidance, tone), and each summary links back to the passage, inside the licensed product: <https://help.alpha-sense.com/en/articles/7238834-get-instant-insights-and-save-time-with-smart-summaries>, <https://www.nasdaq.com/press-release/factset-releases-transcript-assistant-a-game-changing-ai-tool-for-earnings-call>.
- **What the law says.** It sets no word count that is safe. Fair use is a four-factor test, and the vendor's licence can restrict copying regardless (*Swatch v. Bloomberg*, 2d Cir. 2014, <https://www.copyright.gov/fair-use/summaries/swatchgrp-bloomberg-2dcir2014.pdf>). So the cap is a rule this repo chose; the law does not supply the number.
- **The cap's origin, corrected for the record.** The 2026-11-04 licence ruling, verbatim, reads *"our licence covers publishing CIQ-derived facts and Polygon & Tiingo prices"*. The carve-out for transcript text was that record's own choice (`docs/records/2026-11-04-licence-covers-publishing-ciq-derived-facts-and-prices.md`, line 29). On 2026-11-13 the operator reviewed this design, which keeps the cap, and approved it.

**HOW VERIFIED.** Nothing is built, so this section checks the current state the design starts from. All of it was measured at main `047f4c6b`:
- **1,042 transcript driver rows on 25 of 27 pages.** These are rows with `tier == "llm-fenced"` in `data/dossiers/*/dossier.json`. Each carries `figures`, `value_num`, `value_status` and a `locator` naming its `call`, `paragraph`, `speaker`, `transcript_sha256`, `quote_sha256` and `value_sha256`, and none carries its words.
- **No transcript reader in the fact layer.** `grep -i transcript` finds nothing under `vinci/facts/`, and 0 matches in the three committed manifests under `data/facts/manifests/`.
- **Speaker blocks are already read.** `driver_extract._speaker` reads CIQ's two-line speaker blocks (a name, then a title).

**VERIFY-AT-BUILD:**
- whether every committed call marks its Q&A section and the operator's turns well enough to pair its exchanges by code alone;
- the 6 calls that were offloaded on Drive at the 2026-11-12 audit.

**BOUNDARY.** "1,042 rows on 25 of 27 pages":
- **Population:** the committed pages, `data/dossiers/*/dossier.json`, at main `047f4c6b`.
- **Filter:** rows in `mechanical.operating_drivers.rows` with `tier == "llm-fenced"`.
- **Unit:** rows.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The order of work: after fix request 2.**
  - The wiki's Q&A index is $0.
  - The fact-layer half needs STATE row 44's slice-4 ruling first: CIQ-derived data in the store, where `upload_refusal` admits `edgar` only today.
  - The summary half changes the synthesis prompt, so it needs a paid panel check under row 53 with an operator cap.
  - Showing the summaries on the page is a render change, so it needs a preview first (CLAUDE.md, PREVIEW RULE).
- **FALSIFIER for the wiki half:** if code cannot pair a call's exchanges from its speaker blocks and section marks, on the committed calls, then the Q&A index is not deterministic. The design then changes before anything is built, and it is never patched with an LLM pairing.
