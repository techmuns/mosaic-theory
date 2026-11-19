"""W64 — THE COMMITTED COVENANT QUOTES, CHECKED AGAINST THE EXHIBITS THEY CITE
(`vinci/dossier/covenant_evidence_check.py`; engineering report P2-14, the covenant half).

TWO LAYERS.

- THE PINS run everywhere, CI included. Every row pinned is a REAL committed row: read from its
  frozen copy (`tests/fixtures/frozen_pages/`, the cut or a dated copy, byte for byte as committed),
  or, for the two causes no frozen copy holds, stored verbatim from main `545403de` in the fixture.
  Each cited exhibit is served from a temp cache as the verbatim slices
  `fixtures/covenant_evidence/slices.json` holds, written through `CachedHttp`'s own key scheme, so
  the checker reads them as it reads the operator's cache. A case's ``expect`` is the WHOLE
  document's answer, asserted on the operator's cache when the slices were cut.
- THE GUARD walks every covered page (`covered_where`) and reads each cited exhibit from this
  checkout's cache and the primary checkout's (`default_cache_roots`). A quote its held exhibit does
  not carry fails it, unless `KNOWN_MISSES` names it with its cause; an entry there that is no
  longer on a page, or is now found, fails it too: the ratchet only shrinks. An exhibit no root
  holds is ``uncached`` and passes, so the guard proves what the cache can show and no more. It
  SKIPS only where no cited exhibit is held at all, a stated condition: CI holds no SEC cache.

Every socket is refused while a test runs.
"""

from __future__ import annotations

import dataclasses
import html
import json
import pathlib
import socket
from typing import Any

import pytest

from tests.frozen_support import ROOT, covered_where
from vinci.dossier import covenant_evidence_check as cec
from vinci.dossier import covenant_extract as ce
from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp

_FIX = json.loads((ROOT / "tests" / "fixtures" / "covenant_evidence" / "slices.json").read_text())
_CASES = {c["id"]: c for c in _FIX["cases"]}
FOUND_CASES = ("amzn-verbatim", "it-elided", "amzn-component-floor")
MISS_CASES = ("wern-editorial-bracket", "wern-unmarked-join", "wern-reordered", "it-not-a-span",
              "uber-wrong-exhibit", "amzn-label-added")

#: Every committed quote the guard may find not in its exhibit, by (ticker, term, quote_of,
#: source_ref, the quote's sha256), with its cause. Measured on main `8bc138cd` (2026-11-19), the
#: 20 pages with covenant quotes: none. A change that makes a committed quote miss (a converter or
#: a span rule that reads a filing differently) either fixes it or names it here with its cause.
KNOWN_MISSES: dict[tuple[str, str, str, str, str], str] = {}


@pytest.fixture(autouse=True)
def _no_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    """NEVER A FETCH: any connection attempted while a test runs fails the test."""
    def refuse(*_a: object, **_k: object) -> None:
        raise AssertionError("the cache-only checker opened a connection")
    monkeypatch.setattr(socket.socket, "connect", refuse)


def _page(case: dict[str, Any]) -> dict[str, Any]:
    """The case's page: its frozen copy, or the rows git history holds, verbatim."""
    if case["rows"] is not None:
        return {"ticker": case["ticker"], "cik": case["cik"], "mechanical": {"capital_structure": {
            "covenant_term_rows": {"value": case["rows"]}}}}
    path = ROOT / case["page"]
    assert path.is_relative_to(ROOT / "tests" / "fixtures" / "frozen_pages"), path
    page: dict[str, Any] = json.loads(path.read_text())
    return page


def _serve(root: pathlib.Path, cases: list[dict[str, Any]], *,
           withhold: frozenset[str] = frozenset()) -> pathlib.Path:
    """A cache under ``root`` holding each case's documents: its slices of the converted text,
    joined in order, or, where a document carries ``html``, the response's own markup, as is."""
    writer = CachedHttp(cache_dir=root, user_agent="test", min_interval_sec=0.0, namespace="sec")
    for c in cases:
        for d in c["documents"]:
            if d["filename"] in withhold:
                continue
            body = _FIX["gap"].join(s["text"] for s in d["slices"])
            served = (d["html"]["text"] if d.get("html")
                      else f"<html><body><p>{html.escape(body)}</p></body></html>")
            writer._write_cache(d["url"], served)  # noqa: SLF001
    return root


