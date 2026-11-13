"""The replication rule is the DEFAULT for a new registration with a target (coordinator default
3, 2026-11-12, under the operator's delegation — not an operator ruling; STATE §5.0 row 53 item
(7), `docs/records/2026-11-12-operator-delegation-and-defaults.md`). Until this change `register
--ship-alpha 0.01` was opt-in, so a target registered without it was decided by one run at alpha.

- A NEW target registration ships at p_lower <= 0.01 (`compare.SHIP_ALPHA`, the ship alpha every
  target registration under the rule has used: fix 3a's `cceba9d9` and fix 4a's `06ed949b`), needs
  a registered replication in (0.01, 0.05], and does not ship above 0.05.
- `--single-run` opts out: one run decided at 0.05, stated in the registration (`single_run`)
  and printed.
- A registration written before the default carries no `ship_alpha` and reads exactly as it was
  written: its text, its sha256 and its design key, as main's own code wrote them at 98707f29
  (`tests/fixtures/evals_registrations_before_the_default.json`).

$0: no key, no network. The end-to-end test runs the real CLI commands against an index in a
temporary repository, with the paid client spied: a real `AnthropicLlmClient` whose SDK answers
each draw with a queued synthesis built from NFLX's committed one.
"""
from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
import subprocess
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.test_evals_order8 import (
    BASE_953,
    CAND_953,
    _impact_export,
    _repo_with_index,
    _to_main,
)
from vinci.evals import compare as cm
from vinci.evals import registry
from vinci.evals.replay import ReplayError

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "tests" / "fixtures" / "evals_registrations_before_the_default.json"


@pytest.fixture()
def index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """As order 8 round 2's: the CLI's index is a temporary repository's (origin/main empty until
    `_to_main`), the local `.env` is not read, and RG-D12 is stood in (the impact export's BASE is
    #953's, whose production files are not this checkout's; RG-D12's own pins are in the order-8
    modules). This repository's own index is checked unchanged after each test."""
    from tests.evals_scorer_stub import fingerprint_only
    from vinci import config
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    monkeypatch.setattr(cm, "fixed_scorer", lambda base, **k: (cm.scorer_fingerprint(), head))
    monkeypatch.setattr(cm, "refuse_unless_scored_by_base",
                        lambda base_ref, **k: cm.scorer_fingerprint())
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", fingerprint_only)
    monkeypatch.setattr(config, "load_local_env", lambda *a, **k: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    repo = _repo_with_index(tmp_path / "index", [])
    for name in ("record_registered", "require_on_main", "claim_draw"):
        monkeypatch.setattr(registry, name, functools.partial(getattr(registry, name), root=repo))
    before = (ROOT / registry.INDEX).read_bytes()
    yield repo
    assert (ROOT / registry.INDEX).read_bytes() == before, "the repository's own index moved"


def _ledger(tmp_path: Path, name: str) -> Path:
    from vinci.evals import replay as rp
    return rp.Budget.open(tmp_path / f"{name}.jsonl", cap_usd=50.0,
                          approval=f"operator: {name}").ledger


def _cli(*argv: str) -> int:
    from vinci.evals import __main__ as cli
    return cli.main(list(argv))


def _register(export: Path, ledger: Path, out: Path, *flags: str) -> cm.Registration:
    """`register --from-impact`, through the CLI."""
    assert _cli("register", "--from-impact", str(export), *flags, "--budget-ledger", str(ledger),
                "--out", str(out)) == 0
    return cm.Registration.from_json(out.read_text())


def _clean(raw: dict[str, Any]) -> dict[str, Any]:
    """NFLX's committed synthesis with M-LABEL's bleed family dropped."""
    text = json.dumps(raw)
    assert "bleed" in text
    out: dict[str, Any] = json.loads(text.replace("gradual bleed", "decline")
                                     .replace("bleed", "decline"))
    return out


def _nflx_synthesis(page: dict[str, Any]) -> dict[str, Any]:
    raw = page["synthesis"]
    assert isinstance(raw, dict)
    return raw


# ------------------------------------------------------------------------ 1. the default applies


def test_the_ship_alpha_is_the_one_the_registered_runs_used() -> None:
    """VERIFY-AT-BUILD, against the records (never an outcome): fix 3a's registration
    `cceba9d9` and fix 4a's `06ed949b` registered ship alpha 0.01 against alpha 0.05 (each
    record's §2). The default is that value, and the runbook names it."""
    assert cm.SHIP_ALPHA == 0.01 and cm.ALPHA == 0.05
    rec = {"docs/records/2026-11-07-fix3a-measured-on-the-panel.md": "cceba9d9",
           "docs/records/2026-11-09-fix4a-measured-on-the-panel.md": "06ed949b"}
    for path, sha in rec.items():
        text = (ROOT / path).read_text()
        assert sha in text and "ship alpha **0.01**" in text, path
    # the runbook states the default it follows (RUNBOOKS §n)
    assert f"ship alpha {cm.SHIP_ALPHA}" in (ROOT / "docs" / "RUNBOOKS.md").read_text()


def test_a_new_target_registration_is_under_the_replication_rule_by_default(
        tmp_path: Path, index: Path) -> None:
    """(+) FAILS ON MAIN (98707f29): `register` with a target and no `ship_alpha` registered a
    single run decided at alpha. It now registers the replication rule at `SHIP_ALPHA`, in the
    registration's sha, and says nothing of a single run."""
    export, _ = _impact_export(tmp_path)
    reg = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"],
                      captured=cm.captured_from_impact(export))
    assert reg.ship_alpha == 0.01 and reg.rule == cm.REPLICATION_RULE and not reg.single_run
    on_disk = json.loads(reg.to_json())
    assert on_disk["ship_alpha"] == 0.01 and "single_run" not in on_disk
    # an explicit ship alpha still sets another
    other = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"],
                        captured=cm.captured_from_impact(export), ship_alpha=0.005)
    assert other.ship_alpha == 0.005 and other.rule == cm.REPLICATION_RULE


