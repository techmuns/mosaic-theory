---
id: 2026-10-27-release-source-and-page-furniture
status: open
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# The 8-K release parser is the scorecard's third source; a guide in a bullet list reads its period from the list's header, so row 30's ranges are read; and `html_to_text` drops page furniture — 9 of #804's 11 furniture refusals lift, and a stored value its own quote does not state is now counted

**WHAT.** Lane L5 of data-integrity wave 2: items 8 and 17.

**1. `vinci/quality/sources/release.py` — the release source** (`vinci audit quality --source
release`). It reads the committed pages' stored releases and covenant rows, plus each filer's XBRL
`companyfacts` from the SEC cache, read from the cache only: it never fetches. Five checks, each
with its unit, tolerance and population stated on the card.

| check | independence | second source | tolerance |
|---|---|---|---|
| `revenue_vs_xbrl` | independent (same filer, other document) | the 10-Q/10-K XBRL revenue for the fiscal period the row's label names, in the filer's own calendar | `statement_recon`'s 0.5% / $1M, widened to the release's own rounding |
| `gross_margin_vs_xbrl` | independent | XBRL `GrossProfit` ÷ revenue | 0.1 percentage point |
| `guide_scale_vs_xbrl` | independent | XBRL revenue for the same scope a year earlier (a quarterly guide against that quarter) | the midpoint within 2x either way |
| `guide_period_forward` | independent (EDGAR's filing date, the filer's calendar) | where the filer's 10-Q/10-K calendar places the label | the labelled period ends after the release was filed |
| `figure_in_own_quote` | internal (the same document) | the figure's own stored quote, read by `release_parse.quoted_figures` | exact at the quote's stated scale |

`figure_in_own_quote` is item 8's scale check and item 17's "does the quote support the value" check
in one: release actuals, guide bounds, one-offs, event impacts, and covenant rate components
(`margin_pct`, `margin_bps`, `floor_pct`, `pik_pct`). It reads structured values only.
**Diluted EPS has no check:** the parser reads no GAAP diluted-EPS actual — all 34 EPS actuals on the
pages are adjusted or non-GAAP — and XBRL carries no non-GAAP figure. The coverage map says so.

**2. `release_parse._header_period` — row 30.** A guide that opens a bullet item reads its period from
its LIST'S HEADER. The header is found by walking back over the list one item at a time, never by
searching above it. It must introduce the list: a forward word, or the colon a list opens with. It
must state no figure, and "vs." ends no sentence. A results heading, two quarters, a quarter beside
a year, and a reported ("…2026 results") period are each no answer. A date swallows its own year:
nCino's "second quarter ending July 31, 2026" is `Q2`, never `2026`. The lead-in had read it as 2026.
With the periods read, `operating income`, its non-GAAP/adjusted form (`adjusted operating income`)
and non-GAAP EPS (`adjusted eps`) join the vocabulary. The prefix-free "EPS" / "earnings per share"
stays held. The footnote slot takes two markers (Nike's `**`).

**3. `vinci/graph/filings.html_to_text` — page furniture.** Each CSS page break marks the text. The
words at a page's edge are dropped only when the same run recurs at the edge of ≥30% of pages (and
≥3), word for word except page-number words. The run must end on a number, and each page-number
word must advance one per page or stay constant (the year in a running title). A bare number alone
must advance. Everything else is character for character the old text.

**WHY.** VRRM's "$380 million to $385 million" sat on its card as an adjusted EBITDA of $38.0M for
104 days (`docs/records/2026-10-22-release-actuals-at-their-scale.md`). The release parser's output
was checked only where CIQ used it (`ciq.guide_vs_release`). On the 2026-10-27 CIQ snapshot that
check is unchecked on 19 of 26 pages:
- 11 releases state no numeric revenue guide;
- 4 pages have no CIQ revenue guide;
- 3 compare across periods (NCNO, NFLX, SMPL);
- 1 compares across bases (EPAM).

All verified against the pages. **The seven releases that parse no guide row of any metric:**
- NKE: a miss — a `**` marker hid its adjusted-EPS guide. Fixed.
- ROST: a miss of vocabulary — prefix-free "earnings per share" guides. Held, see below.
- GOOGL: a capex guide only, no metric in the vocabulary.
- IT: its outlook sits in a separate earnings supplement.
- PARR, V, WLK: state no numeric guide in the release.

None of the seven was among row 30's ranges.

#804 left page furniture refused on purpose: "the fix belongs in `html_to_text`, not in the check".

**HOW VERIFIED.**

*Row 30, on the 119 EX-99.1 exhibits the 27 pages cite (SEC cache, 0 fetched), origin/main against
this branch, parser and `html_to_text` together:*
- **The probe:** main's parser with the held vocabulary added in memory yields 21 new ranges, and
  17 land on `next-fy`: AMZN 2, CNXC 7, NCNO 5, UBER 3 (row 30 said 22 on 2026-09-18, over 91
  releases). **All 17 now read a period.** The other 4 are ROST's prefix-free EPS: two read a
  period; one is labelled with a date's year; one is a false range ("…full year earnings per share
  of $1.79 and $6.32", two actuals joined by "and"). That is why the prefix-free form stays held.
