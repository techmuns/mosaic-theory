"""`python -m vinci.evals run` as the vote-rule design's measurement needs it (record
`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §7, §8 step 2): one request per page,
drawn as SEPARATE BUILDS under a registration written before any draw.

Before this PR `run` captured with no transform (it defined no ``--transform``, so
``getattr(a, "transform", [])`` was always ``[]``), read its inputs at the default CIQ root (no
``--ciq-root``), checked no request pin (no registration) and recorded no time between builds.
Every test here fails on main `9da0d096`: the module does not exist there, and `run` refuses the
new flags or draws unregistered.

The pages are real committed ones; only the transcripts and the comps export (licensed, never in
CI) are stubbed, and the capture child runs in-process (`replay.capture`) for speed — one test
keeps the real child (`capture_at`).
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.evals import __main__ as cli
from vinci.evals import replay as rp

ROOT = Path(__file__).resolve().parents[1]
TRANSFORMS = ("relabel_drawdown_shape", "survival_read", "gap_types")


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    return page


class _FakeSdk:
    """The SDK object: counts calls; the first writes the prompt cache, the rest read it."""

    def __init__(self) -> None:
        self.calls = 0
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        usage = SimpleNamespace(input_tokens=24, output_tokens=7000,
                                cache_creation_input_tokens=190000 if self.calls == 1 else 0,
                                cache_read_input_tokens=0 if self.calls == 1 else 190000)
        block = SimpleNamespace(type="tool_use",
                                input={"evidence_balance": "strongly-bullish — fake"})
        return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                               stop_reason="tool_use")


@pytest.fixture()
def inputs(monkeypatch: pytest.MonkeyPatch, nflx: dict[str, Any]) -> dict[str, list[Any]]:
    """The frozen inputs, stubbed at the two licensed reads, and the capture child in-process.
    Records where each read was pointed and what each capture was asked for."""
    seen: dict[str, list[Any]] = {"panel_root": [], "comps_root": [], "captured": []}

    def panel_inputs(ticker: str, *, panel: Any = None,
                     ciq_root: Path = rp.DEFAULT_CIQ_ROOT) -> tuple[dict[str, Any], None]:
        seen["panel_root"].append(ciq_root)
        return nflx, None

    def comps_export(ticker: str, *, ciq_root: Path = rp.DEFAULT_CIQ_ROOT) -> None:
        seen["comps_root"].append(ciq_root)
        return None

    def capture_at(code_ref: str, page: dict[str, Any], transcript: str | None, *,
                   draws: int = 5, transforms: Any = (), comps: Path | None = None,
                   **kw: Any) -> rp.Request:
        seen["captured"].append((code_ref, tuple(transforms), draws))
        return rp.capture(page, transcript, draws=draws, transforms=transforms, comps=comps)

    monkeypatch.setattr(rp, "panel_inputs", panel_inputs)
    monkeypatch.setattr(rp, "comps_export", comps_export)
    monkeypatch.setattr(rp, "capture_at", capture_at)
    return seen


def _budget(tmp_path: Path, cap: float = 20.0) -> rp.Budget:
    return rp.Budget.open(tmp_path / "ledger.jsonl", cap_usd=cap, approval="operator: test")


def _register(tmp_path: Path, **over: Any) -> Any:
    from vinci.evals import builds as bd
    kw: dict[str, Any] = {"code_ref": "HEAD", "pages": ("NFLX",), "transforms": TRANSFORMS,
                          "draws": 3, "builds": 2, "min_gap_s": 300.0,
                          "ciq_root": tmp_path / "ciq"}
    kw.update(over)
    return bd.register_run(**kw)


class _Clock:
    def __init__(self, t: float = 1_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def _rows(tmp_path: Path, key: str) -> list[dict[str, Any]]:
    rows = [json.loads(x) for x in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    return [r[key] for r in rows if key in r]


# --------------------------------------------------- 1. the registration pins the request


def test_register_run_pins_each_page_request_with_its_transforms_and_ciq_root(
        tmp_path: Path, nflx: dict[str, Any], inputs: dict[str, list[Any]]) -> None:
    """(+) The request is captured with the transforms, at the code ref resolved to a commit,
    from inputs read at the given CIQ root; its sha256 is pinned and survives a round trip."""
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    want = rp.capture(nflx, None, draws=3, transforms=TRANSFORMS)
    assert reg.requests == {"NFLX": bd.request_sha(want)}
    assert reg.transforms == TRANSFORMS and len(reg.code_ref) == 40
    assert inputs["captured"] == [(reg.code_ref, TRANSFORMS, 3)]
    assert inputs["panel_root"] == [tmp_path / "ciq"] and inputs["comps_root"] == [tmp_path / "ciq"]
    assert bd.RunRegistration.from_json(reg.to_json()).sha == reg.sha
    # (-) the transforms are in the pin: the same page without them is another request
    assert bd.request_sha(rp.capture(nflx, None, draws=3)) != reg.requests["NFLX"]


def test_a_registration_refuses_a_gap_inside_the_cache_lifetime(tmp_path: Path) -> None:
    """(-) Builds closer than the prompt cache's five minutes would open on a cached draw."""
    from vinci.evals import builds as bd
    with pytest.raises(ValueError, match="cache lifetime"):
        bd.RunRegistration(code_ref="a" * 40, transforms=(), pages=("NFLX",), draws=3, builds=2,
                           min_gap_s=120.0, requests={"NFLX": "x"})


