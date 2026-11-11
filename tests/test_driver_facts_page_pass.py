"""RG-D19 PR 3: the page pass, and every reader of a transcript row once its words are off the page.

All of it runs against LOCAL STAND-INS:
- the spool is a pytest temporary folder (`conftest.evidence_spool` or `tmp_path`);
- the CIQ folder is a temporary one.

The pages are real committed pages whose transcript rows are invented ones holding their words
(`tests/stripped_pages.synthetic_page`), so the pass and every reader run on a real page's shape
and no licensed text is in any fixture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.stripped_pages import synthetic_page
from vinci.dossier import driver_evidence as de
from vinci.dossier import driver_pass as dp
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.evals import variants
from vinci.evals.capture_child import pre_synthesis_mech

PRIVATE = ("verbatim", "following_context", "value")


def _tx_rows(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in page["mechanical"]["operating_drivers"]["rows"] if r["tier"] == "llm-fenced"]


def _page_file(tmp_path: Path, ticker: str) -> Path:
    jp = tmp_path / "dossiers" / ticker / "dossier.json"
    jp.parent.mkdir(parents=True)
    jp.write_text(json.dumps(synthetic_page(ticker)))
    return jp


# --- the serializer drops words that are filed, and no others -------------------------------------

def test_a_page_round_trips_byte_for_byte_until_its_words_are_filed() -> None:
    """The live pages before the pass: the one serializer moves no byte of them. A row's words
    leave the page only once `spool_dossier` filed them (its locator carries the claim's hash)."""
    d = ds.Dossier.model_validate(synthetic_page("BRBR"))
    text = ds.dossier_json(d)
    assert ds.dossier_json(ds.Dossier.model_validate_json(text)) == text   # stable, words kept
    assert all(r.get("verbatim") for r in _tx_rows(json.loads(text)))
    od = d.mechanical.operating_drivers
    assert od is not None
    filed = [r.model_copy(update={"locator": ds.TranscriptLocator(
        call="x.rtf", quote_sha256="a" * 64, value_sha256="b" * 64)})
        if r.tier == "llm-fenced" else r for r in od.rows]
    out = json.loads(ds.dossier_json(d.model_copy(update={"mechanical": d.mechanical.model_copy(
        update={"operating_drivers": od.model_copy(update={"rows": filed})})})))
    rows = out["mechanical"]["operating_drivers"]["rows"]
    assert all(not any(k in r for k in PRIVATE) for r in rows if r["tier"] == "llm-fenced")
    # an anchored row keeps its text: a filing's or CIQ's words, not a transcript's
    anchored = [r for r in rows if r["tier"] == "anchored"]
    assert anchored and all(r.get("verbatim") for r in anchored)


# --- the pass -------------------------------------------------------------------------------------

def test_the_pass_files_the_words_then_writes_the_page_without_them(tmp_path: Path) -> None:
    """With no call on disk, each row's locator is call-only (its call, its quote's hash), never a
    guessed paragraph. Every passage and every claim is in the spool, and the page is written
    through the recorded writer, with no word of any transcript row."""
    jp = _page_file(tmp_path, "BRBR")
    before = json.loads(jp.read_text())
    spool_dir = tmp_path / "spool"
    spool_dir.mkdir()
    spool = de.EvidenceSpool(spool_dir)
    out = dp.run(jp, tmp_path / "ciq", spool=spool, dry_run=False)
    assert out.status == "written" and out.rows == len(_tx_rows(before)) > 0
    assert (out.located, out.call_only) == (0, out.rows)
    after = json.loads(jp.read_text())
    rows = _tx_rows(after)
    assert len(rows) == out.rows
    for r, r0 in zip(rows, _tx_rows(before), strict=True):
        assert not any(k in r for k in PRIVATE)
        loc = r["locator"]
        assert loc["paragraph"] is None and loc["transcript_sha256"] is None
        assert loc["call"] == r0["source_ref"].split(": ", 1)[1]
        passage = spool.get(de.evidence_key(ds.TranscriptLocator.model_validate(loc)))
        claim = spool.get(de.claim_key(loc["quote_sha256"], loc["value_sha256"]))
        assert isinstance(passage, de.EvidenceRecord) and isinstance(claim, de.ClaimRecord)
        assert (passage.verbatim, passage.following_context, claim.stated_value) == \
            (r0["verbatim"], r0.get("following_context"), r0["value"])
        assert r["value_status"] in ("verified", "qualitative", "unknown")
    assert after["layer_refreshes"][-1]["writer"] == dp.WRITER
    assert after["layer_refreshes"][-1]["layers"] == ["mechanical.operating_drivers"]
    # and again: nothing left to take off, nothing written
    again = dp.run(jp, tmp_path / "ciq", spool=spool, dry_run=False)
    assert again.status == "unchanged" and json.loads(jp.read_text()) == after


def test_a_call_on_disk_gives_the_paragraph_and_the_speaker(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When the cited call is on disk and holds the quote and its context (the rest of the
    speaker's paragraph after it), the locator is the full one."""
    jp = _page_file(tmp_path, "BRBR")
    row = _tx_rows(json.loads(jp.read_text()))[0]
    call = row["source_ref"].split(": ", 1)[1]
    body = (f"\nJane  Roe \nChief Financial Officer \n\nOpening remarks.\n\n{row['verbatim']} "
            f"{row['following_context']}\n")
    monkeypatch.setattr(dp, "_calls_on_disk", lambda t, root: ({call: body}, {call: "c" * 64}))
    dossier, out = dp.prepare(ds.Dossier.model_validate_json(jp.read_text()), tmp_path)
    od = dossier.mechanical.operating_drivers
    assert od is not None
    first = next(r for r in od.rows if r.tier == "llm-fenced")
    assert first.locator is not None
    assert (first.locator.transcript_sha256, first.locator.paragraph, first.locator.speaker) == \
        ("c" * 64, 2, "Jane Roe")
    assert out.located >= 1


def test_a_context_from_another_export_of_the_call_gets_no_file_hash(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A full locator says the row's words are that file's. When the row's quote is in the call on
    disk but its context is not the one that file gives after it (the UBER fixture of 2026-10-26:
    a comma apart), the locator is call-only, never that file's hash: its
    passage would claim words the file does not hold, under the key another page's passage of the
    same file and paragraph takes."""
    jp = _page_file(tmp_path, "BRBR")
    row = _tx_rows(json.loads(jp.read_text()))[0]
    call = row["source_ref"].split(": ", 1)[1]
    body = (f"\nJane  Roe \nChief Financial Officer \n\n{row['verbatim']} They recovered, in "
            "October.\n")
    monkeypatch.setattr(dp, "_calls_on_disk", lambda t, root: ({call: body}, {call: "c" * 64}))
    dossier, out = dp.prepare(ds.Dossier.model_validate_json(jp.read_text()), tmp_path)
    od = dossier.mechanical.operating_drivers
    assert od is not None
    first = next(r for r in od.rows if r.tier == "llm-fenced")
    assert first.locator is not None
    assert (first.locator.transcript_sha256, first.locator.paragraph) == (None, None)
    assert out.context_differs >= 1 and out.located + out.call_only == out.rows
    # the same file holding the row's own context gives the full locator
    held = body.replace("They recovered, in October.", str(row["following_context"]))
    monkeypatch.setattr(dp, "_calls_on_disk", lambda t, root: ({call: held}, {call: "c" * 64}))
    dossier, out = dp.prepare(ds.Dossier.model_validate_json(jp.read_text()), tmp_path)
    od = dossier.mechanical.operating_drivers
    assert od is not None
    first = next(r for r in od.rows if r.tier == "llm-fenced")
    assert first.locator is not None and first.locator.transcript_sha256 == "c" * 64
    assert out.context_differs == 0


def test_the_pass_never_drops_a_word_unfiled(tmp_path: Path) -> None:
    """No spool, no write: the page is untouched. A dry run spools and writes nothing. A row citing
    no call is refused: its words would have nowhere to be filed."""
    jp = _page_file(tmp_path, "BRBR")
    text = jp.read_text()
    with pytest.raises(de.SpoolNotConfiguredError):
        dp.run(jp, tmp_path, spool=None, dry_run=False)
    assert jp.read_text() == text
    assert dp.run(jp, tmp_path, spool=None, dry_run=True).status == "would write"
    assert jp.read_text() == text
    page = json.loads(text)
    _tx_rows(page)[0]["source_ref"] = "CIQ transcript"
    jp.write_text(json.dumps(page))
    assert dp.run(jp, tmp_path, spool=None, dry_run=False).status == "refused"


def test_a_cited_call_on_disk_that_does_not_read_refuses_the_page(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A cited call that is on disk but does not read refuses the page, unwritten and unspooled.
    LibreOffice fails a conversion while another runs: on the re-sync onto #986 (2026-11-11) FUBO's
    dry run located 0 of its 8 rows, where the first real pass had located all 8. Before this,
    those rows went call-only for a failed read, not for a quote the file lacks, and a call-only
    passage is filed for good under another key. The same file reading gives the full locator
    through the same path, and a call not on disk stays call-only
    (`test_the_pass_files_the_words_then_writes_the_page_without_them`)."""
    from vinci.dossier import ciq_sheets
    from vinci.dossier.ciq import CiqParseError

    jp = _page_file(tmp_path, "BRBR")
    text = jp.read_text()
    row = _tx_rows(json.loads(text))[0]
    call = row["source_ref"].split(": ", 1)[1]
    folder = tmp_path / "ciq" / "BRBR"
    folder.mkdir(parents=True)
    (folder / call).write_bytes(b"{\\rtf1 a stand-in call}")

    def failed_read(path: Path, *_: object, **__: object) -> str:
        raise CiqParseError(f"{path.name}: a failed read")

    monkeypatch.setattr(ciq_sheets, "read_text", failed_read)
    spool_dir = tmp_path / "spool"
    spool_dir.mkdir()
    out = dp.run(jp, tmp_path / "ciq", spool=de.EvidenceSpool(spool_dir), dry_run=False)
    assert out.status == "refused" and call in out.detail
    assert jp.read_text() == text and not any(spool_dir.iterdir())
    # the same file reading: the full locator, through the same `_calls_on_disk`
    body = f"Jane  Roe \nChief Financial Officer \n\n{row['verbatim']} {row['following_context']}\n"
    monkeypatch.setattr(ciq_sheets, "read_text", lambda path, *_, **__: body)
    _, out = dp.prepare(ds.Dossier.model_validate_json(text), tmp_path / "ciq")
    assert out.status != "refused" and out.located >= 1


# --- every reader, once the words are off the page ------------------------------------------------

def _stripped(tmp_path: Path, ticker: str = "BRBR") -> dict[str, Any]:
    jp = _page_file(tmp_path, ticker)
    spool_dir = tmp_path / "spool"
    spool_dir.mkdir()
    dp.run(jp, tmp_path / "ciq", spool=de.EvidenceSpool(spool_dir), dry_run=False)
    page: dict[str, Any] = json.loads(jp.read_text())
    return page


def test_the_replay_refuses_a_page_whose_words_are_off_it(tmp_path: Path) -> None:
    """A replay from a stripped page would send a request the build never sent, and call it the
    build's. Refused; the page as it was replays as before."""
    pre_synthesis_mech(synthetic_page("BRBR"))
    with pytest.raises(ValueError, match="private store"):
        pre_synthesis_mech(_stripped(tmp_path))


def test_the_panel_transform_keeps_a_stripped_rows_committed_fact(tmp_path: Path) -> None:
    page = _stripped(tmp_path)
    mech = ds.MechanicalLayer.model_validate(page["mechanical"])
    assert variants.driver_facts(mech, variants.Context(page=page)) == mech
    od = mech.operating_drivers
    assert od is not None
    blank = [r.model_copy(update={"value_status": None}) if r.tier == "llm-fenced" else r
             for r in od.rows]
    with pytest.raises(variants.TransformError, match="neither words nor a fact"):
        variants.driver_facts(mech.model_copy(update={"operating_drivers": od.model_copy(
            update={"rows": blank})}), variants.Context(page=page))


def test_a_stripped_row_reads_as_its_checked_figures_never_its_lost_words(tmp_path: Path) -> None:
    """The scenario template and the digest read a stripped row from its fact alone."""
    from vinci.dossier import propose

    page = _stripped(tmp_path)
    lines = propose._operating_driver_lines(page)
    rows = _tx_rows(page)
    assert len(lines) == len(page["mechanical"]["operating_drivers"]["rows"]) + 1
    assert not any(": None →" in ln for ln in lines)
    for r in rows:
        want = syn.driver_value_as_read(None, r["value_status"], r.get("unknown_reason"),
                                        r.get("figures"))
        assert any(f"{r['metric']}: {want} →" in ln for ln in lines), r["metric"]
    assert syn.figures_text([{"value": 7.0, "unit": "%", "change": "down"},
                             {"value": 175.0, "scale": "e6", "qualifier": "at_least"}]) == \
        "down 7%; at least 175 million"
    assert syn.driver_value_as_read(None, "qualitative", None, []).startswith("stated, with no")


def test_a_claim_is_its_own_record_checked_by_its_hash(tmp_path: Path) -> None:
    spool = de.EvidenceSpool(tmp_path)
    claim = de.ClaimRecord(quote_sha256="a" * 64, value_sha256=de.value_key("down 7%"),
                           stated_value="down 7%")
    assert spool.put(claim) is True and spool.put(claim) is False
    key = de.claim_key("a" * 64, de.value_key("down 7%"))
    assert de.KEY.match(key) and spool.get(key) == claim
    with pytest.raises(de.EvidenceIntegrityError):
        spool.put(claim.model_copy(update={"stated_value": "up 7%"}))
    path = spool.path(key)
    path.write_bytes(path.read_bytes().replace(b"down", b"up"))
    with pytest.raises(de.EvidenceIntegrityError):
        spool.get(key)


_LLM = object()   # any client: `_require_spool` asks only whether the build is a paid one


def test_a_name_with_a_transcript_needs_the_spool_and_a_name_without_one_does_not(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`assemble._require_spool`, which `assemble_one` calls right after its bundle loads: before
    the covenant, driver and synthesis calls are bought."""
    from vinci.dossier import assemble

    class _Bundle:
        def __init__(self, tx: bool) -> None:
            self.tx = tx

        def all_workbooks(self, kind: str) -> tuple[str, ...]:
            return ("call.rtf",) if self.tx and kind == "transcript" else ()

    assemble._require_spool(_Bundle(tx=False), _LLM)  # type: ignore[arg-type]
    with pytest.raises(de.SpoolNotConfiguredError, match="VINCI_EVIDENCE_SPOOL"):
        assemble._require_spool(_Bundle(tx=True), _LLM)  # type: ignore[arg-type]
    monkeypatch.setenv(de.SPOOL_ENV, str(tmp_path / "not-created"))
    with pytest.raises(de.SpoolMissingError):
        assemble._require_spool(_Bundle(tx=True), _LLM)  # type: ignore[arg-type]
    assert not (tmp_path / "not-created").exists()
    # FAILED before the review fix: the $0 pre-spend build (`llm=None`) extracts no transcript
    # row, so it has no words to file, and was refused for want of the operator's spool
    monkeypatch.delenv(de.SPOOL_ENV)
    assemble._require_spool(_Bundle(tx=True), None)  # type: ignore[arg-type]
    src = Path(assemble.__file__).read_text()
    assert src.index("_require_spool(bundle, llm)") < src.index("extract_transcript_drivers(\n")


def test_a_figure_past_six_digits_reads_whole_not_in_exponent_form() -> None:
    """FAILED before the review fix: `:g` printed 1,234,567 subscribers as "1.23457e+06" in the
    analyst's template and the synthesis digest — a different number, in a form no call says."""
    assert syn.figures_text([{"value": 1234567.0}]) == "1234567"
    assert syn.figures_text([{"value": 1.25, "currency": "$", "scale": "e9"}]) == "$1.25 billion"


def test_a_row_read_back_spools_to_the_passage_it_came_from(tmp_path: Path) -> None:
    """FAILED before the review fix: the passage record embedded the row's locator whole, so a row
    read back (`rehydrate`, its locator still carrying the claim's `value_sha256`) wrote other
    bytes under the passage's key and was refused as an overwrite."""
    spool = de.EvidenceSpool(tmp_path)
    d = ds.Dossier.model_validate(synthetic_page("BRBR"))
    od = d.mechanical.operating_drivers
    assert od is not None
    located = [r.model_copy(update={"locator": ds.TranscriptLocator(
        call=r.source_ref.split(": ", 1)[1], quote_sha256=de.quote_key(r.verbatim))})
        if r.tier == "llm-fenced" and r.verbatim and ": " in r.source_ref else r for r in od.rows]
    d = d.model_copy(update={"mechanical": d.mechanical.model_copy(update={
        "operating_drivers": od.model_copy(update={"rows": located})})})
    written, first = de.spool_dossier(d, spool)
    assert first.written > 0
    wod = written.mechanical.operating_drivers
    assert wod is not None
    stripped = [r.model_copy(update={"verbatim": None, "following_context": None, "value": None})
                if r.tier == "llm-fenced" else r for r in wod.rows]
    back = de.rehydrate(stripped, spool.get)
    again = d.model_copy(update={"mechanical": d.mechanical.model_copy(update={
        "operating_drivers": wod.model_copy(update={"rows": back})})})
    _, second = de.spool_dossier(again, spool)
    assert second.written == 0 and second.already == first.written + first.already


# --- the vote rule's confirmation reads the words back (operator, 2026-11-11) ---------------------
# "Read them back from the store (Recommended)": C(iv)'s ten draws (`confirmation.confirm`, inside
# `log-verdict`) are drawn on the committed page, which no longer holds a filed row's words.

class _Capturing:
    """Records every request the synthesis sends and answers each with a scripted draw, so no call
    is made and none is paid."""

    model = "capturing-model"

    def __init__(self) -> None:
        self.requests: list[str] = []

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.requests.append(json.dumps({"system": system, "user": user, "tool": tool},
                                        sort_keys=True, default=str))
        return {"evidence_balance": "mixed — two-sided and unresolved.",
                "bull_points": [{"claim": "c", "source_ref": "r"}],
                "bear_points": [{"claim": "c", "source_ref": "r"}], "twin_reference_cases": [],
                "decisive_question": {"question": "q?", "evidence_for": [],
                                      "evidence_against": []},
                "key_unknowns": ["u"]}


def _confirmable(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    """TECX's committed page holding the invented transcript rows. Its BUILD record lists no
    transcript, so on an empty CIQ folder the confirmation verifies its inputs. Returned: the page
    as the pass holds it just before the words come off (facts and locators given, words kept),
    the page the pass wrote, and the spool it filed the words in."""
    jp = _page_file(tmp_path, "TECX")
    ciq = tmp_path / "ciq"
    ciq.mkdir()
    held, _ = dp.prepare(ds.Dossier.model_validate_json(jp.read_text()), ciq)
    spool_dir = tmp_path / "spool"
    spool_dir.mkdir()
    assert dp.run(jp, ciq, spool=de.EvidenceSpool(spool_dir), dry_run=False).status == "written"
    after = json.loads(jp.read_text())
    assert _tx_rows(after) and not any(r.get("verbatim") for r in _tx_rows(after))
    before = {**after, "mechanical": json.loads(held.mechanical.model_dump_json())}
    assert all(r.get("verbatim") for r in _tx_rows(before))
    return before, after, spool_dir


def test_the_confirmation_reads_the_words_back_and_sends_the_request_it_sent_before(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) On the stripped page, with the store configured, every one of the ten requests is
    byte-identical to the confirmation's request on the same page before its words came off, and
    the two readers agree on the re-filled layer. (−) Drawn on the page as it stands, without the
    read-back, the request differs: it would hold the rows' figures, not their words."""
    from vinci.dossier import confirmation as cf
    from vinci.evals.capture_child import pre_synthesis_mech

    before, after, spool_dir = _confirmable(tmp_path)
    ciq = tmp_path / "ciq"
    monkeypatch.delenv(de.SPOOL_ENV, raising=False)
    words = _Capturing()
    cf.confirm(before, llm=words, ciq_root=ciq, record=tmp_path / "before.jsonl")
    monkeypatch.setenv(de.SPOOL_ENV, str(spool_dir))
    refilled = _Capturing()
    cf.confirm(after, llm=refilled, ciq_root=ciq, record=tmp_path / "after.jsonl")
    assert len(words.requests) == len(refilled.requests) == cf.CONFIRM_DRAWS
    assert refilled.requests == words.requests
    layer = cf.with_words(cf.layer_as_synthesized(after), "TECX")
    refilled_page = {**after, "mechanical": json.loads(layer.model_dump_json())}
    assert layer.model_dump_json() == pre_synthesis_mech(refilled_page).model_dump_json()
    # the rows read back are the rows before the words came off, but for the hash of the stated
    # value that filing the claim adds to each locator
    def unfiled(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{**r, "locator": {**r["locator"], "value_sha256": None}} if r.get("locator")
                else r for r in rows]
    assert unfiled(_tx_rows(refilled_page)) == _tx_rows(before)
    # the same page drawn without the read-back
    monkeypatch.setattr(cf, "with_words", lambda mech, ticker, get=None: mech)
    bare = _Capturing()
    cf.confirm(after, llm=bare, ciq_root=ciq, record=tmp_path / "bare.jsonl")
    assert bare.requests[0] != words.requests[0]


def test_a_stripped_page_is_not_confirmed_without_its_words(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) No store configured, or a store missing a row's records: refused before any draw and
    not recorded, so the page's one confirmation is not used up. (+) A page that holds its words
    needs no store."""
    from vinci.dossier import confirmation as cf

    before, after, _ = _confirmable(tmp_path)
    ciq, record = tmp_path / "ciq", tmp_path / "c.jsonl"
    monkeypatch.delenv(de.SPOOL_ENV, raising=False)
    for spool in (None, tmp_path / "empty-spool"):
        if spool is not None:
            spool.mkdir()
            monkeypatch.setenv(de.SPOOL_ENV, str(spool))
        llm = _Capturing()
        with pytest.raises(cf.ConfirmationError, match="VINCI_EVIDENCE_SPOOL"):
            cf.confirm(after, llm=llm, ciq_root=ciq, record=record)
        assert llm.requests == [] and not record.exists()
    monkeypatch.delenv(de.SPOOL_ENV)
    assert cf.with_words(cf.layer_as_synthesized(before), "TECX") == \
        cf.layer_as_synthesized(before)