- **This branch against main:**
  - 32 guides added, every one with a period read, 0 on `next-fy`;
  - 23 relabelled: UBER's 3 adjusted-EBITDA guides go annual → quarter; 20 keep their scope
    (NCNO's ten, VRRM's three, VITL, TGT, BURL);
  - 8 new guidance refusals, each with a note: a bullet naming two metrics — CNXC ×3, EPAM ×4,
    LLY ×1;
  - NKE's "no anchored pattern" flag gone;
  - 0 guides removed, 0 actual rows changed;
  - 2 verbatims lose furniture (AORT "Page 2 of 13", SMPL "2").
  Every changed row was read against its text.

*Item 17, `html_to_text`:*
- **148 cached documents** (the 119 releases and 29 refused-quote exhibits): 102 change, every
  change a pure deletion, every deleted run a page number, a running title or a document id. A first
  cut normalized every digit and dropped table rows that end a page ("$ 5,580 $ 4,255"); a second
  ended runs on content words ("…Page 5 of 11 TARGET"). Both are pinned.
- **Covenant quotes at 545403de** (#804's own corpus, 393 quotes, reproduced exactly at 234 / 110 /
  49 first): **49 → 40 refused.** 9 of the 11 furniture refusals lift: BURL, EPAM, NCNO, NFLX, PARR,
  TJX ×2, V, WLK. None newly refuses. The 2 left are AORT's list bullets ("·") — the document's
  text, not furniture.
- **At HEAD 56500bb1** (364 PRESENT quotes, 39 more stored as `(E5) refused` with no quote kept):
  - covenant refusals **12 → 10** — EPAM's and NCNO's lift;
  - 7 of the 39 stored refusals are the lifted #804 quotes, on 6 pages: BURL, NFLX, PARR, TJX ×2,
    V, WLK. They should pass at the next re-assembly if the model returns the same quote;
  - maturity event unchanged, 1 verbatim;
  - graph edges **13 → 12**: EXTR's 6 lift and PENG's 5 now refuse.
  **No page is re-assembled and no page value changes**, so 2 committed pages' quote statuses would
  change now (EPAM, NCNO) and 6 more at re-assembly.
- **EXTR corrects #804.** Its 6 edges were attributed to the prior 10-K. They are verbatim in the
  reconstructed 10-K once its page numbers go: furniture, not vintage.
- **PENG's 5 quote a page number** — "include many **10** of the world's largest" — so they refuse
  now. A re-run of the graph extraction would send the model text without it.

*Item 8, the source on the live corpus* (27 pages at 56500bb1, facts fetched 2026-10-27):

| check | units | confirmed | stated | unexplained | unchecked |
|---|--:|--:|--:|--:|--:|
| `revenue_vs_xbrl` (7 pages) | 25 rows | 23 | 0 | 0 | 2 |
| `gross_margin_vs_xbrl` (4) | 15 rows | 15 | 0 | 0 | 0 |
| `guide_scale_vs_xbrl` (11) | 34 guides | 26 | 0 | 5 | 3 |
| `guide_period_forward` (16) | 99 guides | 53 | 0 | 8 | 38 |
| `figure_in_own_quote` (23) | 440 figures | 406 | 5 | 29 | 0 |

The 2 unchecked revenue rows: V's fiscal Q3 2026 has no 10-Q in the cached facts, and FUBO moved its
fiscal year so its calendar does not tile. A zero-day quarter once read $0. It now places nothing.
The 5 stated figures are release quotes cut at the 200-character cap before their figure
(`release_parse.VERBATIM_CAP`).

*The checks fire on real failures — the pages BEFORE #778 (dd85adf5), same facts:*
- `revenue_vs_xbrl` 4 unexplained: V's "Other revenue of $1.3 billion" filed as revenue ×2, CNXC,
  FUBO.
- `gross_margin_vs_xbrl` 5: NKE's quarterly margins under bare years ×3, SMPL, VITL.
- `figure_in_own_quote` 53 against 29 now: VRRM's "Adjusted EBITDA of $38" ($38 at no scale is not
  a $M figure), UBER's, V's and FUBO's unscaled billions.

The brief's named mutation is that real VRRM row, frozen in `tests/fixtures/release_quality/`.
**What it does not catch:** VRRM's four EPS fragments ("$1.1" out of "$1.19 to $1.25"). Their quotes
were cut the same way, so they agree with them. Only an independent figure could see them, and
non-GAAP EPS has none.

*Pins and mutation:*
- Pins:
  - `tests/test_release_header_period.py`: 14 real excerpts, each verified at generation to emit
    what its full filing emits;
  - `tests/test_html_page_furniture.py`: five real HTML excerpts; the two release excerpts are
    stripped of style attributes, conversion verified identical;
  - `tests/test_quality_release.py`: 13 pages' real stored rows, 5 at dd85adf5, with a real
    companyfacts slice.
  - Each check and guard has a positive and a negative pin. The negatives that are no real case are
    labelled mutations of real text.
- **Mutation: 37 mutants, all killed**: 34 in the first full run; the 3 header guards that
  survived it got their own pins and were killed on re-run. Each kill and its test is in the PR.
