"""MECHANICAL-ONLY REFRESH — move stored numbers under a KEPT synthesis.

Until now the only way to change a mechanical number was full re-assembly, which re-rolls synthesis
— and 2026-07-30 proved a re-roll can produce wrong prose from identical inputs. The argument that
decided it is not cost: **FUBO and MVST cannot be re-assembled at all**, so a path that re-runs
assembly leaves them permanently unfixable.

VERIFIED FROM STORED INPUTS: every primitive the derived subtree needs is already in `dossier.json`
for all 11 names — `stock_info.price`, `shares_out`, `market_cap`, and the peer-grid name row's
`net_debt`. No DataRecord, no CIQ bundle, no network, no LLM.
"""
from __future__ import annotations

import json
import pathlib
import shutil

import pytest

from vinci.dossier.refresh import (
    RefreshRefusedError,
    material_figures,
    moved_cited_claims,
    recompute_derived,
    refresh_dossier,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
# Names whose committed artifact predates fields that now carry defaults. A model round-trip
# BACK-FILLS those (`material: false`, `implied_*_margin: null`) — a migration, not a value change,
# and semantically null. Derived from the artifact rather than hardcoded, so it empties itself.
def _pre_schema() -> set[str]:
    out = set()
    for d in sorted(DOSS.glob("*/dossier.json")):
        if json.loads(d.read_text()).get("extraction_version") is None:
            out.add(d.parent.name)
    return out


# --- the round-trip, which is the whole guarantee ------------------------------------------------


@pytest.mark.skipif(not DOSS.is_dir(), reason="no committed dossiers")
def test_a_noop_refresh_is_byte_identical(tmp_path: pathlib.Path) -> None:
    """THE PIN THE OPERATOR ASKED FOR, and it earned itself on the first run: the first cut wrote
    with `json.dumps(indent=2)` while the assembler writes `model_dump_json(indent=2)`, so a
    zero-change refresh rewrote ALL ELEVEN files — different unicode escaping and float repr, no
    semantic change. Two serializers for one artifact is the twin-drift class, and this one would
    have churned every file it touched.

    Pre-schema names are exempted BY DERIVATION (no `extraction_version`), not by name: for those a
    round-trip back-fills defaulted fields, which the next test pins as value-preserving."""
    pre = _pre_schema()
    drifted = []
    for src in sorted(DOSS.glob("*/dossier.json")):
        if src.parent.name in pre:
            continue
        copy = tmp_path / f"{src.parent.name}.json"
        shutil.copy(src, copy)
        original = copy.read_text()
        changed, _ = refresh_dossier(copy)
        if changed or copy.read_text() != original:
            drifted.append(src.parent.name)
    assert not drifted, (
        f"a no-op refresh rewrote {drifted} — the path is not preserving, so any real refresh "
        "would carry unrelated churn into the diff")


@pytest.mark.skipif(not DOSS.is_dir(), reason="no committed dossiers")
def test_a_pre_schema_name_is_migrated_not_altered(tmp_path: pathlib.Path) -> None:
    """FUBO and MVST are the two names this path EXISTS to serve, and they are the two that do not
    round-trip — because their artifacts predate fields that now default. That is a migration, and
    it must be value-preserving: every difference may only be a key that was absent before.

    Reds if a refresh ever CHANGES a pre-schema value rather than adding a defaulted one."""
    pre = _pre_schema()
    if not pre:
        pytest.skip("no pre-schema artifacts left — the migration already happened")
    for name in sorted(pre):
        src = DOSS / name / "dossier.json"
        copy = tmp_path / f"{name}.json"
        shutil.copy(src, copy)
        before = json.loads(copy.read_text())
        refresh_dossier(copy)
        after = json.loads(copy.read_text())

        def walk(a: object, b: object, path: str = "") -> list[str]:
            bad: list[str] = []
            if isinstance(a, dict) and isinstance(b, dict):
                for k, v in a.items():
                    bad += walk(v, b.get(k), f"{path}.{k}") if k in b else [f"{path}.{k} DROPPED"]
            elif isinstance(a, list) and isinstance(b, list):
                if len(a) != len(b):
                    bad.append(f"{path} length {len(a)}->{len(b)}")
                else:
                    for i, (x, y) in enumerate(zip(a, b, strict=True)):
                        bad += walk(x, y, f"{path}[{i}]")
            elif a != b:
                bad.append(f"{path}: {a!r} -> {b!r}")
            return bad

        changes = walk(before, after)
        assert not changes, (
            f"{name}: refresh changed stored values, not just defaults: {changes[:5]}")


# --- the refusal, at CLAIM grain ------------------------------------------------------------------


def _doc(prose: str, rows: list[dict[str, object]], cols: list[str]) -> dict[str, object]:
    return {"ticker": "X", "synthesis": {"bear_points": [prose], "bull_points": [],
                                         "key_unknowns": []},
            "mechanical": {"financial_summary": {"annual": {"value": {
                "rows": rows, "columns": cols, "is_estimate": [False] * len(cols)}}}}}


def test_a_moved_figure_the_prose_cites_is_refused() -> None:
    """THE RED. Preserving prose across a moved cited figure MANUFACTURES the 19c defect — the page
    would cite a number its own tables no longer show."""
    rows = [{"label": "Asset Writedown ($M)", "values": [-391.9], "material": True}]
    doc = _doc("a $391.9M LTM asset writedown drove GAAP net income negative", rows, ["LTM"])
    after = {"financial_summary": {"annual": {"value": {
        "rows": [{"label": "Asset Writedown ($M)", "values": [-420.0], "material": True}],
        "columns": ["LTM"], "is_estimate": [False]}}}}
    hits = moved_cited_claims(doc["mechanical"], after, doc)  # type: ignore[arg-type]
    assert len(hits) == 1 and "391.9" in hits[0] and "420.0" in hits[0], hits


def test_a_moved_figure_the_prose_never_cites_is_preserved() -> None:
    """The grain that matters. Refusing per DOSSIER would force a re-roll for any change anywhere,
    including changes no sentence mentions — which is most of them."""
    rows = [{"label": "Asset Writedown ($M)", "values": [-391.9], "material": True}]
    doc = _doc("revenue is in absolute decline and the multiple has de-rated", rows, ["LTM"])
    after = {"financial_summary": {"annual": {"value": {
        "rows": [{"label": "Asset Writedown ($M)", "values": [-420.0], "material": True}],
        "columns": ["LTM"], "is_estimate": [False]}}}}
    assert moved_cited_claims(doc["mechanical"], after, doc) == []  # type: ignore[arg-type]


def test_an_unchanged_figure_is_never_refused() -> None:
    """The control: citing a figure that did not move is the normal, correct state."""
    rows = [{"label": "Asset Writedown ($M)", "values": [-391.9], "material": True}]
    doc = _doc("a $391.9M LTM asset writedown", rows, ["LTM"])
    assert moved_cited_claims(doc["mechanical"], doc["mechanical"], doc) == []  # type: ignore[arg-type]


def test_a_vanished_cited_figure_counts_as_moved() -> None:
    """Prose citing a number the tables no longer carry AT ALL is the same defect as a stale one,
    and an `if key in new` check would have missed it."""
    rows = [{"label": "Asset Writedown ($M)", "values": [-391.9], "material": True}]
    doc = _doc("a $391.9M LTM asset writedown", rows, ["LTM"])
    after = {"financial_summary": {"annual": {"value": {
        "rows": [], "columns": ["LTM"], "is_estimate": [False]}}}}
    hits = moved_cited_claims(doc["mechanical"], after, doc)  # type: ignore[arg-type]
    assert len(hits) == 1 and "absent" in hits[0], hits


def test_figures_are_keyed_by_row_and_column_not_by_value() -> None:
    """Two rows may legitimately carry the same number; a value-keyed map collapses them and
    under-reports a move."""
    mech = {"financial_summary": {"annual": {"value": {
        "rows": [{"label": "A ($M)", "values": [-100.0], "material": True},
                 {"label": "B ($M)", "values": [-100.0], "material": True}],
        "columns": ["LTM"], "is_estimate": [False]}}}}
    assert len(material_figures(mech)) == 2


# --- the derived rebuild --------------------------------------------------------------------------


@pytest.mark.skipif(not DOSS.is_dir(), reason="no committed dossiers")
def test_the_derived_rebuild_reproduces_the_stored_values() -> None:
    """`TEV = cap + net_debt` and `implied_level = TEV / multiple` must reproduce what assembly
    stored — otherwise the refresh would silently disagree with the assembler and the two paths
    would drift. Non-vacuous: fails if it finds no name carrying a TEV."""
    seen = 0
    for src in sorted(DOSS.glob("*/dossier.json")):
        mech = json.loads(src.read_text())["mechanical"]
        ie = (mech.get("valuation") or {}).get("implied_expectations") or {}
        ie = ie.get("value") if isinstance(ie, dict) and "value" in ie else ie
        if not isinstance(ie, dict) or not ie.get("tev"):
            continue
        seen += 1
        rebuilt = recompute_derived(mech)
        r_ie = (rebuilt["valuation"]["implied_expectations"])
        r_ie = r_ie.get("value") if "value" in r_ie else r_ie
        assert r_ie["tev"]["value"] == ie["tev"]["value"], src.parent.name
        for a, b in zip(ie.get("rows") or [], r_ie.get("rows") or [], strict=True):
            assert a.get("implied_level") == b.get("implied_level"), (src.parent.name, a["label"])
    assert seen >= 10, f"expected the committed corpus, saw {seen}"


# --- the --no-llm precondition --------------------------------------------------------------------


def test_a_mechanical_only_write_over_an_existing_synthesis_is_refused(
        tmp_path: pathlib.Path) -> None:
    """GATED ON THE FILE, NOT THE MODE. `--no-llm` on a FRESH name is a legitimate declared mode and
    `test_the_mechanical_only_mode_cannot_reach_the_guard` keeps it working — so the precondition is
    not "an LLM was configured", it is "a committed file with a synthesis exists".

    Same artifact the 07-30 AORT incident destroyed, reached through the other door."""
    import vinci.dossier.assemble as asm

    folder = tmp_path / "AORT"
    folder.mkdir()
    (folder / "dossier.json").write_text(json.dumps({"ticker": "AORT", "synthesis": {"x": 1}}))

    class _D:
        ticker = "AORT"
        synthesis = None

    with pytest.raises(asm.DossierAssemblyError, match="replace it with null"):
        asm._refuse_synthesis_overwrite(_D(), folder)  # type: ignore[arg-type]


def test_a_fresh_name_with_no_synthesis_still_writes(tmp_path: pathlib.Path) -> None:
    """THE CONTROL, and the reason the existing pin was read before being touched: a first build
    with no LLM legitimately has no synthesis and must still assemble."""
    import vinci.dossier.assemble as asm

    class _D:
        ticker = "NEW"
        synthesis = None

    asm._refuse_synthesis_overwrite(_D(), tmp_path / "NEW")  # no file -> no refusal


def test_a_prior_file_without_a_synthesis_does_not_block(tmp_path: pathlib.Path) -> None:
    """A mechanical-only artifact re-run mechanical-only destroys nothing, so it must not refuse."""
    import vinci.dossier.assemble as asm

    folder = tmp_path / "MECH"
    folder.mkdir()
    (folder / "dossier.json").write_text(json.dumps({"ticker": "MECH", "synthesis": None}))

    class _D:
        ticker = "MECH"
        synthesis = None

    asm._refuse_synthesis_overwrite(_D(), folder)


def test_the_precondition_is_wired_into_the_write() -> None:
    """A guard nobody calls is not a guard, and this one sits on the single path every build takes
    to disk."""
    import inspect

    import vinci.dossier.assemble as asm

    src = inspect.getsource(asm._write)
    assert "_refuse_synthesis_overwrite(dossier, folder)" in src
    assert src.index("_refuse_synthesis_overwrite") < src.index('"dossier.json").write_text')


def test_refresh_refuses_before_it_writes(tmp_path: pathlib.Path) -> None:
    """A refusal that fires after the write leaves the damaged artifact on disk — the same ordering
    the write-block guard turns on."""
    doc = {"ticker": "X", "synthesis": {"bear_points": ["a $391.9M LTM asset writedown"],
                                        "bull_points": [], "key_unknowns": []},
           "mechanical": {"financial_summary": {"annual": {"value": {
               "rows": [{"label": "W ($M)", "values": [-391.9], "material": True}],
               "columns": ["LTM"], "is_estimate": [False]}}}}}
    p = tmp_path / "d.json"
    p.write_text(json.dumps(doc, indent=2))
    before = p.read_text()

    def drop(m: dict[str, object]) -> dict[str, object]:
        m["financial_summary"]["annual"]["value"]["rows"] = []  # type: ignore[index]
        return m

    with pytest.raises(RefreshRefusedError, match="CITES"):
        refresh_dossier(p, transform=drop)
    assert p.read_text() == before, "the refusal wrote before raising"
