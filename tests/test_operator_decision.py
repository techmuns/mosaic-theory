"""The operator's recipe decision lives in its OWN block (operator ruling 2026-10-22: "keep my
reasons in their own block").

THE INCIDENT, four times on two names. AMZN's R4 re-tag reason was erased by a re-assembly (#700),
by `anchor-backfill` (#752) and again in #762 — restored by hand each time — and UBER's by its
re-assembly on fresh CIQ (#705), never restored. Two causes, one per writer: the rule both writers
share (`preserve_operator_tag`) kept a hand reason only while the machine DISAGREED with the hand
recipe, so a reason went exactly when the machine came to agree; and assembly's guard returned the
FRESH dossier whenever the recipes matched, so even a kept block would not have been written.

Replayed through the REAL write paths with the REAL transitions — `before` → `rebuilt`, frozen from
git in `tests/fixtures/operator_decision_erasures.json` — and READ BACK FROM DISK, because both
failures lived on the write path (a rule-level test of #670 stayed green while they happened).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import vinci.cli as cli
from vinci.dossier import assemble as asm
from vinci.dossier import layer_refresh
from vinci.dossier.anchor import (
    OPERATOR_RETAG_MARK,
    PLACEHOLDER_HINTS,
    Anchor,
    DecisionWriteError,
    preserve_operator_tag,
)
from vinci.dossier.render import _screening_context_lines
from vinci.dossier.schemas import Dossier, write_dossier

ROOT = Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
FIX = json.loads((ROOT / "tests" / "fixtures" / "operator_decision_erasures.json").read_text())
ERASED = sorted(k for k in FIX if not k.startswith("_"))
LEGACY = json.loads((ROOT / "tests" / "fixtures" / "anchor_retag_erasures.json").read_text())
COMMITTED = sorted(p.parent.name for p in DOSS.glob("*/dossier.json"))
DIVERGES = "⚠ **The machine reads"


def _decided(case: dict[str, Any]) -> dict[str, Any]:
    """`before` in the post-2026-10-22 shape — exactly what `anchor-retag` made of the live page:
    the operator's text moved into the block verbatim, the machine's recipe beside it."""
    return {**case["before"], "reason": None, "operator_decision": case["decision"],
            "machine_recipe_hint": case["before"]["recipe_hint"]}


def _carrier(ticker: str, anchor: dict[str, Any]) -> Dossier:
    """Today's committed dossier carrying the anchor the build produced — only the anchor is the
    incident's; everything else is the real artifact the write path renders."""
    live = Dossier.model_validate_json((DOSS / ticker / "dossier.json").read_text())
    return live.model_copy(update={"anchor": Anchor.model_validate(anchor)})


def _seed(tmp_path: Path, ticker: str, anchor: dict[str, Any]) -> Path:
    folder = tmp_path / ticker
    folder.mkdir()
    (folder / "dossier.json").write_text(json.dumps({"ticker": ticker, "anchor": anchor}))
    return folder


# --- the two write paths, on the real erasures ---------------------------------------------------

@pytest.mark.parametrize("ticker", ERASED)
def test_an_agreeing_rebuild_keeps_the_decision_it_used_to_erase(ticker: str,
                                                                 tmp_path: Path) -> None:
    """RE-ASSEMBLY (#700, #705) replayed: the machine's rebuild AGREES with the decided recipe —
    the very case that erased the reason. The block is written back verbatim, the recipe is the
    decision's, and the machine's own recipe and reason sit beside it, refreshed."""
    case = FIX[ticker]
    assert case["rebuilt"]["recipe_hint"] == case["decision"]["recipe"], "fixture lost agreement"
    assert case["before"]["reason"] == case["decision"]["reason"], "fixture lost the operator text"
    folder = _seed(tmp_path, ticker, _decided(case))

    returned = asm._write(_carrier(ticker, case["rebuilt"]), "(test)", tmp_path)

    written = json.loads((folder / "dossier.json").read_text())["anchor"]
    assert written["operator_decision"] == case["decision"], f"{ticker}: the decision moved"
    assert written["recipe_hint"] == case["decision"]["recipe"]
    assert written["machine_recipe_hint"] == case["rebuilt"]["recipe_hint"]
    assert written["reason"] == case["rebuilt"]["reason"], "the machine's own read was not kept"
    page = (folder / "dossier.md").read_text()
    assert case["decision"]["reason"] in page, f"{ticker}: the page lost the operator's reason"
    assert "The machine’s read: " in page and DIVERGES not in page
    assert returned.anchor is not None and returned.anchor.operator_decision is not None


