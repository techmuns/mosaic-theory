"""The vote-rule design's independence measurement, scored by its pre-registered rule
(`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §7; `vinci/evals/independence.py`).

Every test fails on #958's head `31d21828`, where the scorer does not exist. The runs are drawn
through the REAL `builds.run_build` with a scripted SDK, so the scorer reads the rows the guard and
the build ledger actually write; only the licensed inputs are stubbed (as in
`test_evals_run_builds.py`). The χ² tail is checked against its closed form for even degrees of
freedom and against table points, never against the scorer's own output.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.evals import replay as rp

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    return page


@pytest.fixture()
def inputs(monkeypatch: pytest.MonkeyPatch, nflx: dict[str, Any]) -> None:
    def capture_at(code_ref: str, page: dict[str, Any], transcript: str | None, *,
                   draws: int = 5, transforms: Any = (), comps: Path | None = None,
                   **kw: Any) -> rp.Request:
        return rp.capture(page, transcript, draws=draws, transforms=transforms, comps=comps)

    monkeypatch.setattr(rp, "panel_inputs", lambda t, **k: (nflx, None))
    monkeypatch.setattr(rp, "comps_export", lambda t, **k: None)
    monkeypatch.setattr(rp, "capture_at", capture_at)


def _complete(evidence_balance: str) -> dict[str, Any]:
    """A tool output carrying every field the synthesis tool requires (`SYNTHESIS_TOOL`), as a
    usable production draw does."""
    from vinci.dossier.synthesis import SYNTHESIS_TOOL
    body: dict[str, Any] = {k: [] for k in SYNTHESIS_TOOL["input_schema"]["required"]}
    body["decisive_question"] = "q"
    body["evidence_balance"] = evidence_balance
    return body


#: A scripted lean prefixed with this is answered TRUNCATED: the partial tool input carries the
#: lean, and the response stops at max_tokens, which `extract` raises on (a failed draw).
TRUNC = "max_tokens:"
#: A scripted lean prefixed with this is answered with ONLY the evidence balance: the structural
#: fields are missing, which `synthesize` drops as INCOMPLETE (no usable output).
PARTIAL = "partial:"


class _ScriptedSdk:
    """Answers each call with the next lean in ``leans`` ('' answers with no evidence balance)."""

    def __init__(self, leans: list[str], *, warm: bool = False) -> None:
        self.leans, self.calls, self.messages = list(leans), 0, self
        self.warm = warm   # the opening read the cache: a build that did NOT open uncached

    def create(self, **kwargs: Any) -> Any:
        lean = self.leans[self.calls]
        self.calls += 1
        usage = SimpleNamespace(input_tokens=24, output_tokens=700,
                                cache_creation_input_tokens=19000 if self.calls == 1 else 0,
                                cache_read_input_tokens=(19000 if self.calls > 1 or self.warm
                                                         else 0))
        stop = "tool_use"
        if lean.startswith(TRUNC):
            lean, stop = lean[len(TRUNC):], "max_tokens"
            body: dict[str, Any] = {"evidence_balance": f"{lean} — scripted"}
        elif lean.startswith(PARTIAL):
            body = {"evidence_balance": f"{lean[len(PARTIAL):]} — scripted"}
        else:
            body = _complete(f"{lean} — scripted") if lean else {}
        block = SimpleNamespace(type="tool_use", input=body)
        return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                               stop_reason=stop)


B, M, R = "strongly-bullish", "mixed", "strongly-bearish"


def _drawn(tmp_path: Path, builds: list[list[str]], *, complete: bool = True,
           warm: tuple[int, ...] = ()) -> Any:
    """Register NFLX for len(builds) ten-draw builds, draw each through `run_build` with the
    scripted leans, 400 s apart, and return (registration, budget, draws file)."""
    from vinci.evals import builds as bd
    reg = bd.register_run(code_ref="HEAD", pages=("NFLX",), transforms=(), draws=10,
                          builds=len(builds), min_gap_s=300.0, ciq_root=tmp_path / "ciq")
    budget = rp.Budget.open(tmp_path / "ledger.jsonl", cap_usd=50.0, approval="operator: test")
    t = [1_000.0]
    todo = builds if complete else builds[:-1]
    for k, leans in enumerate(todo, start=1):
        bd.run_build(reg, "NFLX", k, budget=budget, draws_out=tmp_path / "d.jsonl",
                     ciq_root=tmp_path / "ciq", sdk=_ScriptedSdk(leans, warm=k in warm),
                     clock=lambda: t[0])
        t[0] += 400.0
    return reg, budget, tmp_path / "d.jsonl"


# --------------------------------------------------------------- 1. the distributions


def test_chi2_tail_equals_its_closed_form_and_the_tables() -> None:
    """(+) For even df the χ² tail is exp(−x/2) Σ_{j<df/2} (x/2)^j / j!; and the familiar 5%
    points (3.841 on 1, 7.815 on 3, 28.869 on 18) read 0.05."""
    from vinci.evals import independence as ind
    for df in (2, 6, 12, 18, 24):
        for x in (0.5, 3.0, 11.0, 28.869, 60.0):
            z = x / 2
            closed = math.exp(-z) * sum(z ** j / math.factorial(j) for j in range(df // 2))
            assert ind.chi2_sf(x, df) == pytest.approx(closed, rel=1e-9, abs=1e-14)
    for x, df in ((3.841459, 1), (7.814728, 3), (28.869299, 18), (24.995790, 15)):
        assert ind.chi2_sf(x, df) == pytest.approx(0.05, abs=1e-6)


def test_r1_bar_is_the_one_sided_binomial_test() -> None:
    from vinci.evals import independence as ind
    assert [ind.r1_k(n) for n in (5, 9, 10, 20)] == [5, 8, 9, 15]


def test_a_lean_is_read_as_production_reads_it() -> None:
    """(+) Two spellings are one lean; (−) a draw with no lean, an unparsed or unrecognized one is
    dissent and joins no majority."""
    from vinci.evals import independence as ind
    assert ind.lean_of(_complete("Strongly bullish — x")) == B
    assert ind.lean_of(_complete("strongly-bullish — x")) == B
    assert ind.lean_of(_complete("bullish — x")) == ind.DISSENT
    assert ind.lean_of(_complete("no dash")) == ind.DISSENT
    assert ind.lean_of(None) == ind.DISSENT and ind.lean_of({}) == ind.DISSENT


def test_a_literal_escape_is_decoded_as_synthesize_decodes_it() -> None:
    """(+) Opus has written the separator as the TEXT `\\u2014` (`synthesis._decode_escapes`);
    production decodes it before `split_lean` and reads the lean, so the scorer must too."""
    from vinci.evals import independence as ind
    assert ind.lean_of(_complete("mixed \\u2014 two-sided")) == M
    assert ind.lean_of(_complete("Strongly bearish \\u2013 x")) == R


def test_a_draw_production_cannot_use_is_dissent(tmp_path: Path, inputs: None) -> None:
    """(−) A draw truncated at max_tokens (`extract` raises: a failed draw) and one missing the
    structural fields (`synthesize` drops it as INCOMPLETE) carry a lean in the raw draws file,
    but production never counts them: under R3 each is dissent, never a vote."""
    from vinci.evals import independence as ind
    odd = [TRUNC + B, PARTIAL + B] + [B] * 6 + [M] * 2
    reg, budget, out = _drawn(tmp_path, [odd, _build(7), _build(7), _build(7)])
    s = ind.score(reg, budget, out)
    assert s.dissent_draws == 2
    assert s.pages[0].counts == (6, 7, 7, 7)


# --------------------------------------------------------------- 2. the rules on one build


def test_each_option_on_one_build() -> None:
    from vinci.evals import independence as ind
    five_then_split = [B] * 5 + [M] * 5          # A proposes; B none; C(i) proposes at five
    four_then_five = [B] * 4 + [M] + [B] * 5     # A borderline; B and C(i) propose at 9 of 10
    three_two = [B] * 3 + [M] * 2 + [B] * 5      # 8 of 10: C(i) continues and cannot propose
    assert ind.r1(five_then_split[:5]) == (B, "proposed")
    assert ind.r1(five_then_split) == (None, "none")
    assert ind.c_i(five_then_split) == (B, "proposed", 5)
    assert ind.r1(four_then_five[:5]) == (None, "borderline")
    assert ind.r1(four_then_five) == (B, "proposed")
    assert ind.c_i(four_then_five) == (B, "proposed", 10)
    assert ind.c_i(three_two) == (None, "borderline", 10)
    assert ind.r1([M] * 10) == (None, "none")                       # mixed proposes nothing
    assert ind.r1([B] * 4 + [ind.DISSENT]) == (None, "borderline")  # a failed draw is dissent


# --------------------------------------------------------------- 3. the score, end to end


def _build(n_b: int, *, first: str | None = None) -> list[str]:
    leans = [B] * n_b + [M] * (10 - n_b)
    if first is not None:
        leans.remove(first)
        leans.insert(0, first)
    return leans


def test_binomial_looking_builds_do_not_falsify_independence(
        tmp_path: Path, inputs: None) -> None:
    """(+) Counts 7, 6, 7, 8 of 10 around p̂ 0.7: X² 0.95 on 3 df, far from the 5% point."""
    from vinci.evals import independence as ind
    reg, budget, out = _drawn(tmp_path, [_build(7), _build(6), _build(7), _build(8)])
    s = ind.score(reg, budget, out)
    (pg,) = s.pages
    assert pg.modal == B and pg.counts == (7, 6, 7, 8) and pg.p_hat == pytest.approx(0.7)
    assert s.df == 3 and s.x2 == pytest.approx(2.0 / 2.1)
    assert not s.falsified and "NOT falsified" in s.decision


def test_overdispersed_builds_falsify_independence(tmp_path: Path, inputs: None) -> None:
    """(−) Counts 10, 2, 10, 2: far more spread between builds than a binomial allows."""
    from vinci.evals import independence as ind
    reg, budget, out = _drawn(tmp_path, [_build(10), _build(2), _build(10), _build(2)])
    s = ind.score(reg, budget, out)
    assert s.falsified and s.vif > 5 and "FALSIFIED" in s.decision
    assert s.disagree["B"] == (4, 6)             # two proposing builds against two not


def test_an_incomplete_run_is_refused(tmp_path: Path, inputs: None) -> None:
    """(−) Three builds of a registered four: the score is of the registered run or none."""
    from vinci.evals import independence as ind
    reg, budget, out = _drawn(tmp_path, [_build(7)] * 4, complete=False)
    with pytest.raises(rp.ReplayError, match="not complete"):
        ind.score(reg, budget, out)


def test_dissent_draws_stop_the_design(tmp_path: Path, inputs: None) -> None:
    """(−) More than four draws with no lean STOP it (record §7), whatever the dispersion says."""
    from vinci.evals import independence as ind
    noisy = [B] * 6 + [""] * 2 + [M] * 2
    reg, budget, out = _drawn(tmp_path, [noisy, noisy, noisy, _build(7)])
    s = ind.score(reg, budget, out)
    assert s.dissent_draws == 6 and s.stop_dissent and s.decision.startswith("STOP: 6 draws")


def test_uncached_first_draws_are_compared_exactly(tmp_path: Path, inputs: None) -> None:
    """(+) First draws that always carry the modal lean while the cached ones mostly do not:
    the stratified exact test reads it; the same counts with the first draw like any other
    do not."""
    from vinci.evals import independence as ind
    odd = [[B] + [M] * 6 + [B] * 3 for _ in range(4)]        # B 4 of 10 → modal M; firsts are B
    reg, budget, out = _drawn(tmp_path, odd)
    s = ind.score(reg, budget, out)
    assert s.pages[0].modal == M and s.first_modal == 0 and s.first_n == 4
    assert s.first_vs_cached_p < 0.25
    # (−) the same 6/4 builds, with 2 of the 4 first draws modal — the likeliest count
    even = [[M] + [B] + [M] * 5 + [B] * 3, [B] + [M] * 6 + [B] * 3] * 2
    reg2, budget2, out2 = _drawn(tmp_path / "even", even)
    s2 = ind.score(reg2, budget2, out2)
    assert s2.pages[0].modal == M and s2.first_modal == 2
    assert s2.first_vs_cached_p == pytest.approx(1.0)


def test_score_run_prints_the_decision_and_exits_on_it(
        tmp_path: Path, inputs: None, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(+/−) `score-run` reads the registration, ledger and draws it is given, prints the
    registered decision, and exits 1 on a STOP so a script cannot read past it."""
    from vinci.evals import __main__ as cli
    from vinci.evals import registry
    # these tests read the exit code; RG-D14's on-main check has its own pins (test_evals_order8)
    monkeypatch.setattr(registry, "require_on_main", lambda sha, **k: None)
    from vinci.evals import builds as bd
    reg, _, out = _drawn(tmp_path, [_build(10), _build(2), _build(10), _build(2)])
    bd.write_registration(reg, tmp_path / "registration.json")
    rc = cli.main(["score-run", "--registration", str(tmp_path / "registration.json"),
                   "--budget-ledger", str(tmp_path / "ledger.jsonl"), "--draws-out", str(out)])
    assert rc == 1 and "independence FALSIFIED" in capsys.readouterr().out