def _answer(root: pathlib.Path, case: dict[str, Any],
            roots: list[pathlib.Path] | None = None) -> cec.QuoteCheck:
    results = cec.check_pages({case["ticker"]: _page(case)},
                              cec.readers_for(roots if roots is not None else [root]))
    mine = [r for r in results if (r.term, r.quote_of, r.source_ref)
            == (case["term"], case["quote_of"], case["source_ref"])]
    assert len(mine) == 1, (case["id"], len(mine))
    return mine[0]


@pytest.mark.parametrize("cid", FOUND_CASES)
def test_a_committed_quote_its_exhibit_carries_is_found(tmp_path: pathlib.Path, cid: str) -> None:
    """(+) AMZN's commitment clause is verbatim once its tag spaces fold ("“ Aggregate Commitments
    ” means"), IT's change-of-control clause is elided in the exhibit's order, and AMZN's floor
    clause is a rate component's OWN quote: each is found, and the row names the root it read.
    AMZN's commitment clause is served as the exhibit's own markup (`&ldquo;<U>Aggregate
    Commitments</U>&rdquo;`), so the check's conversion runs on real HTML (review round 1)."""
    case = _CASES[cid]
    r = _answer(_serve(tmp_path, [case]), case)
    assert (r.outcome, r.match) == (cec.FOUND, case["expect"]["match"])
    assert r.cache_root == str(tmp_path) and r.document_sha256 and not r.cause


@pytest.mark.parametrize("cid", MISS_CASES)
def test_a_committed_quote_its_exhibit_does_not_carry_is_not_found_with_its_cause(
        tmp_path: pathlib.Path, cid: str) -> None:
    """(−) Each a real committed quote that its exhibit does not carry, one per cause: WERN's
    bracketed summary of its events of default, its two clauses joined with no ellipsis, its
    definitions quoted out of the exhibit's order; IT's commitment letter, a clause it does not
    print; UBER's 2021 amortization, a span of the 2023 amendment the page also cites; and AMZN's
    prepayment clause, behind a section number the model put before it."""
    case = _CASES[cid]
    r = _answer(_serve(tmp_path, [case]), case)
    assert r.outcome == cec.NOT_FOUND and r.match == "not_found"
    assert r.cause == case["expect"]["cause"]
    assert list(r.in_other_exhibits) == case["expect"]["in_other_exhibits"]
    assert (r.unfound_piece != "") == (r.cause not in (cec.WRONG_EXHIBIT, cec.REORDERED))


def test_the_six_miss_cases_name_six_causes() -> None:
    """The negatives cover every cause, so no branch of `_cause` is pinned by nothing."""
    assert sorted(_CASES[c]["expect"]["cause"] for c in MISS_CASES) == sorted(cec.CAUSES)


def test_an_exhibit_is_read_from_the_first_root_that_holds_it_and_none_is_uncached(
        tmp_path: pathlib.Path) -> None:
    """(+) A root that does not hold the exhibit is passed over for one that does, and the row
    names the one it read; (−) where no root holds it, the row is UNCACHED, never not_found."""
    case = _CASES["amzn-verbatim"]
    empty = _serve(tmp_path / "a", [case], withhold=frozenset(
        d["filename"] for d in case["documents"]))
    full = _serve(tmp_path / "b", [case])
    read = _answer(full, case, roots=[empty, full])
    assert (read.outcome, read.cache_root) == (cec.FOUND, str(full))
    none = _answer(empty, case, roots=[empty])
    assert (none.outcome, none.match, none.cache_root, none.cause) == (cec.UNCACHED, "", "", "")


def test_a_wrong_exhibit_is_found_only_among_the_exhibits_the_page_cites(
        tmp_path: pathlib.Path) -> None:
    """(−) UBER's 2021 quote without the page's row citing the 2023 amendment is no longer read as
    the wrong exhibit: it is a quote its own exhibit does not carry, and the first piece it misses
    is named."""
    case = dict(_CASES["uber-wrong-exhibit"])
    case["rows"] = case["rows"][:1]
    r = _answer(_serve(tmp_path, [case]), case)
    assert (r.outcome, r.in_other_exhibits) == (cec.NOT_FOUND, ())
    assert r.cause != cec.WRONG_EXHIBIT and r.unfound_piece


class _Llm(LlmClient):
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "fake-model-1"

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        return self._payload


