---
status: recorded
date: 2026-11-11
prs: [976]
supersedes:
superseded-by:
---

# The guidance reader (#976) on the panel: the check ended at $0, nothing drawn. `compare` refused ("reaches no page's request"), and a re-read of every cited release on the six panel pages moves no guide and no refusal note

**THE APPROVAL.** The operator, 2026-11-11, verbatim: **"go ahead with the correct steps as per
experts"**. The coordinator relayed it as the approval text **"go ahead with the correct steps as per
experts (#976 panel check, $35 cap)"**. No budget ledger was opened, since nothing reached a draw.

**THE $0 STEP (RUNBOOKS §n step 2).**
- `python -m vinci.evals compare --base origin/main --cand 0f8a02b8` (#976 after its re-sync onto
  `c2a4d743`): **REFUSED: 0f8a02b8 reaches no page's request**. All six panel pages are identical, with
  the system prompt equal.
- **That refusal alone is not the proof.** `compare` replays the committed layer, and a release-parser
  change reaches a request only at re-assembly. No `variants.py` transform re-reads guidance, so the
  re-read is the $0 replay below. The coordinator has passed the gap to the impact-check session.

**THE RE-READ.** Every EX-99.1 cited on the six panel pages was read offline from the local SEC
caches through main's parser (`c2a4d743`) and #976's (`0f8a02b8`):

| Page | Cited exhibits | Guides | Guides that move | Refusal notes that move | Other flags that move | New default-period flags |
|---|---|---|---|---|---|---|
| BURL | 6 | 10 | 0 | 0 | 0 | 1 |
| CNXC | 4 | 18 | 0 | 0 | 0 | 0 |
| LLY | 6 | 1 | 0 | 0 | 0 | 0 |
| MCK | 3 | 0 | 0 | 0 | 0 | 0 |
| ROST | 5 | 0 | 0 | 0 | 0 | 0 |
| SMPL | 6 | 21 | 0 | 0 | 0 | 13 |

**WHAT REACHES A REQUEST.**
- **A guide** reaches it through the mechanical lines built from it. None moves.
- **A guidance refusal note** reaches it through `mechanical.guidance_refusal_flags`. None moves.
- **The default-period flags** ("Guidance period not read") stay in each release's own `qa_flags`
  inside `primary_source`, which `synthesis.NOT_SENT` excludes. `primary_source.qa_flags` is built
  from fetch and parse failures only. So BURL's 1 and SMPL's 13 reach no request.
- **So no panel request moves at re-assembly,** and a paid run would compare identical requests on
  all six.

**OFF THE PANEL.** NFLX (3) and VITL (2) gain refusal notes for single-point guides, which reach their
requests at re-assembly. #976's record lists them.

**BOUNDARY.**
- **Pages:** the six panel pages, as committed at `c2a4d743`.
- **Exhibits:** their 30 cited EX-99.1s, read offline. None missed and none errored.
- **Unit:** one guide item, or one `qa_flags` line of one exhibit.
- **Date:** 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The check rests on the replay, not on the harness's own capture,
until a guidance re-read transform exists. *Falsifier:* a re-assembled panel page whose request
differs, between #976's parser and main's, in a guide line or a guidance caveat.
