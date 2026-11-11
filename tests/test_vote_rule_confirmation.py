"""C(iv) of the vote rule, and R4's sealed split (`docs/records/2026-11-10-the-proposal-vote-rule-
design.md` §9): before `log-verdict` writes its row, the committed page's synthesis is drawn TEN
times and R1 at ten decides the sealed proposal; one confirmation per page version, recorded and
reused; the split sealed beside the proposal in an optional ledger field.

Run against main `e73e7a54`, every test here errors at setup (the record's path,
`cli._confirmation_record`, does not exist there). One is a GUARD that would pass there without
that fixture, by design: `test_a_row_before_the_rule_serializes_as_it_did`. The page is a real
committed one (GOOGL, whose verdict is already in the ledger), read from an empty CIQ folder, so
no licensed file is read; the LLM is scripted, so no call is paid.
"""
from __future__ import annotations

import argparse
import json
import typing
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BULL = "strongly-bullish — the runway outruns the multiple."
MIXED = "mixed — two-sided and unresolved."


def _payload(lean: str, n: int) -> dict[str, typing.Any]:
    return {"evidence_balance": lean, "bull_points": [{"claim": f"c{n}", "source_ref": "r"}],
            "bear_points": [{"claim": "c", "source_ref": "r"}], "twin_reference_cases": [],
            "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []},
            "key_unknowns": ["u"]}


class _Scripted:
    def __init__(self, leans: list[str]) -> None:
        self._leans, self.calls = leans, 0

    @property
    def model(self) -> str:
        return "scripted-model"

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        from vinci.graph.llm import LlmError
        lean = self._leans[self.calls]
        self.calls += 1
        if lean == "fail":
            raise LlmError("tool call incomplete")
        return _payload(lean, self.calls)


@pytest.fixture()
def googl() -> dict[str, typing.Any]:
    """GOOGL's committed page. Its input record lists no transcripts (built before input records),
    so on an empty CIQ folder the confirmation reads none, unverified — no stub needed."""
    page: dict[str, typing.Any] = json.loads(
        (ROOT / "data/dossiers/GOOGL/dossier.json").read_text())
    return page


def _confirm(page: dict[str, typing.Any], leans: list[str], record: Path,
             **kw: typing.Any) -> tuple[typing.Any, _Scripted]:
    from vinci.dossier.confirmation import confirm
    llm = _Scripted(leans)
    return confirm(page, llm=llm, ciq_root=record.parent, record=record, **kw), llm


# ------------------------------------------------------------------- C(iv): ten draws, R1 at ten


