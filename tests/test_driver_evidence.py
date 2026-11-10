"""RG-D19 PR 2: the private evidence store, i.e. the spool the assembling machine writes and the
R2 upload the ingest machine runs (operator ruling 2026-11-10, option 1).

Run against a LOCAL STAND-IN, never the operator's Drive folder or the bucket:
- a pytest temporary folder plays the spool;
- `tests.test_facts_remote.FakeBucket`, the fact store's S3 stand-in, plays R2.

`tests/conftest.py` unsets ``$VINCI_EVIDENCE_SPOOL`` for every test, so a shell that has it set
cannot send a fixture row to the real folder.

The end-to-end pins run on REAL committed pages. Each transcript row is given the call-only
locator PR 3's pass writes (its call, from `source_ref`, and its quote's hash), then spooled and
read back. Licensed text never leaves memory and the temporary folder.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.stripped_pages import rows_with_words, synthetic_page
from tests.test_facts_remote import FakeBucket, _client
from vinci.dossier import assemble
from vinci.dossier import driver_evidence as de
from vinci.dossier import schemas as ds
from vinci.dossier.driver_extract import quote_key
from vinci.facts.remote import R2RequestError

ROOT = Path(__file__).resolve().parents[1]
_CALL = "Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf"
_QUOTE = "Widget shipments were down 7% in the quarter, as we expected."


def _rec(**kw: object) -> de.EvidenceRecord:
    loc = ds.TranscriptLocator(call=_CALL, transcript_sha256="a" * 64, paragraph=4,
                               speaker="Paul A. Smith", quote_sha256=quote_key(_QUOTE))
    base = {"locator": loc, "verbatim": _QUOTE,
            "following_context": "It recovered in October."}
    return de.EvidenceRecord(**{**base, **kw})  # type: ignore[arg-type]


# --- the spool is the operator's folder: never created, never in the repo, never manual/ciq -------

def test_an_unset_spool_names_its_variable() -> None:
    with pytest.raises(de.SpoolNotConfiguredError, match="VINCI_EVIDENCE_SPOOL"):
        de.EvidenceSpool.from_env({})
    assert de.EvidenceSpool.configured({}) is None


def test_a_missing_spool_fails_loud_names_its_variable_and_is_never_created(tmp_path: Path) -> None:
    """The coordinator's rule (2026-11-10): the code NEVER creates the folder."""
    missing = tmp_path / "driver-evidence"
    for make in (lambda: de.EvidenceSpool(missing),
                 lambda: de.EvidenceSpool.from_env({de.SPOOL_ENV: str(missing)}),
                 lambda: de.EvidenceSpool.configured({de.SPOOL_ENV: str(missing)})):
        with pytest.raises(de.SpoolMissingError, match="VINCI_EVIDENCE_SPOOL"):
            make()
    assert not missing.exists()


def test_a_spool_in_the_repo_or_under_manual_ciq_is_refused(tmp_path: Path) -> None:
    with pytest.raises(de.SpoolRefusedError, match="inside this repository"):
        de.EvidenceSpool(ROOT / "docs")
    ciq = tmp_path / "data for frontend (vinci)" / "manual" / "ciq"
    ciq.mkdir(parents=True)
    with pytest.raises(de.SpoolRefusedError, match="manual/ciq"):
        de.EvidenceSpool(ciq)
    beside = ciq.parent / "driver-evidence"   # BESIDE manual/ciq is where the ruling puts it
    beside.mkdir()
    assert de.EvidenceSpool(beside).root == beside


