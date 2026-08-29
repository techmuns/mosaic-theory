"""The theme thesis card + gate (brief Item 1, rulings R1–R3 adopted 2026-08-28).

The negative pins are the load-bearing ones (the brief names their observed failure shapes): a
blank null thesis recorded as present would be worse than the stamp; a deadline-less falsifier is
the class the monitor can never flag (today's ``watchlist_triggers``, at theme level); a silent
overwrite is the class ``assert_basket_writable`` closed for baskets (#424). The gate's ORDERING
inside the freeze path is pinned on the CLI source — before the ledger append — because #424 was
precisely a write that ran before its preflight.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.scenarios import DatedTrigger
from vinci.themes.drivers import DRIVER_SPECS
from vinci.themes.thesis import (
    ThemeThesis,
    ThesisMechanism,
    load_thesis,
    require_thesis_card,
    stamped,
    thesis_path,
    write_thesis,
)


def _card(**over: Any) -> ThemeThesis:
    base: dict[str, Any] = {
        "driver_key": "ai-datacenter",
        "declared_date": date(2026, 8, 29),
        "mechanism": ThesisMechanism.SUPPLY_SIDE,
        "market_mistake": "test mistake stated as a mechanism",
        "null_thesis": "test null: the driver is noise and members mean-revert",
        "first_confirming": DatedTrigger(trigger="test confirming datapoint",
                                         deadline="2026-11-15", basis="test"),
        "falsifiers": (DatedTrigger(trigger="test falsifier", deadline="2027-01-31"),),
    }
    base.update(over)
    return ThemeThesis.model_validate(base)


def test_valid_card_writes_stamped_and_round_trips(tmp_path: Path) -> None:
    card = stamped(_card())
    assert card.mirror_slug == DRIVER_SPECS["ai-datacenter"].mirror_slug
    path = write_thesis(card, data_dir=tmp_path)
    assert path == thesis_path("ai-datacenter", data_dir=tmp_path)
    assert load_thesis("ai-datacenter", data_dir=tmp_path) == card


def test_blank_null_thesis_refused() -> None:
    with pytest.raises(ValueError, match="blank"):
        _card(null_thesis="   ")


def test_no_falsifiers_refused() -> None:
    with pytest.raises(ValueError, match="nothing that can kill it"):
        _card(falsifiers=())


def test_deadline_that_is_not_a_date_refused() -> None:
    """The theme-level SMPL class: a criterion the monitor can never place in time."""
    with pytest.raises(ValueError, match="not an ISO date"):
        _card(falsifiers=(DatedTrigger(trigger="vague", deadline="Q3 2026"),))
    with pytest.raises(ValueError, match="not an ISO date"):
        _card(first_confirming=DatedTrigger(trigger="vague", deadline="soon"))


def test_unknown_driver_refused_at_write(tmp_path: Path) -> None:
    card = _card(driver_key="not-a-driver")
    with pytest.raises(ValueError, match="unknown driver"):
        write_thesis(card, data_dir=tmp_path)
    with pytest.raises(ValueError, match="unknown driver"):
        stamped(card)


def test_hand_typed_wrong_mirror_slug_refused_at_write(tmp_path: Path) -> None:
    """The #412 mirror-binding lesson: the stamp is the machine's to write."""
    card = _card(mirror_slug="wrong-slug")
    with pytest.raises(ValueError, match="declare path stamps this"):
        write_thesis(card, data_dir=tmp_path)


def test_existing_card_refuses_then_supersede_archives(tmp_path: Path) -> None:
    first = stamped(_card(declared_date=date(2026, 8, 1)))
    write_thesis(first, data_dir=tmp_path)
    second = stamped(_card(declared_date=date(2026, 8, 29),
                           null_thesis="revised null thesis text"))
    with pytest.raises(FileExistsError, match="NOTHING was written"):
        write_thesis(second, data_dir=tmp_path)
    write_thesis(second, data_dir=tmp_path, supersede=True)
    arch = tmp_path / "themes/thesis/archive/ai-datacenter-2026-08-01.json"
    assert arch.is_file(), "supersede must archive the prior card, never destroy it"
    assert ThemeThesis.model_validate_json(arch.read_text()) == first
    assert load_thesis("ai-datacenter", data_dir=tmp_path) == second


