"""Fix request 2, order 8 — round 2 of #1030's review (2026-11-12, at 3640be07: the coordinator's
independent review, its repro scripts `shop_e2e.py`, `mutate_cli.py`, `spellings.py`,
`two_checkouts.py` and `judge_test.py`, and the operator's rulings of 2026-11-12 on F3, "Refuse by
request pins (Recommended)", and F4, "One drawing machine (Recommended)").

Each FIX's test fails on 3640be07 for its finding's own reason; each PIN names the mutant it
kills. $0: no key, no network. A paid path runs with the client class spied, so a refusal is shown
to come before any client exists, and a draw that passes every refusal is shown to reach the
client, where the spy stops it. The CLI's tests run the real commands against an index in a
temporary repository; this repository's own index is checked unchanged after each.
"""
from __future__ import annotations

import dataclasses
import functools
import json
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests.test_evals_order8 import (
    BASE_953,
    CAND_953,
    _a_build_run,
    _a_comparison,
    _impact_export,
    _indexed,
    _page,
    _repo_with_index,
    _to_main,
)
from tests.test_evals_order8_gaps import _budget, _Spy
from vinci.evals import compare as cm
from vinci.evals import registry
from vinci.evals.replay import ReplayError

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def spy(monkeypatch: pytest.MonkeyPatch) -> type[_Spy]:
    from vinci.evals import replay as rp
    _Spy.built = 0
    monkeypatch.setattr(rp, "AnthropicLlmClient", _Spy)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return _Spy


@pytest.fixture()
def index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """The CLI's index is a temporary repository's (its origin/main empty until `_to_main`), the
    local `.env` is not read, and RG-D12 is stood in: the impact export's BASE is #953's, whose
    production files are not this checkout's (RG-D12's own pins are in the order-8 modules)."""
    from tests.evals_scorer_stub import fingerprint_only
    from vinci import config
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    monkeypatch.setattr(cm, "fixed_scorer", lambda base, **k: (cm.scorer_fingerprint(), head))
    monkeypatch.setattr(cm, "refuse_unless_scored_by_base",
                        lambda base_ref, **k: cm.scorer_fingerprint())
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", fingerprint_only)
    monkeypatch.setattr(config, "load_local_env", lambda *a, **k: None)
    repo = _repo_with_index(tmp_path / "index", [])
    for name in ("record_registered", "require_on_main", "claim_draw"):
        monkeypatch.setattr(registry, name, functools.partial(getattr(registry, name), root=repo))
    before = (ROOT / registry.INDEX).read_bytes()
    yield repo
    assert (ROOT / registry.INDEX).read_bytes() == before, "the repository's own index moved"


def _register(export: Path, ledger: Path, out: Path, *flags: str) -> Any:
    """`register --from-impact`, through the CLI."""
    from vinci.evals import __main__ as cli
    assert cli.main(["register", "--from-impact", str(export), *flags, "--budget-ledger",
                     str(ledger), "--out", str(out)]) == 0
    return cm.Registration.from_json(out.read_text())


def _run_compare(registration: Path, ledger: Path, out_dir: Path) -> int:
    """`run-compare --paid`, through the CLI."""
    from vinci.evals import __main__ as cli
    return cli.main(["run-compare", "--registration", str(registration), "--budget-ledger",
                     str(ledger), "--out-dir", str(out_dir), "--paid"])


def _approvals(tmp_path: Path) -> tuple[Path, Path]:
    return _budget(tmp_path, "approval-1").ledger, _budget(tmp_path, "approval-2").ledger


# ------------------------- F1: the CLI's design wiring, end to end; the claim derives the key