def test_the_quote_reader_reads_back_what_the_writer_wrote() -> None:
    """(+) The real extractor's note, for AMZN's committed commitment quote (it holds curly quotes
    of its own), reads back as that quote; (−) a refused term's note, a not-stated note and none
    read as no quote."""
    case = _CASES["amzn-verbatim"]
    quote = ce.note_quote(next(r for r in _page(case)["mechanical"]["capital_structure"][
        "covenant_term_rows"]["value"] if r["name"] == case["term"]
        and r["value"]["source_ref"] == case["source_ref"])["value"]["note"])
    assert quote and "“" in quote
    text = _FIX["gap"].join(s["text"] for s in case["documents"][0]["slices"])
    payload = {"terms": [{"name": case["term"], "present": True, "value": "US$15,000,000,000",
                          "quote": quote}]}
    (row,), _flags, _ = ce._extract_from_exhibit(  # noqa: SLF001
        _Llm(payload), text, name="Amazon.com, Inc.", ticker="AMZN",
        source_ref=case["source_ref"])
    assert ce.note_quote(row.value.note) == quote
    refused = {"terms": [{"name": case["term"], "present": True, "value": "US$15,000,000,000",
                          "quote": "a clause the exhibit never printed"}]}
    (bad,), _f, _ = ce._extract_from_exhibit(  # noqa: SLF001
        _Llm(refused), text, name="Amazon.com, Inc.", ticker="AMZN",
        source_ref=case["source_ref"])
    assert ce.note_quote(bad.value.note) is None
    assert ce.note_quote(f"not stated in {case['source_ref']}") is None
    assert ce.note_quote(None) is None


def test_a_present_term_that_stores_no_quote_fails_loud() -> None:
    """(−) A PRESENT term is always written with its quote and its exhibit: one without either is
    a page this check cannot vouch for, and it raises rather than reading as checked."""
    case = _CASES["amzn-verbatim"]
    page = _page(case)
    row = next(r for r in page["mechanical"]["capital_structure"]["covenant_term_rows"]["value"]
               if r["name"] == case["term"] and r["value"]["source_ref"] == case["source_ref"])
    row["value"]["note"] = "a note that stores no quote"
    with pytest.raises(ValueError, match="stores no quote or names no exhibit"):
        list(cec.page_quotes(page))