# --------------------------------------------------------------- 4. decided before the draw


def test_the_runs_test_reads_serial_dependence_inside_builds(
        tmp_path: Path, inputs: None) -> None:
    """(+/−) Record §7's reported runs test: each build's draws as carrying the page's pooled
    modal label or not, Wald–Wolfowitz runs pooled over builds into one z. Clumped builds give
    too few runs (z far below 0); alternating builds too many (z far above)."""
    from vinci.evals import independence as ind
    clumped = [[B] * 5 + [M] * 5] * 4
    reg, budget, out = _drawn(tmp_path, clumped)
    s = ind.score(reg, budget, out)
    assert s.runs_z < -3 and s.runs_p < 0.01
    alternating = [[B, M] * 5] * 4
    reg2, budget2, out2 = _drawn(tmp_path / "alt", alternating)
    s2 = ind.score(reg2, budget2, out2)
    assert s2.runs_z > 3


def test_the_first_draw_test_reads_the_recorded_cache_state(
        tmp_path: Path, inputs: None) -> None:
    """(−) A build whose first draw READ the cache is not an uncached opening, whatever its
    position: the ledger's `first_draw_cache_read` decides, and the count is reported."""
    from vinci.evals import independence as ind
    reg, budget, out = _drawn(tmp_path, [_build(7)] * 4, warm=(2,))
    s = ind.score(reg, budget, out)
    assert s.uncached_openings == 3 and s.first_n == 3


