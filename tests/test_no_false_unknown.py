"""ITEM 18 — NO FALSE UNKNOWN.

    > Any field the dossier would render as UNKNOWN must first be checked against the record.
    > A false UNKNOWN fails the build.

THE LIVE INSTANCE, dated. A fresh 2026-07-30 build of SMPL printed

    covenant basis: UNKNOWN (not disclosed)

while the decision ledger's V-SMPL row records, verbatim, *"the 8-K's loan-basis reads 1.2x"*. The
fund asserting ignorance it does not have, on a page, that day. A gap invites a look; an UNKNOWN
closes the question — which is why this is worse than a blank.

THE MECHANISM WAS NOT WHAT THE SPEC ASSUMED, and it is worse. "A field the dossier would render as
UNKNOWN" implies a resolution path that came up empty. There is none: the line was a HARDCODED
STRING LITERAL in ``basis_triangulation``, emitted unconditionally for every name on every build.
Nothing was ever consulted, so nothing could be checked.

THE THREE STATES, and only the middle one is new:

  * no underwrite record        -> "UNKNOWN (not disclosed)" stands. Honest: nothing contradicts it.
  * record, no typed fact       -> "no structured source for this decision vintage". EVERY committed
                                   record today. The basis exists only as V-row prose, so UNKNOWN is
                                   false and the prose value is unreadable without a prose reader —
                                   out of scope by decision. This says the true third thing.
  * record with the typed fact  -> render it, source-bound.

NO PROSE IS READ ANYWHERE. The legacy branch is selected by the ABSENCE of a typed fact, never by
inspecting thesis text. Legacy rows are not backfilled and no sidecar exists; the message
self-clears per name as V-rows are written under 18a's schema.
"""
from __future__ import annotations

import inspect
import json
import pathlib

import pytest

import vinci.dossier.mechanical as dm
from vinci.edgar import primary_source as ps

ROOT = pathlib.Path(__file__).resolve().parents[1]


class _Fact:
    def __init__(self, value: float, unit: str, basis: str, source: str) -> None:
        self.value, self.unit, self.basis, self.source = value, unit, basis, source


class _Card:
    """An underwrite record, as ``_read_scenario_card`` returns it."""

    def __init__(self, facts: dict[str, _Fact] | None = None) -> None:
        self.facts = facts or {}


# --- the resolver's three states ----------------------------------------------------------------


def test_no_record_leaves_the_historical_unknown_alone() -> None:
    """Most names are never underwritten. With no record to contradict it the line is honest, and
    widening the change to those names would be scope this item does not have."""
    assert dm._covenant_basis(None) is None


def test_a_legacy_record_says_no_structured_source_not_unknown() -> None:
    """THE SECOND RED, and the one every committed name hits. A record whose facts predate 18a
    carries the basis only as prose — so UNKNOWN is FALSE, and the vintage message is the true
    statement that needs no prose reader."""
    out = dm._covenant_basis(_Card())
    assert out == "no structured source for this decision vintage"
    assert "UNKNOWN" not in out


def test_the_legacy_message_never_quotes_the_prose_value() -> None:
    """The design boundary, pinned. SMPL's V-row prose holds "1.2x"; the render must NOT surface it
    — reading it would need the prose parser this item deliberately does not build, and it is the
    display-string parse the repo forbids besides. Driven with a card whose facts are empty but
    whose (ignored) prose is present, so a future prose reader reds this test."""
    card = _Card()
    card.thesis = "net debt ~1.5x; the 8-K's loan-basis reads 1.2x, self-funding"  # type: ignore[attr-defined]
    assert "1.2" not in (dm._covenant_basis(card) or "")


def test_a_typed_fact_is_rendered_source_bound() -> None:
    """The forward branch. Unreachable on today's corpus — no committed record carries the key — so
    it is pinned here rather than discovered broken the day an analyst writes one."""
    card = _Card({dm.COVENANT_LEVERAGE_FACT: _Fact(1.2, "x", "net debt / covenant EBITDA", "8-K")})
    out = dm._covenant_basis(card)
    assert out is not None and "1.2x" in out and "net debt / covenant EBITDA" in out
    assert "UNKNOWN" not in out


