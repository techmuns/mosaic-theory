---
id:
status: shipped
date: 2026-09-01
prs: []
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

**LOOKBACK.** `_FORMER_NAME_LOOKBACK_DAYS = 2190` (~6y = the 5 rendered fiscal years + up to a
year of report/filing lag). Face-validity, never outcome-tuned. Aging out is designed: FUBO's
four-shell chain flags at a 2022 reference (four true lines — Carolco → Recall → Pulse Evolution →
FaceBank, each captioning then-rendered vintages) and is clean today, the contaminated vintages
having left the page with it.

**HOW VERIFIED.** Live sweep over all 17 committed dossier CIKs + TECX/ORKA/NU at reference
2026-09-01 AND backdated 2026-06-01(2022): today flags exactly MVST (Tuscan Holdings) and AORT
(CryoLife → Artivion 2022 — a true rename, honestly hedged); backdated adds FUBO (its chain),
VRRM (Gores Holdings — SPAC); LLY/AAPL/FUBO-"/FL" flag NOWHERE. 13 pins in
`tests/test_former_name_marker.py`, every fixture the REAL fetched payload: the dedupe (TECX
exactly once), the in-window cut (ORKA: ARCA yes, Nuvelo/Hyseq no), all three restyle classes as
no-flag pins, the FUBO pin PAIR (four flags backdated, zero today), fetch-failure loudness, the
`partition()` surface pin (caveat, not QA — this is what routes it onto the human PDF/web without
any renderer change, since `dossier.json` carries `caveats` pre-split), a no-mechanism-words pin,
and the client parse (unreadable rows skipped). Suite 3,377 green; ruff + `mypy --strict` clean.

**WHAT IT COSTS / WHAT IS ACCEPTED.** (1) A true rename that is NOT a business change (AORT's
CryoLife → Artivion) flags too — accepted: the text directs verification rather than asserting,
and a closed suffix list cannot know a rebrand from a merger. (2) A reverse merger that KEEPS the
base name while changing only its legal suffix would be collapsed as a restyle — accepted as rare
and honestly ambiguous; the falsifier is an observed live case, which would justify promoting the
suffix in question out of the style list. (3) Committed dossiers gain the caveat only at their
next re-assembly (the standing post-merge artifact pass); until then MVST/AORT's pages do not show
it — the flag is in the assembler, not backfilled into artifacts by this PR.