def test_the_confirmation_draws_ten_and_r1_at_ten_decides(
        googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(+) 9 of 10 bullish passes R1 at ten (5 of 5 would be needed at five), so the sealed
    proposal is BUY, with its split; the row records the request's sha256 and the model."""
    conf, llm = _confirm(googl, [BULL] * 9 + [MIXED], tmp_path / "c.jsonl")
    assert llm.calls == 10 and not conf.reused
    assert (conf.gate.count, conf.gate.attempted, conf.gate.required) == (9, 10, 9)
    assert conf.gate.passes and conf.proposal.action is not None
    assert conf.proposal.split == "9x strongly-bullish, 1x mixed of 10 draws (the 9-of-10 rule)"
    (row,) = [json.loads(x) for x in (tmp_path / "c.jsonl").read_text().splitlines()]
    assert row["ticker"] == "GOOGL" and row["assembled_at"] == googl["assembled_at"]
    assert row["model"] == "scripted-model" and len(row["request_sha256"]) == 64
    assert row["proposal"] == conf.proposal.action.value and row["dry_run"] is False
    # GOOGL's page predates input records: the transcripts read could not be checked, and say so
    assert row["transcripts_verified"] is False and conf.transcripts_verified is False


def test_eight_of_ten_is_borderline(googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(−) 8 of 10 fails R1 at ten: no proposal, C(iii)'s borderline, the split printed."""
    conf, _ = _confirm(googl, [BULL] * 8 + [MIXED] * 2, tmp_path / "c.jsonl")
    assert conf.proposal.action is None and conf.gate.state == "borderline"


def test_a_page_version_is_confirmed_once(googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(−) A second log of the same page REUSES the recorded confirmation and draws nothing, so
    it cannot be re-drawn until it agrees; (+) a re-assembled page is a new version and draws."""
    record = tmp_path / "c.jsonl"
    first, _ = _confirm(googl, [BULL] * 8 + [MIXED] * 2, record)
    again, llm = _confirm(googl, [BULL] * 10, record)
    assert llm.calls == 0 and again.reused and again.gate == first.gate
    assert again.proposal.action is None
    newer = {**googl, "assembled_at": "2026-12-01T00:00:00+00:00"}
    fresh, llm2 = _confirm(newer, [BULL] * 10, record)
    assert llm2.calls == 10 and not fresh.reused and fresh.proposal.action is not None


def test_a_confirmation_that_learned_nothing_is_not_recorded(
        googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(−) Every draw failed (an outage, a missing key): refused, and NOT recorded, so the page's
    one confirmation is not used up."""
    from vinci.dossier.confirmation import ConfirmationError
    with pytest.raises(ConfirmationError, match="nothing recorded"):
        _confirm(googl, ["fail"] * 10, tmp_path / "c.jsonl")
    assert not (tmp_path / "c.jsonl").exists()


def test_transcripts_that_differ_from_the_page_s_record_refuse_before_any_draw(
        googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(−) A page whose input record lists a transcript that is not on disk: refused before any
    draw — the confirmation never draws on other inputs than the page's."""
    from vinci.dossier.confirmation import ConfirmationError
    page = json.loads(json.dumps(googl))
    page.setdefault("inputs", {}).setdefault("ciq", []).append(
        {"file": "GOOGL call.pdf", "kind": "transcript", "sha256": "0" * 64})
    with pytest.raises(ConfirmationError, match="transcripts"):
        _confirm(page, [BULL] * 10, tmp_path / "c.jsonl")
    assert not (tmp_path / "c.jsonl").exists()


def test_the_layer_is_read_as_the_replay_harness_reads_it() -> None:
    """(+) Parity: the decision path's reader (it may not import the harness) equals the harness's
    `pre_synthesis_mech` on every committed page."""
    from vinci.dossier.confirmation import layer_as_synthesized
    from vinci.evals.capture_child import pre_synthesis_mech
    pages = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
    assert len(pages) >= 20
    for p in pages:
        page = json.loads(p.read_text())
        if not page.get("mechanical"):
            continue
        assert (layer_as_synthesized(page).model_dump_json()
                == pre_synthesis_mech(page).model_dump_json()), p.parent.name


def test_the_transcripts_are_read_as_the_replay_harness_reads_them(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Parity with `replay.transcript_for` on the pages whose transcripts are on this machine
    (licensed, never in CI: skipped there). EACH FILE IS READ ONCE and the read is shared by both
    readers: GOOGL's Q3 call is converted by LibreOffice, which fails a conversion while another
    runs, so two reads of one file could differ under load (the gate saw it, 2026-11-11). What is
    compared is the readers' code on the same reads; a call that will not read in three tries
    skips its page, saying so."""
    from vinci.dossier import ciq_sheets
    from vinci.dossier.ciq import CiqBundle, CiqParseError
    from vinci.dossier.confirmation import page_transcripts
    from vinci.evals.replay import transcript_for
    ciq = ROOT.parents[2] / "data" / "manual" / "ciq" if (ROOT / ".git").is_file() else (
        ROOT / "data" / "manual" / "ciq")
    if not ciq.is_dir():
        pytest.skip("no licensed CIQ folder on this machine")
    real, memo = ciq_sheets.read_text, {}

    def once(path: Path, fmt: typing.Any = None, **kw: typing.Any) -> str:
        key = (path, fmt, tuple(sorted(kw.items())))
        if key not in memo:
            memo[key] = real(path, fmt, **kw)
        return memo[key]
    monkeypatch.setattr(ciq_sheets, "read_text", once)
    done, busy = 0, []
    for t in ("GOOGL", "LLY", "SMPL"):
        if not (ciq / t).is_dir():
            continue
        page = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        bundle = CiqBundle.from_files(t, sorted(p for p in (ciq / t).iterdir() if p.is_file()))
        unread = []
        for wb in bundle.all_workbooks("transcript"):
            for _try in range(3):
                try:
                    once(wb.path, wb.fmt)
                    break
                except CiqParseError:
                    continue
            else:
                unread.append(wb.path.name)
        if unread:
            busy.append(f"{t}: {unread}")
            continue
        assert page_transcripts(t, ciq_root=ciq, page=page)[0] == transcript_for(
            t, ciq_root=ciq, page=page), t
        done += 1
    if not done:
        pytest.skip("no page compared: " + ("; ".join(busy) if busy
                                            else "none of the three pages' CIQ folders is here"))


# ------------------------------------------------------------------- log-verdict's seal


def _args(tmp_path: Path, *, dry_run: bool) -> argparse.Namespace:
    return argparse.Namespace(ciq_root=str(tmp_path), dry_run=dry_run)


@pytest.fixture(autouse=True)
def _record_in_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The ONE canonical record is the repository's; tests point it at their own folder."""
    from vinci import cli
    monkeypatch.setattr(cli, "_confirmation_record", lambda cfg: tmp_path / "c.jsonl")


def test_log_verdict_seals_the_confirmation_and_both_splits(
        googl: dict[str, typing.Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) R4: the sealed tally carries the page's own build and the confirmation; the sealed
    proposal is the confirmation's. A dry run's confirmation is REVEALED: reused by a later log,
    it seals `revealed_pre_verdict`."""
    from vinci import cli
    from vinci.config import get_config
    from vinci.graph import llm as llm_mod
    monkeypatch.setattr(llm_mod.AnthropicLlmClient, "from_config",
                        classmethod(lambda cls, c=None: _Scripted([BULL] * 10)))
    cfg = get_config()
    dry = cli._confirm_seal(cfg, _args(tmp_path, dry_run=True), "GOOGL")
    assert dry.action is not None and not dry.revealed
    assert dry.tally is not None and dry.tally["sealed_from"] == "confirmation"
    assert dry.tally["page"] == googl["synthesis"]["draw_agreement"]
    assert dry.tally["confirmation"]["modal_count"] == 10
    assert dry.tally["confirmation"]["revealed_by_dry_run"] is True
    assert any("R1 at 10" in line for line in dry.lines)
    real = cli._confirm_seal(cfg, _args(tmp_path, dry_run=False), "GOOGL")
    assert real.revealed and real.action == dry.action


def test_the_dry_run_returns_before_the_ledger_write() -> None:
    """STRUCTURAL, like the edge-basis gate's: the seal is drawn, and a dry run returns, BEFORE
    `log_verdict` — the append-only ledger is never touched by a dry run."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    body = src[src.index("def _cmd_log_verdict"):]
    body = body[:body.index("\ndef ", 10)]
    write = body.index("= log_verdict(")
    assert body.index("_confirm_seal(") < write
    assert body.index('getattr(args, "dry_run", False)') < write
    from vinci.cli import build_parser
    ns = build_parser().parse_args(["log-verdict", "GOOGL", "--verdict", "BUY", "--twin", "t",
                                    "--thesis", "th", "--kill", "k", "--horizon-days", "180",
                                    "--confidence", "medium", "--dry-run"])
    assert ns.dry_run is True


# ------------------------------------------------------------------- the ledger field


def _entry(**over: typing.Any) -> typing.Any:
    from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
    base: dict[str, typing.Any] = {
        "entry_id": "e1", "candidate_id": "c1", "internal_id": "i1", "ticker": "X",
        "verdict": Verdict.BUY, "twin_call": "t", "entry_price": 10.0,
        "entry_price_as_of": date(2026, 11, 10), "thesis": "th", "kill_criteria": "k",
        "horizon_days": 180, "confidence": Confidence("medium"),
        "decided_at": datetime(2026, 11, 10, 12, 0)}
    return LedgerEntry(**{**base, **over})


def test_a_row_before_the_rule_serializes_as_it_did() -> None:
    """(+) The field is omitted while None: every committed ledger row re-serializes byte for
    byte (the store re-validates each row it appends)."""
    assert "machine_tally" not in json.loads(_entry().model_dump_json())
    assert "machine_tally" not in _entry().model_dump()


def test_the_sealed_split_round_trips_through_the_store(tmp_path: Path) -> None:
    from vinci.store import Store
    tally = {"sealed_from": "confirmation", "page": {"attempted": 5},
             "confirmation": {"draws": 10, "modal_count": 9, "passes": True}}
    with Store(tmp_path / "v.db") as store:
        store.append_ledger(_entry(machine_tally=tally))
        (got,) = list(store.iter_ledger())
    assert got.machine_tally == tally


# ------------------------------------------------------------------- review round 0 (code-review)


def test_a_reused_confirmation_is_revealed_whichever_command_drew_it(
        googl: dict[str, typing.Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Every `log-verdict` prints the confirmation BEFORE `log_verdict`'s own gates run, so a
    real log REFUSED there (a stale entry price, a stated limit) has shown the human the proposal
    exactly as a dry run does. A later log reusing that confirmation must seal it as revealed; it
    did so only when the drawing command was a dry run."""
    from vinci import cli
    from vinci.config import get_config
    from vinci.graph import llm as llm_mod
    monkeypatch.setattr(llm_mod.AnthropicLlmClient, "from_config",
                        classmethod(lambda cls, c=None: _Scripted([BULL] * 10)))
    cfg = get_config()
    first = cli._confirm_seal(cfg, _args(tmp_path, dry_run=False), "GOOGL")
    assert not first.revealed   # drawn by this command, which already carries its verdict
    again = cli._confirm_seal(cfg, _args(tmp_path, dry_run=False), "GOOGL")
    assert again.revealed, "a confirmation printed by an earlier command sealed as unseen"


def test_a_reused_confirmation_is_the_gate_that_was_drawn_on_a_tie(
        googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(−) The record is written with sorted keys, so a TIED split came back from it in name
    order and the reused gate named another modal lean than the one drawn and recorded."""
    record = tmp_path / "c.jsonl"
    first, _ = _confirm(googl, [BULL] * 5 + [MIXED] * 5, record)
    assert first.gate.lean == "strongly-bullish"
    again, llm = _confirm(googl, [BULL] * 10, record)
    assert llm.calls == 0 and again.gate == first.gate


# ------------------------------------------------------------------- review round 0 (pre-PR)


def test_a_partial_outage_is_not_recorded(googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(−) More than two of ten draws FAILED (an outage, a rate limit): not the model's read, so
    it is refused and NOT recorded, and the page's one confirmation is not used up."""
    from vinci.dossier.confirmation import ConfirmationError
    with pytest.raises(ConfirmationError, match="nothing recorded"):
        _confirm(googl, ["fail"] * 3 + [BULL] * 7, tmp_path / "c.jsonl")
    assert not (tmp_path / "c.jsonl").exists()


def test_two_failed_draws_count_as_dissent(googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(+) Up to two failed draws are R3's dissent: 8 bullish of 10 attempted is borderline, and
    it is recorded."""
    conf, _ = _confirm(googl, ["fail"] * 2 + [BULL] * 8, tmp_path / "c.jsonl")
    assert (conf.gate.count, conf.gate.attempted, conf.gate.state) == (8, 10, "borderline")
    assert (tmp_path / "c.jsonl").exists()


def test_a_corrupt_record_refuses_cleanly(googl: dict[str, typing.Any], tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) A truncated record line is a LedgerError the command reports, not a traceback."""
    from vinci import cli
    from vinci.config import get_config
    from vinci.graph import llm as llm_mod
    from vinci.ledger import LedgerError
    monkeypatch.setattr(llm_mod.AnthropicLlmClient, "from_config",
                        classmethod(lambda cls, c=None: _Scripted([BULL] * 10)))
    (tmp_path / "c.jsonl").write_text('{"ticker": "GOOGL", "assembled_')
    with pytest.raises(LedgerError, match="C\\(iv\\)"):
        cli._confirm_seal(get_config(), _args(tmp_path, dry_run=True), "GOOGL")


def test_there_is_one_record_and_no_flag_to_name_another() -> None:
    """(−) A log that could name a fresh record could re-draw a page version until it agreed."""
    from vinci.cli import build_parser
    with pytest.raises(SystemExit):
        build_parser().parse_args(["log-verdict", "GOOGL", "--verdict", "BUY", "--twin", "t",
                                   "--thesis", "th", "--kill", "k", "--horizon-days", "180",
                                   "--confidence", "medium", "--confirmations", "/tmp/x.jsonl"])


def test_a_page_without_a_sleeve_draws_on_the_default_sleeve(
        googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(+) Review round 0: a page that records no `sleeve` is drawn on `DEFAULT_SLEEVE`, as the
    build defaults it — never `None`, which `synthesize` refuses. The request is the one an
    explicit default-sleeve page sends, and differs from the page's own sleeve's."""
    from vinci.sleeves import DEFAULT_SLEEVE
    assert googl["sleeve"] != DEFAULT_SLEEVE     # GOOGL is quality: the default is visible
    bare = {k: v for k, v in googl.items() if k != "sleeve"}
    explicit = {**googl, "sleeve": DEFAULT_SLEEVE}
    got, _ = _confirm(bare, [BULL] * 10, tmp_path / "a" / "c.jsonl")
    want, _ = _confirm(explicit, [BULL] * 10, tmp_path / "b" / "c.jsonl")
    own, _ = _confirm(googl, [BULL] * 10, tmp_path / "c" / "c.jsonl")
    assert got.request_sha256 == want.request_sha256 != own.request_sha256


def test_a_page_built_before_the_rule_prints_its_split_not_a_dict(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Found by the real dry run on GOOGL: a page built before the rule printed its own build as
    a raw Python dict. Every committed page is in that state, so it is the line the human reads at
    every log. It reads as the labels, and as the rule that page decides by (unanimity, C7)."""
    from vinci import cli
    from vinci.config import get_config
    from vinci.graph import llm as llm_mod
    monkeypatch.setattr(llm_mod.AnthropicLlmClient, "from_config",
                        classmethod(lambda cls, c=None: _Scripted([BULL] * 10)))
    seal = cli._confirm_seal(get_config(), _args(tmp_path, dry_run=True), "GOOGL")
    (line,) = [x for x in seal.lines if "the page's own build" in x]
    assert "{" not in line
    assert "4x mixed, 1x strongly-bullish of 5 draws" in line
    assert "unanimity" in line and "not unanimous" in line


def _tecx() -> dict[str, typing.Any]:
    """TECX's committed page: its input record is a BUILD record (complete — every export the
    bundle held is listed) and lists no transcript, because the build read none."""
    page: dict[str, typing.Any] = json.loads(
        (ROOT / "data/dossiers/TECX/dossier.json").read_text())
    assert page["inputs"]["recorded"] == "build"
    assert not [c for c in page["inputs"]["ciq"] if c["kind"] == "transcript"]
    return page


def test_a_transcript_added_since_a_complete_build_refuses(tmp_path: Path) -> None:
    """(−) Found by the corpus run of the transcript check: on a page whose COMPLETE record lists
    no transcript, a transcript on disk now is an input the build never read. The check skipped
    such a page (it compared only where a transcript was listed), so the confirmation would have
    drawn on it unverified. It refuses."""
    from vinci.dossier.confirmation import ConfirmationError, page_transcripts
    folder = tmp_path / "TECX"
    folder.mkdir()
    call = folder / "Tectonic Therapeutic, Inc., Q3 2026 Earnings Call, Nov 06, 2026.rtf"
    call.write_text("{\\rtf1 x}")
    with pytest.raises(ConfirmationError, match="differ from the page's input record"):
        page_transcripts("TECX", ciq_root=tmp_path, page=_tecx())


def test_a_complete_build_that_read_no_transcript_is_verified_on_an_empty_folder(
        tmp_path: Path) -> None:
    """(+) The same page with no transcript on disk is VERIFIED: the record is complete, and both
    sides list none."""
    from vinci.dossier.confirmation import page_transcripts
    assert page_transcripts("TECX", ciq_root=tmp_path, page=_tecx()) == (None, True)


def test_a_backfilled_record_reads_unverified_and_says_why(
        googl: dict[str, typing.Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) GOOGL's record is a BACKFILL, which never lists a transcript: unverified, and the line
    says so rather than claim the page has no input record (the real dry run printed that)."""
    from vinci import cli
    from vinci.config import get_config
    from vinci.dossier.confirmation import page_transcripts
    from vinci.graph import llm as llm_mod
    assert googl["inputs"]["recorded"] == "backfill"
    assert page_transcripts("GOOGL", ciq_root=tmp_path, page=googl)[1] is False
    monkeypatch.setattr(llm_mod.AnthropicLlmClient, "from_config",
                        classmethod(lambda cls, c=None: _Scripted([BULL] * 10)))
    seal = cli._confirm_seal(get_config(), _args(tmp_path, dry_run=True), "GOOGL")
    (line,) = [x for x in seal.lines if "its transcripts" in x]
    assert "UNVERIFIED" in line and "backfill" in line
    assert "built before input records" not in line


_PROSE = ("Thank you, operator. Revenue grew in every segment this quarter and cloud backlog rose "
          "again; we continue to invest in capacity while holding operating discipline. ") * 8


def _two_calls(tmp_path: Path) -> Path:
    """A GOOGL folder holding two RTF-text calls (plain striprtf reads, no LibreOffice)."""
    folder = tmp_path / "ciq" / "GOOGL"
    folder.mkdir(parents=True)
    for q in ("Q2 2026 Earnings Call, Jul 22, 2026", "Q3 2026 Earnings Call, Oct 28, 2026"):
        (folder / f"Alphabet Inc., {q}.rtf").write_text("{\\rtf1\\ansi " + _PROSE + "}")
    return folder.parent


def test_a_call_that_does_not_read_refuses_rather_than_draw_on_fewer_calls(
        googl: dict[str, typing.Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Found by the gate: GOOGL's Q3 call is an OLE Word doc read through LibreOffice, which
    fails a conversion while another runs, and production's reader then drops the call silently
    (the build flags it). A confirmation is drawn ONCE per page version, so drawing on fewer calls
    than are on file would seal a read of other inputs for good: it refuses, and records nothing."""
    from vinci.dossier import ciq_sheets
    from vinci.dossier.ciq import CiqParseError
    from vinci.dossier.confirmation import ConfirmationError, confirm
    root = _two_calls(tmp_path)
    real = ciq_sheets.read_text

    def busy(path: Path, fmt: typing.Any = None, **kw: typing.Any) -> str:
        if "Q3 2026" in path.name:
            raise CiqParseError(f"{path.name}: LibreOffice exited 1 converting it")
        return real(path, fmt, **kw)
    monkeypatch.setattr(ciq_sheets, "read_text", busy)
    record = tmp_path / "c.jsonl"
    llm = _Scripted([BULL] * 10)
    with pytest.raises(ConfirmationError, match="did not read"):
        confirm(googl, llm=llm, ciq_root=root, record=record)
    assert llm.calls == 0 and not record.exists()


def test_every_call_that_reads_is_drawn_on(googl: dict[str, typing.Any], tmp_path: Path) -> None:
    """(+) Both calls read: both reach the request, and the confirmation is drawn."""
    from vinci.dossier.confirmation import page_transcripts
    text, verified = page_transcripts("GOOGL", ciq_root=_two_calls(tmp_path), page=googl)
    assert text is not None and text.count("Earnings Call") == 2 and verified is False