- `/code-review high --fix` found six. Four are fixed, each behind a pin that fails without it:
  - a scaled count ("61.2 million diluted common shares") read as $M;
  - a gross margin dividing one filing's gross profit by another's revenue;
  - "U.S." / "Inc." / "No." / "approx." read as full stops;
  - the fiscal calendar rebuilt per check.
  Two are reported, not fixed: the cap heuristic (its root fix changes every stored quote) and the
  covenant note format re-typed outside `covenant_extract`. None moved a count on the corpus.
- **#804's real-case fixture moves with the text it was cut from** (`tests/fixtures/verbatim/
  real_cases.json`, checked against EDGAR by its network-marked test). Four of its 16 windows held a
  page number: uber-cut-stop, uber-cut-stop-after-ellipsis and tgt-elided-out-of-order are re-cut
  from the document as read now, each dropping only that number, with their answers unchanged.
  tjx-page-furniture goes from refused to verbatim — this fix's effect. Its old window is kept as
  `window_with_furniture`, where the span check still refuses the digit gap.
- One existing pin asserted the held vocabulary
  (`test_guidance_gaap_eps.py::test_a_non_gaap_diluted_eps_is_never_read_as_gaap`, "`== []`"). It
  now asserts the row is `adjusted eps`, never GAAP — its own stated intent.
- Full offline suite on the final code (rebased on main 23a6b855): 7,328 passed, 528 skipped,
  0 failed; ruff and `mypy --strict vinci` clean. The snapshot is
  `data/snapshots/data_quality/release/2026-10-27.json`, written at f0d144cc.

**DIFFERS-UNEXPLAINED ROWS — gold-corpus candidates, not built:**
- `guide_scale_vs_xbrl`: NCNO ×5 — quarterly revenue guides $142–160M labelled 2025 / 2026,
  releases 2025-05-28 → 2026-05-27.
- `guide_period_forward`:
  - NCNO ×4, the same guides;
  - SMPL ×2 — adjusted-EBITDA change guides labelled 2024 (filed 2025-07-10) and 2025 (2025-10-23);
  - VITL — revenue $900–920M labelled 2025, filed 2026-02-26;
  - AORT — adjusted EBITDA $105–110M labelled 2025, filed 2026-02-12. **AORT's own sentence says
    "in 2025"**: a filer's slip, read faithfully.
  Today's parser fixes all but AORT; the pages carry them until re-assembly.
- `figure_in_own_quote`: **29 of 48 covenant rate components are not stated in their own quote**:
  AMZN 3, AORT 2, BRBR 1, BURL 2, CNXC 1, EPAM 2, IT 2, NCNO 2, NFLX 5, NKE 1, PARR 1, TJX 1,
  UBER 3, WERN 1, WLK 2. The typical case is a margin and a floor of 0 beside "…plus the Applicable
  Rate". **No committed floor of 0 is stated in its quote.** The quote is present (#804); it does
  not support the value.

**BOUNDARY.**
- Pages: the 27 `data/dossiers/*/dossier.json` at main 56500bb1, and at dd85adf5 (pre-#778) and
  545403de (#804) read from git.
- Releases: the 119 `primary_source.releases` EX-99.1 exhibits they cite, from the shared SEC cache.
- XBRL: the companyfacts in that cache, all fetched 2026-10-27.
- Covenant population: PRESENT `covenant_term_rows` with a `verbatim: “…”` note.
- Graph population: `data/graph_coverage.json` as committed (339 edges), each 10-K reconstructed
  by `scripts/audit_verbatim_corpus.py` (cut 2026-06-26); submissions re-fetched 2026-10-27 under a
  one-day TTL.
- "Changed" means a different row, flag or status.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The pages are not re-read.** Guidance lands at each name's next re-assembly; until then the
  source counts what the pages carry. UBER's 3 quarterly guides on `next-fy` are uncounted:
  adjusted EBITDA has no XBRL figure, and a label with no year is unchecked.
- **The guide-scale band selects on size, not period, beyond 2x.** A name more than doubling or
  halving its revenue differs for a true reason. None on the corpus.
- **"Independent" is the same filer.** A filer that misstates its own numbers in both documents
  passes. AORT shows the release side alone can carry a slip.
- **`html_to_text` feeds every filing reader.** Furniture is dropped only by the recurrence rule.
  A document whose furniture is too irregular to recur keeps it, as before. Old `.txt` filings with
  `<PAGE>` tags carry no CSS break and are untouched.
- **Not done here, reported:**
  - the ambiguity refusal counts every metric from a bullet's start, so a bullet stating two
    metrics each with its own range refuses the second (CNXC, EPAM, LLY);
  - a refused covenant rate component is not withheld (a decision for its own build);
  - the prefix-free EPS form (ROST) needs an "X and Y" refusal before it can be admitted.

**Incident → invariant.** Row 30 → `_header_period`, pinned on real text, the vocabulary admitted.
#804's furniture follow-up → `html_to_text`, pinned on real HTML. "A quote is present, not
supporting" → `figure_in_own_quote`, scored. Shipped: Y.