def test_the_cli_prints_every_miss_whole_and_exits_one(
        tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    """(+) A read with misses prints each one, its quote and its cause whole, and exits 1; (−) a
    read with none exits 0."""
    cases = [_CASES[c] for c in ("wern-reordered", "it-not-a-span", "amzn-verbatim")]
    cache = _serve(tmp_path / "cache", cases)
    pages = tmp_path / "pages"
    for c in cases:
        (pages / c["id"]).mkdir(parents=True)
        page = _page(c)
        cs = page["mechanical"]["capital_structure"]["covenant_term_rows"]
        cs["value"] = [r for r in cs["value"] if (r["name"], r["value"].get("source_ref"))
                       == (c["term"], c["source_ref"])]
        (pages / c["id"] / "dossier.json").write_text(json.dumps(page))
    code = cec.main(["--pages", str(pages), "--cache-root", str(cache),
                     "--ticker", "wern-reordered", "--ticker", "it-not-a-span"])
    out = capsys.readouterr().out
    assert code == 1 and "not_found: 2 — reordered 1 · not_a_span 1" in out
    for c in cases[:2]:
        r = _answer(cache, c)
        assert f"      quote: {r.quote}" in out and f"| {r.cause}" in out
    assert cec.main(["--pages", str(pages), "--cache-root", str(cache),
                     "--ticker", "amzn-verbatim"]) == 0


# --- the guard ----------------------------------------------------------------------------------

_Key = tuple[str, str, str, str, str]


def _key(r: cec.QuoteCheck) -> _Key:
    return (r.ticker, r.term, r.quote_of, r.source_ref, r.quote_sha256)


def _ratchet(results: list[cec.QuoteCheck], known: dict[_Key, str]
             ) -> tuple[list[cec.QuoteCheck], list[_Key], list[_Key]]:
    """(the misses `known` does not name, the named entries that are stale, the named entries whose
    stored cause is not the cause the check reads now). An entry is stale when its quote is no
    longer on a page, or is now found; an entry whose exhibit no root holds cannot be read either
    way, and is none of the three."""
    by_key = {_key(r): r for r in results}
    new = [r for r in results if r.outcome == cec.NOT_FOUND and _key(r) not in known]
    stale = sorted(k for k in known if k not in by_key or by_key[k].outcome == cec.FOUND)
    wrong = sorted(k for k, cause in known.items() if k in by_key
                   and by_key[k].outcome == cec.NOT_FOUND and by_key[k].cause != cause)
    return new, stale, wrong


def test_the_ratchet_refuses_a_new_miss_and_a_stale_entry(tmp_path: pathlib.Path) -> None:
    """(+) A miss named with its cause passes, and so does an entry whose exhibit is not held;
    (−) an unnamed miss is new, an entry whose quote is found, or gone, is stale, and an entry
    naming another cause than the one the check reads is refused (review round 1)."""
    miss = _answer(_serve(tmp_path / "m", [_CASES["wern-reordered"]]), _CASES["wern-reordered"])
    hit = _answer(_serve(tmp_path / "h", [_CASES["amzn-verbatim"]]), _CASES["amzn-verbatim"])
    gone = ("AAA", "Maturity date", cec.ROW_QUOTE, "8-K 0000000001-26-000001 · ex.htm", "0" * 64)
    assert _ratchet([miss, hit], {_key(miss): cec.REORDERED}) == ([], [], [])
    assert _ratchet([miss, hit], {}) == ([miss], [], [])
    assert _ratchet([miss, hit], {_key(miss): cec.REORDERED, _key(hit): cec.REORDERED,
                                  gone: cec.REORDERED}) == ([], sorted([_key(hit), gone]), [])
    assert _ratchet([miss, hit], {_key(miss): cec.NOT_A_SPAN}) == ([], [], [_key(miss)])
    unheld = dataclasses.replace(miss, outcome=cec.UNCACHED)
    assert _ratchet([unheld], {_key(miss): cec.NOT_A_SPAN}) == ([], [], [])


def _guard(pages: dict[str, dict[str, Any]], roots: list[pathlib.Path],
           known: dict[_Key, str]) -> str:
    """THE GUARD's body: what it checked, in one line, after refusing a miss `known` does not
    name, a stale entry and a wrong cause. HOW MUCH it checks is per machine (each Mac holds its
    own SEC cache), so it is REPORTED, never held to a number (review round 2): a cache holding
    some of the cited exhibits checks those. It FAILS only where a cache root exists and holds none
    of them, since then it checked nothing; it SKIPS where there is no cache at all (CI)."""
    if not roots:
        pytest.skip(f"no data/cache/sec in this checkout or its primary: the guard reads the SEC "
                    f"cache, and CI holds none ({len(pages)} pages not checked)")
    results = cec.check_pages(pages, cec.readers_for(roots))
    cited = sorted({(r.ticker, r.accession, r.filename) for r in results})
    held = {(r.ticker, r.accession, r.filename) for r in results if r.outcome != cec.UNCACHED}
    checked = sum(1 for r in results if r.outcome != cec.UNCACHED)
    unheld = [f"{t} {a} · {f}" for t, a, f in cited if (t, a, f) not in held]
    report = (f"covenant guard: {checked} of {len(results)} quotes checked, {len(held)} of "
              f"{len(cited)} cited exhibits held, from {[str(r) for r in roots]}; not held "
              f"({len(unheld)} of {len(unheld)}): {'; '.join(unheld) or 'none'}")
    assert checked, (f"the cache roots {[str(r) for r in roots]} hold none of the {len(cited)} "
                     f"exhibits the {len(pages)} pages cite, so the guard checked nothing: "
                     "point a root at a cache that holds them")
    new, stale, wrong = _ratchet(results, known)
    assert not new, (
        f"{len(new)} committed covenant quote(s) are not in the exhibit each cites: "
        + "; ".join(f"{r.ticker} | {r.term} | {r.quote_of} | {r.source_ref} | {r.cause}"
                    f" — {r.unfound_piece or r.quote}" for r in new)
        + ". Fix the page, or name each in KNOWN_MISSES with its cause "
        "(python -m vinci.dossier.covenant_evidence_check prints them all).")
    assert not stale, (f"{len(stale)} KNOWN_MISSES entr(ies) are found now or left the pages: "
                       f"{stale}. Delete each: the ratchet only shrinks.")
    assert not wrong, (f"{len(wrong)} KNOWN_MISSES entr(ies) name another cause than the check "
                       f"reads: {[(k, known[k]) for k in wrong]}.")
    return report


def test_every_committed_covenant_quote_is_in_the_exhibit_it_cites() -> None:
    """THE GUARD, over every covered page with a covenant quote: each quote whose exhibit a cache
    root holds is a span of it, unless `KNOWN_MISSES` names it; no entry there is stale or names
    another cause; and it says how much it checked."""
    pages = dict(covered_where(lambda _t, d: next(cec.page_quotes(d), None) is not None,
                               "stores a covenant quote"))
    print(_guard(pages, cec.default_cache_roots(ROOT), KNOWN_MISSES))


def test_the_guard_reports_a_partial_cache_fails_an_empty_one_and_skips_without_one(
        tmp_path: pathlib.Path) -> None:
    """Review round 2. (+) A cache holding only some of the exhibits real pages cite passes and
    says how much it checked: the cut's AMZN and IT, each cut to its pinned row, AMZN's keeping
    too a row of another exhibit, which is not served; (−) a cache root that holds none of them
    fails, since it checked nothing; and with no cache root at all, as in CI, the guard skips."""
    cases = [_CASES["amzn-verbatim"], _CASES["it-elided"]]
    pages = {}
    for c in cases:
        page = _page(c)
        block = page["mechanical"]["capital_structure"]["covenant_term_rows"]
        keep = [r for r in block["value"] if (r["name"], r["value"].get("source_ref"))
                == (c["term"], c["source_ref"])]
        if c["ticker"] == "AMZN":
            keep.append(next(r for r in block["value"] if r["value"]["status"] == "present"
                             and r["value"]["source_ref"] != c["source_ref"]))
        block["value"] = keep
        pages[c["ticker"]] = page
    report = _guard(pages, [_serve(tmp_path / "some", cases)], {})
    assert report.startswith("covenant guard: 2 of 3 quotes checked, 2 of 3 cited exhibits held"), (
        report)
    assert "not held (1 of 1): AMZN " in report
    empty = tmp_path / "none"
    (empty / "sec").mkdir(parents=True)
    with pytest.raises(AssertionError, match="hold none of the"):
        _guard(pages, [empty], {})
    with pytest.raises(pytest.skip.Exception, match="CI holds none"):
        _guard(pages, [], {})


def test_a_quote_with_no_ellipsis_is_never_called_reordered(tmp_path: pathlib.Path) -> None:
    """(−) Review round 0: AMZN's committed commitment clause with a stray leading comma is no span
    (`vinci.verbatim` trims a cut's punctuation only at its end), and a quote of ONE piece has no
    order to break: it reads `not_a_span`, its piece named, never `reordered`."""
    case = json.loads(json.dumps(_CASES["amzn-verbatim"]))
    page = _page(case)
    row = next(r for r in page["mechanical"]["capital_structure"]["covenant_term_rows"]["value"]
               if r["name"] == case["term"] and r["value"]["source_ref"] == case["source_ref"])
    quote = ce.note_quote(row["value"]["note"])
    row["value"]["note"] = f"{ce.VERBATIM_NOTE_OPEN}, {quote}{ce.VERBATIM_NOTE_CLOSE}"
    want = (case["term"], cec.ROW_QUOTE, case["source_ref"])
    readers = cec.readers_for([_serve(tmp_path, [case])])
    r = next(x for x in cec.check_pages({"AMZN": page}, readers)
             if (x.term, x.quote_of, x.source_ref) == want)
    assert (r.outcome, r.cause) == (cec.NOT_FOUND, cec.NOT_A_SPAN) and r.unfound_piece


def _amzn_with(quote: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """AMZN's committed commitment row (from the cut) carrying ``quote`` in place of its own."""
    case = json.loads(json.dumps(_CASES["amzn-verbatim"]))
    page = _page(case)
    row = next(r for r in page["mechanical"]["capital_structure"]["covenant_term_rows"]["value"]
               if r["name"] == case["term"] and r["value"]["source_ref"] == case["source_ref"])
    row["value"]["note"] = f"{ce.VERBATIM_NOTE_OPEN}{quote}{ce.VERBATIM_NOTE_CLOSE}"
    return case, page


@pytest.mark.parametrize("quote, piece", [
    (", “ Aggregate Commitments ” means, at any time ... As of the Closing Date",
     ", “ Aggregate Commitments ” means, at any time"),
    ("As of the Closing Date ... As of the Closing Date", "As of the Closing Date"),
], ids=["in-order-pieces-a-stray-comma", "a-piece-repeated"])
def test_pieces_the_exhibit_holds_are_reordered_only_out_of_its_order(
        tmp_path: pathlib.Path, quote: str, piece: str) -> None:
    """(−) Review round 1: two pieces of AMZN's committed clause IN the exhibit's order, the first
    behind a stray comma, and one piece quoted twice where the exhibit prints it once, are each a
    miss that no other order of the same pieces repairs: `not_a_span`, the piece named, never
    `reordered`. (+) WERN's definitions out of the exhibit's order stay `reordered` (above)."""
    case, page = _amzn_with(quote)
    readers = cec.readers_for([_serve(tmp_path, [case])])
    r = next(x for x in cec.check_pages({"AMZN": page}, readers)
             if (x.term, x.quote_of) == (case["term"], cec.ROW_QUOTE)
             and x.source_ref == case["source_ref"])
    assert (r.outcome, r.cause, r.unfound_piece) == (cec.NOT_FOUND, cec.NOT_A_SPAN, piece)