@pytest.mark.parametrize("ticker", ERASED)
def test_the_backfill_keeps_the_decision_it_used_to_erase(ticker: str, tmp_path: Path,
                                                          monkeypatch: pytest.MonkeyPatch) -> None:
    """`anchor-backfill` (#752) replayed AS A COMMAND on a copy of the decided page: its machine
    read is the real `rebuilt` block (EDGAR stubbed out, nothing else). The written page keeps the
    decision verbatim and takes the machine's reason as its own."""
    case = FIX[ticker]
    folder = tmp_path / "dossiers" / ticker
    folder.mkdir(parents=True)
    page = json.loads((DOSS / ticker / "dossier.json").read_text())
    page["anchor"] = _decided(case)
    (folder / "dossier.json").write_text(json.dumps(page))
    _stub_cli(monkeypatch, tmp_path, Anchor.model_validate(case["rebuilt"]))

    assert cli._cmd_anchor_backfill(argparse.Namespace(tickers=ticker, dry_run=False)) == 0

    written = json.loads((folder / "dossier.json").read_text())["anchor"]
    assert written["operator_decision"] == case["decision"], f"{ticker}: the backfill moved it"
    assert written["recipe_hint"] == case["decision"]["recipe"]
    assert written["reason"] == case["rebuilt"]["reason"]
    assert case["decision"]["reason"] in (folder / "dossier.md").read_text()


def test_a_disagreeing_rebuild_keeps_the_decision_and_says_so(tmp_path: Path) -> None:
    """GOOGL's real 09-18 rebuild (#631, R1) against its decided R3: the decision stands, the
    machine's recipe is recorded beside it, and the page states the divergence — first, above the
    machine's read. Assembly adds no caveat: the block carries both recipes, so every render shows
    it, not only the render after a rebuild."""
    live = json.loads((DOSS / "GOOGL" / "dossier.json").read_text())["anchor"]
    rebuilt = LEGACY["GOOGL"]["rebuilt"]
    assert live["operator_decision"]["recipe"] != rebuilt["recipe_hint"], "no divergence to show"
    folder = _seed(tmp_path, "GOOGL", live)
    carrier = _carrier("GOOGL", rebuilt)

    asm._write(carrier, "(test)", tmp_path)

    doc = json.loads((folder / "dossier.json").read_text())
    written = doc["anchor"]
    assert written["operator_decision"] == live["operator_decision"]
    assert written["recipe_hint"] == live["operator_decision"]["recipe"]
    assert written["machine_recipe_hint"] == rebuilt["recipe_hint"]
    assert doc["caveats"] == list(carrier.caveats), "assembly added a caveat the block already says"
    page = (folder / "dossier.md").read_text()
    flag = f"{DIVERGES} {rebuilt['recipe_hint']}.**"
    assert flag in page
    assert page.index("**The operator's decision: ") < page.index(flag)


def test_a_hand_retag_without_its_block_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    """The pre-2026-10-22 shape — the operator's text in `reason`, no block — is what the machine
    erased, so no write carries it any more. GOOGL's real committed block (#557's re-tag) is on
    disk; the rebuild is refused LOUD, and neither artifact is touched."""
    committed = LEGACY["GOOGL"]["committed"]
    assert committed["reason"].startswith(OPERATOR_RETAG_MARK)
    folder = _seed(tmp_path, "GOOGL", committed)
    before = (folder / "dossier.json").read_text()
    with pytest.raises(DecisionWriteError, match="anchor-retag"):
        asm._write(_carrier("GOOGL", LEGACY["GOOGL"]["rebuilt"]), "(test)", tmp_path)
    assert (folder / "dossier.json").read_text() == before
    assert not (folder / "dossier.md").exists()


# --- the guard, on every write (positive AND negative pins) --------------------------------------

def _live(ticker: str) -> tuple[str, Dossier]:
    text = (DOSS / ticker / "dossier.json").read_text()
    return text, Dossier.model_validate_json(text)


def _has_decision(t: str) -> bool:
    return '"operator_decision"' in (DOSS / t / "dossier.json").read_text()


def _undecided_live() -> str:
    return next(t for t in COMMITTED if not _has_decision(t))


def _decided_live() -> str:
    names = [t for t in COMMITTED if _has_decision(t)]
    assert names, "no committed page carries a decision — the guard pins below would test nothing"
    return names[0]


@pytest.mark.parametrize("edit", ["drop", "alter_reason", "alter_recipe"])
def test_a_write_that_drops_or_alters_the_decision_is_refused(edit: str, tmp_path: Path) -> None:
    t = _decided_live()
    text, d = _live(t)
    path = tmp_path / "dossier.json"
    path.write_text(text)
    a = d.anchor
    assert a is not None and a.operator_decision is not None
    dec = a.operator_decision
    new = {"drop": a.model_copy(update={"operator_decision": None}),
           "alter_reason": a.model_copy(update={"operator_decision": dec.model_copy(
               update={"reason": dec.reason + " (edited)"})}),
           "alter_recipe": a.model_copy(update={"operator_decision": dec.model_copy(
               update={"recipe": "R2_NEEDED"}), "recipe_hint": "R2_NEEDED"})}[edit]
    with pytest.raises(DecisionWriteError):
        write_dossier(path, d.model_copy(update={"anchor": new}))
    with pytest.raises(DecisionWriteError):
        layer_refresh.write_recorded(path, text, d.model_copy(update={"anchor": new}),
                                     "anchor-backfill")
    assert path.read_text() == text, "a refused write wrote anyway"
    # ...and the ONE writer allowed to change a decision may
    write_dossier(path, d.model_copy(update={"anchor": new}), decision_change=True)
    assert path.read_text() != text


