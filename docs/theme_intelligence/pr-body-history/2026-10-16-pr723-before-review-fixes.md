Operator, 2026-10-15: "group the rest of the U-list and start the first". The full account is in `docs/records/2026-10-15-theme-intelligence-group-5-facts.md`.

## The rest of the U-list, grouped

| Group | Theme | Leads |
|---|---|---|
| **5 (this PR)** | Writes a wrong fact or loses one | U7, U12 (both live on the pilot; U12 costs money), U5, U6, U25, U55, U10 |
| 6 | Verification and extraction checks | U17, U19, U20, U48 |
| 7 | Parsing and documents | U30, U15, U22, U50 |
| 8 | Companies and publishers | U11, U60a, U51 |
| 9 | Operations and alerts | U31a, U31c, U31d, U31f, U37, U57, U28 |
| 10 | Structure and reuse (no behaviour change) | U33, U53, U56, U58, U59, U60b, U27, U41, U34 |
| 11 | Docs and records | U35, U39, U40 |

No published view changes: no render code is touched. This PR changes what runs write, and it stops for the operator's merge approval.

## What changes

| Lead | Defect | Fix |
|---|---|---|
| U7 | Re-analysis reverted a page-stated class to the channel default (pilot A-b4589733a42a) | The stored class is kept when the page stated it |
| U12 | Re-analysis and file ingest never archived, so SKIP theses stayed active; the pilot's re-analysis paid to enrich three of them | Re-analysis archives before it enriches; the ingest commands end with `finish_ingest` (archive, then finish) |
| U5 | A new claim was read against the held claim whose id sorted last; a third origin confirming a moved date was a "timing change" in 2 of 6 wordings | It is read against its own origin's latest reading, else one it agrees with, else the latest linked |
| U6 | A discarded re-read version's review issues and context links were already stored | Built with `defer=True`; written only with a kept version |
| U25 | Re-running `article --url` without `--published` wiped the operator-verified date and the text-credited authors | The record keeps what an earlier run verified when the fetch cannot restate it; a page-stated date still wins |
| U55 | Reassess reused the recorded source tier, re-joined the old hold note (doubling a reason, never clearing a hold), and passed an empty article id | Holds derived as the update path derives them; the current tier read from the sources; the article named |
| U10 | `--retire T --retire T` failed the run with T retired | The retire list is de-duplicated |

## Real-run verification

**On copies of the pilot**, main 2a794602's code against this branch, $0:
- **U12:** after an ingest run's end, **7** SKIP theses are still active on main (19 active) and **0** on this branch (12 active). These are what the next enrichment would pay for.
- **U7:** re-analysis rebuilds A-b4589733a42a's record. On main it reads "channel default for jpm_tmt"; on this branch it keeps "page states it 'should not be regarded as a research report'".
- **U55:** a reassess of every thesis changes the same 3 on both, and all **23** current versions are identical afterwards. The pilot doesn't contain U55's triggers.

The live pilot's checksum is unchanged.

**U6, reproduced on the tests' re-read harness**, with a stub review that re-anchors one line. On main, the discarded version leaves **1** link for a version that does not exist and **1** review record. On this branch, **0** and **0**.

Checks:
- Pins: `tests/test_theme_intelligence_group5.py`, 18 tests, each fix with its negative. For U5, a six-wording end-to-end test checks that the third date moves from 2Q27, never 1Q27.
- Mutants: 12 of 12 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.

Offline suite (`pytest -m "not network"`): **5,528 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 734 passed.

## Disposition

| Item | Status | Note |
|---|---|---|
| Group the rest of the U-list | SHIPPED | groups 5–11, in the record and STATE |
| U7 page-stated class | SHIPPED | |
| U12 archive at every thesis-changing run's end | SHIPPED | the live pilot's 7 SKIP theses leave the active list at its next run |
| U5 reading against the right held claim | SHIPPED | stored classes stand; the next classification changes |
| U6 discarded re-read leaves nothing | SHIPPED | |
| U25 verified date and credited authors kept | SHIPPED | |
| U55 reassess holds, tier, timing article | SHIPPED | no change on the pilot |
| U10 retire once | SHIPPED | |
| STATE row 32: #722 merged | SHIPPED | |

Accepted, stated in the record:
- Three phrases (`CHANNEL_DEFAULT`, `TEXT_CREDIT`, `REVIEW_HOLD`) are read back from stored text, because older records carry no structured field for them. Each has one writer and one reader sharing a constant.
- The U6 and U55-doubling pins construct their trigger. The create path never links a failed-span claim.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

