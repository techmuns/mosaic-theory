---
id: 2026-10-15-theme-intelligence-u-leads-review-fixes
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the review of the U24/U16/U46/U49 change: seven findings fixed

**WHAT.** A high-effort review of PR #714 (`docs/records/2026-10-15-theme-intelligence-u24-u16-u46-u49.md`)
reported seven findings on it (three more on PR #713); operator, 2026-10-15: "fix all ten".

| Finding | Fix |
|---|---|
| **A "since X" window cut a later window off.** `timing_of` ended the WHOLE union at the publication date: a forecast "since 2019, and again by 2027" read as a window already past. | `window_of(text, ref, source_date=)` ends only the "since" part at the source's date; any other window in the text keeps its own end. The post-hoc cut is gone. |
| **Other readers saw "since" windows ending at the as-of.** The thesis-timeframe comparison and the contradiction check read the raw window; a "since 2019" claim overlapped every 2026 period. | The engine passes each claim's article date (`evidence_windows(…, published)`). The contradiction check reads a change accumulated SINCE a date and a change over another span as DIFFERENT SPANS — compatible, never a contradiction (a rise since 2019 is not contradicted by a fall in 2026). |
| **The cardiovascular terms were GLP-1's outcome vocabulary** ("cardiovascular", "heart failure", "cholesterol" — semaglutide's readouts): a GLP-1 thesis would have been re-keyed. | The segment's terms are the lipid drug classes' own (Lp(a), Lp(a)-lowering, LDL, PCSK9, statins, lipid-lowering, atherosclerosis…). "Lp(a)-lowering" is a term of its own: a whole-word match does not read "Lp(a)" inside it, so the lead's own title had stayed unsegmented. |
| **The stale-key lookup read only the BARE key.** A thesis whose segment SET grew (keyed `obesity_metabolic` before a second segment it names existed) was missed under the composite key — a duplicate. | `_stale_holder`: the thesis on the same node, mechanism, direction, geography and product whose key names another segment set than it reads as TODAY — found and re-keyed. A last resort: every earlier route (same article, earlier match, held sibling) keeps its own reason. |
| **"2025/26" and "2030 per the IEA" stopped being years** (the amount guard took any "/" or "per"). | "/" and "per" make an amount only before a unit ("$2050/oz", "2050 per ounce"). |
| **The desk's dating explanation contradicted the timing note** for a "since" claim. | It says the date is the article's — "a change since a date runs to the source's own date". |
| `thesis_segment` was computed twice for one warning. | Once. |

**WHY.** One misreads a forecast's horizon; one could file a false contradiction; two split or
duplicate a thesis on the fund's declared GLP-1 driver; one drops real years.

**HOW VERIFIED.**
- **Real data, main (fcef226a) against this branch:**
  - 2,203 stored claims: the same 18 timing changes as before these fixes (16 "since X"
    historical → current, 2 undated → straddling) — no new one.
  - 26,038 stored claim pairs with a "since" claim: **no CONTRADICTS either way**; 650 move
    AMBIGUOUS → COMPATIBLE (different spans).
  - 38 real texts: 2,906 → 2,938 ledger figures (unchanged by these fixes); 4 pharma theses:
    only gene editing changes segment.
  - **A $0 reassess of a pilot copy: still exactly ONE action change** — TH-DEE87FCF51 SKIP →
    WATCH (`docs/records/2026-10-15-theme-intelligence-u24-u16-u46-u49.md`). Pilot checksum
    unchanged.
- **Pins:** 14 more in `tests/test_theme_intelligence_u_leads_batch1.py` (45 in all): the union,
  the source-dated window, different spans vs the same span, evidence windows with and without a
  date, the desk's wording, GLP-1 outcome titles vs an Lp(a) title, a grown segment set, "/" and
  "per", and the relation built in BOTH orders.
- **Mutants: 29 of 29 killed**: 16 of the change's own still applicable, 4 rewritten for the
  new code (3 retired with the code they targeted), and 9 for these fixes. One survived the first pass —
  the engine passing no dates for the NEW thesis — and the relation pin now runs both orders.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.** Code: PR #714's branch, 2026-10-15. "2,203 claims / 26,038 pairs / 38 texts / 4
theses": distinct by id over every `registry.db` under the `theme-intelligence` worktree's
`data/theme_intelligence/` (backups excluded); a pair = a "since" claim with any other claim of
its registry, distinct as an unordered pair.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- A "since" claim's window in the contradiction check still ends at the as-of (the check has no
  article dates); it is only ever compared as a span, never as a contradiction of another span.