def test_the_guard_passes_every_ordinary_write(tmp_path: Path) -> None:
    """NEGATIVE, on the whole committed corpus: a page rewritten over itself, and a decided page
    whose MACHINE fields move under an unchanged decision (the backfill's normal write), are never
    refused — nor is a machine reason on a page with no decision."""
    for t in COMMITTED:
        text, d = _live(t)
        path = tmp_path / f"{t}.json"
        path.write_text(text)
        assert write_dossier(path, d) == text, t
        assert d.anchor is not None
        moved = d.anchor.model_copy(update={"reason": "a machine refusal, refreshed",
                                            "machine_recipe_hint": d.anchor.machine_recipe_hint
                                            and "R2_NEEDED"})
        write_dossier(path, d.model_copy(update={"anchor": moved}))


def test_a_hand_retag_typed_into_reason_is_refused_on_any_page(tmp_path: Path) -> None:
    """The old way of re-tagging — editing `reason` by hand — is refused on a page with no
    decision: it would be erased by the next machine write, which is the incident."""
    t = _undecided_live()
    text, d = _live(t)
    path = tmp_path / "dossier.json"
    path.write_text(text)
    assert d.anchor is not None
    marked = d.anchor.model_copy(update={"reason": f"{OPERATOR_RETAG_MARK} {date.today()}. R3."})
    with pytest.raises(DecisionWriteError, match="anchor-retag"):
        write_dossier(path, d.model_copy(update={"anchor": marked}))
    assert path.read_text() == text


# --- the one writer of a decision: `vinci anchor-retag` ------------------------------------------

class _Resolver:
    def resolve_ticker(self, t: str) -> Any:
        raise AssertionError("EDGAR must not be reached — _machine_anchor is stubbed")


def _stub_cli(monkeypatch: pytest.MonkeyPatch, data_dir: Path, fresh: Anchor) -> None:
    """The command as it runs, minus the network: the machine's read is `fresh`."""
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    monkeypatch.setattr(cli, "get_config", lambda: SimpleNamespace(data_dir=data_dir))
    monkeypatch.setattr(EntityResolver, "from_config", classmethod(lambda cls, cfg: _Resolver()))
    monkeypatch.setattr(EdgarClient, "from_config", classmethod(lambda cls, cfg: None))
    monkeypatch.setattr(cli, "_machine_anchor", lambda *a, **k: fresh)


def _retag_args(ticker: str, **kw: Any) -> argparse.Namespace:
    base: dict[str, Any] = {"ticker": ticker, "recipe": None, "reason_file": None,
                            "decided_by": None, "decided_on": None, "source_ref": None,
                            "machine_at_decision": None, "retire": False, "dry_run": False,
                            "values_held": False}
    return argparse.Namespace(**{**base, **kw})


def _copy_page(tmp_path: Path, ticker: str) -> Path:
    folder = tmp_path / "dossiers" / ticker
    folder.mkdir(parents=True)
    shutil.copy(DOSS / ticker / "dossier.json", folder / "dossier.json")
    return folder / "dossier.json"


def _machine_only(a: Anchor, recipe: str) -> Anchor:
    return a.model_copy(update={"operator_decision": None, "machine_recipe_hint": None,
                                "recipe_hint": recipe, "reason": f"the machine's {recipe} read"})


_OWN = {"recipe_hint", "reason", "operator_decision", "machine_recipe_hint", "computed_at",
        "scenario_eligibility"}


def test_retag_records_a_decision_and_moves_no_value(tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    before = json.loads(path.read_text())
    committed = Dossier.model_validate(before).anchor
    assert committed is not None
    fresh = _machine_only(committed, committed.recipe_hint)
    _stub_cli(monkeypatch, tmp_path, fresh)
    reason = tmp_path / "why.txt"
    reason.write_text("  The forward P/E fits this name; the operator's words, verbatim.\n")

    rc = cli._cmd_anchor_retag(_retag_args(t, recipe="R3_forward_pe", reason_file=str(reason),
                                           decided_by="operator", source_ref="docs/records/x.md"))

    assert rc == 0
    after = json.loads(path.read_text())
    a = after["anchor"]
    assert a["operator_decision"] == {
        "recipe": "R3_forward_pe", "decided_by": "operator", "source_ref": "docs/records/x.md",
        "reason": "The forward P/E fits this name; the operator's words, verbatim.",
        # the operator's calendar, as `anchor-retag` dates it — UTC's here made this pin red every
        # night from local midnight to UTC's (00:00–05:30 IST) and green in CI, which runs in UTC
        "decided_on": date.today().isoformat(),
        "machine_recipe_at_decision": committed.recipe_hint}
    assert a["recipe_hint"] == "R3_forward_pe" and a["machine_recipe_hint"] == committed.recipe_hint
    assert a["reason"] == fresh.reason
    assert {k: v for k, v in a.items() if k not in _OWN} == {
        k: v for k, v in before["anchor"].items() if k not in _OWN}, "a re-tag moved a value"
    assert {k: v for k, v in after.items() if k not in {"anchor", "valuation_basis",
                                                        "layer_refreshes"}} == {
        k: v for k, v in before.items() if k not in {"anchor", "valuation_basis",
                                                     "layer_refreshes"}}
    assert after["layer_refreshes"][-1]["writer"] == "anchor-retag"
    md = path.with_name("dossier.md").read_text()
    assert "The forward P/E fits this name; the operator's words, verbatim." in md


def test_a_backdated_decision_never_records_todays_machine_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    t = _decided_live()
    path = _copy_page(tmp_path, t)
    committed = Dossier.model_validate_json(path.read_text()).anchor
    assert committed is not None and committed.operator_decision is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, "R1_midcycle_margin_evebitda"))
    reason = tmp_path / "why.txt"
    reason.write_text(committed.operator_decision.reason)
    rc = cli._cmd_anchor_retag(_retag_args(
        t, recipe=committed.operator_decision.recipe, reason_file=str(reason),
        decided_by="operator", decided_on="2026-07-21", source_ref="docs/records/x.md"))
    assert rc == 0
    dec = json.loads(path.read_text())["anchor"]["operator_decision"]
    assert "machine_recipe_at_decision" not in dec, "today's read was recorded as July's"


