"""EDGAR as it stood on a page's price date, and every amendment named (TeamNostra fix request 2,
group E1: RE1-D8, RE1-D9, RE1-D12, RE1-D13 with document 11's E1-D7 residual).

- RE1-D8: `AsOfEdgar` with no window read the submissions document's RECENT page only — today's
  newest ~1,000 filings — so a cut before it found nothing and a cut just inside it found weeks.
- RE1-D9: the view passed the frames API and the share-count readers built on it through uncut.
- RE1-D12: no 10-Q/A rule: the page's 10-Q reader listed `forms=("10-Q",)`.
- RE1-D13 / E1-D7: the exposure graph's annual-report excerpts read the newest 10-K by date, with
  no 10-K/A and no pointer.
- RE1-D14 (order 4, the same reader): the excerpts' 24,000-character cap dropped sentences and
  said nothing.

Fixtures are real SEC JSON, cut to the rows read:
- Gartner's submissions document and older page -001 (`tests/fixtures/submissions_pages`);
- Ducommun's 10-K/A restating FY2025 and Skyworks' Part III 10-K/A
  (`tests/fixtures/amended_filings`);
- new here, cut from this machine's SEC cache on 2026-11-09: Simply Good Foods' 10-Q for the
  quarter to 2021-02-27 and its 10-Q/A of 2021-06-30, which re-files the quarter's statements;
  and Verra Mobility's 10-Q for the quarter to 2023-09-30 and its 10-Q/A of 2023-11-22, which
  carries no fact for the quarter. Each is the filings' companyfacts rows at the quarter's end and
  the submissions rows of the two accessions.

HTTP is mocked.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.edgar.asof import AsOfEdgar, UncutReadError
from vinci.edgar.client import EdgarClient, events, quarterly_report
from vinci.netcache import CachedHttp, HttpError

_ROOT = Path(__file__).resolve().parent / "fixtures"
_PAGES = _ROOT / "submissions_pages"
_AMEND = _ROOT / "amended_filings"
_IT_DOC = json.loads((_PAGES / "IT.json").read_text())
_IT_PAGE1 = json.loads((_PAGES / "IT-submissions-001.json").read_text())
_IT = "0000749251"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text()))


class _Sec:
    """Serves a submissions document, its older page -001, and companyfacts; refuses the rest."""

    def __init__(self, doc: dict[str, Any], *, page1: dict[str, Any] | None = None,
                 facts: dict[str, Any] | None = None) -> None:
        self.doc, self.page1, self.facts = doc, page1, facts
        self.urls: list[str] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> Any:
        self.urls.append(url)
        if "-submissions-001.json" in url and self.page1 is not None:
            return self.page1
        if "/submissions/CIK" in url:
            return self.doc
        if "/companyfacts/" in url and self.facts is not None:
            return self.facts
        raise HttpError(f"not served: {url}")

    def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
        self.urls.append(url)
        return "<html><body>Our largest customer accounted for 12% of revenue.</body></html>"


def _gartner() -> tuple[EdgarClient, _Sec]:
    sec = _Sec(_IT_DOC, page1=_IT_PAGE1)
    return EdgarClient(http=cast(CachedHttp, sec)), sec


def _page1(form: str) -> set[str]:
    return {a for a, f in zip(_IT_PAGE1["accessionNumber"], _IT_PAGE1["form"], strict=True)
            if f == form}


# ─── RE1-D8: a read with no window reaches back from the cut ───────────────────────────────────

def test_a_cut_before_the_recent_page_reads_the_older_page() -> None:
    """⊖ TeamNostra's reproduction on Gartner: the recent page starts 2021-12-02, and at a
    2021-11-30 cut the view found no 8-K, no 10-Q and no events, while older page -001 holds 7
    8-Ks and 3 10-Qs filed before the cut."""
    client, sec = _gartner()
    view = AsOfEdgar(client, date(2021, 11, 30))
    assert {f.accession for f in view.recent_filings(_IT, forms=("8-K",))} == _page1("8-K")
    assert {f.accession for f in view.recent_filings(_IT, forms=("10-Q",))} == _page1("10-Q")
    assert len(_page1("8-K")) == 7 and len(_page1("10-Q")) == 3
    assert {f.accession for f in events(view, _IT)} == _page1("8-K")
    # page -002 (1996–2010) lies wholly before the reach and is never fetched
    assert not any("-submissions-002" in u for u in sec.urls)


def test_a_cut_just_inside_the_recent_page_reads_back_past_its_start() -> None:
    """⊖ at a 2022-01-15 cut the recent page held six weeks of Gartner's filings; the page as it
    stood then held at least a year of them (SEC: "at least one year's of filing or to 1,000")."""
    client, _ = _gartner()
    got = AsOfEdgar(client, date(2022, 1, 15)).recent_filings(_IT, forms=("8-K",))
    assert _page1("8-K") <= {f.accession for f in got}
    assert all(f.filing_date <= date(2022, 1, 15) for f in got)


def test_a_cut_on_or_after_the_newest_filing_reads_the_recent_page_alone() -> None:
    """⊕ the negative pin: when nothing on the recent page was filed after the cut, the page is
    what EDGAR showed then, and no older page is fetched — as before."""
    client, sec = _gartner()
    newest = max(date.fromisoformat(d) for d in _IT_DOC["filings"]["recent"]["filingDate"])
    uncut = client.recent_filings(_IT, forms=("8-K",))
    assert AsOfEdgar(client, newest).recent_filings(_IT, forms=("8-K",)) == uncut
    assert not any("-submissions-0" in u for u in sec.urls)


def test_a_window_the_caller_names_is_kept() -> None:
    """⊕ a reader that asks for a window gets that window, cut — the reach applies only when it
    asked for none."""
    client, sec = _gartner()
    got = AsOfEdgar(client, date(2026, 8, 1)).recent_filings(_IT, forms=("8-K",),
                                                             since=date(2022, 1, 1))
    assert got and all(date(2022, 1, 1) <= f.filing_date <= date(2026, 8, 1) for f in got)
    assert not any("-submissions-0" in u for u in sec.urls)


# ─── RE1-D9: what the view cannot cut, it refuses ──────────────────────────────────────────────

@pytest.mark.parametrize(("name", "args", "kwargs"), [
    ("frame", ("EntityCommonStockSharesOutstanding",), {"period": "CY2021Q3I"}),
    ("shares_outstanding_with_provenance", (["CY2021Q3I"],), {}),
    ("shares_outstanding_by_cik", (["CY2021Q3I"],), {}),
    ("_submissions", (_IT,), {}),
])
def test_a_read_the_view_cannot_cut_is_refused(name: str, args: tuple[Any, ...],
                                               kwargs: dict[str, Any]) -> None:
    """⊖ TeamNostra's probe: `frame()` through the view returned today's value at both cuts. The
    frames API carries no filing date, so the view refuses — loudly, and not as an HttpError a
    reader would degrade to UNKNOWN."""
    client, sec = _gartner()
    view = AsOfEdgar(client, date(2021, 11, 30))
    with pytest.raises(UncutReadError, match=name):
        getattr(view, name)(*args, **kwargs)
    assert not issubclass(UncutReadError, HttpError)
    assert sec.urls == []  # nothing was sent


def test_reads_of_the_filer_as_it_is_now_still_pass_through() -> None:
    """⊕ the negative pin: the registrant's names and incorporation describe it today by design,
    and `.uncut` still reaches every read for a reader saying what the cut left out."""
    client, _ = _gartner()
    view = AsOfEdgar(client, date(2021, 11, 30))
    assert view.registrant_history(_IT).current
    assert view.uncut is client


# ─── RE1-D12: a 10-Q/A is read or named, by the annual rule ────────────────────────────────────

def _quarter(ticker: str) -> EdgarClient:
    sec = _Sec(_load(_AMEND / f"{ticker}-10qa-submissions.json"),
               facts=_load(_AMEND / f"{ticker}-10qa-facts.json"))
    return EdgarClient(http=cast(CachedHttp, sec))


def test_a_ten_q_amendment_carrying_the_quarters_statements_is_read_in_its_place() -> None:
    """⊖ Simply Good Foods' 10-Q/A of 2021-06-30 re-files the quarter to 2021-02-27 (a balance
    sheet and an income statement, 168 tags against the original's 164): the reader listed only
    "10-Q" and read the original, naming nothing."""
    read = quarterly_report(_quarter("SMPL"), "1702744")
    assert read is not None
    assert read.original.accession == "0001702744-21-000035"
    assert read.filing.accession == "0001702744-21-000068" and read.filing.form == "10-Q/A"
    assert read.pointer is not None and "read in its place" in read.pointer


def test_a_ten_q_amendment_with_no_statements_is_named_and_not_read() -> None:
    """⊖ Verra Mobility's 10-Q/A of 2023-11-22 carries no fact for the quarter to 2023-09-30: the
    10-Q is read, and the /A is named beside it."""
    read = quarterly_report(_quarter("VRRM"), "1682745")
    assert read is not None and read.filing.accession == "0000950170-23-062105"
    assert read.pointer is not None and "0001193125-23-282249" in read.pointer
    assert "carries no financial statements" in read.pointer


def test_the_pages_ten_q_read_names_the_amendment_it_read() -> None:
    """⊖ end to end through the page's primary-source pass: its 10-Q sections come from the
    10-Q/A that carries the quarter, and the source says so."""
    from types import SimpleNamespace

    from vinci.dossier import mechanical as mech
    from vinci.dossier.ciq import CiqBundle

    edgar = _quarter("SMPL")
    rec = SimpleNamespace(identity=SimpleNamespace(cik="0001702744", ticker="SMPL"))
    layer = SimpleNamespace(capital_structure=None, leverage_survival=None)
    sec = cast(_Sec, edgar._http)  # noqa: SLF001
    ps, _lat, _drv = mech._primary_source(  # noqa: SLF001
        rec, edgar, cast(CachedHttp, sec), CiqBundle.from_files("SMPL", []),  # type: ignore[arg-type]
        date(2021, 8, 1), layer)  # type: ignore[arg-type]
    assert ps.filing is not None
    assert ps.filing.source_ref.startswith("10-Q/A 0001702744-21-000068")
    assert "read in its place" in ps.filing.source_ref


# ─── RE1-D13 / E1-D7: the graph's excerpts read the annual report by the /A rule ───────────────

def _annual(ticker: str) -> tuple[EdgarClient, _Sec]:
    name = (f"{ticker}-period-facts" if (_AMEND / f"{ticker}-period-facts.json").exists()
            else f"{ticker}-facts")
    sec = _Sec(_load(_AMEND / f"{ticker}-submissions.json"), facts=_load(_AMEND / f"{name}.json"))
    return EdgarClient(http=cast(CachedHttp, sec)), sec


def test_the_graphs_excerpts_read_an_amendment_carrying_the_statements() -> None:
    """⊖ Ducommun's 10-K/A restates FY2025: `latest_10k_excerpts` read the original 10-K and
    named nothing (TeamNostra's probe: "the later 10-K/A … is neither read nor named")."""
    from vinci.graph.filings import latest_10k_excerpts

    edgar, sec = _annual("DCO")
    got = latest_10k_excerpts(edgar, "30305", http=cast(CachedHttp, sec))
    assert got is not None
    accession, text, amendments, cut = got
    assert accession == "0001628280-26-032536" and cut is None
    assert amendments is not None and "read in its place" in amendments
    assert "customer" in text


def test_the_graphs_excerpts_name_a_part_iii_amendment_they_do_not_read() -> None:
    """⊖ Skyworks' Part III 10-K/A carries no statements: the 10-K is read, the /A named."""
    from vinci.graph.filings import latest_10k_excerpts

    edgar, sec = _annual("SWKS")
    got = latest_10k_excerpts(edgar, "4127", http=cast(CachedHttp, sec))
    assert got is not None
    assert got[0] == "0000004127-25-000085"
    assert got[2] is not None and "0000004127-26-000003" in got[2] and "not read" in got[2]


def test_the_graphs_excerpts_read_an_unamended_annual_as_before() -> None:
    """⊕ the negative pin: Gartner files no annual /A, so its newest 10-K is read and nothing is
    named — as before."""
    from vinci.graph.filings import latest_10k_excerpts

    client, sec = _gartner()
    rows = client.recent_filings(_IT, forms=("10-K",))
    got = latest_10k_excerpts(client, _IT, http=cast(CachedHttp, sec))
    assert got is not None and got[0] == max(rows, key=lambda f: f.filing_date).accession
    assert got[2] is None


# ─── RE1-D14: the excerpt cap says what it left out ────────────────────────────────────────────

def _customers(n: int) -> str:
    return " ".join(f"Customer {i} accounted for {i % 9 + 1}% of our revenue in fiscal 2025."
                    for i in range(n))


def test_the_excerpt_cap_says_how_much_it_left_unread() -> None:
    """⊖ TeamNostra's probe: 600 customer sentences (36,599 characters) kept 400, and neither the
    excerpt nor the graph's info said so. The excerpt is unchanged — a statement beside it, never
    inside it, since the excerpt is what an extractor quotes — and the graph records it."""
    from vinci.graph.filings import excerpt_cut, relevant_excerpts

    text = _customers(600)
    kept = relevant_excerpts(text).split("\n")
    assert 0 < len(kept) < 600
    cut = excerpt_cut(text)
    assert cut is not None and f"kept {len(kept)} of 600" in cut and "24,000" in cut
    assert "cap" not in relevant_excerpts(text)


def test_an_excerpt_under_the_cap_states_no_cut() -> None:
    """⊕ the negative pin: every matching sentence kept, nothing said."""
    from vinci.graph.filings import excerpt_cut

    assert excerpt_cut(_customers(40)) is None


def test_the_graph_records_a_cut_beside_the_accession(monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ end to end through `extract_graph_edges`: the cut reaches the edge info."""
    from types import SimpleNamespace

    from vinci.graph import extract as gx

    served = ("ACC-1", "Customer A accounted for 12% of our revenue.", None,
              "the 24,000-character excerpt cap kept 400 of 600 matching sentences; the 200 "
              "after it were not read")
    monkeypatch.setattr(gx, "latest_10k_excerpts", lambda edgar, cik, http=None: served)
    llm = SimpleNamespace(extract=lambda **kw: {"relationships": []})
    focal = SimpleNamespace(eod_symbol="X", cik="0000000001", ticker="X", name="X Corp")
    _edges, info = gx.extract_graph_edges(cast(EdgarClient, None), cast(Any, None),
                                          cast(Any, llm), cast(Any, focal))
    assert info["excerpts_cut"] == served[3] and "amendments" not in info
