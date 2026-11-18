"""THE COMMITTED EXPOSURE MAP'S EVIDENCE, CHECKED AGAINST ITS FILINGS (`graph/evidence_check.py`).

Every edge pinned here is a REAL committed edge: the five graph cases of
``fixtures/verbatim/real_cases.json`` (#804, the committed map's quotes at 545403de, each with a
verbatim window of its cited 10-K), and ATKR → Wesco (``fixtures/graph_evidence/atkr_window.json``,
cut from ATKR's 10-K on 2026-11-18). These are frozen fixtures, never the living map. Each window
is served as its accession's document from a temp cache, written through `CachedHttp`'s own key
scheme, so the checker reads it exactly as it reads the operator's cache. Every socket is refused.
"""

from __future__ import annotations

import json
import pathlib
import socket
from datetime import date
from typing import Any

import pytest

from vinci.graph import evidence_check as gec
from vinci.netcache import CachedHttp

_FIX = pathlib.Path(__file__).parent / "fixtures"
_CASES = {c["id"]: c for c in json.loads((_FIX / "verbatim" / "real_cases.json").read_text())[
    "cases"] if c["corpus"] == "graph_edge"}
_ATKR = json.loads((_FIX / "graph_evidence" / "atkr_window.json").read_text())
#: Each case's filing date, read from its focal's submissions feed in the operator's cache
#: (2026-11-18): the fixtures carry the accession and document, not the date.
_FILED = {"klic-quote-marks": "2025-11-20", "cts-elided-in-order": "2026-02-24",
          "bkti-typo-corrected": "2026-03-12", "mrcy-slash-stitch": "2025-08-11",
          "atom-sentences-reordered": "2026-02-24", "atkr-excerpt-join": _ATKR["filing_date"]}
#: The committed map's extraction date (be4268e6, 2026-06-26; #937 re-judged it, extraction fixed).
_FILED_BY = date(2026, 6, 26)


def _edge(c: dict[str, Any]) -> dict[str, Any]:
    return {"focal_ticker": c["ticker"], "focal_cik": c["cik"], "counterparty_name": c["item"],
            "evidence": c["quote"]}


def _accession_doc(c: dict[str, Any]) -> tuple[str, str]:
    _form, accession, _dot, doc = c["source"].split()
    return accession, doc


def _cache(root: pathlib.Path, cases: list[dict[str, Any]], *,
           withhold_docs: frozenset[str] = frozenset(),
           extra: dict[str, list[tuple[str, str, str, str]]] | None = None) -> pathlib.Path:
    """A cache under ``root`` holding each case's focal submissions feed and, unless withheld, its
    window as the accession's document. ``extra`` adds (form, date, accession, doc) rows to a
    focal's feed, held by no document."""
    writer = CachedHttp(cache_dir=root, user_agent="test", min_interval_sec=0.0, namespace="sec")
    feeds: dict[str, list[tuple[str, str, str, str]]] = {}
    for c in cases:
        accession, doc = _accession_doc(c)
        feeds.setdefault(c["cik"], []).append(("10-K", _FILED[c["id"]], accession, doc))
        if c["id"] not in withhold_docs:
            url = gec._ARCHIVE.format(cik=int(c["cik"]), acc=accession.replace("-", ""), doc=doc)
            writer._write_cache(url, f"<html><body><p>{c['window']}</p></body></html>")  # noqa: SLF001
    for cik, rows in (extra or {}).items():
        feeds.setdefault(cik, []).extend(rows)
    for cik, rows in feeds.items():
        recent = {"form": [r[0] for r in rows], "filingDate": [r[1] for r in rows],
                  "accessionNumber": [r[2] for r in rows], "primaryDocument": [r[3] for r in rows]}
        writer._write_cache(gec._SUBMISSIONS.format(cik10=f"{int(cik):010d}"),  # noqa: SLF001
                            json.dumps({"filings": {"recent": recent}}))
    return root


@pytest.fixture(autouse=True)
def _no_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    """NEVER A FETCH: any connection attempted while a test runs fails the test."""
    def refuse(*_a: object, **_k: object) -> None:
        raise AssertionError("the cache-only checker opened a connection")
    monkeypatch.setattr(socket.socket, "connect", refuse)