def test_the_default_through_the_cli_is_in_the_registration_and_printed(
        tmp_path: Path, index: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """(+) FAILS ON MAIN: `register --target M-LABEL` with no rule flag writes ship alpha 0.01 and
    prints the rule it registered."""
    export, _ = _impact_export(tmp_path)
    reg = _register(export, _ledger(tmp_path, "a1"), tmp_path / "r.json", "--target", "M-LABEL")
    assert json.loads((tmp_path / "r.json").read_text())["ship_alpha"] == 0.01
    assert reg.rule == cm.REPLICATION_RULE
    out = capsys.readouterr().out
    assert "the replication rule (the default)" in out and "p_lower <= 0.01" in out
    assert "(0.01, 0.05]" in out and "SINGLE RUN" not in out


def test_an_explicit_ship_alpha_is_printed_as_set_at_registration_not_as_the_default(
        tmp_path: Path, index: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """(+) #1048 review round 1: `--ship-alpha 0.005` printed "the replication rule (the
    default): ships at p_lower <= 0.005", which reads as if 0.005 were the default. A ship alpha
    given at registration says so, and names the default it departs from. FAILS AT 5005b7fd."""
    export, _ = _impact_export(tmp_path)
    reg = _register(export, _ledger(tmp_path, "a1"), tmp_path / "r.json", "--target", "M-LABEL",
                    "--ship-alpha", "0.005")
    assert reg.ship_alpha == 0.005
    rule = next(x for x in capsys.readouterr().out.splitlines() if x.startswith("rule: "))
    assert "(the default)" not in rule and "p_lower <= 0.005" in rule
    assert "ship alpha 0.005 set at registration with --ship-alpha; the default is 0.01" in rule


def test_no_worsening_is_registered_as_it_was(tmp_path: Path, index: Path) -> None:
    """(+) A no-worsening-only registration has no target, so the default never reaches it: no
    `ship_alpha`, no `single_run`, and the keys of the real ones drawn under it (fix 3b's
    `4d6fe10e`, whose fields the fixture keeps) — never an `--ship-alpha` refusal it did not ask
    for."""
    export, _ = _impact_export(tmp_path)
    reg = _register(export, _ledger(tmp_path, "a1"), tmp_path / "r.json", "--no-worsening")
    on_disk = json.loads((tmp_path / "r.json").read_text())
    # (getattr: this pin runs on main as well, where the field does not exist yet)
    assert reg.ship_alpha is None and not getattr(reg, "single_run", False)
    assert "ship_alpha" not in on_disk and "single_run" not in on_disk
    fix3b = json.loads(json.loads(BEFORE.read_text())["registrations"][0]["text"])
    assert set(on_disk) - {"inputs", "scorer_ref", "note"} == set(fix3b) - {"inputs", "note"}


def test_the_printed_rule_names_a_gated_metric_s_families(
        tmp_path: Path, index: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """(+) Review round 0: the printed rule is the registered one. A metric gated on some of its
    families (#929, `--no-worsening-families`) is checked on those only, so the print names them;
    without them it read as if every family were gated."""
    export, _ = _impact_export(tmp_path)
    _register(export, _ledger(tmp_path, "a1"), tmp_path / "r.json", "--no-worsening",
              "--no-worsening-families", "M-LABEL=trailing-only,bleed")
    rule = next(x for x in capsys.readouterr().out.splitlines() if x.startswith("rule: "))
    assert rule.startswith("rule: no-worsening only")
    assert "M-LABEL's no-worsening check counts only ['bleed', 'trailing-only']" in rule


# --------------------------------------------------------------- 2. the opt-out, stated and printed


def test_the_opt_out_is_a_single_run_stated_in_the_registration_and_printed(
        tmp_path: Path, index: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """(+) FAILS ON MAIN (no `--single-run`): the opt-out registers a single run decided at
    alpha — no ship alpha, the plain rule — and STATES it, in the registration (so in its sha) and
    on screen. It is not the default's shape and not a no-worsening one."""
    export, _ = _impact_export(tmp_path)
    reg = _register(export, _ledger(tmp_path, "a1"), tmp_path / "r.json", "--target", "M-LABEL",
                    "--single-run")
    on_disk = json.loads((tmp_path / "r.json").read_text())
    assert on_disk["single_run"] is True and "ship_alpha" not in on_disk
    assert reg.single_run and reg.ship_alpha is None and reg.rule == cm.Registration.rule
    out = capsys.readouterr().out
    assert "SINGLE RUN" in out and "--single-run" in out and "p_lower <= 0.05" in out
    # the statement is in the sha: the same design without it is another registration
    assert dataclasses.replace(reg, single_run=False).sha != reg.sha


def test_a_single_run_in_the_band_ships_on_one_run(tmp_path: Path, index: Path) -> None:
    """(+) The opt-out does what it states: a first run at p_lower 6/252 = 0.024, in the band,
    ships with no replication — where the default registration requires one."""
    export, page = _impact_export(tmp_path)
    cap = cm.captured_from_impact(export)
    single = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"], captured=cap,
                         single_run=True)
    default = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"], captured=cap)
    raw = _nflx_synthesis(page)
    band = [_clean(raw)] * 4 + [raw]
    for reg, want in ((single, "ships"), (default, cm.REPLICATION_REQUIRED)):
        s = cm.score_run(_drawn(tmp_path / f"run-{reg.sha[:8]}", reg, [raw] * 5, band), reg)
        assert s.metrics["M-LABEL"].p_lower == pytest.approx(6 / 252)
        assert s.decision.startswith(want), (want, s.decision, s.reasons)


def test_the_opt_out_is_refused_where_it_contradicts_the_rule(tmp_path: Path,
                                                              index: Path) -> None:
    """(−) A single run has no ship alpha, a no-worsening registration has no target to run once,
    and a replication is of a registration under the rule: each contradiction is refused, in the
    CLI's parser, the library and the registration itself."""
    export, _ = _impact_export(tmp_path)
    with pytest.raises(SystemExit) as stop:
        _cli("register", "--from-impact", str(export), "--target", "M-LABEL", "--single-run",
             "--ship-alpha", "0.01", "--budget-ledger", str(_ledger(tmp_path, "a1")), "--out",
             str(tmp_path / "x.json"))
    assert stop.value.code == 2 and not (tmp_path / "x.json").exists()
    cap = cm.captured_from_impact(export)
    with pytest.raises(ReplayError, match="single run"):
        cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"], captured=cap,
                    single_run=True, ship_alpha=0.02)
    # a single run with no target is refused by `register` itself, as a ReplayError (the CLI's
    # parser does not exclude `--single-run --no-worsening`), never a bare dataclass ValueError
    with pytest.raises(ReplayError, match="no target to run once"):
        cm.register(BASE_953, CAND_953, pages=["NFLX"], captured=cap, no_worsening=True,
                    single_run=True)
    base = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"], captured=cap,
                       single_run=True)
    with pytest.raises(ValueError, match="single"):
        dataclasses.replace(base, ship_alpha=0.01)
    with pytest.raises(ValueError, match="single"):
        dataclasses.replace(base, targets=(), no_worsening=True)
    with pytest.raises(ValueError, match="under the replication rule"):
        dataclasses.replace(base, replicates="f" * 64)


# ----------------------------------- 3. a registration written before the default reads as written


def _before() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = json.loads(BEFORE.read_text())["registrations"]
    return rows


@pytest.mark.parametrize("row", _before(), ids=lambda r: r["name"])
def test_a_registration_written_before_the_default_reads_as_it_was_written(
        row: dict[str, str]) -> None:
    """(+) Each text as main's own `Registration.to_json` wrote it at 98707f29 — fix 3b's real
    fields (its inputs' root path and file names replaced), a target with no ship alpha, the rule
    at 0.01 as fix 3a and fix 4a registered it, and a replication — reads back byte for byte, to
    the sha256 and the index's design key main derived. A target written with no ship alpha is
    still a single run: the default is `register`'s, never the field's. (Mutant: the field's
    default set to `SHIP_ALPHA` reads 0.01 into the old text and moves its sha.)"""
    text = row["text"]
    reg = cm.Registration.from_json(text)
    assert reg.to_json() == text
    assert reg.sha == hashlib.sha256(text.encode()).hexdigest() == row["sha256"]
    assert registry.identity(reg)["design"] == cm.draw_key(reg) == row["design"]
    assert reg.ship_alpha == json.loads(text).get("ship_alpha")
    assert not getattr(reg, "single_run", False)   # (getattr: the pin runs on main too)


def test_the_fixture_was_written_by_main_s_code() -> None:
    """The fixture's provenance: main's commit, and no local path in a public repository."""
    data = json.loads(BEFORE.read_text())
    assert data["written_by"] == "98707f297a16982f1281c76ec2477ce1c5ab76dc"
    assert "/Users/" not in BEFORE.read_text() and "@" not in BEFORE.read_text()
    assert {r["name"] for r in data["registrations"]} == {
        "no-worsening, fix 3b's real fields", "a target, no ship_alpha",
        "the replication rule at 0.01", "a replication"}


def test_a_target_written_before_the_default_still_ships_on_one_run(tmp_path: Path,
                                                                    index: Path) -> None:
    """(+) The old text's MEANING, not only its bytes: a target registration in the shape written
    before the default (no `ship_alpha`), in the band at 6/252, is read as the single run it was
    registered as, and ships. (Mutant: the field's default set to `SHIP_ALPHA` requires a
    replication of a run that was never registered under the rule.)"""
    export, page = _impact_export(tmp_path)
    reg = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"],
                      captured=cm.captured_from_impact(export))
    old = json.loads(reg.to_json())
    old.pop("ship_alpha", None)   # the shape main wrote with no rule flag: no ship_alpha, no
    old.pop("single_run", None)   # single_run, the plain rule (built so the pin runs on main too)
    old["rule"] = cm.Registration.rule
    text = json.dumps(old, sort_keys=True)
    legacy = cm.Registration.from_json(text)
    assert legacy.to_json() == text and legacy.ship_alpha is None
    assert not getattr(legacy, "single_run", False)
    raw = _nflx_synthesis(page)
    s = cm.score_run(_drawn(tmp_path / "old", legacy, [raw] * 5, [_clean(raw)] * 4 + [raw]),
                     legacy)
    assert s.decision.startswith("ships"), s.reasons


