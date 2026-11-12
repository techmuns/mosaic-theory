"""THE 12-WORD RULE AT BUILD, AND THE $0 CUT (operator ruling 2026-11-11, verbatim: "$0 guard +
redaction now (Recommended)"; owner: "A's driver facts, after PR A (Recommended)").

CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS. Its corpus test
(`tests/test_public_transcript_text.py`) holds that between quotation marks only, and three
committed synthesis claims copied 14 to 15 of a call's words without them (LLY, VITL, WERN —
Codex, round 2 of #1006). So:
- the build reads every synthesis string against its own calls (`synthesis.transcript_runs`) and
  REFUSES a page holding a run of more than 12 (`assemble._refuse_transcript_runs`);
- `vinci transcript-run-cut` cut the three committed runs to 12 words and "…" ($0, recorded).

Words are compared as the rule counts them (split on whitespace), folded by the verbatim check's
key (case, quote marks, dashes) with edge punctuation read off. Value pins sit on the frozen SMPL
page with a constructed call; the committed corpus is checked against the licensed calls, which
CI cannot hold, so that check skips there.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests.stripped_pages import ciq_root
from vinci.dossier import assemble
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.dossier import transcript_run_pass as trp
from vinci.dossier.confirmation import ConfirmationError

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"
_COMMITTED = sorted((ROOT / "data/dossiers").glob("*/dossier.json"))


def _page() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(_FROZEN_SMPL.read_text())
    return page


def _claim(page: dict[str, Any]) -> tuple[str, str]:
    """(where, text) of the frozen page's first bull point of 20 words or more."""
    for i, p in enumerate(page["synthesis"]["bull_points"]):
        if len(p["claim"].split()) >= 20:
            return f"bull_points[{i}].claim", p["claim"]
    raise AssertionError("the frozen SMPL page has no bull point of 20 words")


def _call_holding(claim: str, n: int, *, start: int = 2) -> str:
    """A call's text holding ``n`` consecutive words of ``claim`` (from its ``start``-th word), set
    among words no synthesis writes."""
    words = claim.split()[start:start + n]
    return "Operator: thank you. " + " ".join(words) + " — and that concludes the call."


def test_a_string_sharing_13_words_with_its_calls_is_refused_at_build() -> None:
    page = _page()
    where, claim = _claim(page)
    synth = ds.Synthesis.model_validate(page["synthesis"])
    call = _call_holding(claim, 13)
    runs = syn.transcript_runs(synth, call)
    assert [(r.where, r.words) for r in runs] == [(where, 13)]
    with pytest.raises(assemble.DossierAssemblyError,
                       match=re.escape(f"{where} (13 words)")):
        assemble._refuse_transcript_runs(synth, call, ticker="SMPL")
    # the guard in `_validate` names the field and the run length
    mech = ds.MechanicalLayer.model_validate(page["mechanical"])
    _, flags = syn._validate(synth, mech, ticker="SMPL", name="Simply Good Foods",
                             transcript=call)
    assert any(f.startswith(f"TRANSCRIPT-RUN {where}: shares 13 consecutive words")
               and f.endswith("assembly refuses such a page") for f in flags)


@pytest.mark.parametrize("n", [11, 12])
def test_an_overlap_of_12_words_or_fewer_passes(n: int) -> None:
    page = _page()
    _, claim = _claim(page)
    synth = ds.Synthesis.model_validate(page["synthesis"])
    call = _call_holding(claim, n)
    assert syn.transcript_runs(synth, call) == []
    assemble._refuse_transcript_runs(synth, call, ticker="SMPL")   # does not raise


def test_the_words_are_compared_folded() -> None:
    """Case, quote marks, dashes and edge punctuation do not hide a run: the call prints the
    claim's words in capitals, each followed by a comma."""
    page = _page()
    where, claim = _claim(page)
    synth = ds.Synthesis.model_validate(page["synthesis"])
    words = claim.split()[2:17]
    call = "Speaker: " + ", ".join(w.upper().replace("'", "’") for w in words) + "."
    assert [(r.where, r.words) for r in syn.transcript_runs(synth, call)] == [(where, 15)]


def test_no_synthesis_or_no_call_is_no_run() -> None:
    page = _page()
    synth = ds.Synthesis.model_validate(page["synthesis"])
    assert syn.transcript_runs(None, "a b c") == []
    assert syn.transcript_runs(synth, None) == []
    assert syn.transcript_runs(synth, "") == []


def test_the_cut_keeps_12_words_and_marks_the_rest() -> None:
    """A 15-word run becomes its first 12 words and "…"; the text before and after the run is kept
    character for character; no other string moves; the cut page holds no run; a second pass cuts
    nothing."""
    page = _page()
    where, claim = _claim(page)
    call = _call_holding(claim, 15)
    out, cuts = trp.prepare(page, call)
    assert [c[0] for c in cuts] == [where]
    # where the 14th and 17th words of the claim end (the run is words 3 to 17), punctuation off
    ends = [m.end() - (len(m.group()) - len(m.group().rstrip(syn._RUN_EDGE)))
            for m in re.finditer(r"\S+", claim)]
    assert cuts[0][1] == claim
    assert cuts[0][2] == claim[:ends[2 + 11]] + trp.ELLIPSIS + claim[ends[2 + 14]:]
    moved = [k for k, v in out["synthesis"].items() if v != page["synthesis"][k]]
    assert moved == [where.split("[")[0]]
    assert syn.transcript_runs(ds.Synthesis.model_validate(out["synthesis"]), call) == []
    again, more = trp.prepare(out, call)
    assert more == [] and again == out


