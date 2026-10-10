"""Two ways the anchor writer told a reader something untrue (review of #534).

Both are the same shape: a value was produced correctly and then PRESENTED wrongly — once by
omitting the provenance flag that belongs to it, once by leaving the page asserting the previous
anchor. Neither is caught by testing `compute_anchor` alone, because both live on the write path.
"""
from __future__ import annotations

import inspect
import pathlib

from vinci.dossier.anchor import DQ_VENDOR_BRIDGE, _with_bridge

ROOT = pathlib.Path(__file__).resolve().parents[1]


class _A:
    """Minimal stand-in carrying only what `_with_bridge` reads and updates."""

    def __init__(self) -> None:
        self.data_quality: str | None = None
        self.data_quality_detail: list[str] | None = None
        self.seen: dict[str, object] = {}

    def model_copy(self, *, update: dict[str, object]) -> _A:
        self.seen = update
        return self


def _bridge(vendor_filled: list[str]) -> dict[str, object]:
    return {"d_and_a": 1.0, "net_debt": 2.0, "diluted_shares": 3.0, "ltm_revenue": 4.0,
            "ltm_fcf": 5.0, "vendor_filled": vendor_filled}


def test_a_vendor_fill_is_flagged_even_when_the_recipe_did_not_resolve() -> None:
    """FUBO and MVST took an EARLY RETURN, where `DQ_VENDOR_BRIDGE` was never composed — so
    CIQ-supplied numbers (FUBO net_debt 172.4; MVST d_and_a 33.201, net_debt 65.2) sat under a
    null `data_quality`, presented as though EDGAR had produced them. The understatement is worst
    on exactly these names: the R2 cohort underwrites FROM the bridge.
    """
    got = _with_bridge(_A(), _bridge(["net_debt"])).seen
    assert got.get("data_quality") == DQ_VENDOR_BRIDGE, (
        f"a vendor fill on an unresolved recipe carried data_quality={got.get('data_quality')!r}")
    detail = got.get("data_quality_detail") or []
    assert any("net_debt" in d and "CIQ workbook" in d for d in detail), detail


def test_no_vendor_fill_leaves_the_quality_flag_alone() -> None:
    """NEGATIVE: the stamp is evidence, not decoration — an EDGAR-only bridge stays unflagged."""
    got = _with_bridge(_A(), _bridge([])).seen
    assert "data_quality" not in got and "data_quality_detail" not in got, got


def test_the_backfill_re_renders_the_page_it_invalidates() -> None:
    """`anchor-backfill` wrote dossier.json and left dossier.md asserting the PREVIOUS anchor —
    GOOGL printed $706.41 against a record saying 699.65, and later a refusal sentence beneath an
    applicable anchor. Its own docstring claimed the page ignores the block; the renderer prints
    both the base and the reason. Pinned on the COMMAND, since that is where the omission was.

    A SOURCE PIN, AND ITS LIMIT STATED. This asserts the call is written, not that it runs — a
    call disabled behind a falsy guard would still read as present here. What catches the
    CONSEQUENCE is the corpus-level invariant in `test_dossier.py`
    (`test_analysis_tier_reads_in_decision_order_e2e`), which reddens with "committed dossier.md is
    STALE against its own JSON" — it is what caught LLY during the phase-1 build. This pin exists
    to keep the INTENT legible at the write site, where the omission was, and defers detection to
    the artifact layer where it belongs.
    """
    from vinci.cli import _cmd_anchor_backfill

    src = inspect.getsource(_cmd_anchor_backfill)
    assert "_rerender_only(path)" in src, (
        "the backfill must re-render dossier.md — writing one committed artifact of two leaves the "
        "page contradicting the record")
    # THROUGH THE ONE WRITE (2026-10-10, #702): the splice left the derived blocks describing the
    # old anchor. Byte preservation of every other field is now the one write's property, proven
    # on every committed page by `test_the_backfill_write_moves_nothing_but_the_anchor` below.
    assert "layer_refresh.write_recorded(" in src and '"anchor-backfill"' in src, (
        "the JSON write must go through the one write, recording itself")
    assert "the UI ignores it" not in src, (
        "the docstring still claims the page ignores the anchor — it prints its base and reason")


def test_one_unrenderable_page_does_not_strand_the_rest_of_the_batch() -> None:
    """REVIEW FINDING (#536). The re-render was the only unguarded per-ticker step in the loop.

    An unguarded raise lands in the worst possible place: AFTER this name's JSON is written, so it
    leaves precisely the stale-page state the call exists to prevent — and takes every later name
    with it. Every other step in that loop catches and continues; this one now does too, reporting
    the stale page rather than dying quietly mid-batch.
    """
    import inspect

    from vinci.cli import _cmd_anchor_backfill

    src = inspect.getsource(_cmd_anchor_backfill)
    body = src.split("_rerender_only(path)", 1)[0]
    assert body.rstrip().endswith("try:") or "try:" in body.split("replace_anchor_block")[-1], (
        "the re-render must sit inside a try — an unguarded raise strands the batch after a write")
    assert "could NOT be" in src and "stale until it is" in src, (
        "a swallowed failure must SAY the page is stale; a silent continue is worse than the raise")


def test_the_docstring_no_longer_claims_the_page_ignores_the_anchor() -> None:
    """The `Anchor` docstring still asserted "the UI ignores it (data-only)" — the very claim this
    work disproves and pins against in the CLI. A false comment outlives the reader who could
    correct it."""
    import inspect

    from vinci.dossier.anchor import Anchor

    doc = " ".join((inspect.getdoc(Anchor) or "").split())   # newline-insensitive
    assert "UI ignores it" not in doc, "the false data-only claim is still in the docstring"
    assert "prints the base value and the reason" in doc, (
        "the docstring should say what the page actually does with the block")


def test_the_backfill_write_moves_nothing_but_the_anchor(tmp_path: pathlib.Path) -> None:
    """BYTE PRESERVATION, AS BEHAVIOUR (2026-10-10). The backfill once spliced the anchor into the
    text so no other field's bytes could move. It now writes through the one write
    (`layer_refresh.write_recorded`), and this proves the same property on EVERY committed page: an
    anchor edit moves the anchor, the blocks derived from it, and the refresh record — every other
    top-level key is unchanged, and an unchanged anchor writes the page's own bytes."""
    import json as _json

    from vinci.dossier import layer_refresh
    from vinci.dossier.schemas import Dossier

    derived = {"anchor", "valuation_basis", "date_semantics", "qa_flags", "layer_refreshes"}
    for src in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        original = src.read_text()
        path = tmp_path / f"{src.parent.name}.json"
        d = Dossier.model_validate_json(original)
        assert d.anchor is not None
        assert layer_refresh.write_recorded(path, original, d, "anchor-backfill") == original
        edited = d.model_copy(update={"anchor": d.anchor.model_copy(update={"reason": "edited"})})
        after = _json.loads(layer_refresh.write_recorded(path, original, edited,
                                                         "anchor-backfill"))
        before = _json.loads(original)
        assert {k: v for k, v in after.items() if k not in derived} == {
            k: v for k, v in before.items() if k not in derived}, src.parent.name
        assert after["layer_refreshes"][-1]["layers"] == ["anchor"], src.parent.name