def test_one_design_registered_twice_through_the_cli_is_drawn_once(
        tmp_path: Path, spy: type[_Spy], index: Path) -> None:
    """PIN, the reviewer's CLI mutant (`mutate_cli.py`: `register` writing `design=reg.sha` for
    `design=cm.draw_key(reg)`). Every item-1 test wrote its keys by hand, and the CLI's one pin
    grepped its source for "design=", so the mutant survived all 363 evals, git-ref and RG-D20
    tests while `shop_e2e.py` drew one design under two approvals. End to end (TEST-LAYER RULE):
    the CLI registers one design twice, under two approvals and two notes; (+) the first is drawn
    — it reaches the client, which the spy stops; (−) the second is refused before any client."""
    export, _ = _impact_export(tmp_path)
    l1, l2 = _approvals(tmp_path)
    r1 = _register(export, l1, tmp_path / "r1.json", "--no-worsening", "--note", "first words")
    r2 = _register(export, l2, tmp_path / "r2.json", "--no-worsening", "--note", "new words")
    assert r1.sha != r2.sha and not cm.design_differs(r1, r2)
    _to_main(index)
    with pytest.raises(AssertionError, match="paid client"):
        _run_compare(tmp_path / "r1.json", l1, tmp_path / "run1")
    assert spy.built == 1
    with pytest.raises(ReplayError, match="design was already drawn"):
        _run_compare(tmp_path / "r2.json", l2, tmp_path / "run2")
    assert spy.built == 1


@pytest.mark.parametrize("field", ["design", "pins"])
def test_a_draw_whose_indexed_row_is_not_its_registration_is_refused(
        tmp_path: Path, spy: type[_Spy], index: Path, field: str) -> None:
    """(−) F1: `claim_draw` read the key its row recorded and never derived it from the
    registration it was drawing, so a row written with the wrong key — the CLI mutant wrote the
    registration's own sha — made a twin a design of its own. The claim now derives the design and
    the request pins from the registration and refuses a row that disagrees, before any client.
    On 3640be07 the draw reached the client."""
    export, _ = _impact_export(tmp_path)
    l1, _ = _approvals(tmp_path)
    r1 = _register(export, l1, tmp_path / "r1.json", "--no-worsening")
    path = index / registry.INDEX
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    assert rows[-1]["design"] == cm.draw_key(r1)
    rows[-1][field] = r1.sha if field == "design" else {"NFLX:BASE": "0" * 64}
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    _to_main(index)
    with pytest.raises(ReplayError, match="disagree"):
        _run_compare(tmp_path / "r1.json", l1, tmp_path / "run1")
    assert spy.built == 0


def _builds_through_the_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`register-run` and `run` capture in-process from NFLX's committed page: the frozen inputs'
    two licensed reads and the capture child are stood in, as `test_evals_run_builds` does."""
    from vinci.evals import replay as rp
    page = _page("NFLX")
    monkeypatch.setattr(rp, "panel_inputs", lambda t, **k: (page, None))
    monkeypatch.setattr(rp, "comps_export", lambda t, **k: None)
    monkeypatch.setattr(rp, "capture_at", lambda ref, p, tx, *, draws=5, transforms=(),
                        comps=None, **k: rp.capture(p, tx, draws=draws, transforms=transforms,
                                                    comps=comps))


@pytest.mark.parametrize(("second", "refusal"), [
    (["--note", "new words"], "design was already drawn"),   # PIN: the CLI mutant, register-run
    (["--min-gap-s", "301"], "every request"),               # FIX, F3: another design, same bytes
])
def test_a_build_design_or_its_bytes_registered_again_through_the_cli_is_refused(
        tmp_path: Path, spy: type[_Spy], index: Path, monkeypatch: pytest.MonkeyPatch,
        second: list[str], refusal: str) -> None:
    """End to end, `register-run` then `run`. (+) The first registration's build reaches the
    client. (−) PIN, the CLI mutant's `register-run` half (`design=breg.sha`): the same design
    with new words is refused. (−) F3: a design one field away (`--min-gap-s 301`) pinning the
    same request bytes is refused too — on 3640be07 it was drawn, as any harness commit or a
    build's code ref let the same bytes be drawn again under a new approval."""
    from vinci.evals import __main__ as cli
    _builds_through_the_cli(tmp_path, monkeypatch)
    l1, l2 = _approvals(tmp_path)
    common = ["register-run", "--code-ref", "HEAD", "--ticker", "NFLX", "--draws", "2",
              "--builds", "2", "--ciq-root", str(tmp_path / "ciq")]
    assert cli.main([*common, "--note", "first words", "--budget-ledger", str(l1),
                     "--out", str(tmp_path / "r1.json")]) == 0
    assert cli.main([*common, *second, "--budget-ledger", str(l2),
                     "--out", str(tmp_path / "r2.json")]) == 0
    _to_main(index)

    def run(n: int, ledger: Path) -> int:
        return cli.main(["run", "--registration", str(tmp_path / f"r{n}.json"), "--ticker",
                         "NFLX", "--build", "1", "--budget-ledger", str(ledger), "--draws-out",
                         str(tmp_path / f"d{n}.jsonl"), "--paid"])
    with pytest.raises(AssertionError, match="paid client"):
        run(1, l1)
    assert spy.built == 1
    with pytest.raises(ReplayError, match=refusal):
        run(2, l2)
    assert spy.built == 1