# ---------------------------------------------- 4. the bands of a DEFAULT registration, scored


def _drawn(out: Path, reg: cm.Registration, base: list[Any], cand: list[Any]) -> Path:
    out.mkdir(parents=True)
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (out / "draws.jsonl").open("w") as f:
        for cond, raws in (("BASE", base), ("CAND", cand)):
            for n, raw in enumerate(raws):
                f.write(json.dumps({"label": f"NFLX:{cond}", "draw": n + 1, "raw": raw,
                                    "stop_reason": "tool_use"}) + "\n")
    return out


@pytest.mark.parametrize(("cleaned", "p_lower", "decision"), [
    (5, 1 / 252, "ships"),                    # at or under the ship alpha
    (4, 6 / 252, cm.REPLICATION_REQUIRED),    # in (ship alpha, alpha]
    (0, 1.0, cm.DOES_NOT_SHIP),               # above alpha
])
def test_a_default_registration_ships_only_at_the_ship_alpha(
        tmp_path: Path, index: Path, cleaned: int, p_lower: float, decision: str) -> None:
    """(+/−) FAILS ON MAIN in the band (main's default ships it). A registration made by the
    default, scored on NFLX's committed synthesis: five of five CAND draws dropping the label ship
    (p_lower 1/252 <= 0.01), four of five need a replication (6/252), none does not ship. (Mutants:
    the ship comparison flipped, or tested at alpha, ships the band or holds the ship band.)"""
    export, page = _impact_export(tmp_path)
    reg = cm.register(BASE_953, CAND_953, targets=["M-LABEL"], pages=["NFLX"],
                      captured=cm.captured_from_impact(export))
    raw = _nflx_synthesis(page)
    cand = [_clean(raw)] * cleaned + [raw] * (5 - cleaned)
    s = cm.score_run(_drawn(tmp_path / "run", reg, [raw] * 5, cand), reg)
    assert s.metrics["M-LABEL"].p_lower == pytest.approx(p_lower)
    assert s.decision.startswith(decision), (s.decision, s.reasons)
    assert s.ships == (decision == "ships" and not s.reasons)