def test_retag_retires_a_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    t = _decided_live()
    path = _copy_page(tmp_path, t)
    committed = Dossier.model_validate_json(path.read_text()).anchor
    assert committed is not None
    fresh = _machine_only(committed, "R1_midcycle_margin_evebitda")
    _stub_cli(monkeypatch, tmp_path, fresh)
    assert cli._cmd_anchor_retag(_retag_args(t, retire=True)) == 0
    a = json.loads(path.read_text())["anchor"]
    assert "operator_decision" not in a and "machine_recipe_hint" not in a
    assert a["recipe_hint"] == fresh.recipe_hint and a["reason"] == fresh.reason


@pytest.mark.parametrize("bad", ["missing", "recipe", "empty", "drift", "undecided_retire"])
def test_retag_refuses_and_writes_nothing(bad: str, tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    decided = bad != "undecided_retire"
    t = _decided_live() if decided else _undecided_live()
    path = _copy_page(tmp_path, t)
    text = path.read_text()
    committed = Dossier.model_validate_json(text).anchor
    assert committed is not None
    fresh = _machine_only(committed, "R1_midcycle_margin_evebitda")
    if bad == "drift":   # the machine's read today moves a committed value
        assert committed.net_debt is not None and committed.net_debt.value is not None
        fresh = fresh.model_copy(update={"net_debt": committed.net_debt.model_copy(
            update={"value": committed.net_debt.value + 1.0})})
    _stub_cli(monkeypatch, tmp_path, fresh)
    reason = tmp_path / "why.txt"
    reason.write_text("" if bad == "empty" else "a reason")
    args = {"missing": _retag_args(t, recipe="R3_forward_pe", reason_file=str(reason)),
            "recipe": _retag_args(t, recipe="unknown", reason_file=str(reason),
                                  decided_by="operator", source_ref="x"),
            "empty": _retag_args(t, recipe="R3_forward_pe", reason_file=str(reason),
                                 decided_by="operator", source_ref="x"),
            "drift": _retag_args(t, recipe="R3_forward_pe", reason_file=str(reason),
                                 decided_by="operator", source_ref="x"),
            "undecided_retire": _retag_args(t, retire=True)}[bad]
    assert cli._cmd_anchor_retag(args) == 1
    assert path.read_text() == text, f"{bad}: a refused re-tag wrote anyway"


def test_retag_dry_run_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    t = _decided_live()
    path = _copy_page(tmp_path, t)
    text = path.read_text()
    committed = Dossier.model_validate_json(text).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, "R1_midcycle_margin_evebitda"))
    assert cli._cmd_anchor_retag(_retag_args(t, retire=True, dry_run=True)) == 0
    assert path.read_text() == text


# --- the human surface: decision first, machine's read beneath, divergence stated ----------------

@pytest.mark.parametrize("ticker", ERASED)
def test_the_page_prints_the_decision_above_the_machines_read(ticker: str) -> None:
    case = FIX[ticker]
    anchor = Anchor.model_validate({**_decided(case), "reason": case["rebuilt"]["reason"]})
    md = "\n".join(_screening_context_lines(anchor))
    head = f"**The operator's decision: {case['decision']['recipe']}** — "
    assert md.index(head) < md.index(f"> {case['decision']['reason']}") < md.index(
        "_The machine’s read: ")
    assert case["decision"]["decided_on"] in md[md.index(head):]
    assert case["decision"]["reason"] in md and case["decision"]["source_ref"] in md
    assert DIVERGES not in md
    split = anchor.model_copy(update={"machine_recipe_hint": "R1_midcycle_margin_evebitda"})
    flag = f"{DIVERGES} R1_midcycle_margin_evebitda.**"
    assert flag in "\n".join(_screening_context_lines(split))


def test_an_undecided_page_reads_as_it_did() -> None:
    """NEGATIVE: no decision, no decision line, no "machine's read" label — the machine's reason
    prints bare, as before 2026-10-22."""
    a = Anchor.model_validate({**FIX["AMZN"]["rebuilt"]})
    md = "\n".join(_screening_context_lines(a))
    assert "operator's decision" not in md and "The machine’s read" not in md
    assert f"_{a.reason}_" in md