# ------------------------------------------- F3: one set of request bytes, drawn once (CLI)


@pytest.mark.parametrize("how", ["a design field", "a harness commit"])
def test_the_same_request_bytes_registered_as_another_design_are_not_drawn_again(
        tmp_path: Path, spy: type[_Spy], index: Path, monkeypatch: pytest.MonkeyPatch,
        how: str) -> None:
    """(−) F3 (operator 2026-11-12: "Refuse by request pins (Recommended)" — "Closes the gap at
    the byte level"). The design key carries the scorer's fingerprint, so a commit to the harness
    gave byte-identical requests a new design, and a second approval drew them again; so did any
    other design field (here a target for no-worsening). Every request the second registration
    pins was already drawn under the first, so it is refused before any client. On 3640be07 it
    was drawn."""
    export, _ = _impact_export(tmp_path)
    l1, l2 = _approvals(tmp_path)
    real = cm.scorer_fingerprint
    harness: dict[str, str | None] = {"fingerprint": None}
    monkeypatch.setattr(cm, "scorer_fingerprint",
                        lambda *a, **k: harness["fingerprint"] or real(*a, **k))
    r1 = _register(export, l1, tmp_path / "r1.json", "--no-worsening")
    if how == "a harness commit":
        harness["fingerprint"] = "e" * 64
        r2 = _register(export, l2, tmp_path / "r2.json", "--no-worsening")
        assert cm.design_differs(r1, r2) == ["scorer"]
    else:
        r2 = _register(export, l2, tmp_path / "r2.json", "--target", "M-LABEL")
        assert "targets" in cm.design_differs(r1, r2)
    assert r1.requests == r2.requests
    _to_main(index)
    second = harness["fingerprint"]
    harness["fingerprint"] = None
    with pytest.raises(AssertionError, match="paid client"):
        _run_compare(tmp_path / "r1.json", l1, tmp_path / "run1")
    harness["fingerprint"] = second
    with pytest.raises(ReplayError, match="every request"):
        _run_compare(tmp_path / "r2.json", l2, tmp_path / "run2")
    assert spy.built == 1


def test_a_registration_with_a_request_not_yet_drawn_is_drawn(tmp_path: Path) -> None:
    """(+) F3's boundary is the ruling's "whole set": a registration with even one request not
    yet drawn is drawn, and a build registration's undrawn page is not counted as drawn."""
    r1 = _a_comparison()
    r3 = dataclasses.replace(r1, requests={"BURL:BASE": "1" * 64, "BURL:CAND": "3" * 64},
                             note="one request is new")
    b1 = _a_build_run(pages=("NFLX", "EPAM"), requests={"NFLX": "4" * 64, "EPAM": "5" * 64})
    b2 = _a_build_run("EPAM's bytes", pages=("EPAM",), requests={"EPAM": "5" * 64},
                      min_gap_s=301.0)
    b3 = dataclasses.replace(b2, min_gap_s=302.0)   # another design, EPAM's same bytes
    repo = _indexed(tmp_path, [(r1, "a1"), (r3, "a2"), (b1, "a1"), (b2, "a2"), (b3, "a2")])
    registry.claim_draw(r1, approval="a1", root=repo)
    registry.claim_draw(r3, approval="a2", root=repo)
    registry.claim_draw(b1, approval="a1", unit="NFLX:1", root=repo)
    registry.claim_draw(b2, approval="a2", unit="EPAM:1", root=repo)   # b1 drew NFLX only
    with pytest.raises(ReplayError, match="every request"):            # (−) b2 drew EPAM's
        registry.claim_draw(b3, approval="a2", unit="EPAM:1", root=repo)