# ----------------------------- 5. end to end through the CLI: needs, and accepts, a replication


_QUEUE: list[dict[str, Any]] = []


class _QueueSdk:
    """The SDK behind the spied client: each draw answers with the next queued synthesis."""

    def __init__(self) -> None:
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        raw = _QUEUE.pop(0)
        usage = SimpleNamespace(input_tokens=10, output_tokens=10,
                                cache_creation_input_tokens=0, cache_read_input_tokens=0)
        block = SimpleNamespace(type="tool_use", input=raw)
        return SimpleNamespace(usage=usage, content=[block], model=kwargs["model"],
                               stop_reason="tool_use")


@pytest.fixture()
def drawer(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[int]]:
    """The paid client, spied: production's `AnthropicLlmClient`, built with no key read, its SDK
    the queue's. Counts the clients built, so a refusal is shown to come before any."""
    from vinci.evals import replay as rp
    from vinci.graph.llm import AnthropicLlmClient
    built: list[int] = []

    def client(*, model: str, max_tokens: int = 16384, api_key: str | None = None) -> Any:
        built.append(1)
        c = AnthropicLlmClient(model=model, max_tokens=max_tokens, api_key="test-not-a-key")
        c._client = _QueueSdk()  # type: ignore[assignment]
        return c

    monkeypatch.setattr(rp, "AnthropicLlmClient", client)
    _QUEUE.clear()
    yield built
    _QUEUE.clear()