def _check(root: pathlib.Path, cases: list[dict[str, Any]]) -> dict[str, gec.EdgeCheck]:
    results = gec.check_edges([_edge(c) for c in cases], gec.held_reader(root), filed_by=_FILED_BY)
    return {f"{r.focal}:{r.counterparty}": r for r in results}


def test_each_real_edge_reads_found_or_not_found_from_its_filing(tmp_path: pathlib.Path) -> None:
    """(+/-) Found: KLIC's phrase is verbatim once quote marks are folded, and CTS's is elided in
    the document's order. Not found: BKTI's quotes `LLC,` for the filing's `LLC,,`, and MRCY's
    stitches two sentences with ` / `. Each row names what it checked; a miss is a row, never
    dropped."""
    ids = ["klic-quote-marks", "cts-elided-in-order", "bkti-typo-corrected", "mrcy-slash-stitch"]
    cases = [_CASES[i] for i in ids]
    got = _check(_cache(tmp_path, cases), cases)
    assert len(got) == 4
    for i in ids:
        c = _CASES[i]
        r = got[f"{c['ticker']}:{c['item']}"]
        label = f"10-K {_accession_doc(c)[0]} ({_FILED[i]})"
        assert r.checked == (label,) and r.not_held == () and r.newest == label
        if c["expect"] in ("verbatim", "elided"):
            assert (r.outcome, r.found_in) == (gec.FOUND, (label,)), i
        else:
            assert (r.outcome, r.found_in, r.in_excerpts) == (gec.NOT_FOUND, (), ()), i


def test_a_phrase_the_excerpt_cut_joined_is_not_found_and_says_so(tmp_path: pathlib.Path) -> None:
    """ATKR → Wesco. The excerpt keeps `…Consolidated Electrical Distributors, Inc.` and `and Wesco
    International, Inc.)…` as neighbours, having dropped the clause between them (CED, Graybar,
    Rexel, Sonepar). So the quote is a span of the excerpts and NOT of the filing. The checker
    refuses it, and names the cause."""
    got = _check(_cache(tmp_path, [_ATKR]), [_ATKR])
    r = got[f"ATKR:{_ATKR['item']}"]
    label = f"10-K 0001628280-25-054049 ({_ATKR['filing_date']})"
    assert (r.outcome, r.found_in, r.in_excerpts) == (gec.NOT_FOUND, (), (label,))


def test_a_report_the_cache_does_not_hold_is_uncached_never_fetched(tmp_path: pathlib.Path) -> None:
    """(-) ATOM's 10-K is in its submissions feed but not in the cache: uncached, the report named
    as not held, and no connection is opened (the autouse refusal). A focal with no submissions
    feed at all is uncached too. A miss is a row."""
    atom, klic = _CASES["atom-sentences-reordered"], _CASES["klic-quote-marks"]
    root = _cache(tmp_path, [atom], withhold_docs=frozenset({atom["id"]}))
    got = _check(root, [atom, klic])          # KLIC's feed was never written
    a = got[f"ATOM:{atom['item']}"]
    assert (a.outcome, a.checked, a.found_in) == (gec.UNCACHED, (), ())
    assert a.not_held == (f"10-K {_accession_doc(atom)[0]} ({_FILED[atom['id']]})",)
    k = got[f"KLIC:{klic['item']}"]
    assert (k.outcome, k.checked, k.not_held, k.newest) == (gec.UNCACHED, (), (), None)
    assert k.note == "no submissions feed in the cache"


def test_a_held_feed_with_no_report_by_the_cutoff_is_not_found_and_noted(
        tmp_path: pathlib.Path) -> None:
    """(review round 0) A held feed listing no annual report by the cut-off lacks nothing in the
    cache, so it is NOT uncached: not_found, with the reason. And an /A of a form the focal did not
    file as an original is no candidate."""
    klic = _CASES["klic-quote-marks"]
    root = _cache(tmp_path, [klic], withhold_docs=frozenset({klic["id"]}),
                  extra={klic["cik"]: [("20-F/A", "2025-12-02", "0000056978-25-999996", "x.htm")]})
    late = gec.check_edges([_edge(klic)], gec.held_reader(root), filed_by=date(2025, 1, 1))
    assert [(r.outcome, r.note) for r in late] == [
        (gec.NOT_FOUND, "the feed lists no annual report filed by the cut-off")]
    (r,) = gec.check_edges([_edge(klic)], gec.held_reader(root), filed_by=_FILED_BY)
    assert r.outcome == gec.UNCACHED and not any("20-F/A" in x for x in r.not_held)