def test_a_drawn_registration_whose_row_records_no_pins_stops_every_draw(tmp_path: Path) -> None:
    """(−) The request-pins rule reads what each drawn registration drew. A drawn row whose
    registration records no pins cannot be read, so nothing is drawn rather than checked against
    less than the index holds."""
    old = {"event": "registered", "registration": "o" * 64, "kind": "compare",
           "approval": "a1", "design": "x" * 64}
    repo = _repo_with_index(tmp_path, [old, {"event": "drawn", "registration": "o" * 64,
                                             "approval": "a1", "unit": None}])
    reg = _a_comparison()
    registry.record_registered(reg, approval="a2", root=repo)
    _to_main(repo)
    with pytest.raises(ReplayError, match="no request pins"):
        registry.claim_draw(reg, approval="a2", root=repo)


# ------------------------------------------------------- F2: one spelling per design


def _spelled(monkeypatch: pytest.MonkeyPatch, **k: Any) -> Any:
    monkeypatch.setattr(cm, "refuse_unless_scored_by_base",
                        lambda base_ref, **kw: cm.scorer_fingerprint())   # RG-D12 stood in
    return cm.register(BASE_953, CAND_953, draws=5, **k)


@pytest.mark.parametrize("respelling", ["target pages reordered", "targets reordered",
                                        "no-worsening families reordered"])
def test_one_design_respelled_is_one_design(monkeypatch: pytest.MonkeyPatch,
                                            respelling: str) -> None:
    """(−) F2 (`spellings.py`): the same pages, targets or gated families given in another order
    were another design — `design_differs` named a field and `draw_key` moved — so the index's
    cross-approval refusal and `run_compare`'s per-ledger one both let the same design through.
    The order they are given in draws and decides nothing different."""
    a, b = {
        "target pages reordered": ({"targets": ["M-LABEL"], "pages": ["NFLX", "EPAM"]},
                                   {"targets": ["M-LABEL"], "pages": ["EPAM", "NFLX"]}),
        "targets reordered": ({"targets": ["M-LABEL", "M-ABSENT"], "pages": ["NFLX"]},
                              {"targets": ["M-ABSENT", "M-LABEL"], "pages": ["NFLX"]}),
        "no-worsening families reordered": (
            {"no_worsening": True, "pages": ["NFLX"],
             "no_worsening_families": {"M-LABEL": ["bleed", "trailing-only"]}},
            {"no_worsening": True, "pages": ["NFLX"],
             "no_worsening_families": {"M-LABEL": ["trailing-only", "bleed"]}}),
    }[respelling]
    ra, rb = _spelled(monkeypatch, **a), _spelled(monkeypatch, **b)
    assert cm.design_differs(ra, rb) == [] and cm.draw_key(ra) == cm.draw_key(rb)


def test_one_build_design_with_its_pages_reordered_is_one_design() -> None:
    """(−) F2 for `register-run`: `builds.draw_key` moved with the order of the pages alone."""
    from vinci.evals import builds as bd
    r = _a_build_run(pages=("NFLX", "EPAM"), requests={"NFLX": "1" * 64, "EPAM": "2" * 64})
    assert bd.draw_key(r) == bd.draw_key(dataclasses.replace(r, pages=("EPAM", "NFLX")))
    assert bd.draw_key(r) != bd.draw_key(dataclasses.replace(r, draws=3))   # (+) a real field


