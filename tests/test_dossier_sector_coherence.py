"""A committed dossier never reports a sector the entity master can resolve — on EITHER surface.

THE FOSSIL (2026-08-31 artifact pass). Eight of seventeen dossiers carried `"sector": "Unknown"`
while their SIC resolved to a real sector — GOOGL 7370, IT 8741, MVST 3690, NCNO 7372, NFLX 7841,
UBER 7389, V 7389, WERN 4213. Not a renderer fault: `assemble.py:923` sets
`sector=resolve_label(rec.identity.sic).sector` from the STORE AT ASSEMBLY TIME, and the runbook
makes `vinci refresh <TICKER> IWM MDY SPY` MANDATORY immediately before every assembly. Until #528
that refresh resolved un-enriched and `INSERT OR REPLACE` nulled the SIC — so the mandatory
pre-flight destroyed the SIC of the very name being assembled, and the dossier recorded the hole as
a label. All seventeen were assembled the day after the #464 clobber; the nine that read correctly
are the ones a later `build_universe` re-enriched, and every one of the eight is an out-of-cap-band
name — the same ledgered/followed-but-out-of-universe class as Gartner.

The upstream causes are fixed (#523 COALESCE, #525 backfill, #528 refresh enriches). These are the
downstream pins: the same failure class has now appeared on `vinci monitor` AND on the dossier
surface, so it is pinned where a human actually reads it.

UNKNOWN STAYS LEGAL WHEN IT IS TRUE — a name the entity master genuinely has no SIC for (a BDC,
where EDGAR publishes none) is never flagged. The fund reports absence; it never guesses past it.
"""
from __future__ import annotations

import json
from pathlib import Path

from vinci.labels import resolve_label

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS = ROOT / "data" / "dossiers"
MIRRORS = ROOT / "frontend" / "dossiers"

#: Sector values that mean "not resolved" rather than a real answer.
ABSENT = (None, "Unknown")


def _sic_by_ticker() -> dict[str, str | None]:
    """{TICKER: SIC}, with AMBIGUOUS tickers mapped to None rather than last-wins.

    Two `securities.jsonl` rows can share a ticker under different CIKs (XPRO, CLBK today). A plain
    dict would silently keep whichever appeared last, so a dossier for such a name would be checked
    against a DIFFERENT company's SIC — passing while it disagrees, or failing against a code the
    reader cannot reconcile with the page. Ambiguity resolves to None, which these pins read as
    "cannot confirm" and skip, matching the resolver's own refusal to guess an ambiguous ticker.
    """
    seen: dict[str, str | None] = {}
    ambiguous: set[str] = set()
    for line in (ROOT / "data" / "snapshots" / "securities.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        t = r.get("ticker")
        if not t:
            continue
        t = str(t)
        if t in seen and seen[t] != r.get("sic"):
            ambiguous.add(t)
        seen[t] = r.get("sic")
    return {t: (None if t in ambiguous else s) for t, s in seen.items()}


def _dossiers() -> list[Path]:
    folders = sorted(p for p in DOSSIERS.iterdir() if (p / "dossier.json").exists())
    assert folders, "no committed dossiers found — these pins would be vacuous"
    return folders


def _sector(path: Path) -> object:
    return json.loads(path.read_text()).get("sector")


def test_no_dossier_reports_unknown_for_a_sector_the_entity_master_can_resolve() -> None:
    """THE FOSSIL ITSELF: a dossier saying Unknown while its SIC resolves is a stale label on the
    human's decision surface — and, since assembly reads the store, evidence that the store was
    wrong at assembly time."""
    sic_by_ticker = _sic_by_ticker()
    stale = []
    for folder in _dossiers():
        if _sector(folder / "dossier.json") not in ABSENT:
            continue
        resolvable = resolve_label(sic_by_ticker.get(folder.name)).sector
        if resolvable and resolvable not in ABSENT:
            stale.append(f"{folder.name} (SIC {sic_by_ticker.get(folder.name)} "
                         f"resolves to {resolvable!r})")
    assert not stale, (
        f"dossier(s) reporting a sector the entity master already knows: {stale}. Either the store "
        f"was wrong when they were assembled (check the pre-assembly `vinci refresh`) or the SIC "
        f"was filled in afterwards — correct `sector` from `resolve_label(<SIC>).sector`.")


def test_a_dossier_that_states_a_sector_states_the_right_one() -> None:
    """THE OTHER HALF, deliberately PARTITIONED from the pin above (review of #530): this one
    considers only dossiers that already state a real sector, so a single stale name reddens ONE
    test with one diagnostic message rather than two near-identical ones. A wrong value is as bad
    as an absent one — the human cannot tell which side is stale from the page."""
    sic_by_ticker = _sic_by_ticker()
    disagree = []
    for folder in _dossiers():
        got = _sector(folder / "dossier.json")
        if got in ABSENT:
            continue                      # the absent case belongs to the pin above
        want = resolve_label(sic_by_ticker.get(folder.name)).sector
        if want and want not in ABSENT and got != want:
            disagree.append(f"{folder.name}: dossier {got!r} vs entity master {want!r}")
    assert not disagree, (
        f"dossier/entity-master sector disagreement: {disagree}. One of the two is stale and the "
        f"page cannot say which — reconcile before shipping.")


def test_the_served_json_mirror_carries_the_same_sector_as_its_source() -> None:
    """FUBO'S BANNER, ON THE JSON SIDE (review of #530). The existing mirror pin
    (`test_every_web_mirror_is_byte_identical_to_its_source`) compares only the `.md` files, so
    `frontend/dossiers/<T>.json` had NO guard: a correction applied to `data/` alone would leave
    the served JSON stating the old sector, with the whole suite green and nobody able to say which
    surface is current. That is the same defect the `.md` pin was written for, one file type over —
    and a half-applied fix is not hypothetical here: this pass's own first commit corrected four of
    the eight affected names."""
    for folder in _dossiers():
        mirror = MIRRORS / f"{folder.name}.json"
        assert mirror.exists(), f"{folder.name}: no web JSON mirror"
        assert _sector(mirror) == _sector(folder / "dossier.json"), (
            f"{folder.name}: frontend/dossiers/{folder.name}.json states sector "
            f"{_sector(mirror)!r} but data/ states {_sector(folder / 'dossier.json')!r} — the "
            f"served page is not what data/ says it is.")