def test_the_web_twin_prints_the_decision_the_same_way() -> None:
    """The web page (`anchorInner`), on every committed frontend mirror: a decided page shows the
    decision, its source and — only when they differ — the machine's recipe; an undecided page
    shows none of it."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, readdirSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const out = {{}};
for (const f of readdirSync("frontend/dossiers").filter(f => f.endsWith(".json"))) {{
  const t = f.slice(0, -5);
  const d = JSON.parse(readFileSync(`frontend/dossiers/${{f}}`));
  const cp = `frontend/scenarios/${{t}}.json`;
  const h = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
  out[t] = {{ decision: h.includes("The operator's decision: "),
             machine: h.includes("The machine reads "),
             label: h.includes("The machine’s read: "),
             where: h.includes("Where this decision is recorded") }};
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout)
    assert res, "no frontend mirror rendered"
    for t, seen in res.items():
        a = json.loads((ROOT / "frontend" / "dossiers" / f"{t}.json").read_text()).get("anchor")
        dec = (a or {}).get("operator_decision")
        assert seen["decision"] is (dec is not None) and seen["where"] is (dec is not None), t
        diverges = (dec is not None and a["machine_recipe_hint"] != dec["recipe"]
                    and a["machine_recipe_hint"] not in PLACEHOLDER_HINTS)
        assert seen["machine"] is diverges, t
        assert seen["label"] is (dec is not None and bool(a.get("reason"))), t


# --- the committed corpus: invariants, phrasing-free ---------------------------------------------

_RECORD = re.compile(r"docs/records/[\w.-]+\.md")


@pytest.mark.parametrize("ticker", COMMITTED)
def test_no_committed_reason_carries_a_hand_retag_and_every_decision_is_sourced(
        ticker: str) -> None:
    raw = json.loads((DOSS / ticker / "dossier.json").read_text())
    a = raw.get("anchor") or {}
    assert not (a.get("reason") or "").startswith(OPERATOR_RETAG_MARK), (
        f"{ticker}: a hand re-tag sits in the machine's field — `vinci anchor-retag` it")
    dec = a.get("operator_decision")
    if dec is None:
        assert "machine_recipe_hint" not in a, f"{ticker}: a machine recipe with no decision"
        return
    assert a["recipe_hint"] == dec["recipe"], f"{ticker}: the recipe is not the decision's"
    assert dec["recipe"] in cli._decidable_recipes()
    assert a.get("machine_recipe_hint"), f"{ticker}: the machine's read is not recorded"
    for k in ("reason", "decided_by", "source_ref"):
        assert dec[k].strip(), f"{ticker}: decision.{k} is empty"
    date.fromisoformat(dec["decided_on"])
    refs = _RECORD.findall(dec["source_ref"])
    assert refs and all((ROOT / r).exists() for r in refs), f"{ticker}: {dec['source_ref']!r}"
    md = (DOSS / ticker / "dossier.md").read_text()
    assert all(ln in md for ln in dec["reason"].splitlines() if ln.strip()), (
        f"{ticker}: the page lost the operator's reason")
    assert dec["source_ref"] in md, f"{ticker}: the page lost where the decision is recorded"
    assert (f"{DIVERGES} {a['machine_recipe_hint']}.**" in md) is (
        a["machine_recipe_hint"] != dec["recipe"]
        and a["machine_recipe_hint"] not in PLACEHOLDER_HINTS), ticker


def test_the_corpus_check_has_something_to_check() -> None:
    """CORPUS BEFORE SYNTHETIC — the invariant above passes vacuously on a corpus with no
    decision."""
    assert any(_has_decision(t) for t in COMMITTED)


def test_preserve_is_the_one_rule_and_carries_the_block() -> None:
    """RULE-LEVEL, beside the write-path pins above (never instead of them): a decided block in, the
    same block out, whichever side the machine lands on."""
    for t in ERASED:
        case = FIX[t]
        kept, _ = preserve_operator_tag(Anchor.model_validate(_decided(case)),
                                        Anchor.model_validate(case["rebuilt"]))
        assert kept.operator_decision is not None
        assert kept.operator_decision.model_dump(mode="json") == case["decision"]


# --- review of #780: each finding pinned, positive and negative ---------------------------------

_CONFLICTED = ('<<<<<<< HEAD\n{"ticker": "GOOGL", "anchor": {}}\n=======\n'
               '{"ticker": "GOOGL"}\n>>>>>>> origin/main\n')


def test_an_unreadable_committed_page_is_refused_not_written_over(tmp_path: Path) -> None:
    """FINDING 1 — the guard failed OPEN. A rebase leaves conflict markers in a decided page;
    assembly reads that as no recipe to keep, and the guard read it as no decision, so a fresh R1
    anchor would have been written over GOOGL's R3. Every writer now refuses, and nothing moves."""
    folder = tmp_path / "GOOGL"
    folder.mkdir()
    (folder / "dossier.json").write_text(_CONFLICTED)
    carrier = _carrier("GOOGL", LEGACY["GOOGL"]["rebuilt"])
    with pytest.raises(DecisionWriteError, match="cannot be read"):
        asm._write(carrier, "(test)", tmp_path)
    assert (folder / "dossier.json").read_text() == _CONFLICTED
    assert not (folder / "dossier.md").exists()
    for bad in ("[1, 2]", ""):          # a JSON non-object, and a write cut short
        (folder / "dossier.json").write_text(bad)
        with pytest.raises(DecisionWriteError):
            write_dossier(folder / "dossier.json", carrier)
        assert (folder / "dossier.json").read_text() == bad
    # NEGATIVE: no file is a FIRST write, never refused
    first = tmp_path / "NEW" / "dossier.json"
    first.parent.mkdir()
    write_dossier(first, carrier)
    assert json.loads(first.read_text())["ticker"] == "GOOGL"


