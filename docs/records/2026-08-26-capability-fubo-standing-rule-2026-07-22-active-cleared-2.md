---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier (2026-07-22, per the heading). The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **FUBO — STANDING RULE (2026-07-22). ~~ACTIVE~~ → CLEARED 2026-08-13 (operator ruling).** No

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - `share-count` — `shares_out` **30,200,000** from the CIQ bridge (`Comparable Analysis→Financial
    Data`), and 30.2M × $9.70 = **$292.9M** against a stated cap of **$293.0M**, 0.03% apart. That
    was the 11.1x error the seal existed for. Corroborated independently: the freshness suite now
    reports **no name fails on share basis**, and its own message calls that "genuinely the goal".
  - `caveat-text-pre-fix` — the P/E caveat asserting a normalized/adjusted denominator is gone.
  - `agreement-bug` — `13.1x rest on` appears nowhere in the page BODY. **Checked with the banner's
    own blockquote stripped**: a first pass matched the marker QUOTING ITSELF, which is the seal's
    text and not the page's — a check that would have "confirmed" a defect the page no longer has.
  - `pre-combination-entity` — Hulu, Newco, Class B, reverse split and noncontrolling interest are
    all present. The page describes the post-combination issuer.
  - `g3-never-valued` was a READING CAUTION ("FUBO's admission is not a valuation judgment"), not a
    known-false figure, and retired with the rest.
  **THE MECHANISM SURVIVES THE INSTANCE.** `known_wrong.json` is general infrastructure, so
  `tests/test_known_wrong_marker.py` was REWRITTEN rather than deleted: it now exercises the sidecar
  on a TEMPORARY marker (banner renders, leads the page, and a corrupt marker still fails loud per
  #308) and adds a roster pin asserting **no** record is sealed — so the next seal has to be
  declared here with its evidence instead of appearing silently. The retired sidecar's text is
  preserved in this entry and in git history.
