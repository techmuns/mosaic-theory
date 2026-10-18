---
id: 2026-10-14-theme-intelligence-tabs-audit
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# The reading page's Evidence, History, Sources and Full record tabs read as plain lists; the same audit across the other screens

**WHAT.** At the operator's request (2026-10-14): "deep dive into the section Evidence - History -
Sources - Full record which is under each article as this looks complete unreadable / illegible …
check for … TH-38CA111885 and then also look at similar sections in other screens as well (run a
full audit)". All changes are render-time; nothing stored changed.
- **Evidence tab** (`desk.evidence_html`). It was one table per article, five columns (figure,
  what it measures plus the source's words, period, type, role), with "Observed" and "key evidence"
  repeated on almost every row. It is now three lists:
  - a summary line ("54 cited items from 2 sources · 38 supporting · 9 against · 7 context");
  - **Against the thesis** first;
  - **Supporting**, one fold per article (the first open);
  - **Context and other cited figures**.

  Each item is one line: figure, what it measures, period, source. It opens to the source's words;
  the quote is no longer printed under every row. A type shows only when it is not "Observed". Ten
  items show per list, the rest one click away ("Showing 10 of 29 items — show all 29").
- **History tab**: "Version 2", not "v2" wrapping over two lines.
- **Sources tab**: each article says how many cited items it gave and how many go against ("39
  cited, 4 against").
- **Full record tab**: the section list no longer prints its numbers twice ("1. 01 Bottom line").
- **Related theses**: one entry per thesis, its reasons joined. TH-38CA111885 listed the same
  thesis twice, once per reason.
- **The card (Full record page)**: the line labels ("SOURCE OPINION", "MEASURED OBSERVATION") are
  small lowercase tags, and the system notes in ⟨…⟩ ("new evidence from an origin already counted
  — not an independent confirmation") are muted. The words are unchanged.
- **Articles**: an article's open items ("3 items to check · 60 of 62 figures captured") were a
  fold squeezed into the narrow Follow-up column. They are now a full-width row under the article.
  Filtering hides the row with its article, and the cap counts it with its article. An open item
  with no known cause no longer ends "— not accounted for — not accounted for".
- **Review**:
  - resolved findings are three lines each: the line, what resolved it, and the thesis;
  - article completeness items are grouped under their article ("21 in 6 articles"), where each
    article's title used to repeat on every item.

**WHY.** Every tab item repeated what its heading already said, and the words that matter (the
figure, the source's words, whether it goes against the thesis) were buried among them. The
against items, which a reader needs first, were mixed into the supporting ones.

**HOW VERIFIED.**
- **The live local preview** (the app on 127.0.0.1:8895, the pilot registry published, not
  committed; headless Brave at 1280 and 390 px). On TH-38CA111885:
  - Evidence: 9 against, then 29 + 9 supporting under two articles, then 7 context. The first
    screen at 1280 px shows all 9 against items and the first article's first 10. Before, it
    showed the first 12 rows of one article's table.
  - Sources: 15 cited / 5 against and 39 / 4, which sum to the tab's 54 and 9.
  - Related lists the one related thesis once.

  - Articles, filtered by publisher (Morgan Stanley, then Nomura, then all): every items row was
    shown or hidden with its article, 0 mismatched; 4, 2 and 10 items rows shown.
  - At 390 px there was no horizontal page overflow on any of the four tabs, Articles or Review,
    with every fold open.
  - The only console errors are the known missing `frontend/snapshots/` of this worktree.
- **Pins** (`tests/test_theme_intelligence_desk.py`, real 12-week synthetic registry, plus a
  hypothetical thesis carrying counter-evidence):
  - the Evidence tab holds no table; every item has a summary and a quote that opens from it;
  - against comes first and is counted in the summary;
  - related theses are unique;
  - the Full record list prints no second number;
  - an article's items sit in a full-width row under it, sharing its show-all state, and the
    follow-up cell holds no fold;
  - Review's completeness is grouped, one entry per article with its items under it.
  - The existing "every long list says how much it holds" pin counts entries, not the items rows.
  - Mutants: 6 of 6 killed. The one that first survived (completeness ungrouped) is killed since
    the pin checks each article holds its items.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.** The figures for TH-38CA111885 are from a copy of the pilot registry at
`R-20261014T070200Z-ingest`, published 2026-10-14 07:46 UTC. "21 in 6 articles" is Review's open
completeness items over every article in that registry. The before is the same registry rendered by
the previous commit at 07:21 UTC.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **Found by the audit, reported, not fixed:**
  - **The weekly report** (`dashboard.html`) still prints raw diagnostics in its source table and
    findings: states ("BLOCKED UNKNOWN"), dash placeholders ("— — — 0 / 0"), error names
    ("robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED") and check internals
    ("number check failed: value=50.0 value_text='roughly half'"). The desk's screens say the same
    things in plain words.
  - **The card's "At a glance" boxes** repeat the first lines of its sections, by design (the
    guide's card layout). Whether to fold them is the operator's call.
  - **The Morgan Stanley titles** keep the browser tab's " | Morgan Stanley" suffix, so Review reads
    "… | Morgan Stanley Morgan Stanley · 7 items" (first reported in
    `docs/records/2026-10-14-theme-intelligence-ms-batch-citi-links.md`).
  - **The Caffeine article's seven open figures** read "Figure '666111%' not captured". The PDF
    prints each chart label with every character tripled: "Need more energy 666111%%%" is 61%. The
    model read 61%, and the number check rightly held the claim because the page's text does not
    say 61. The item is correct, but it is unreadable as printed.