def test_a_typed_fact_of_a_different_name_does_not_satisfy_the_check() -> None:
    """The key is exact. A record full of other typed facts — which is every record today — is still
    a LEGACY record for this field, not a resolved one."""
    card = _Card({"net_debt": _Fact(324.6, "$M", "consolidated", "CIQ"),
                  "ltm_revenue": _Fact(1392.2, "$M", "LTM", "CIQ")})
    assert dm._covenant_basis(card) == "no structured source for this decision vintage"


# --- the rendered line ----------------------------------------------------------------------------


def _tri(covenant: str | None) -> str:
    return ps.basis_triangulation("1.5x", "1.6x", 324.6, 222.5, gaap_gross_margin=None,
                                  impairment=None, revenue=None, covenant_basis=covenant)


def test_the_table_renders_each_state_verbatim() -> None:
    """The renderer stays record-ignorant — it lives in ``vinci.edgar`` and must not learn what an
    underwrite record is. It prints what the caller resolved, defaulting to the historical text."""
    assert "covenant basis: UNKNOWN (not disclosed)" in _tri(None)
    assert "covenant basis: no structured source for this decision vintage" in _tri(
        ps.COVENANT_BASIS_NO_STRUCTURED_SOURCE)
    assert "covenant basis: 1.2x (net debt / covenant EBITDA)" in _tri(
        "1.2x (net debt / covenant EBITDA)")
    # the other three basis rows are untouched by this item
    for row in (f"{ps.CIQ_NET_DEBT_LABEL}: 1.5x", f"{ps.CIQ_COMPS_LABEL}: 1.6x"):
        assert row in _tri(None), row


# --- the wiring, which is where a guard quietly stops existing ------------------------------------


def test_the_resolver_is_wired_into_the_assembled_line() -> None:
    """A guard nobody calls is not a guard — the freshness gate shipped measuring the wrong date and
    a wiring pin is what would have caught it. Matches the EXACT call, not the bare name: a comment
    mentioning ``_covenant_basis`` would satisfy a name search while the call sat nowhere.

    TWO HOPS since 2026-10-22 (review of #778): the line is composed in ONE builder,
    ``_release_lines``, which the assembler and the refresh that re-reads releases both call — so
    the pin follows the chain: the assembler hands the builder the card, and the builder makes the
    exact call. Either hop missing is the unconditional line again."""
    src = inspect.getsource(dm._primary_source)
    assert "_release_lines(" in src and "card=card" in src, (
        "the assembler no longer hands the card to the one line builder")
    assert "covenant_basis=_covenant_basis(card)" in inspect.getsource(dm._release_lines), (
        "the resolver is not wired into basis_triangulation — the line is unconditional again")


def test_the_card_reaches_the_mechanical_layer_from_the_assembler() -> None:
    """The other half of the wiring, one hop up. ``_covenant_basis(card)`` is vacuous if ``card`` is
    always None, and it would be: the parameter defaults to None all the way down."""
    import vinci.dossier.assemble as asm

    src = inspect.getsource(asm.assemble_one)
    assert "card=_read_scenario_card(ticker)" in src, (
        "assemble_mechanical is called without the record, so every name looks un-underwritten")


def test_the_false_unknown_fails_the_build() -> None:
    """THE FIRST RED, as a source pin on the refusal. A behavioural drive would need a full
    ``_primary_source`` run (EDGAR + CIQ + HTTP), so what is pinned here is that the refusal exists,
    keys on the typed fact AND the UNKNOWN text together, and RAISES rather than flagging."""
    src = inspect.getsource(dm._primary_source)
    assert "raise ValueError" in src
    i = src.index("COVENANT_LEVERAGE_FACT) is not None")
    window = src[i:i + 600]
    assert "COVENANT_BASIS_UNKNOWN" in window and "raise ValueError" in window, (
        "the refusal must fire on typed-fact-present AND still-UNKNOWN, and must raise")


# --- the corpus ----------------------------------------------------------------------------------