def _drawable_export(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """`_impact_export`, with each arm's request captured at FIVE draws as a real export's is
    (`impact-captures-format.md`: one of the run's five identical calls, `cache_control`
    included). Order 8's helper captures one draw, and its tests never reach a draw; a five-draw
    run sends the cache flag, which the guard checks against the pinned bytes."""
    from vinci.evals import replay as rp
    export, page = _impact_export(tmp_path)
    manifest = json.loads((export / "manifest.json").read_text())
    for arm, side in (("BASE", "base"), ("CAND", "head")):
        d = export / side / "NFLX"
        kwargs = rp.capture(json.loads((d / "built.json").read_text()), None, draws=5).kwargs
        assert "cache_control" in kwargs
        (d / "request.json").write_text(json.dumps(kwargs))
        manifest["pages"]["NFLX"][arm]["request_wire_sha256"] = hashlib.sha256(
            rp.wire(kwargs).encode()).hexdigest()
    (export / "manifest.json").write_text(json.dumps(manifest))
    return export, page


def _run_compare(registration: Path, ledger: Path, out_dir: Path) -> int:
    return _cli("run-compare", "--registration", str(registration), "--budget-ledger",
                str(ledger), "--out-dir", str(out_dir), "--paid")


def _score(out_dir: Path, registration: Path, ledger: Path) -> str:
    assert _cli("score", "--out-dir", str(out_dir), "--registration", str(registration),
                "--budget-ledger", str(ledger)) == 0
    row = json.loads((out_dir / "score_log.jsonl").read_text().splitlines()[-1])
    decision: str = row["decision"]
    return decision


def test_a_default_first_run_in_the_band_needs_and_accepts_a_replication_through_the_cli(
        tmp_path: Path, index: Path, drawer: list[int],
        capsys: pytest.CaptureFixture[str]) -> None:
    """END TO END (TEST-LAYER RULE), FAILS ON MAIN: there the first run, registered with no rule
    flag, ships on one run at 6/252.

    1. `register --target M-LABEL` (no rule flag) registers the replication rule at 0.01; its row
       merges to main; `run-compare --paid` draws it (the spied client, $0) and `score` decides
       "replication required" (p_lower 6/252, in (0.01, 0.05]).
    2. (−) The same design registered again under another approval, with new words and no
       `--replicates`, is refused before any client: a first run's band is not re-rolled.
    3. (+) `register --replicates` (the same ledger) registers its replication; drawn on the
       first run's own request bytes — the F3 exemption (operator 2026-11-12, "Refuse by request
       pins": "A replication under the replication rule stays allowed") — it reaches p_lower
       1/252 <= 0.05, and `score` decides "replicated: ships"."""
    export, page = _drawable_export(tmp_path)
    raw = _nflx_synthesis(page)
    l1, l2 = _ledger(tmp_path, "a1"), _ledger(tmp_path, "a2")

    first = _register(export, l1, tmp_path / "first.json", "--target", "M-LABEL")
    assert first.ship_alpha == 0.01 and first.replicates is None
    assert "the replication rule" in capsys.readouterr().out
    _to_main(index)
    _QUEUE.extend([raw] * 5 + [_clean(raw)] * 4 + [raw])
    assert _run_compare(tmp_path / "first.json", l1, tmp_path / "run-first") == 0
    assert drawer == [1, 1] and not _QUEUE
    assert _score(tmp_path / "run-first", tmp_path / "first.json", l1) == cm.REPLICATION_REQUIRED

    again = _register(export, l2, tmp_path / "again.json", "--target", "M-LABEL", "--note",
                      "the same design, other words")
    assert again.sha != first.sha and not cm.design_differs(again, first)
    _to_main(index)
    with pytest.raises(ReplayError, match="design was already drawn"):
        _run_compare(tmp_path / "again.json", l2, tmp_path / "run-again")
    assert drawer == [1, 1] and not (tmp_path / "run-again").exists()

    repl = _register(export, l1, tmp_path / "repl.json", "--target", "M-LABEL", "--replicates",
                     str(tmp_path / "first.json"))
    assert repl.replicates == first.sha and repl.requests == first.requests
    assert "REPLICATION of" in capsys.readouterr().out
    _to_main(index)
    _QUEUE.extend([raw] * 5 + [_clean(raw)] * 5)
    assert _run_compare(tmp_path / "repl.json", l1, tmp_path / "run-repl") == 0
    assert drawer == [1, 1, 1, 1] and not _QUEUE
    assert _score(tmp_path / "run-repl", tmp_path / "repl.json", l1).startswith(
        "replicated: ships")
    drawn = [r for r in registry.working_rows(index) if r.get("event") == "drawn"]
    assert [r["registration"] for r in drawn] == [first.sha, repl.sha]


def test_a_band_result_re_registered_as_a_single_run_is_not_drawn_through_the_cli(
        tmp_path: Path, index: Path, drawer: list[int]) -> None:
    """(−) #1048 review round 1, THE SINGLE-RUN LOOPHOLE, END TO END: a default first run decides
    "replication required"; the same pages and arms re-registered with `--single-run` under a
    second approval would ship on one run at 6/252. It is ANOTHER DESIGN (`ship_alpha` and `rule`
    differ), so neither the per-approval ledger check nor the design key catches it: order 8's
    request-pins check does (F3; operator 2026-11-12, "Refuse by request pins") — every pin it
    would draw was drawn by the first run, and only a replication of that run is exempt. Refused
    by `claim_draw` before any client is built. (Mutant: the pins check stubbed out — the single
    run is drawn.)"""
    export, page = _drawable_export(tmp_path)
    raw = _nflx_synthesis(page)
    band = [raw] * 5 + [_clean(raw)] * 4 + [raw]
    l1, l2 = _ledger(tmp_path, "a1"), _ledger(tmp_path, "a2")
    first = _register(export, l1, tmp_path / "first.json", "--target", "M-LABEL")
    _to_main(index)
    _QUEUE.extend(band)
    assert _run_compare(tmp_path / "first.json", l1, tmp_path / "run-first") == 0
    assert _score(tmp_path / "run-first", tmp_path / "first.json", l1) == cm.REPLICATION_REQUIRED
    assert drawer == [1, 1]

    single = _register(export, l2, tmp_path / "single.json", "--target", "M-LABEL",
                       "--single-run")
    assert single.single_run and single.requests == first.requests
    assert cm.design_differs(single, first) == ["ship_alpha", "rule"]
    assert cm.draw_key(single) != cm.draw_key(first)
    _to_main(index)
    _QUEUE.extend(band)   # what it would draw, were it drawn
    with pytest.raises(ReplayError, match="every request"):
        _run_compare(tmp_path / "single.json", l2, tmp_path / "run-single")
    assert drawer == [1, 1] and not (tmp_path / "run-single").exists()
    drawn = [r for r in registry.working_rows(index) if r.get("event") == "drawn"]
    assert [r["registration"] for r in drawn] == [first.sha]