def test_a_spool_in_another_checkout_of_this_repo_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Agents build in WORKTREES: the main checkout and every sibling worktree are this repo
    too, so a spool in any of them is refused, not only one inside the running checkout."""
    main = tmp_path / "main"
    common = main / ".git"
    wt, sibling = main / ".claude" / "worktrees" / "wt", tmp_path / "elsewhere" / "sib"
    for tree in (wt, sibling):
        meta = common / "worktrees" / tree.name
        meta.mkdir(parents=True)
        tree.mkdir(parents=True)
        (tree / ".git").write_text(f"gitdir: {meta}\n")
        (meta / "gitdir").write_text(f"{tree / '.git'}\n")
    (main / "data").mkdir()
    (sibling / "data").mkdir()
    monkeypatch.setattr(de, "_REPO", wt)
    for inside in (main / "data", sibling / "data", wt):
        with pytest.raises(de.SpoolRefusedError, match="inside this repository"):
            de.EvidenceSpool(inside)
    outside = tmp_path / "driver-evidence"
    outside.mkdir()
    assert de.EvidenceSpool(outside).root == outside


def test_a_record_is_written_flat_once_and_never_overwritten(tmp_path: Path) -> None:
    spool = de.EvidenceSpool(tmp_path)
    rec = _rec()
    assert spool.put(rec) is True
    assert spool.put(rec) is False   # the same bytes again: a no-op
    (only,) = list(tmp_path.iterdir())
    assert only.is_file() and "/" not in only.name and only.name.endswith(".json")
    key = de.evidence_key(rec.locator)
    assert spool.get(key) == rec
    with pytest.raises(de.EvidenceBytesDifferError):
        spool.put(_rec(following_context="Another paragraph."))   # same key, another passage
    assert spool.get(key) == rec
    assert [p.name for p in tmp_path.iterdir()] == [only.name]   # no partial file left behind


def test_a_partial_write_left_in_the_spool_is_named_and_kept(tmp_path: Path) -> None:
    """A `.part` from a build that died mid-write is refused as evidence-store trouble, by name,
    and never removed here (it may be a running writer's)."""
    spool = de.EvidenceSpool(tmp_path)
    rec = _rec()
    path = spool.path(de.evidence_key(rec.locator))
    part = path.with_name(path.name + ".part")
    part.write_bytes(b"{")
    with pytest.raises(de.EvidenceError, match="partial write"):
        spool.put(rec)
    assert part.exists() and not path.exists()


def test_a_quote_that_does_not_hash_to_its_locator_is_refused(tmp_path: Path) -> None:
    spool = de.EvidenceSpool(tmp_path)
    with pytest.raises(de.EvidenceIntegrityError):
        spool.put(_rec(verbatim="Widget shipments were up 7% in the quarter."))
    rec = _rec()
    spool.put(rec)
    path = spool.path(de.evidence_key(rec.locator))
    path.write_bytes(path.read_bytes().replace(b"down 7%", b"up 7%"))   # tampered on disk
    with pytest.raises(de.EvidenceIntegrityError):
        spool.get(de.evidence_key(rec.locator))


def test_a_call_only_locator_keys_by_the_calls_name() -> None:
    loc = ds.TranscriptLocator(call=_CALL, quote_sha256=quote_key(_QUOTE))
    key = de.evidence_key(loc)
    assert key.startswith("driver-evidence/v1/unlocated/") and de.KEY.match(key)
    assert de.evidence_key(_rec().locator) == (
        f"driver-evidence/v1/{'a' * 64}/4/{quote_key(_QUOTE)}.json")


# --- the upload: the ingest machine's one write to R2 -------------------------------------------

def test_the_upload_writes_each_record_once_reads_it_back_and_leaves_other_files(
        tmp_path: Path) -> None:
    spool = de.EvidenceSpool(tmp_path)
    rec = _rec()
    spool.put(rec)
    (tmp_path / "driver-evidence__v1__copy 2.json").write_text("{}")   # a Drive conflict copy
    bucket = FakeBucket()
    with _client(bucket) as client:
        rep = de.upload_spool(spool, client)
        assert rep.written == [de.evidence_key(rec.locator)] and rep.already == []
        assert rep.skipped == ["driver-evidence__v1__copy 2.json"]
        again = de.upload_spool(spool, client)
        assert again.written == [] and again.already == rep.written
        assert de.fetch(client, rep.written[0]) == rec
    assert list(bucket.objects) == rep.written
    assert (tmp_path / "driver-evidence__v1__copy 2.json").exists()   # never deleted


def test_a_read_only_token_cannot_upload(tmp_path: Path) -> None:
    """This Mac's token: the upload refuses loud, and nothing is written."""
    spool = de.EvidenceSpool(tmp_path)
    spool.put(_rec())
    bucket = FakeBucket(writable=False)
    with _client(bucket) as client, pytest.raises(R2RequestError):
        de.upload_spool(spool, client)
    assert bucket.objects == {}


def test_a_second_upload_puts_and_compares_once_per_record(tmp_path: Path) -> None:
    """A key the bucket already holds is compared by `put_new` (PUT 412, then GET): no second
    read-back on top of it."""
    spool = de.EvidenceSpool(tmp_path)
    spool.put(_rec())
    bucket = FakeBucket()
    with _client(bucket) as client:
        de.upload_spool(spool, client)
        bucket.requests.clear()
        de.upload_spool(spool, client)
    assert [r.method for r in bucket.requests] == ["PUT", "GET"]


# --- end to end on committed pages --------------------------------------------------------------

def _with_call_only_locators(page: dict[str, object]) -> ds.Dossier:
    d = ds.Dossier.model_validate(page)
    od = d.mechanical.operating_drivers
    assert od is not None
    rows = [r.model_copy(update={"locator": ds.TranscriptLocator(
                call=r.source_ref.split(": ", 1)[1], quote_sha256=quote_key(r.verbatim))})
            if r.tier == "llm-fenced" and ": " in r.source_ref else r for r in od.rows]
    return d.model_copy(update={"mechanical": d.mechanical.model_copy(update={
        "operating_drivers": od.model_copy(update={"rows": rows})})})


def test_a_pages_transcript_rows_spool_and_read_back_whole(tmp_path: Path) -> None:
    """On a real page whose transcript rows are invented ones holding their words: every passage
    and every claim lands, and each stripped row reads back as the row it was. ONE RECORD PER
    PASSAGE, ONE PER CLAIM — three rows share one quote (as 63 committed passages did), so they
    share its passage and keep three claims."""
    spool = de.EvidenceSpool(tmp_path)
    d = _with_call_only_locators(synthetic_page())
    tx = [r for r in (d.mechanical.operating_drivers.rows
                      if d.mechanical.operating_drivers else []) if r.tier == "llm-fenced"]
    written, rep = de.spool_dossier(d, spool)
    assert rep.no_evidence == 0 and rep.written + rep.already == 2 * len(tx)
    keys = {de.evidence_key(r.locator) for r in tx if r.locator is not None}
    claims = {de.claim_key(r.locator.quote_sha256, de.value_key(r.value))
              for r in tx if r.locator is not None and r.value is not None}
    od = written.mechanical.operating_drivers
    assert od is not None
    stripped = [r.model_copy(update={"verbatim": None, "following_context": None,
                                     "value": None}) if r.tier == "llm-fenced" else r
                for r in od.rows]
    back = de.rehydrate(stripped, spool.get)
    assert [(r.verbatim, r.following_context, r.value) for r in back] == \
        [(r.verbatim, r.following_context, r.value) for r in od.rows]
    held, other = spool.keys()
    assert other == [] and all(p.is_file() for p in tmp_path.iterdir())   # flat: no folder made
    assert sorted(held) == sorted(keys | claims) and (len(keys), len(claims)) == (2, 4)


def test_every_committed_rows_locator_finds_its_passage_on_disk() -> None:
    """Each committed transcript row's locator finds its quote in its call on disk: the file by its
    sha256, the paragraph by its index, the quote by its hash (`stripped_pages.passage` asserts
    each). A row whose call is no longer on disk is counted, not checked; with no CIQ export at
    all (CI) the test skips and says so."""
    rows, skipped = rows_with_words()
    assert len(rows) > 500, (len(rows), skipped)


def test_the_assembly_spools_before_it_writes_the_page_and_a_bad_spool_stops_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(RG-D19 PR 3) The spool is REQUIRED: the page is written without its transcript words, so
    the spool is their only copy outside the licensed call. Unset, the build stops before the
    page; set and created, the words land first, and the page carries none of them."""
    d = _with_call_only_locators(synthetic_page())
    spool, out = tmp_path / "spool", tmp_path / "out"
    # unset: the build stops BEFORE the page
    with pytest.raises(de.SpoolNotConfiguredError, match="VINCI_EVIDENCE_SPOOL"):
        assemble._write(d, "", out / "a")
    assert not (out / "a" / "BRBR" / "dossier.json").exists()
    # set to a folder the operator has not created: the build stops BEFORE the page
    monkeypatch.setenv(de.SPOOL_ENV, str(spool))
    with pytest.raises(de.SpoolMissingError):
        assemble._write(d, "", out / "b")
    assert not (out / "b" / "BRBR" / "dossier.json").exists() and not spool.exists()
    # created by hand: the evidence lands, then the page
    spool.mkdir()
    assemble._write(d, "", out / "c")
    held, _ = de.EvidenceSpool(spool).keys()
    written = json.loads((out / "c" / "BRBR" / "dossier.json").read_text())
    rows = [r for r in written["mechanical"]["operating_drivers"]["rows"]
            if r["tier"] == "llm-fenced"]
    assert held and rows and not any(k in r for r in rows for k in
                                     ("verbatim", "following_context", "value"))
    assert all(r["locator"]["value_sha256"] for r in rows)
    # a transcript row with nothing to spool is said, never dropped silently
    od = d.mechanical.operating_drivers
    assert od is not None
    bare = [r.model_copy(update={"locator": None}) if r.tier == "llm-fenced" else r
            for r in od.rows]
    assemble._write(d.model_copy(update={"mechanical": d.mechanical.model_copy(update={
        "operating_drivers": od.model_copy(update={"rows": bare})})}), "", out / "d")
    assert "kept only in the licensed call" in capsys.readouterr().err


def test_a_bad_spool_stops_the_build_before_any_paid_phase(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refused at the TOP of `assemble_one`, before it reads the finalist, so no LLM call is
    made and thrown away: the finalist here is not even one."""
    monkeypatch.setenv(de.SPOOL_ENV, str(tmp_path / "not-created"))
    with pytest.raises(de.SpoolMissingError):
        assemble.assemble_one(None, cfg=None, resolver=None, graph=None,  # type: ignore[arg-type]
                              manual=None, out_root=tmp_path, llm=None)  # type: ignore[arg-type]
    assert not (tmp_path / "not-created").exists()


def test_two_listings_citing_one_call_share_its_record(tmp_path: Path) -> None:
    """The record is the passage, not the page (#PR2 review): a second share class citing the same
    call file meets the first one's record and writes nothing, never a refused build."""
    d = _with_call_only_locators(synthetic_page())
    twin = d.model_copy(update={"ticker": "BRBR.B"})
    spool = de.EvidenceSpool(tmp_path)
    _, first = de.spool_dossier(d, spool)
    _, second = de.spool_dossier(twin, spool)
    assert first.written > 0 and second.written == 0 and second.already == first.written + \
        first.already


def test_the_example_env_declares_the_spool_commented_and_with_no_path() -> None:
    """The operator's folder is named only in the git-ignored `.env` (coordinator, 2026-11-10:
    never a local path in a committed file). The example declares the variable, commented out,
    so a copied `.env.example` sets no spool at all."""
    lines = [ln for ln in (ROOT / ".env.example").read_text().splitlines()
             if de.SPOOL_ENV in ln]
    assert lines == [f"# {de.SPOOL_ENV}="]