def test_the_candidates_are_two_originals_by_the_cutoff_and_their_held_amendments(
        tmp_path: pathlib.Path) -> None:
    """The source is searched in the two newest ORIGINAL annual reports filed on or before the
    cut-off. A report filed after it is never a candidate. An /A of them that is not held is
    named, and it does not make a found row uncached. An older original that is not held does
    make a miss uncached, because it could be the source (EXTR's edges, #804's record)."""
    klic = _CASES["klic-quote-marks"]
    cik = klic["cik"]
    later = ("10-K", "2026-11-19", "0000056978-26-999999", "later.htm")   # after the cut-off
    amend = ("10-K/A", "2025-12-01", "0000056978-25-999998", "amend.htm")  # an /A, not held
    prior = ("10-K", "2024-11-14", "0000056978-24-999997", "prior.htm")   # the prior year, not held
    root = _cache(tmp_path, [klic], extra={cik: [later, amend, prior]})
    r = _check(root, [klic])[f"KLIC:{klic['item']}"]
    assert r.outcome == gec.FOUND
    assert [x.split()[1] for x in r.checked + r.not_held] == [
        "0000056978-25-000081", "0000056978-25-999998", "0000056978-24-999997"]
    assert not any("26-999999" in x for x in r.checked + r.not_held), "a post-cut-off filing"
    # the same feed, but the phrase changed so nothing holds it: the unheld prior original makes
    # the miss UNCACHED, not NOT_FOUND
    missing = dict(_edge(klic), evidence="a phrase no filing of KLIC states")
    (m,) = gec.check_edges([missing], gec.held_reader(root), filed_by=_FILED_BY)
    assert m.outcome == gec.UNCACHED


def test_the_reader_refuses_to_send(tmp_path: pathlib.Path) -> None:
    """The cache-only reader raises rather than fetch, before any socket — by construction, not
    only by the autouse refusal."""
    (tmp_path / "sec").mkdir()
    http = gec.held_reader(tmp_path)
    url = "https://www.sec.gov/Archives/edgar/data/1/2/x.htm"
    with pytest.raises(gec.NotHeldError):
        http.get_text(url, ttl_seconds=None)
    assert http.held_text(url) is None
    # each of the two guards on its own: either alone keeps the reader from sending
    with pytest.raises(gec.NotHeldError, match="never fetched"):      # before any pacing
        http._fetch_with_retries(url)                                      # noqa: SLF001
    with pytest.raises(gec.NotHeldError, match="sends nothing"):
        http._send(url, None)                                              # noqa: SLF001
    assert not list((tmp_path / "sec").iterdir()), "the reader wrote to the cache"
    with pytest.raises(FileNotFoundError):
        gec.held_reader(tmp_path / "nowhere")


