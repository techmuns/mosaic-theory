---
id:
status: shipped
date: 2026-08-31
prs: [530]
supersedes:
superseded-by:
---

# Nine dossiers reported a sector they already knew — the clobber's downstream fossil

**WHAT.** The post-merge artifact pass for #523/#525/#528 found that **nine of seventeen** committed
dossiers carried `"sector": "Unknown"` while their entity-master SIC resolved to a real sector:
GOOGL 7370, IT 8741, LLY 2834, MVST 3690, NCNO 7372, NFLX 7841, UBER 7389, V 7389, WERN 4213. Every
one is an **out-of-cap-band** name — the same ledgered/followed-but-out-of-universe class as
Gartner. Corrected on main across three artifact commits; the invariant ships in #530.

**WHY — the clobber reached further than the monitor.** Not a renderer fault. `assemble.py:923`
sets `sector=resolve_label(rec.identity.sic).sector` **from the store at assembly time**, and
RUNBOOKS §PRE-ASSEMBLY EOD REFRESH makes `vinci refresh <TICKER> IWM MDY SPY` **mandatory
immediately before every assembly**. Until #528 that refresh resolved un-enriched, so `INSERT OR
REPLACE` nulled the SIC — **the mandatory pre-flight destroyed the SIC of the very name it was
about to assemble**, and the dossier wrote the hole down as a label. All seventeen were assembled
2026-08-18, the day after #464 landed; the eight that read correctly are the ones a later
`build_universe` re-enriched. #523/#525/#528 fixed the causes; this corrected the fossils.

**METHOD — surgical, not re-assembly (operator's call).** Per RUNBOOKS §SURGICAL EDITS (the #134
near-clobber): one line rewritten per file, no `json.load → json.dump`. The value is **derived, not
chosen** — literally `resolve_label(<committed SIC>).sector`, the expression assembly itself
evaluates — so it writes what a re-assembly would write for that field and nothing else. A full
re-assembly would additionally have re-rolled seventeen LLM synthesis texts and re-dated every
artifact: a re-underwrite, not an artifact refresh.

**TWO THINGS THE PASS GOT WRONG AND THE PIN CAUGHT.**
1. **The first commit fixed four of eight.** The ticker list came from `ls data/dossiers/` run in
   the PRIMARY CHECKOUT — another session's stale working copy — which held twelve names against
   main's seventeen. The coherence test written for this incident **failed on its first run** and
   named GOOGL, NFLX, V and WERN. Fixed in the second commit, which is driven by the real
   directory listing rather than any hardcoded list.
2. **LLY could not be fixed at all** at first: it had a committed dossier but **no
   `securities.jsonl` row**, so nothing could resolve its label. Recorded as an operator item
   rather than papered over. #527 ("the theme altitude gets its own universe") then introduced
   `SEC-0000059478-LLY` / SIC 2834, and the third artifact commit closed it — the item retired
   without the operator ever having to action it.

**THE PINS** (`tests/test_dossier_sector_coherence.py`), three and **partitioned** so one stale
name reddens exactly one test with one diagnostic message:
- no dossier reports Unknown for a sector the entity master can resolve;
- a dossier that *states* a sector states the **right** one;
- the served `frontend/dossiers/<T>.json` carries the same sector as its source.

**THE MIRROR PIN EXISTS BECAUSE OF A REVIEW FINDING.** The first draft read `data/` only, and the
standing mirror guard (`test_every_web_mirror_is_byte_identical_to_its_source`) compares **only the
`.md` files** — so a correction applied to `data/` alone would have shipped a stale served JSON
with the whole suite green and nobody able to say which surface was current. That is the
FUBO-banner defect one file type over, and a half-applied fix was not hypothetical: this pass's own
first commit was one.

**UNKNOWN STAYS LEGAL WHEN IT IS TRUE.** A name the entity master genuinely has no SIC for — a BDC,
where EDGAR publishes none — is never flagged. The fund reports absence; it never guesses past it.

**VERIFIED.** 18 files, 18 lines; `git diff -U0` shows only `"sector":` lines. Every `.md`
byte-proofed untouched (`git diff --quiet`). All data/frontend mirrors byte-identical. Every one of
the seventeen dossier sectors now agrees with the entity master. Each pin demonstrated failing by
mutation, and each fires alone: reverting both sides of IT fires only the Unknown pin, writing a
wrong value fires only the disagreement pin, reverting the mirror alone fires only the mirror pin.
Full offline suite re-run **on the freshly-written artifacts** per the ARTIFACT-PASS RULE — 3368
passed, 0 failed, 144 network-skipped; ruff + `mypy --strict vinci` clean.