def test_a_cut_is_named_without_its_words() -> None:
    """The string before a cut holds the copied run, which no log may carry: the pass names a cut
    by its word counts, the span it removed and two hashes. No four consecutive words of the
    string reach the line, and the CLI prints a cut through this alone."""
    page = _page()
    _, claim = _claim(page)
    _, cuts = trp.prepare(page, _call_holding(claim, 15))
    where, before, after = cuts[0]
    line = trp.describe_cut(before, after)
    words = before.split()
    assert line.startswith(f"{len(words)} → {len(after.split())} words; characters ")
    assert not any(" ".join(words[i:i + 4]) in line for i in range(len(words) - 3))
    import inspect

    from vinci import cli
    body = inspect.getsource(cli._cmd_transcript_run_cut)
    assert "trp.describe_cut(before, after)" in body and "before:" not in body


def test_the_pass_refuses_a_page_whose_call_did_not_read(tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    jp = tmp_path / "SMPL" / "dossier.json"
    jp.parent.mkdir()
    jp.write_text(_FROZEN_SMPL.read_text())
    def unread(t: str, *, ciq_root: Path, page: dict[str, Any]) -> tuple[str, bool]:
        raise ConfirmationError(f"{t}: 1 of 1 call(s) on file did not read (call.rtf)")
    monkeypatch.setattr(trp, "page_transcripts", unread)
    o = trp.run(jp, tmp_path, dry_run=False, record=False)
    assert o.status == "refused" and "did not read" in o.detail
    assert jp.read_text() == _FROZEN_SMPL.read_text()


def test_the_pass_refuses_a_page_citing_a_call_not_on_disk(tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """(review round 0) A page whose driver rows cite a call that is not on disk is refused, never
    read against the calls that are: it would be called clean against text it was not built from.
    (−) The same page citing the call that IS on disk is read."""
    page = _page()
    _, claim = _claim(page)
    rows = page["mechanical"]["operating_drivers"]["rows"]
    row = next(r for r in rows if r.get("tier") == "llm-fenced")
    row["locator"] = {"transcript_sha256": "b" * 64}
    jp = tmp_path / "SMPL" / "dossier.json"
    jp.parent.mkdir()
    jp.write_text(json.dumps(page))
    call = _call_holding(claim, 15)
    monkeypatch.setattr(trp, "page_transcripts", lambda t, **_k: (call, False))
    # every other call the page cites is on disk; the row's is not
    on_disk = trp.cited_calls(page) - {"b" * 64}
    monkeypatch.setattr(trp, "_on_disk_shas", lambda t, r: on_disk)
    o = trp.run(jp, tmp_path, dry_run=True, record=False)
    assert o.status == "refused" and o.detail.count("is not on disk") == 1
    assert "cited call bbbbbbbbbbbb is not on disk" in o.detail
    on_disk.add("b" * 64)
    assert trp.run(jp, tmp_path, dry_run=True, record=False).status == "would write"


def test_the_build_refuses_after_the_synthesis_and_before_the_write() -> None:
    """`assemble_one` calls the refusal on the synthesis it is about to write: after the null
    check, before `_write`."""
    src = Path(assemble.__file__).read_text()
    at = src.index("_refuse_transcript_runs(synthesis, transcript, ticker=ticker)")
    assert (src.index("synthesis = _require_synthesis(synthesis") < at
            < src.index("return _write(dossier, llm_log, out_root)"))


@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_no_committed_synthesis_copies_more_than_12_words_of_its_calls(path: Path) -> None:
    """The committed corpus against the licensed calls on disk (CI holds none, so this skips
    there). FAILED before the cut on LLY (15 words), VITL (14) and WERN (14)."""
    root = ciq_root()
    page = json.loads(path.read_text())
    if not page.get("synthesis"):
        pytest.skip("no synthesis on this page")
    transcript, problems = trp.page_transcript(page, root)
    # a checkout whose calls are not the page's own (an older copy of the exports) cannot check
    # it, and says so; a call that is the page's and does not read is a failure
    if problems and all("is not on disk" in p or "input record" in p for p in problems):
        pytest.skip(f"this checkout's calls are not the page's own ({problems[0]}): point "
                    "VINCI_CIQ_ROOT at the Drive mirror")
    assert not problems, f"the page's calls cannot all be read: {problems}"
    if transcript is None:
        pytest.skip("no call on disk for this page")
    runs = syn.transcript_runs(ds.Synthesis.model_validate(page["synthesis"]), transcript)
    assert runs == [], [(r.where, r.words) for r in runs]