def test_a_held_page_records_its_decision_and_keeps_every_value(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FINDING 2 — VITL's shape: a hand reason with no marker, on a page whose values are HELD.
    Unmarked, no guard can tell it from a machine reason, so it is safe only inside a block — and
    the machine's read today moves a held value, so a plain re-tag is refused. `--values-held`
    records the decision, keeps every committed value, and writes NO machine reason beside numbers
    it does not describe; the machine's recipe is still recorded."""
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    before = json.loads(path.read_text())
    committed = Dossier.model_validate(before).anchor
    assert committed is not None and committed.net_debt is not None
    assert committed.net_debt.value is not None
    fresh = _machine_only(committed, "R1_midcycle_margin_evebitda").model_copy(update={
        "net_debt": committed.net_debt.model_copy(update={"value": committed.net_debt.value + 1})})
    _stub_cli(monkeypatch, tmp_path, fresh)
    reason = tmp_path / "why.txt"
    reason.write_text("the hand reason, verbatim")
    kw = {"recipe": "R2_NEEDED", "reason_file": str(reason), "decided_by": "operator",
          "decided_on": "2026-10-07", "source_ref": "docs/records/x.md"}
    assert cli._cmd_anchor_retag(_retag_args(t, **kw)) == 1, "a plain re-tag moved held values"
    assert cli._cmd_anchor_retag(_retag_args(t, values_held=True, **kw)) == 0
    a = json.loads(path.read_text())["anchor"]
    assert a["operator_decision"]["reason"] == "the hand reason, verbatim"
    assert a["recipe_hint"] == "R2_NEEDED"
    assert a["machine_recipe_hint"] == "R1_midcycle_margin_evebitda"
    assert a["reason"] is None, "a machine reason was written beside values it does not describe"
    assert {k: v for k, v in a.items() if k not in _OWN} == {
        k: v for k, v in before["anchor"].items() if k not in _OWN}, "a held value moved"
    # ...and HELD never licenses a RETIRE over moved values: retiring takes the machine's reason,
    # which would describe numbers the page does not show
    text = path.read_text()
    assert cli._cmd_anchor_retag(_retag_args(t, retire=True, values_held=True)) == 1
    assert path.read_text() == text, "a retire over held values wrote anyway"


def test_a_refresh_that_would_drop_a_decision_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FINDING 3 — `refresh_dossier` writes without `write_dossier`. Its top-level seam cannot set
    the anchor today; opened (monkeypatched), a transform dropping the decision is refused and the
    page is left as it was. NEGATIVE: a plain refresh of the same decided page passes."""
    from vinci.dossier import refresh

    t = _decided_live()
    folder = tmp_path / "dossiers" / t
    folder.mkdir(parents=True)
    for f in ("dossier.json", "dossier.md"):
        shutil.copy(DOSS / t / f, folder / f)
    path = folder / "dossier.json"
    text = path.read_text()
    refresh.refresh_dossier(path)          # NEGATIVE first: an ordinary refresh is never refused
    assert path.read_text() == text
    monkeypatch.setattr(refresh, "_TOP_LEVEL_REFRESHABLE",
                        refresh._TOP_LEVEL_REFRESHABLE | {"anchor"})

    def drop(doc: dict[str, Any]) -> dict[str, Any]:
        a = {k: v for k, v in doc["anchor"].items()
             if k not in {"operator_decision", "machine_recipe_hint"}}
        return {"anchor": a}

    with pytest.raises(DecisionWriteError, match="drop"):
        refresh.refresh_dossier(path, top_level=drop)
    assert path.read_text() == text


def test_a_placeholder_machine_hint_is_a_gap_not_a_disagreement() -> None:
    """FINDING 4. EDGAR fails during a rebuild of a decided page, and the machine writes `unknown`:
    that is a data gap, as it is on an undecided page — never "the machine reads unknown". The
    decision stands, the note says NO MACHINE READ, and the page prints the gap, not the flag."""
    case = FIX["AMZN"]
    for hint in sorted(PLACEHOLDER_HINTS):
        gap = Anchor.model_validate({**case["rebuilt"], "recipe_hint": hint})
        kept, notes = preserve_operator_tag(Anchor.model_validate(_decided(case)), gap)
        assert kept.recipe_hint == case["decision"]["recipe"]
        assert kept.machine_recipe_hint == hint
        assert not [n for n in notes if n.startswith("DIVERGES")], notes
        assert [n for n in notes if n.startswith("NO MACHINE READ")], notes
        md = "\n".join(_screening_context_lines(kept))
        assert DIVERGES not in md and "a data gap, not a disagreement" in md
    # NEGATIVE: a real recipe that differs is still a divergence
    split = Anchor.model_validate({**case["rebuilt"], "recipe_hint": "R3_forward_pe"})
    _, notes = preserve_operator_tag(Anchor.model_validate(_decided(case)), split)
    assert [n for n in notes if n.startswith("DIVERGES")], notes


def test_the_web_twin_knows_the_same_placeholders(tmp_path: Path) -> None:
    """The web page's placeholder list IS the Python set (a twin pinned, never trusted), and the
    web page prints the gap — not the flag — for each."""
    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    m = re.search(r"const PLACEHOLDER_HINTS = \[(.*?)\];", js)
    assert m is not None and set(re.findall(r'"([^"]+)"', m.group(1))) == set(PLACEHOLDER_HINTS)
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    page = json.loads((ROOT / "frontend" / "dossiers" / "AMZN.json").read_text())
    for hint in sorted(PLACEHOLDER_HINTS):
        page["anchor"]["machine_recipe_hint"] = hint
        (tmp_path / f"{hint}.json").write_text(json.dumps(page))
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const out = {{}};
for (const h of {json.dumps(sorted(PLACEHOLDER_HINTS))}) {{
  const html = renderDossier(JSON.parse(readFileSync("{tmp_path}/" + h + ".json")), null, null);
  out[h] = {{ gap: html.includes("a data gap, not a disagreement"),
             flag: html.includes("The machine reads ") }};
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout)
    assert res == {h: {"gap": True, "flag": False} for h in PLACEHOLDER_HINTS}, res


@pytest.mark.parametrize("given", ["10/22/2026", "2026-13-01", "yesterday", "2026-10-22T09:00"])
def test_a_decision_date_is_an_iso_date_or_refused(given: str, tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """FINDING 5: a non-ISO `--decided-on` was stored in a field documented as ISO."""
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    text = path.read_text()
    committed = Dossier.model_validate_json(text).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, committed.recipe_hint))
    reason = tmp_path / "why.txt"
    reason.write_text("a reason")
    rc = cli._cmd_anchor_retag(_retag_args(t, recipe="R3_forward_pe", reason_file=str(reason),
                                           decided_by="operator", source_ref="x",
                                           decided_on=given))
    assert rc == 1 and path.read_text() == text


def test_today_is_the_operators_calendar_and_never_the_future(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FINDING 5: just after local midnight the operator's today is UTC's tomorrow. A decision
    dated the operator's today is made NOW (the machine's read is recorded), never read as
    backdated; a date after it is refused."""
    class _Day(date):
        @classmethod
        def today(cls) -> _Day:
            return cls(2031, 1, 2)          # a local date no UTC clock reads today

    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    text = path.read_text()
    committed = Dossier.model_validate_json(text).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, committed.recipe_hint))
    monkeypatch.setattr(cli, "date", _Day)
    reason = tmp_path / "why.txt"
    reason.write_text("a reason")
    kw = {"recipe": "R3_forward_pe", "reason_file": str(reason), "decided_by": "operator",
          "source_ref": "x"}
    assert cli._cmd_anchor_retag(_retag_args(t, decided_on="2031-01-03", **kw)) == 1
    assert path.read_text() == text
    assert cli._cmd_anchor_retag(_retag_args(t, decided_on="2031-01-02", **kw)) == 0
    dec = json.loads(path.read_text())["anchor"]["operator_decision"]
    assert dec["decided_on"] == "2031-01-02"
    assert dec["machine_recipe_at_decision"] == committed.recipe_hint


