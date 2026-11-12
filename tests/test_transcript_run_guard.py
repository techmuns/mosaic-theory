"""THE 12-WORD RULE AT BUILD, AND THE $0 CUT (operator ruling 2026-11-11, verbatim: "$0 guard +
redaction now (Recommended)"; owner: "A's driver facts, after PR A (Recommended)").

CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS. Its corpus test
(`tests/test_public_transcript_text.py`) holds that between quotation marks only, and three
committed synthesis claims copied 13 or 14 of a call's words without them (LLY 14, VITL 13, WERN
14; measured on #1036, found by #1006's review). So:
- the build reads every synthesis string against its own calls (`synthesis.transcript_runs`) and
  REFUSES a page holding a run of more than 12 (`assemble._refuse_transcript_runs`);
- `vinci transcript-run-cut` cut the three committed runs to 12 words and "…" ($0, recorded).

Words end at whitespace, at every dash form and at a slash, and are folded for case, quote marks,
apostrophes and primes, with edge punctuation read off (review round 2 of #1036: the whitespace
count alone read WERN's 14-word copy as 11). Value pins sit on the frozen SMPL page and on
constructed words, never a transcript's; the committed corpus is checked against the licensed
calls, which CI cannot hold, so that check skips there.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

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
    """A call's text holding ``n`` consecutive words of ``claim`` as the guard counts them (from
    its ``start``-th), copied character for character, set among words no synthesis writes."""
    toks = syn._run_words(claim)
    return ("Operator: thank you. " + claim[toks[start][1]:toks[start + n - 1][2]]
            + " zzqx concludes the call.")


#: Sixteen words no call or synthesis writes in a row: the constructed strings below are built
#: from them, so no fixture holds a transcript word
_NATO = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india",
         "juliett", "kilo", "lima", "mike", "november", "oscar", "papa"]


def _with(page: dict[str, Any], where: str, text: str) -> ds.Synthesis:
    """The frozen page's synthesis with ``text`` as its first key unknown or its decisive
    question."""
    s = json.loads(json.dumps(page["synthesis"]))
    if where == "key_unknowns[0]":
        s["key_unknowns"][0] = text
    else:
        s["decisive_question"]["question"] = text
    return ds.Synthesis.model_validate(s)


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
    words = [claim[a:b] for _w, a, b in syn._run_words(claim)[2:17]]
    call = "Speaker: " + ", ".join(w.upper().replace("'", "’") for w in words) + "."
    assert [(r.where, r.words) for r in syn.transcript_runs(synth, call)] == [(where, 15)]


@pytest.mark.parametrize("joined,spaced", [("—", " -- "), ("–", " — "), ("-", " "), ("--", " "),
                                           ("/", " "), ("—", " ")])
def test_a_dash_or_slash_between_words_does_not_hide_a_run(joined: str, spaced: str) -> None:
    """(review round 2) A dash or a slash between two words is a word boundary, on both sides.
    The calls write " -- " (996 times on the committed calls) and the syntheses join words with
    "—" (35 times): "hotel—india" against "hotel -- india" was one token against two, and a 16-word
    copy read as none. FAILED before the fold split on dashes."""
    page = _page()
    text = (" ".join(_NATO[:7]) + f" {_NATO[7]}{joined}{_NATO[8]} " + " ".join(_NATO[9:]))
    call = ("Operator: thank you. " + " ".join(_NATO[:8]) + spaced + " ".join(_NATO[8:])
            + " zzqx.")
    runs = syn.transcript_runs(_with(page, "key_unknowns[0]", text), call)
    assert [(r.where, r.words) for r in runs] == [("key_unknowns[0]", 16)]


def test_a_hyphenated_compound_is_its_words() -> None:
    """(review round 2) "year-over-year" in the synthesis against "year over year" in the call."""
    page = _page()
    text = " ".join(_NATO[:6]) + " year-over-year " + " ".join(_NATO[6:13])
    call = "Operator: " + " ".join(_NATO[:6]) + " year over year " + " ".join(_NATO[6:13]) + "."
    runs = syn.transcript_runs(_with(page, "key_unknowns[0]", text), call)
    assert [(r.where, r.words) for r in runs] == [("key_unknowns[0]", 16)]


@pytest.mark.parametrize("mark", ["’", "‘", "′", "`"])
def test_an_apostrophe_inside_a_word_is_one_mark_in_every_form(mark: str) -> None:
    """(review round 2) A word's own apostrophe — "charlie's" — read as one mark whatever form
    either side types: a curly or a prime one in the call does not end the run. FAILED for the
    prime before the fold took primes. Inside the word, so stripping edge punctuation cannot
    stand in for the fold (a case-fold-only reading leaves "charlie's" and "charlie’s" apart)."""
    page = _page()
    words = [w + "'s" if i in (2, 9) else w for i, w in enumerate(_NATO)]
    text = " ".join(words)
    call = "Operator: " + " ".join(words).replace("'", mark) + " zzqx."
    runs = syn.transcript_runs(_with(page, "key_unknowns[0]", text), call)
    assert [(r.where, r.words) for r in runs] == [("key_unknowns[0]", 16)]


def test_a_quoted_run_over_12_words_is_refused() -> None:
    """(review round 2) Quotation marks are no exemption: 16 copied words between them are a run
    (the corpus test of `test_public_transcript_text.py` reads quotes only; this reads all)."""
    page = _page()
    text = "Management said “" + " ".join(_NATO) + "” on the call."
    call = "Operator: " + " ".join(_NATO) + " zzqx."
    synth = _with(page, "key_unknowns[0]", text)
    assert [(r.where, r.words) for r in syn.transcript_runs(synth, call)] == [
        ("key_unknowns[0]", 16)]
    with pytest.raises(assemble.DossierAssemblyError, match=re.escape("(16 words)")):
        assemble._refuse_transcript_runs(synth, call, ticker="SMPL")


@pytest.mark.parametrize("where", ["key_unknowns[0]", "decisive_question.question"])
def test_every_prose_field_is_read_not_only_claims(where: str) -> None:
    """(review round 2) A key unknown and the decisive question are prose the page publishes."""
    page = _page()
    call = "Operator: " + " ".join(_NATO) + " zzqx."
    runs = syn.transcript_runs(_with(page, where, " ".join(_NATO) + "?"), call)
    assert [(r.where, r.words) for r in runs] == [(where, 16)]


def test_synthesize_hands_its_transcript_to_the_guard() -> None:
    """(review round 2) Through `synthesize`, with a scripted model whose draw copies the call:
    the flag is written. A `synthesize` that handed `_validate` no transcript writes none (the
    second call is that case, by construction)."""
    from tests.test_dossier import _minimal_mech
    from tests.test_synthesis_draws import _LEANS, _payload

    class _Copies:
        model = "copies"

        def extract(self, *, system: str, user: str, tool: dict[str, Any],
                    cache: bool = False) -> dict[str, Any]:
            p = _payload(_LEANS["mixed"])
            p["key_unknowns"] = [" ".join(_NATO)]
            return p

    call = "Operator: " + " ".join(_NATO) + " zzqx."
    _s, flags, _log = syn.synthesize(_minimal_mech(), llm=cast(Any, _Copies()), ticker="X",
                                     name="X Co", transcript=call)
    assert any(f.startswith("TRANSCRIPT-RUN key_unknowns[0]: shares 16 consecutive words")
               for f in flags), flags
    _s, flags, _log = syn.synthesize(_minimal_mech(), llm=cast(Any, _Copies()), ticker="X",
                                     name="X Co", transcript=None)
    assert not any(f.startswith("TRANSCRIPT-RUN") for f in flags)


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
    # where the claim's 14th and 17th words end (the run is words 3 to 17), punctuation off
    ends = [b for _w, _a, b in syn._run_words(claim)]
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
    assert line.startswith(f"{len(syn._run_words(before))} → {len(syn._run_words(after))} "
                           "words; characters ")
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
    """`assemble_one` CALLS the refusal on the synthesis it is about to write, with the transcript
    it handed `synthesize`: after the null check, before `_write`. Read off the parsed code, so a
    call commented out is no call (review round 2: a text search matched inside a comment).
    `test_prespend.py`'s post-spend set pins the same call from the other side."""
    import ast

    tree = ast.parse(Path(assemble.__file__).read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "assemble_one")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    guard = [n for n in calls if cast(ast.Name, n.func).id == "_refuse_transcript_runs"]
    assert len(guard) == 1
    assert [ast.unparse(a) for a in guard[0].args] == ["synthesis", "transcript"]
    synth = [n for n in calls if cast(ast.Name, n.func).id == "synthesize"]
    assert len(synth) == 1 and any(k.arg == "transcript" and ast.unparse(k.value) == "transcript"
                                   for k in synth[0].keywords)
    req = max(n.lineno for n in calls if cast(ast.Name, n.func).id == "_require_synthesis")
    write = max(n.lineno for n in calls if cast(ast.Name, n.func).id == "_write")
    assert req < guard[0].lineno < write


@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_no_committed_synthesis_copies_more_than_12_words_of_its_calls(path: Path) -> None:
    """The committed corpus against the licensed calls on disk (CI holds none, so this skips
    there). FAILED before the cut on LLY (14 words), VITL (13) and WERN (14, which the first,
    whitespace-only count read as 11)."""
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
