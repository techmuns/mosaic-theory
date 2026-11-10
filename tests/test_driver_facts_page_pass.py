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

    assemble._require_spool(_Bundle(tx=False))  # type: ignore[arg-type]
    with pytest.raises(de.SpoolNotConfiguredError, match="VINCI_EVIDENCE_SPOOL"):
        assemble._require_spool(_Bundle(tx=True))  # type: ignore[arg-type]
    monkeypatch.setenv(de.SPOOL_ENV, str(tmp_path / "not-created"))
    with pytest.raises(de.SpoolMissingError):
        assemble._require_spool(_Bundle(tx=True))  # type: ignore[arg-type]
    assert not (tmp_path / "not-created").exists()
    src = Path(assemble.__file__).read_text()
    assert src.index("_require_spool(bundle)") < src.index("extract_transcript_drivers(\n")