def test_a_run_with_no_degree_of_freedom_is_not_testable(tmp_path: Path, inputs: None) -> None:
    """(−) Every page unanimous over its draws: the dispersion test cannot run, so the score says
    NOT TESTABLE and STOPS, rather than a traceback or a pass."""
    from vinci.evals import independence as ind
    reg, budget, out = _drawn(tmp_path, [[M] * 10] * 4)
    s = ind.score(reg, budget, out)
    assert not s.testable and s.df == 0 and s.decision.startswith("STOP: NOT TESTABLE")


def test_score_run_exits_1_on_a_run_that_is_not_testable(
        tmp_path: Path, inputs: None, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Codex round 1 (#978): a NOT TESTABLE run is a STOP, so `score-run` exits 1 on it as on
    a falsification or a dissent STOP; a script gating on the exit code cannot read past it."""
    from vinci.evals import __main__ as cli
    from vinci.evals import registry
    # these tests read the exit code; RG-D14's on-main check has its own pins (test_evals_order8)
    monkeypatch.setattr(registry, "require_on_main", lambda sha, **k: None)
    from vinci.evals import builds as bd
    reg, _, out = _drawn(tmp_path, [[M] * 10] * 4)
    bd.write_registration(reg, tmp_path / "registration.json")
    rc = cli.main(["score-run", "--registration", str(tmp_path / "registration.json"),
                   "--budget-ledger", str(tmp_path / "ledger.jsonl"), "--draws-out", str(out)])
    assert "STOP: NOT TESTABLE" in capsys.readouterr().out and rc == 1
