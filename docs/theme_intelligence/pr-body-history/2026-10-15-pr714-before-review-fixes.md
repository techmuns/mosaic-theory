Fixes four review leads confirmed in techmuns/mosaic-theory#710: U24, U16, U46 and U49. Operator, 2026-10-15: "fix U24, U16, U46, U49".

> **One research action changes on the pilot.** On its next reassess, TH-DEE87FCF51 (in-vivo gene editing) moves from **SKIP to WATCH**.
> - **Why:** one of its opinions names "next 18 months". Main could not read that period; this branch can. Twelve of those 18 months fall inside the next four quarters.
> - **The rule:** by the existing rule, a window mostly inside the next four quarters is "straddling", not "longer-term only". So SKIP-3 no longer applies.
> - **Your call:** decide whether that's the reading you want.

## What changes
| Lead | Before | After |
|---|---|---|
| U24 | A page with no body took its version id from its content hash. Two such pages share that hash, so the second article's version collided: StoreIntegrityError, the whole scan FAILED, and every resume failed again. | A body-less page's version id is scoped to its own article. A page with a body keeps its content id, and a copy at another URL is still DUPLICATE_CONTENT. |
| U16 | Time windows were misread:<br>• "since May 2026" read as May alone, then called historical;<br>• "next four quarters" counted as 368 days;<br>• "$2050 per ounce" read as the year 2050;<br>• "Q1 FY27" read as calendar 2027, with no note;<br>• "next N months" and "within two quarters" not read at all. | • "Since X" runs from X to the source's own date, unless an end follows it ("since 2019 to 2023" is that range).<br>• N quarters are N fourths of a year.<br>• An amount is not a year.<br>• A fiscal quarter is not placed, and the note says why.<br>• "N months" and "within N quarters" are read. |
| U46 | Pharma had four segments. An immunology, vaccine or Lp(a) thesis named none of them, so it took the bare key the gene-editing thesis held. | Four segments are added: genetic medicine, immunology, vaccines and cardiovascular. The term lists are in the record for review. A thesis keyed before its segment existed is found under the bare key and re-keyed, not duplicated. An area still uncovered is flagged `UNSEGMENTED_KEY`. |
| U49 | The figure reader cut a number at its decimal point when the unit was unknown ("707.5GVA" became 707), and it missed grid and gas units. | A number is read whole: a figure with an unknown unit is missed, never cut. The reader now knows kV, kVA/MVA/GVA, bcf/d, bln, ppt and g/kWh. |

## Verification (real data, compared with main fcef226a)
- **U24:** I processed the two real cached BofA pages that have no body. On main, the second raises `StoreIntegrityError … AV-e3b0c44298fc1c14`. On this branch, both are recorded NO_BODY, each under its own id.
- **U16:** of 2,203 stored claims, 18 change timing.
  - 16 "since X" observations move from historical to current.
  - 2 previously undated claims are now placed as straddling.
- **U49:** across 38 real article texts, the figure ledger goes from 2,906 to 2,938 figures.
  - 44 figures are now read that were missed or cut, such as 2,358.5, 707.5, 110 kV, 7.5 bcf/d and 1.3 ppt.
  - The 12 cut versions are gone.
- **U46:** of the 4 stored pharma theses, only gene editing changes segment. It is re-keyed when an article next reaches it.
- **Pilot reassess ($0, on a copy):** one action changes, the one described at the top. The pilot registry's checksum is unchanged.
- **Tests:** `tests/test_theme_intelligence_u_leads_batch1.py`, 31 tests.
  - On main's code 25 fail. The 6 that pass are controls of behaviour main already gets right.
  - One existing test pinned the cut figure "2,358"; it now reads "2,358.5".
- **Mutation check:** 19 of 19 mutants killed. Two survived the first pass, and I added tests that see them.
- **Lint and suite:**
  - `ruff check .`: All checks passed!
  - `mypy --strict vinci`: Success: no issues found in 187 source files.
  - `pytest -m "not network"`: `5328 passed, 513 skipped, 37 deselected, 19 warnings in 110.96s`.
  - Record, STATE and new-test lints: `745 passed, 1 skipped`.
- **Cost:** $0, with no model or SEC requests.

## Not changed
- U16's plausible sub-item: an ACTUAL claim's quote is still never read for its period. No stored claim is wrong because of it.

## Merge note
Branched from main fcef226a, independently of techmuns/mosaic-theory#713. Both PRs edit STATE row 32 item (8), so whichever merges second needs that line merged again. I'll handle that.

## Files
- **Code:** in `vinci/theme_intelligence/`:
  - `pipeline.py` (U24);
  - `timewindow.py` (U16);
  - `config/taxonomy.toml` and `engine.py` (U46);
  - `completeness.py` (U49).
- **Tests:**
  - new: `tests/test_theme_intelligence_u_leads_batch1.py`;
  - updated: `tests/test_theme_intelligence_verification_quality.py`.
- **Docs, in their own commit:** `docs/records/2026-10-15-theme-intelligence-u24-u16-u46-u49.md` and STATE row 32 item (8).

## Disposition
| Brief item | Disposition |
|---|---|
| U24: body-less pages | SHIPPED |
| U16: time windows | SHIPPED for (a), (c), (d) and (e), plus N months; (b) SKIPPED because it is plausible only, with no wrong stored claim |
| U46: pharma segments | SHIPPED: 4 segments, stale-key lookup, `UNSEGMENTED_KEY` flag |
| U49: figure units and decimals | SHIPPED |
| Real-data runs | SHIPPED: BofA pages, 2,203 claims, 38 texts, 4 theses, pilot reassess (1 action change, flagged) |
| Tests and mutation check | SHIPPED: 31 tests; 19 of 19 mutants killed |
| Record and STATE | SHIPPED |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