def test_no_committed_page_asserts_a_false_unknown() -> None:
    """THE CORPUS PIN, and the first cut of it was VACUOUS — measured, not suspected.

    That version only asserted inside ``if COVENANT_LEVERAGE_FACT in facts``, which is true for no
    record on the corpus. It walked 11 covenant lines and reached its only real assertion **0
    times**, while a ``seen >= 5`` counter made it look covered. Same shape as the batch e2e that
    covered 0 of 11: a guard whose gate is never satisfied is not a guard.

    What is checkable TODAY, on every name, is the whole mapping: the committed line must equal what
    this build's resolver produces from that name's own record. That reaches all 11, and it is the
    property the item actually promises — no page asserting ignorance the fund does not have.

    A name absent from the screen cohort CANNOT be re-assembled (``load_finalists`` raises), so its
    artifact is frozen by circumstance, not neglect — MVST and FUBO are there today after an 11.13x
    corporate action. Those are reported, never silently passed, and the exemption is DERIVED from
    ``candidate_records.jsonl`` rather than a hardcoded name list, so it self-clears the moment the
    name re-enters a screen."""
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.rank import load_candidates_from_snapshot

    snap = ROOT / "data" / "snapshots" / "candidate_records.jsonl"
    cohort = ({r.data_record.identity.ticker for r in load_candidates_from_snapshot(snap)}
              if snap.exists() else set())
    checked, stale, frozen = 0, [], []
    for folder in sorted((ROOT / "data" / "dossiers").glob("*")):
        jf = folder / "dossier.json"
        if not jf.exists():
            continue
        tri = (((json.loads(jf.read_text()).get("mechanical") or {}).get("primary_source") or {})
               .get("basis_triangulation") or {}).get("value") or ""
        line = next((ln for ln in tri.splitlines() if "covenant basis:" in ln), None)
        if line is None:
            continue
        checked += 1
        want = dm._covenant_basis(_read_scenario_card(folder.name)) or ps.COVENANT_BASIS_UNKNOWN
        got = line.split("covenant basis:", 1)[1].strip()
        if got == want:
            continue
        (frozen if folder.name not in cohort else stale).append(
            f"{folder.name}: page says {got!r}, record implies {want!r}")
    assert checked >= 10, f"expected the committed corpus, reached {checked} covenant lines"
    assert not stale, (
        "committed pages disagree with their own underwrite records — re-run the artifact pass:\n  "
        + "\n  ".join(stale))
    if frozen:  # visible, not swallowed — these clear when the name re-enters a screen
        print("\nNOT RE-ASSEMBLABLE (absent from the screen cohort):\n  " + "\n  ".join(frozen))


def test_the_corpus_pin_reaches_both_branches() -> None:
    """The anti-vacuity check ON the pin above, because 'it reaches 11 names' would still be hollow
    if all 11 took one branch. Both must be represented: names WITH a record (the vintage message)
    and names WITHOUT (the historical line). Reds if the corpus ever collapses to one side, which
    is when the pin above quietly stops discriminating."""
    from vinci.dossier.assemble import _read_scenario_card

    with_rec = [f.name for f in (ROOT / "data" / "dossiers").glob("*")
                if (f / "dossier.json").exists() and _read_scenario_card(f.name) is not None]
    without = [f.name for f in (ROOT / "data" / "dossiers").glob("*")
               if (f / "dossier.json").exists() and _read_scenario_card(f.name) is None]
    assert with_rec and without, (
        f"the corpus pin only exercises one branch — with-record {sorted(with_rec)}, "
        f"without {sorted(without)}")


@pytest.mark.parametrize("name", ["AORT", "EPAM", "IT", "MVST", "NCNO", "SMPL"])
def test_every_underwritten_name_is_legacy_today(name: str) -> None:
    """MEASURED, and it is why the vintage message is the whole delivery. Not one committed record
    carries the typed key, so every underwritten name takes the legacy branch and the typed branch
    is forward-looking. Reds the day a record gains the fact — at which point that page must show
    the number, and this pin should be narrowed rather than deleted."""
    p = ROOT / "scenarios" / f"{name}.json"
    if not p.exists():
        pytest.skip(f"no committed record for {name}")
    facts = json.loads(p.read_text()).get("facts") or {}
    assert dm.COVENANT_LEVERAGE_FACT not in facts, (
        f"{name} now carries a typed {dm.COVENANT_LEVERAGE_FACT} — the typed branch is live for it")
