---
id:
status: shipped
date: 2026-09-01
prs: [558]
supersedes:
superseded-by:
---

# Former-registrant-name marker (`vinci/dossier/mechanical._former_name_flags`) — the reverse-merger vintage caveat

**WHAT.** A dossier whose CIK filed under a different registrant name inside the rendered ~6y
lookback now carries a human caveat per former name: *"former registrant name: this CIK filed as
"AvroBio, Inc." (2018-02-02 → 2024-06-18) — multi-year series on this page may span a different
underlying business; verify continuity across the change (SEC submissions formerNames, CIK …)"*.
Source-bound to the submissions `formerNames` array, read from the SAME cached JSON the 8-K scan
already fetches (1-day TTL — zero new network on an assembly). A submissions fetch failure emits an
explicit *"not checked"* caveat — silence would read as a confirmed clean history. New public
client surface: `EdgarClient.former_names()` → `FormerName(name, from_date, to_date)`; rows
missing a name or end date are SKIPPED, never guessed.

**WHY.** Multi-year blocks on a dossier page (financial summary, margin trend, share trajectory)
can silently span a DIFFERENT underlying business filed under the same CIK. The live proof is the
committed corpus itself: FUBO's CIK was FaceBank Group and four shells before that (`audit_r1.py`
already cites it as the perimeter-change proof), MVST's was Tuscan Holdings (a SPAC), and the two
onboarding candidates that prompted this build — TECX (AvroBio until 2024-06) and ORKA (ARCA
biopharma until 2024-08, Nuvelo and Hyseq before) — both carry predecessor XBRL that the trailing
windows would read as theirs. Nothing marked it: searched `formerNames` / `predecessor` /
`reverse merger` / `shell` across `vinci/` plus `git log --grep` both vocabularies — the class was
known only in prose.

**THE KEY DESIGN FACT — the same array records restyles, which must NEVER flag.** The three
false-positive classes were found by running the check over the LIVE corpus before pinning
anything (all 17 committed dossier CIKs + TECX/ORKA/NU, fetched live):

- **casing/punctuation**: "APPLE INC" → "Apple Inc." (AAPL 2019); TECX carries both "AvroBio,
  Inc." and "AVROBIO, Inc." — one predecessor, not two;
- **word order**: LLY filed as "LILLY ELI & CO" until 2019-10 — in-window at a 2022 reference, so
  a string-compare key would have captioned Eli Lilly's history as a different company's;
- **trailing filer suffix**: FUBO's "fuboTV Inc. /FL" (a 2025 reincorporation row) and AAPL's
  "APPLE COMPUTER INC/ FA" — EDGAR filer-record artifacts, not name changes.

The registrant key is therefore a token SET (order-free) after stripping a trailing `/XX` filer
suffix and a CLOSED legal-style token list (inc/corp/co/…/et/al) — every member demanded by an
observed live restyle, grown only from observed false positives, never speculatively. "holdings"
is deliberately NOT in the list: SPAC shells are literally "<name> Holdings" (Tuscan), and
stripping it would erase exactly the class the marker exists for. The marker's text asserts NO
mechanism ("reverse merger"/"SPAC"/"shell" never appear — the input is a rename record and cannot
support them; the "heavy distribution" lesson): it states the filed fact and hedges the
implication ("may span … verify continuity").

**LOOKBACK.** `_FORMER_NAME_LOOKBACK_DAYS = (midcycle.MIN_YEARS + 1) * 365` — 11 years, IMPORTED
from the mid-cycle constant rather than copied, so the two cannot drift. Sized to the DEEPEST
window any rendered block reads: the mid-cycle margin anchor averages 10 fiscal years and feeds
the R1 recipe's *valuation*, so a rename inside it contaminates the multiple itself, not merely a
trend chart. Face-validity, never outcome-tuned. Aging out is still designed — a rename older than
the deepest window captions vintages the page no longer renders.

**HOW VERIFIED.** Live sweep over all 17 committed dossier CIKs + TECX/ORKA/NU at reference
2026-09-01 AND backdated 2022-06-01, PLUS a replay over the repo's whole cached submissions corpus
(**1,880 CIKs carrying a `formerNames` array**) — the scale that surfaced the false positives the
20-name sweep could not. Today flags MVST (Tuscan Holdings), AORT (CryoLife → Artivion), VRRM
(Gores Holdings), FUBO's four-shell chain, TECX (AvroBio), ORKA (ARCA); LLY/AAPL/`/FL`/`/DE/`
restyles flag NOWHERE. **Across the 1,880-CIK corpus: ZERO false positives** — every one of the
five the review named (ARCBEST `/TX/`↔`/DE/`, Huntington `/MD/`↔`/MD`, Air Products, Jack in the
Box `/NEW/`, American Bitcoin) is now silent or correctly flags a real predecessor chain. 23 pins in
`tests/test_former_name_marker.py`, every fixture the REAL fetched payload: the dedupe (TECX
exactly once), the in-window cut (ORKA: ARCA yes, Nuvelo/Hyseq no), all three restyle classes as
no-flag pins, the FUBO pin PAIR (four flags backdated, zero today), fetch-failure loudness, the
`partition()` surface pin (caveat, not QA — this is what routes it onto the human PDF/web without
any renderer change, since `dossier.json` carries `caveats` pre-split), a no-mechanism-words pin,
the client parse (unreadable rows skipped, malformed dates raised), and every review fix listed
below. Suite 3,388 green; ruff + `mypy --strict` clean.

