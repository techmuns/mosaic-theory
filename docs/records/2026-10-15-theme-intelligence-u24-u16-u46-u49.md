---
id: 2026-10-15-theme-intelligence-u24-u16-u46-u49
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — four verified review leads fixed: U24, U16, U46, U49

**WHAT.** Operator, 2026-10-15: "fix U24, U16, U46, U49" — leads confirmed in
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`.

| Lead | Defect | Fix |
|---|---|---|
| U24 | A page with NO body (an empty JavaScript shell, a consent wall) took its version id from its content hash; two such pages share one, so the second article's version collided — StoreIntegrityError, the whole scan FAILED, and every resume failed again. | A body-less page's version id is scoped to its own article (`pipeline.py`); a page with a body keeps its content id, and a copy at another URL is still DUPLICATE_CONTENT. |
| U16 | Time windows: "since May 2026" read as May alone and dated its end (historical); "next four quarters" as 368 days, past the 366-day near-term bound; "$2050 per ounce" as the year 2050; "Q1 FY27" as calendar 2027, with no note; "next N months" / "within two quarters" not read. | "Since X" runs from X (mid = 1 July, late = 1 October, the start of = 1 January) to the SOURCE'S date — never when an end follows ("since 2019 to 2023" is that range). N quarters are N fourths of a year. A four-digit number after a currency sign or before a unit is an amount. A fiscal QUARTER is not placed (its calendar quarter depends on the issuer), and says so; a fiscal year keeps its "approximate" calendar reading. "Next/within N months" and "within N quarters" are read. |
| U46 | Pharma had four segments; a thesis on immunology, vaccines or Lp(a) named none and took the node's BARE key — the key the pilot's in-vivo gene-editing thesis held — so the next such article would have updated it silently. | Four segments added (`taxonomy.toml`): genetic medicine, immunology, vaccines, cardiovascular — terms by face validity, from the lead's shapes. A thesis keyed before its segment existed is FOUND under the bare key and re-keyed (`KEY_CORRECTED`), never duplicated under the new one. An unsegmented hypothesis that updates an unsegmented thesis it shares no evidence with is flagged `UNSEGMENTED_KEY` — the next uncovered therapy area is said, not silent. |
| U49 | The completeness figure reader missed grid and gas units and CUT a decimal before an unknown unit ("707.5GVA" read as 707). | The number is read whole (possessive): a figure with an unknown unit is missed, never cut. Units added from the real corpus: kV, kVA/MVA/GVA, bcf/d (mmcf/d, bcfd), bln/mln/trn, ppt, g/kWh. |

**WHY.** U24 fails a whole weekly scan on one pair of pages; U16 and U49 read real data wrong; U46
is one article away from merging two theses.

**HOW VERIFIED.**
- **U24, real pages:** the two cached BofA pages that parse to no body, processed one after the
  other into a scratch registry — main (fcef226a): the second RAISES `StoreIntegrityError … AV-e3b0c44298fc1c14`;
  this branch: both NO_BODY, `AV-84f6ccf1b356fe0c` and `AV-07ebcebfcdeccf8d`.
- **U16, every stored claim** (2,203 distinct, 147 registries; as of 2026-10-14, each against its
  article's publication date): **18 change** — 16 "since X" observations historical → current, 2
  undated → straddling ("next 18 months").
- **U49, every real article text** (38 distinct versions): 2,906 → 2,938 ledger figures — 44 read
  that were missed or cut (2,358.5, 707.5, 110 kV, 7.5 bcf/d, 1.3 ppt, 0.10 g/kWh), the 12 cut
  versions (2,358, 707, 1, 0) gone.
- **U46, every stored pharma thesis** (4): only the gene-editing thesis changes segment ("" →
  genetic medicine, re-keyed when an article next reaches it); no real immunology, vaccine or
  Lp(a) hypothesis exists yet — the leads' shapes were constructed.
- **A $0 reassess of a copy of the pilot, main against this branch: ONE action changes** —
  TH-DEE87FCF51 (in-vivo gene editing) **SKIP → WATCH**. One of its opinions names "next 18
  months", which main could not read; 12 of those 18 months fall inside the next four quarters,
  and by the existing rule a window MOSTLY inside them is "straddling" — not longer-term only — so
  SKIP-3 ("longer-term only") no longer holds. No other thesis moves. The pilot registry's checksum
  is unchanged.
- **Pins:** `tests/test_theme_intelligence_u_leads_batch1.py`, 31 tests (each fix with its
  negative); against main, 25 fail and the 6 that pass are controls of what main already gets
  right (a body's content id, a past forecast window, a far year, a quarter label, a closed
  "since … to …" range, labels that are not figures). One existing test
  (`test_theme_intelligence_verification_quality.py`) pinned the cut figure "2,358" from
  "2,358.5GVA"; it now reads the whole figure.
- **Mutants: 19 of 19 killed.** Two survived the first pass — the end-guard on "since" and the
  mid-year start — and got pins that see them.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.** Code: main fcef226a against this branch, 2026-10-15. "2,203 claims / 38 versions /
4 theses": distinct by id over every `registry.db` under the `theme-intelligence` worktree's
`data/theme_intelligence/` (backups excluded); versions only where the text is held.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **The pilot's gene-editing thesis moves SKIP → WATCH** on the next reassess, for the reason
  above — a decision-path change from reading a window main left undated. Flagged for the
  operator; nothing is re-graded until a run reassesses it.
- **The four segment term lists are face-validity choices**, recorded here for review; an area
  they do not cover is now flagged (`UNSEGMENTED_KEY`), not split.
- **A fiscal quarter is undated** until an issuer's fiscal calendar is known — never near-term.
- U16's plausible sub-item (an ACTUAL claim's quote never read for its period) is not changed: no
  stored claim is wrong for it.