# --------------------------------------------------- 2. the CLI: --ciq-root, --transform, paid


def _write_reg(tmp_path: Path) -> tuple[Any, Path]:
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    path = tmp_path / "registration.json"
    bd.write_registration(reg, path)
    return reg, path


def test_run_reads_its_inputs_at_the_given_ciq_root(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(+) `run --ciq-root DIR` reads the transcripts and the comps export there."""
    _, path = _write_reg(tmp_path)
    _budget(tmp_path)
    inputs["panel_root"].clear()
    rc = cli.main(["run", "--registration", str(path), "--ticker", "NFLX", "--build", "1",
                   "--budget-ledger", str(tmp_path / "ledger.jsonl"),
                   "--draws-out", str(tmp_path / "d.jsonl"), "--ciq-root", str(tmp_path / "x")])
    assert rc == 2          # not --paid: captured and checked, nothing drawn
    assert inputs["panel_root"] == [tmp_path / "x"]


def test_run_transform_must_be_the_registration_s(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(-) `run --transform` cannot draw other transforms than the ones registered."""
    _, path = _write_reg(tmp_path)
    _budget(tmp_path)
    with pytest.raises(rp.ReplayError, match="transforms"):
        cli.main(["run", "--registration", str(path), "--ticker", "NFLX", "--build", "1",
                  "--budget-ledger", str(tmp_path / "ledger.jsonl"),
                  "--draws-out", str(tmp_path / "d.jsonl"), "--transform", "gap_types"])
    # (+) the registration's own transforms, given in full, are accepted
    args = ["run", "--registration", str(path), "--ticker", "NFLX", "--build", "1",
            "--budget-ledger", str(tmp_path / "ledger.jsonl"),
            "--draws-out", str(tmp_path / "d.jsonl")]
    for t in TRANSFORMS:
        args += ["--transform", t]
    assert cli.main(args) == 2


def test_a_paid_run_needs_a_registration(
        tmp_path: Path, inputs: dict[str, list[Any]], monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) Paid draws only on a registration written before them (RUNBOOKS §n step 4)."""
    drawn: list[Any] = []
    monkeypatch.setattr(rp, "run_request", lambda *a, **k: drawn.append(a) or [])
    _budget(tmp_path)
    with pytest.raises(rp.ReplayError, match="registration"):
        cli.main(["run", "--ticker", "NFLX", "--budget-ledger", str(tmp_path / "ledger.jsonl"),
                  "--draws-out", str(tmp_path / "d.jsonl"), "--label", "x", "--paid"])
    assert drawn == []


# --------------------------------------------------- 3. a build is drawn once, in order, pinned


def test_a_build_is_drawn_once(tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    budget, sdk = _budget(tmp_path), _FakeSdk()
    bd.run_build(reg, "NFLX", 1, budget=budget, draws_out=tmp_path / "d.jsonl",
                 ciq_root=tmp_path / "ciq", sdk=sdk, clock=_Clock())
    assert sdk.calls == 3
    with pytest.raises(rp.ReplayError, match="drawn once"):
        bd.run_build(reg, "NFLX", 1, budget=budget, draws_out=tmp_path / "d.jsonl",
                     ciq_root=tmp_path / "ciq", sdk=sdk, clock=_Clock(10_000.0))
    assert sdk.calls == 3


def test_a_build_whose_request_moved_is_refused_before_any_draw(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    moved = bd.RunRegistration(**{**reg.__dict__, "requests": {"NFLX": "0" * 64}})
    budget, sdk = _budget(tmp_path), _FakeSdk()
    with pytest.raises(rp.ReplayError, match="registered bytes"):
        bd.run_build(moved, "NFLX", 1, budget=budget, draws_out=tmp_path / "d.jsonl",
                     ciq_root=tmp_path / "ciq", sdk=sdk, clock=_Clock())
    assert sdk.calls == 0 and _rows(tmp_path, "build_start") == []


def test_a_page_s_builds_go_in_order_and_stay_inside_the_registration(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    budget, sdk = _budget(tmp_path), _FakeSdk()
    kw: dict[str, Any] = {"budget": budget, "draws_out": tmp_path / "d.jsonl",
                          "ciq_root": tmp_path / "ciq", "sdk": sdk, "clock": _Clock()}
    with pytest.raises(rp.ReplayError, match="build 1"):
        bd.run_build(reg, "NFLX", 2, **kw)
    with pytest.raises(rp.ReplayError, match="registers 2 builds"):
        bd.run_build(reg, "NFLX", 3, **kw)
    with pytest.raises(rp.ReplayError, match="not a registered page"):
        bd.run_build(reg, "LLY", 1, **kw)
    assert sdk.calls == 0


# --------------------------------------------------- 4. the gap between a page's builds


def test_the_gap_since_the_page_s_last_build_is_recorded_and_a_short_one_refused(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(+/-) Build 2 of a page starts at least `min_gap_s` after build 1's last draw, so it opens
    past the prompt cache's lifetime; the gap is written into the ledger, not assumed."""
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    budget, sdk, clock = _budget(tmp_path), _FakeSdk(), _Clock(1_000.0)
    kw: dict[str, Any] = {"budget": budget, "draws_out": tmp_path / "d.jsonl",
                          "ciq_root": tmp_path / "ciq", "sdk": sdk, "clock": clock}
    bd.run_build(reg, "NFLX", 1, **kw)
    (end,) = _rows(tmp_path, "build_end")
    assert end["ticker"] == "NFLX" and end["build"] == 1 and end["t"] == 1_000.0
    clock.t = 1_000.0 + 299.0
    with pytest.raises(rp.ReplayError, match="299"):
        bd.run_build(reg, "NFLX", 2, **kw)
    assert sdk.calls == 3
    clock.t = 1_000.0 + 301.0
    bd.run_build(reg, "NFLX", 2, **kw)
    starts = _rows(tmp_path, "build_start")
    assert [s["build"] for s in starts] == [1, 2]
    assert starts[0]["gap_s"] is None and starts[1]["gap_s"] == pytest.approx(301.0)


def test_the_first_draw_s_cache_state_is_recorded(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(+) The end row carries the first draw's cache-read tokens from the ledger the guard
    wrote: 0 is an uncached opening, shown rather than assumed."""
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    bd.run_build(reg, "NFLX", 1, budget=_budget(tmp_path), draws_out=tmp_path / "d.jsonl",
                 ciq_root=tmp_path / "ciq", sdk=_FakeSdk(), clock=_Clock())
    (end,) = _rows(tmp_path, "build_end")
    assert end["first_draw_cache_read"] == 0 and end["usable"] == 3 and end["draws"] == 3


def test_the_end_row_is_written_when_a_build_stops(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(-) A build the cap stops still records its end, so the next build's gap is measured from
    its last draw rather than refused as unknowable."""
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    budget = _budget(tmp_path, cap=2.0)
    with pytest.raises(rp.BudgetStop):
        bd.run_build(reg, "NFLX", 1, budget=budget, draws_out=tmp_path / "d.jsonl",
                     ciq_root=tmp_path / "ciq", sdk=_FakeSdk(), clock=_Clock())
    (end,) = _rows(tmp_path, "build_end")
    assert end["build"] == 1 and end["stopped"]


def test_run_build_captures_through_the_real_child_at_the_registered_ref(
        tmp_path: Path, nflx: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Without the in-process stand-in: `capture_at` runs the registered commit's code in a
    child and the pin matches the in-process capture of the same code."""
    from vinci.evals import builds as bd
    monkeypatch.setattr(rp, "panel_inputs", lambda t, **k: (nflx, None))
    monkeypatch.setattr(rp, "comps_export", lambda t, **k: None)
    reg = bd.register_run(code_ref="HEAD", pages=("NFLX",), transforms=("relabel_drawdown_shape",),
                          draws=2, builds=2, min_gap_s=300.0, ciq_root=tmp_path)
    head = rp.capture(nflx, None, draws=2, transforms=("relabel_drawdown_shape",))
    assert reg.requests == {"NFLX": bd.request_sha(head)}


# --------------------------------------------------- 5. review round 0 (`/code-review high --fix`)


def test_run_reads_at_the_registered_ciq_root_when_none_is_given(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(+) `run` without --ciq-root reads where the registration was captured, not at the
    assembler's default: the registration records its root, and a run reads the same inputs."""
    reg, path = _write_reg(tmp_path)
    _budget(tmp_path)
    inputs["panel_root"].clear()
    rc = cli.main(["run", "--registration", str(path), "--ticker", "NFLX", "--build", "1",
                   "--budget-ledger", str(tmp_path / "ledger.jsonl"),
                   "--draws-out", str(tmp_path / "d.jsonl")])
    assert rc == 2
    assert [Path(p).resolve() for p in inputs["panel_root"]] == [Path(reg.inputs["ciq_root"])]
    assert rp.DEFAULT_CIQ_ROOT not in inputs["panel_root"]


# --------------------------------------------------- 5. one approval draws a request once


def test_a_request_drawn_under_one_registration_is_refused_under_another(
        tmp_path: Path, inputs: dict[str, list[Any]]) -> None:
    """(-) Review round 0: a second registration of the same request (a reworded note gives it a
    new sha) cannot draw it again under the same approval — the design is drawn once, as
    `compare.run_compare` refuses a design already drawn whatever its note."""
    from vinci.evals import builds as bd
    first = _register(tmp_path, note="first")
    again = _register(tmp_path, note="reworded")
    assert first.sha != again.sha and first.requests == again.requests
    budget, sdk, clock = _budget(tmp_path), _FakeSdk(), _Clock(1_000.0)
    kw: dict[str, Any] = {"budget": budget, "draws_out": tmp_path / "d.jsonl",
                          "ciq_root": tmp_path / "ciq", "sdk": sdk, "clock": clock}
    bd.run_build(first, "NFLX", 1, **kw)
    clock.t += 10_000.0
    with pytest.raises(rp.ReplayError, match="drawn once"):
        bd.run_build(again, "NFLX", 1, **kw)
    assert sdk.calls == 3


def test_two_runs_cannot_draw_one_build_at_once(
        tmp_path: Path, inputs: dict[str, list[Any]], nflx: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) Review round 0: the check and the claim are one step. A second `run` of the same build
    that starts while the first is still capturing is refused, rather than both passing the
    drawn-once check and both drawing."""
    from vinci.evals import builds as bd
    reg = _register(tmp_path)
    budget, sdk = _budget(tmp_path), _FakeSdk()
    kw: dict[str, Any] = {"budget": budget, "draws_out": tmp_path / "d.jsonl",
                          "ciq_root": tmp_path / "ciq", "sdk": sdk, "clock": _Clock()}
    inner: list[BaseException] = []
    entered: list[bool] = []
    real = rp.capture_at

    def capture_at(*a: Any, **k: Any) -> rp.Request:
        if not entered:   # the other terminal, starting while this one captures
            entered.append(True)
            try:
                bd.run_build(reg, "NFLX", 1, **kw)
                inner.append(AssertionError("the second run drew"))
            except rp.ReplayError as exc:
                inner.append(exc)
        return real(*a, **k)

    monkeypatch.setattr(rp, "capture_at", capture_at)
    bd.run_build(reg, "NFLX", 1, **kw)
    (exc,) = inner
    assert isinstance(exc, rp.ReplayError) and "another run" in str(exc)
    assert sdk.calls == 3