@contextmanager
def _process_zone(offset_hours: int) -> Iterator[None]:
    """The process's LOCAL zone — what `date.today()` reads — at a fixed UTC offset, restored on
    exit. A POSIX TZ string, so no tz database is needed; its sign is inverted: `<+14>-14` is
    UTC+14."""
    old = os.environ.get("TZ")
    os.environ["TZ"] = f"<{offset_hours:+03d}>{-offset_hours:+d}"
    time.tzset()
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old
        time.tzset()


def test_a_decision_made_now_is_dated_on_the_local_calendar_under_a_real_zone(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE NIGHTLY FLAKE (2026-10-24): the first re-tag pin expected UTC's date while the command
    dates the operator's, so it was red every night from local midnight to UTC's (00:00–05:30 IST)
    and green in CI, which runs in UTC. The `_Day` pin above patches `date` and drives an EXPLICIT
    date; this one sets the process's REAL zone and drives the DEFAULT — no `--decided-on` — always
    in the divergent case: UTC−12 reads yesterday until 12:00 UTC and UTC+14 reads tomorrow from
    10:00 UTC, and switching at 11:00 keeps the zone's own midnight an hour from the run."""
    now = datetime.now(UTC)
    offset = -12 if now.hour < 11 else 14
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    committed = Dossier.model_validate_json(path.read_text()).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, committed.recipe_hint))
    reason = tmp_path / "why.txt"
    reason.write_text("a reason")
    with _process_zone(offset):
        local_today = datetime.now(timezone(timedelta(hours=offset))).date()
        assert date.today() == local_today != now.date(), "the run is not the divergent case"
        rc = cli._cmd_anchor_retag(_retag_args(t, recipe="R3_forward_pe", reason_file=str(reason),
                                               decided_by="operator", source_ref="x"))
    assert rc == 0
    dec = json.loads(path.read_text())["anchor"]["operator_decision"]
    assert dec["decided_on"] == local_today.isoformat(), "dated on UTC's calendar"
    assert dec["machine_recipe_at_decision"] == committed.recipe_hint, "made now, read as backdated"