def test_two_supersessions_of_same_dated_cards_do_not_collide_in_the_archive(
    tmp_path: Path,
) -> None:
    """REVIEW FINDING — the archive name is DATE-KEYED, so superseding two cards that share a
    ``declared_date`` overwrote the first archive and lost the operator's earlier declared
    judgment. `write_baskets` found and closed this exact hole (its own same-day pin); this file
    copied the shape without the fix. Declare → fix a typo → fix again, all on one day, is normal.
    """
    a = stamped(_card(market_mistake="first declared mistake"))
    b = stamped(_card(market_mistake="second declared mistake"))
    c = stamped(_card(market_mistake="third declared mistake"))   # all three share declared_date
    write_thesis(a, data_dir=tmp_path)
    write_thesis(b, data_dir=tmp_path, supersede=True)   # archives a
    write_thesis(c, data_dir=tmp_path, supersede=True)   # archives b — SAME declared_date
    archived = sorted((tmp_path / "themes/thesis/archive").glob("*.json"))
    assert len(archived) == 2, (
        f"a same-day supersession overwrote the earlier archive: {[p.name for p in archived]}")
    contents = [ThemeThesis.model_validate_json(p.read_text()) for p in archived]
    assert a in contents and b in contents, "an archived card was lost"
    assert load_thesis("ai-datacenter", data_dir=tmp_path) == c


def test_gate_absent_card_raises_the_remedy(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="theme thesis gate"):
        require_thesis_card("ai-datacenter", data_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="vinci theme-thesis declare"):
        require_thesis_card("ai-datacenter", data_dir=tmp_path)
    card = stamped(_card())
    write_thesis(card, data_dir=tmp_path)
    assert require_thesis_card("ai-datacenter", data_dir=tmp_path) == card


def test_gate_runs_before_the_ledger_append_in_the_freeze_path() -> None:
    """SOURCE-ORDER PIN (the #424 class): the thesis gate must sit in the preflight cluster,
    BEFORE any ``append_record`` — a gate after the append refuses a freeze whose ledger rows
    already landed. Pinned on the CLI source because the ordering IS the fix."""
    src = (Path(__file__).resolve().parents[1] / "vinci/cli.py").read_text()
    fn = src.split("def _cmd_themes_forward(", 1)[1].split("\ndef ", 1)[0]
    gate = fn.index("require_thesis_card")
    append = fn.index("append_record")
    basket_preflight = fn.index("assert_basket_writable")
    assert gate < append, "thesis gate must run before the ledger append (preflight, #424)"
    assert gate < basket_preflight, "thesis gate is the cheapest check — first in the cluster"


def test_schema_cannot_conclude() -> None:
    """The card records a declared thesis; it must not smuggle a conclusion field."""
    forbidden = ("verdict", "recommendation", "score", "rank", "priority", "decision",
                 "conclude", "target", "weight", "buy", "sell")
    for n in ThemeThesis.model_fields:
        for tok in forbidden:
            assert tok not in n.lower(), f"field {n!r} smuggles a conclusion ({tok})"


def test_card_only_fields_never_appear_in_llm_tool_schema_sources() -> None:
    """OPERATOR-TYPED ONLY: no LLM phase may be asked to produce a card field. Source-string pin
    over the modules that construct LLM tool schemas in this repo (the parity-pin pattern —
    quoted keys, so a prose mention cannot false-positive). If a new LLM phase is added, extend
    the file list — the pin's docstring is the reminder."""
    card_only = ('"market_mistake"', '"null_thesis"', '"first_confirming"', '"falsifiers"')
    root = Path(__file__).resolve().parents[1]
    llm_schema_files = (
        root / "vinci/themes/exposure.py",
        root / "vinci/themes/drafts.py",
        root / "vinci/dossier/synthesis.py",
    )
    for f in llm_schema_files:
        src = f.read_text()
        for key in card_only:
            assert key not in src, f"{f.name} carries card-only key {key} — the card is human-typed"
