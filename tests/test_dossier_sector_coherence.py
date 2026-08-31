"""A committed dossier never reports a sector the entity master can resolve.

THE FOSSIL (2026-08-31 artifact pass). Four of twelve dossiers carried `"sector": "Unknown"` while
their SIC resolved to a real sector — IT 8741 Industrials, MVST 3690 / NCNO 7372 / UBER 7389
Technology. Not a renderer fault: `assemble.py` sets `sector=resolve_label(rec.identity.sic).sector`
from the STORE AT ASSEMBLY TIME, and the runbook makes `vinci refresh <TICKER> IWM MDY SPY`
MANDATORY immediately before every assembly. Until #528 that refresh resolved un-enriched and
`INSERT OR REPLACE` nulled the SIC — so the mandatory pre-flight destroyed the SIC of the very name
being assembled, and the dossier recorded the hole as a label. All twelve were assembled the day
after the #464 clobber; the eight that read correctly are the ones a later `build_universe`
re-enriched.

The upstream causes are fixed (#523 COALESCE, #525 backfill, #528 refresh enriches). This is the
downstream pin: the same class of failure has now appeared on `vinci monitor` AND on the dossier
surface, so it is pinned where a human actually reads it. Unknown is still legal when it is TRUE —
the entity master genuinely having no SIC (a BDC) — because the fund reports absence, never guesses
past it.
"""
from __future__ import annotations

import json
from pathlib import Path

from vinci.labels import resolve_label

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS = ROOT / "data" / "dossiers"


def _sic_by_ticker() -> dict[str, str | None]:
    path = ROOT / "data" / "snapshots" / "securities.jsonl"
    out: dict[str, str | None] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("ticker"):
                out[str(r["ticker"])] = r.get("sic")
    return out


def test_no_dossier_reports_unknown_for_a_sector_the_entity_master_can_resolve() -> None:
    """The pin. A dossier saying Unknown while its SIC resolves is a stale label on the human's
    decision surface — and, since assembly reads the store, evidence that the store was wrong at
    assembly time."""
    sic_by_ticker = _sic_by_ticker()
    folders = sorted(p for p in DOSSIERS.iterdir() if (p / "dossier.json").exists())
    assert folders, "no committed dossiers — this pin would be vacuous"

    stale: list[str] = []
    for folder in folders:
        d = json.loads((folder / "dossier.json").read_text())
        if d.get("sector") not in (None, "Unknown"):
            continue
        resolvable = resolve_label(sic_by_ticker.get(folder.name)).sector
        if resolvable and resolvable != "Unknown":
            stale.append(f"{folder.name} (says {d.get('sector')!r}, "
                         f"SIC {sic_by_ticker.get(folder.name)} resolves to {resolvable!r})")
    assert not stale, (
        f"dossier(s) reporting a sector the entity master already knows: {stale}. Either the store "
        f"was wrong when they were assembled (check the pre-assembly `vinci refresh`) or the SIC "
        f"was filled afterwards — correct `sector` from `resolve_label(<committed SIC>).sector`."
    )


def test_a_dossier_sector_always_matches_what_its_sic_resolves_to() -> None:
    """The complement, and the stronger half: not merely non-Unknown, but the RIGHT value. A
    dossier disagreeing with the entity master means one of the two is stale, and the human cannot
    tell which from the page."""
    sic_by_ticker = _sic_by_ticker()
    disagree: list[str] = []
    for folder in sorted(p for p in DOSSIERS.iterdir() if (p / "dossier.json").exists()):
        d = json.loads((folder / "dossier.json").read_text())
        want = resolve_label(sic_by_ticker.get(folder.name)).sector
        got = d.get("sector")
        # Unknown-on-both is consistent (a BDC EDGAR publishes no SIC for); it is caught above only
        # when the master CAN resolve one.
        if want and want != "Unknown" and got != want:
            disagree.append(f"{folder.name}: dossier {got!r} vs entity master {want!r}")
    assert not disagree, f"dossier/entity-master sector disagreement: {disagree}"