@pytest.mark.parametrize("typed", [False, True])
def test_a_decision_made_as_local_midnight_passes_is_still_made_now(
        typed: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE DOUBLE READ (found in #794's review): the command read the local date once for the stamp
    and the future check, and AGAIN after the machine's EDGAR read to ask whether the decision is
    made now. A decision made as local midnight passed during that read was dated by the first
    day and judged by the second, so it read as backdated and lost the machine's read at decision
    — defaulted or typed as today. The clock is real: the process's zone moves to UTC+14 during
    the stubbed EDGAR read, which steps the local date forward at any hour. It starts at UTC−12,
    or at UTC from 11:00 to 13:00 UTC, so the start zone's own midnight is an hour from the run."""
    start_offset = 0 if 11 <= datetime.now(UTC).hour < 13 else -12
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    committed = Dossier.model_validate_json(path.read_text()).anchor
    assert committed is not None
    fresh = _machine_only(committed, committed.recipe_hint)
    _stub_cli(monkeypatch, tmp_path, fresh)
    after_read: list[date] = []

    def _read_across_midnight(*a: Any, **k: Any) -> Anchor:
        os.environ["TZ"] = "<+14>-14"
        time.tzset()
        after_read.append(date.today())
        return fresh

    monkeypatch.setattr(cli, "_machine_anchor", _read_across_midnight)
    reason = tmp_path / "why.txt"
    reason.write_text("a reason")
    with _process_zone(start_offset):
        start = date.today()
        rc = cli._cmd_anchor_retag(_retag_args(
            t, recipe="R3_forward_pe", reason_file=str(reason), decided_by="operator",
            source_ref="x", decided_on=start.isoformat() if typed else None))
    assert rc == 0
    assert after_read and after_read[0] > start, "local midnight did not pass during the read"
    dec = json.loads(path.read_text())["anchor"]["operator_decision"]
    assert dec["decided_on"] == start.isoformat(), "dated after the read, not when it was made"
    assert dec["machine_recipe_at_decision"] == committed.recipe_hint, "made now, read as backdated"


@pytest.mark.parametrize("blank", ["decided_by", "source_ref", "recipe"])
def test_a_blank_field_is_a_missing_field(blank: str, tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    """FINDING 6: whitespace passed the missing-argument check and was stored as ''."""
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    text = path.read_text()
    committed = Dossier.model_validate_json(text).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, committed.recipe_hint))
    reason = tmp_path / "why.txt"
    reason.write_text("a reason")
    kw = {"recipe": "R3_forward_pe", "reason_file": str(reason), "decided_by": "operator",
          "source_ref": "x", blank: "   "}
    assert cli._cmd_anchor_retag(_retag_args(t, **kw)) == 1
    assert path.read_text() == text
    # ...and a padded field is stored as the words, never with the padding
    kw = {**kw, "recipe": " R3_forward_pe ", "decided_by": "  operator ", "source_ref": " x  "}
    assert cli._cmd_anchor_retag(_retag_args(t, **kw)) == 0
    dec = json.loads(path.read_text())["anchor"]["operator_decision"]
    stored = (dec["recipe"], dec["decided_by"], dec["source_ref"])
    assert stored == ("R3_forward_pe", "operator", "x"), stored


def test_a_page_that_will_not_rerender_fails_the_command_loud(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """FINDING 7: the JSON is written; a re-render that raises is reported and the command fails —
    the backfill's treatment (review of #536), never a traceback hiding which half landed."""
    from vinci.dossier import refresh

    t = _decided_live()
    path = _copy_page(tmp_path, t)
    committed = Dossier.model_validate_json(path.read_text()).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, "R1_midcycle_margin_evebitda"))

    def boom(_p: Path) -> bool:
        raise RuntimeError("render failed")

    monkeypatch.setattr(refresh, "_rerender_only", boom)
    assert cli._cmd_anchor_retag(_retag_args(t, retire=True)) == 1
    assert "could NOT be re-rendered" in capsys.readouterr().err
    assert "operator_decision" not in json.loads(path.read_text())["anchor"], "JSON not written"


def test_the_machine_read_at_decision_must_be_a_recipe(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """FINDING 8's neighbour: the recipes are read off their constants, and a stated machine read
    must be one of them (or a placeholder) — never free text in the sealed block."""
    assert set(cli._decidable_recipes()).isdisjoint(PLACEHOLDER_HINTS)
    t = _undecided_live()
    path = _copy_page(tmp_path, t)
    text = path.read_text()
    committed = Dossier.model_validate_json(text).anchor
    assert committed is not None
    _stub_cli(monkeypatch, tmp_path, _machine_only(committed, committed.recipe_hint))
    reason = tmp_path / "why.txt"
    reason.write_text("a reason")
    kw = {"recipe": "R3_forward_pe", "reason_file": str(reason), "decided_by": "operator",
          "source_ref": "x", "decided_on": "2026-10-01"}
    assert cli._cmd_anchor_retag(_retag_args(t, machine_at_decision="R1-ish", **kw)) == 1
    assert path.read_text() == text
    assert cli._cmd_anchor_retag(_retag_args(t, machine_at_decision="unknown", **kw)) == 0