def test_the_cli_prints_every_miss_with_its_boundary(tmp_path: pathlib.Path,
                                                     capsys: pytest.CaptureFixture[str]) -> None:
    """End to end through `main`: the counts lead, with the boundary (map, edges, focals,
    cut-off, cache), and every not-found and uncached row is printed. None is cut."""
    cases = [_CASES[i] for i in ("klic-quote-marks", "bkti-typo-corrected",
                                 "mrcy-slash-stitch", "atom-sentences-reordered")] + [_ATKR]
    root = _cache(tmp_path / "cache", cases, withhold_docs=frozenset({"atom-sentences-reordered"}))
    graph = tmp_path / "graph_coverage.json"
    graph.write_text(json.dumps({"edges": [_edge(c) for c in cases]}))
    rows = tmp_path / "rows.json"
    assert gec.main(["--map", str(graph), "--cache-root", str(root),
                     "--filed-by", _FILED_BY.isoformat(), "--json", str(rows)]) == 0
    out = capsys.readouterr().out
    assert "5 edges from 5 focals" in out and "on or before 2026-06-26" in out
    # THE ACCESSION EACH FOUND PHRASE IS IN, by focal, every focal printed
    assert "found, by focal (5 of 5)" in out
    assert "    KLIC: 1 of 1 found — 10-K 0000056978-25-000081 (2025-11-20) 1" in out
    assert "    BKTI: 0 of 1 found" in out
    # and per edge, in the file: every row with its outcome and accessions, in the map's order
    written = json.loads(rows.read_text())
    assert written["filed_by"] == "2026-06-26" and len(written["map_sha256"]) == 64
    assert [r["outcome"] for r in written["rows"]] == [
        gec.FOUND, gec.NOT_FOUND, gec.NOT_FOUND, gec.UNCACHED, gec.NOT_FOUND]
    assert written["rows"][0]["found_in"] == ["10-K 0000056978-25-000081 (2025-11-20)"]
    assert "found 1 · not_found 3 · uncached 1" in out
    assert "not_found: 3, of which 1 are a span of a report's excerpts" in out
    for c in cases[1:]:
        assert f"{c['ticker']} → {c['item']}" in out, c["id"]


def test_a_phrase_found_only_in_a_newer_amendment_is_not_called_older(
        tmp_path: pathlib.Path) -> None:
    """(review round 1) KLIC's original 10-K is held with another filing's text, and a held 10-K/A
    filed after it carries KLIC's window. The phrase is found in the /A alone, which is NEWER than
    the newest original: the printout counts it as found in an amendment, never as "older"."""
    klic, bkti = _CASES["klic-quote-marks"], _CASES["bkti-typo-corrected"]
    other = dict(klic, window=bkti["window"])          # the original holds text without the phrase
    root = _cache(tmp_path, [other])
    amend = ("10-K/A", "2025-12-01", "0000056978-25-999998", "amend.htm")
    writer = CachedHttp(cache_dir=root, user_agent="test", min_interval_sec=0.0, namespace="sec")
    writer._write_cache(gec._ARCHIVE.format(cik=int(klic["cik"]), acc=amend[2].replace("-", ""),  # noqa: SLF001
                                            doc=amend[3]),
                        f"<html><body><p>{klic['window']}</p></body></html>")
    feed = {"filings": {"recent": {
        "form": ["10-K", amend[0]], "filingDate": [_FILED[klic["id"]], amend[1]],
        "accessionNumber": [_accession_doc(klic)[0], amend[2]],
        "primaryDocument": [_accession_doc(klic)[1], amend[3]]}}}
    writer._write_cache(gec._SUBMISSIONS.format(cik10=f"{int(klic['cik']):010d}"),  # noqa: SLF001
                        json.dumps(feed))
    results = gec.check_edges([_edge(klic)], gec.held_reader(root), filed_by=_FILED_BY)
    assert [(r.outcome, r.found_in, r.found_where) for r in results] == [
        (gec.FOUND, ("10-K/A 0000056978-25-999998 (2025-12-01)",), "amendment")]
    lines = gec.report_lines(results, map_path="m", map_sha256="0" * 64, filed_by=_FILED_BY,
                             cache_root=root)
    assert "  found only in a report older than the newest: 0" in lines
    assert "  found only in an amendment of a candidate: 1" in lines


def test_the_outcome_reads_a_structured_feed_flag_not_the_note(tmp_path: pathlib.Path) -> None:
    """(review round 1; CLAUDE.md: display formatting is never load-bearing) Whether the focal's
    feed is held is a field of the row, and the outcome reads it. The note is only its words."""
    klic, atom = _CASES["klic-quote-marks"], _CASES["atom-sentences-reordered"]
    root = _cache(tmp_path, [atom], withhold_docs=frozenset({atom["id"]}))
    got = _check(root, [atom, klic])
    assert got[f"KLIC:{klic['item']}"].feed_held is False
    assert got[f"ATOM:{atom['item']}"].feed_held is True