## CORRECTED IN REVIEW BEFORE MERGE (#558) — six defects, each now regression-pinned

The first cut passed a 20-name live sweep and a 13-pin suite while carrying all six. Five were
invisible at that scale; the review replayed the logic over 1,880 cached CIKs and over backdated
reference dates, which is what surfaced them.

1. **LOOKAHEAD — the sharpest.** Only the OLD edge of the window was bounded, so a rename that had
   not yet happened was announced. Assembling AORT at a 2021 reference printed *"filed as CRYOLIFE
   INC (… → 2022-01-06)"* — telling the reader about their own future on a page whose every other
   number is bounded by the reference date (the #416/#426 lookahead class). Now only spans that
   CLOSED on or before the reference date are predecessors.
2. **The baseline was today's name, not the reference date's.** `identity.name` is resolver output
   persisted inside stored records, so a rename AFTER screening left it holding the OLD name, which
   matched the former row and silently suppressed the marker for the freshest case. The marker now
   takes NO name from the caller: it derives the name in force at the reference date from the
   submissions payload the same fetch already returned.
3. **The lookback was shorter than the deepest window the page reads** (~6y vs `midcycle.MIN_YEARS`
   = 10 FYs feeding R1's valuation), so renames 7–9 years back went unmarked while the mid-cycle
   band averaged across two businesses — the exact error the marker exists to catch.
4. **`"group"` was a style token**, silently erasing the shell→successor case whenever the shell
   shared a base word (`"Ajax Capital Group, Inc."` → `"Ajax Capital, Inc."`). Its justification
   traced to a **misidentified CIK** — Cowen Group, probed in place of Artivion. Removing it changed
   no live corpus result. `holdings` and `group` are now both kept, for the same stated reason.
5. **EDGAR's closed filer suffix `/DE/` was unmatched** — the regex required the name to END in
   letters, so only the open `/FL`, `/ FA` spellings collapsed. Five in-window false positives
   existed in the cached corpus (ARCBEST, Huntington, Air Products, Jack in the Box, American
   Bitcoin); this repo's own `graph_coverage.json` carries `"PITNEY BOWES INC /DE/"`.
6. **A blanket `except Exception` laundered every failure into "fetch failed"** — a systematic
   EDGAR format change would have read as one flaky request forever. Fetch and PARSE failures now
   read differently, and a programming error (a client missing the method) propagates instead of
   being converted into a benign caveat.

Also fixed: **spans are no longer merged.** `min(from) → max(to)` over a shared key fabricated a
continuous tenure across a gap another registrant held — live in the cache, where Elevance's two
Anthem rows would have printed *"Anthem, Inc. (2001-12-17 → 2022-06-24)"*, silently erasing the
WellPoint decade between them. One row per registrant now, the latest-closing, never merged. And
**inverted rows** (EDGAR really ships them — Columbia/HCA `from 2000-05-26 to 2000-05-19`) drop the
unusable start rather than printing an impossible range.

**ONE PARSE, TWO CONSUMERS.** `EntityResolver._enrich_issuer` already read the same array with its
own inline comprehension — the twin-drift class (the `share_count_change` precedent), which the
first cut's record wrongly described as "nothing marked it". Both now read
`vinci/edgar/submissions.parse_former_names`. That parser lives in its own module because the
obvious home, `edgar/client.py`, imports `pad_cik` from the resolver and would close a cycle.

**WHAT IT COSTS / WHAT IS ACCEPTED.** (1) A true rename that is NOT a business change (AORT's
CryoLife → Artivion) flags too — accepted: the text directs verification rather than asserting,
and a closed suffix list cannot know a rebrand from a merger. (2) A reverse merger that KEEPS the
base name while changing only its legal suffix would be collapsed as a restyle — accepted as rare
and honestly ambiguous; the falsifier is an observed live case, which would justify promoting the
suffix in question out of the style list. (3) Committed dossiers gain the caveat only at their
next re-assembly (the standing post-merge artifact pass); until then MVST/AORT's pages do not show
it — the flag is in the assembler, not backfilled into artifacts by this PR. (4) **VOLUME, measured
rather than guessed: 527 of 1,880 cached CIKs (28%) carry at least one caveat, 616 lines total.**
Most are true-but-immaterial rebrands (PerkinElmer→Revvity, Herman Miller→MillerKnoll). Accepted:
every line is a filed fact, the text directs verification rather than asserting a mechanism, and
the dossier corpus is hand-picked finalists rather than the screen population. **Falsifier:** if an
analyst reports skimming the caveat block because of this, the marker moves to its own rendered
row instead of the shared block — the fix is placement, not suppression, since suppressing a true
filed fact is the one thing that would make it useless.