def test_a_target_given_twice_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) F2: `M-LABEL, M-LABEL` registered, Holm ran on one target (`target_family` is a dict),
    and the decision said "Holm across 2 target(s)" (`score_run`). A target is registered once."""
    with pytest.raises(ValueError, match="each target is registered once"):
        _spelled(monkeypatch, targets=["M-LABEL", "M-LABEL"], pages=["NFLX"])
    _spelled(monkeypatch, targets=["M-LABEL"], pages=["NFLX"])   # (+) once


def test_reordered_pages_are_not_drawn_twice_under_one_approval(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) F2 within ONE approval: `run_compare`'s own design check read the page order as a design
    field, so the same pages and request bytes registered in the other order were drawn a second
    time under the approval's one ledger. On 3640be07 the second run drew."""
    from tests.evals_scorer_stub import fingerprint_only
    from tests.test_evals_pr2_round2 import _FakeSdk
    from vinci.evals import replay as rp
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", fingerprint_only)
    base = rp.capture(_page("NFLX"), None)
    cand = rp.Request(json.loads(json.dumps({**base.kwargs, "system": base.system + " "})))

    def captured(order: tuple[str, ...]) -> cm.Captured:
        c = cm.Captured(BASE_953, CAND_953, ())
        for t in order:
            c.requests[(t, "BASE")], c.requests[(t, "CAND")] = base, cand
            c.diffs.append(cm.PageDiff(t, False, 0, False, {}, {}))
        return c
    c1, c2 = captured(("NFLX", "EPAM")), captured(("EPAM", "NFLX"))
    r1 = _spelled(monkeypatch, targets=["M-LABEL"], pages=["NFLX", "EPAM"], captured=c1)
    r2 = _spelled(monkeypatch, targets=["M-LABEL"], pages=["EPAM", "NFLX"], captured=c2)
    first = tmp_path / "run1"
    first.mkdir()
    (first / "registration.json").write_text(r1.to_json())
    budget = _budget(tmp_path)
    budget.record({"registration": r1.sha, "out_dir": str(first), "usd": 0.0})
    sdk = _FakeSdk()
    with pytest.raises(ReplayError, match="this design was already drawn under this approval"):
        cm.run_compare(c2, budget=budget, out_dir=tmp_path / "run2", registration=r2, sdk=sdk)
    assert sdk.calls == 0


# --------------------------------------------- F5: the judge's TEST read, once, in the library


def _test_half() -> tuple[list[Any], dict[str, Any]]:
    from vinci.evals import gold as gd
    sub = [g for g in gd.load_gold() if g.half == "test" and g.page == "TECX"]
    return sub, {"TECX": _page("TECX")}


def test_the_library_judge_reads_the_test_half_once_across_approvals(
        tmp_path: Path, spy: type[_Spy]) -> None:
    """(−) F5 (`judge_test.py`): `judge.run_half("test")` under a fresh approval reached the paid
    client, because only the CLI's `judge` command claimed the read (`claim_judge_test`). The
    committed index holds PR 2's read of 2026-11-06, so the library itself refuses a TEST read
    under any other approval, before any client exists. On 3640be07 the spy was built."""
    from vinci.evals import judge as jg
    sub, pages = _test_half()
    before = (ROOT / registry.INDEX).read_bytes()
    with pytest.raises(ReplayError, match="TEST half was already read"):
        jg.run_half("test", budget=_budget(tmp_path), out_dir=tmp_path / "judge", gold=sub,
                    pages=pages)
    assert spy.built == 0 and (ROOT / registry.INDEX).read_bytes() == before


def test_a_first_test_read_is_claimed_by_the_library_before_its_client(
        tmp_path: Path, spy: type[_Spy]) -> None:
    """(+) Under an index that holds no TEST read, `run_half` claims it for its approval and only
    then reaches the client."""
    from vinci.evals import judge as jg
    sub, pages = _test_half()
    repo = _repo_with_index(tmp_path, [])
    b = _budget(tmp_path)
    with pytest.raises(AssertionError, match="paid client"):
        jg.run_half("test", budget=b, out_dir=tmp_path / "judge", gold=sub, pages=pages,
                    root=repo)
    (row,) = registry.working_rows(repo)
    assert (row["event"], row["approval"]) == ("judge_test_read", registry.approval_id(b.ledger))
    assert spy.built == 1
