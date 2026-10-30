"""X1(a) — a share count tagged AFTER its own filing is dated from its cover sentence.

107 of 91,485 share points in the 2,253 cached companyfacts end after their own filing (2026-10-30),
and the one-sided age check (`ref - end <= bound`) passed each one: a future date is never too old.
For five filers it was the NEWEST count. THM served a 2023 count, tagged 2033, as fresh; REPX served
a 2024 count, tagged 2029, over its real 2026-08-03 one; VRRM's page carries a count tagged
2026-08-31 in a 10-Q filed 2026-08-05.

The operator's ruling (2026-10-30, "Yes, cross-check"): such a count is DATED from the filing's
cover sentence by an anchored parse; an unreadable cover dates it at its filing day, printed
"filed <date>"; its VALUE is checked against another count in the same filing, and a disagreement
past the tolerance makes it UNKNOWN naming both figures; every correction is a QA flag.

Every fixture is real: VRRM's committed companyfacts subset and cover sentence, JJSF's cover
sentence, and the share tags of AAL's, THM's and REPX's companyfacts (`tests/fixtures/cover_count`).
HTTP is mocked."""
from __future__ import annotations

import ast
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.dossier.mechanical import (
    _edgar_shares_outstanding,
    _share_count_flags,
    _share_count_trend,
)
from vinci.edgar import cover_count as cc
from vinci.edgar.client import EdgarClient, Filing
from vinci.edgar.concepts import ConceptPoint, extract_points
from vinci.graph.filings import html_to_text
from vinci.netcache import CachedHttp, HttpError

_ROOT = Path(__file__).resolve().parent.parent
_FIX = _ROOT / "tests" / "fixtures" / "cover_count"
COVERS: dict[str, dict[str, Any]] = json.loads((_FIX / "covers.json").read_text())


def _facts(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text()))


VRRM = _facts(_ROOT / "tests" / "fixtures" / "companyfacts" / "VRRM.json")


# ─── the anchored parse ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ticker", ["VRRM", "JJSF"])
def test_the_cover_sentence_dates_its_own_count(ticker: str) -> None:
    """VRRM: "As of August 3, 2026, there were 151,982,804 shares"; JJSF's cover table:
    "Outstanding as of May 1, 2026 Common Stock, no par value 18,753,416 shares"."""
    c = COVERS[ticker]
    got = cc.cover_date(c["cover_window"], float(c["value"]))
    assert got == date.fromisoformat(c["cover_date"])
    assert got < date.fromisoformat(c["filed"]) < date.fromisoformat(c["tagged_end"])


def test_a_cover_sentence_dates_only_the_count_it_states() -> None:
    """The negative pin: the sentence must carry the tagged value itself — one share off reads
    nothing, and so does a value the window does not hold at all."""
    c = COVERS["VRRM"]
    assert cc.cover_date(c["cover_window"], 151_982_805.0) is None
    assert cc.cover_date(c["cover_window"], 18_753_416.0) is None


def test_a_sentence_with_two_dates_is_not_read() -> None:
    """Two introduced dates in the count's sentence name neither — never a guess between them."""
    two = COVERS["VRRM"]["cover_window"].replace(
        "As of August 3, 2026, there were",
        "As of August 3, 2026 and as of July 31, 2026, there were")
    assert cc.cover_date(two, 151_982_804.0) is None


# ─── the resolver over real companyfacts ──────────────────────────────────────────────────────

def _read(*tickers: str) -> Any:
    by_acc = {COVERS[t]["accession"]: COVERS[t]["cover_window"] for t in tickers}
    return lambda p: by_acc.get(p.accession)


def test_vrrm_reads_at_its_cover_date_and_the_rest_at_their_filing_day() -> None:
    counts = cc.date_counts(extract_points(VRRM, "shares"), VRRM, read=_read("VRRM"))
    moved = {c.point.accession: c for c in counts if c.tagged != c.point.period_end}
    assert len(moved) == 5  # the five VRRM tags after their own filing
    newest = moved["0001193125-26-335490"]
    assert (newest.point.period_end, newest.bound, newest.when) == (
        date(2026, 8, 3), False, "2026-08-03")
    assert newest.point.value == 151_982_804 and newest.refused is None
    may = moved["0001193125-26-209227"]  # its cover was not supplied: the filing day bounds it
    assert (may.point.period_end, may.bound, may.when) == (
        date(2026, 5, 6), True, "filed 2026-05-06")
    assert all(c.point.period_end <= c.point.filed for c in counts)


def test_each_correction_flags_the_tagged_date_the_date_read_and_the_accession() -> None:
    counts = cc.date_counts(extract_points(VRRM, "shares"), VRRM, read=_read("VRRM"))
    flag = next(c for c in counts if c.point.accession == "0001193125-26-335490").flags[0]
    for part in ("0001193125-26-335490", "2026-08-31", "2026-08-05", "2026-08-03", "151,982,804"):
        assert part in flag
    unread = next(c for c in counts if c.point.accession == "0001193125-26-209227").flags[0]
    assert "could not be read" in unread and "filed 2026-05-06" in unread
    assert not next(c for c in counts if c.tagged == c.point.period_end).flags


def test_a_count_its_own_filing_contradicts_is_unknown_naming_both() -> None:
    """VRRM's newest count mutated 10% high. Its 10-Q carries no undimensioned balance-sheet count,
    so the same filing's quarter diluted weighted average (151,945,000) is the check, and it
    disagrees past the 5% tolerance: the count is refused — never picked over the other."""
    facts = json.loads(json.dumps(VRRM))
    for r in facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]:
        if r["accn"] == "0001193125-26-335490":
            r["val"] = round(r["val"] * 1.10)
    counts = cc.date_counts(extract_points(facts, "shares"), facts, read=_read("VRRM"))
    c = next(c for c in counts if c.point.accession == "0001193125-26-335490")
    assert c.refused is not None and "UNKNOWN" in c.refused
    assert "167,181,084" in c.refused and "151,945,000" in c.refused
    assert "diluted weighted average" in c.refused and re.search(r"\+\d+\.\d%", c.refused)
    assert c.flags[-1].endswith(c.refused)


def test_a_refused_count_is_unknown_on_the_page() -> None:
    """The refusal reaches the readers: no share count, and no trend across it."""
    facts = json.loads(json.dumps(VRRM))
    for r in facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]:
        if r["accn"] == "0001193125-26-335490":
            r["val"] = round(r["val"] * 1.10)
    edgar, http = cast(EdgarClient, _Edgar(facts)), cast(CachedHttp, _Http(refuse=True))
    assert _edgar_shares_outstanding(edgar, "0001682745", as_of=date(2026, 8, 14),
                                     http=http) is None
    trend = _share_count_trend(edgar, "0001682745", date(2026, 8, 14), http=http)
    assert trend.value is None and "UNKNOWN" in (trend.note or "")


def test_the_tolerance_admits_vrrms_real_count() -> None:
    """The negative pin: unmutated, VRRM's count sits within 5% of its own filing's counts."""
    counts = cc.date_counts(extract_points(VRRM, "shares"), VRRM, read=_read("VRRM"))
    assert not [c for c in counts if c.refused]


@pytest.mark.parametrize(("ticker", "newest_acc", "read_at", "value"), [
    # a 2033 tag on a 2023 filing no longer shadows the real 2026 count
    ("THM", "0001104659-26-057981", date(2026, 5, 1), 261_637_473),
    # a 2029 tag on a 2024 10-K/A no longer shadows the real 2026-08-03 count
    ("REPX", "0001001614-26-000051", date(2026, 8, 3), 22_153_785),
    # a 2027 tag on a 2026 10-Q: the count stays, dated no later than its filing
    ("AAL", "0000006201-26-000052", date(2026, 7, 23), 661_969_951),
])
def test_a_typo_year_no_longer_wins_newest(ticker: str, newest_acc: str, read_at: date,
                                           value: float) -> None:
    facts = _facts(_FIX / f"{ticker}.json")
    counts = cc.date_counts(extract_points(facts, "shares"), facts, read=lambda p: None)
    newest = max(counts, key=lambda c: (c.point.period_end, c.point.filed))
    assert (newest.point.accession, newest.point.period_end, newest.point.value) == (
        newest_acc, read_at, value)
    assert newest.refused is None


# ─── through the page's readers, with mocked HTTP ─────────────────────────────────────────────

class _Edgar:
    """The two client methods the readers touch: companyfacts, and the submissions index that names
    each filing's primary document."""

    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        c = COVERS["VRRM"]
        if c["form"] not in forms:
            return []
        return [Filing(cik="0001682745", form=c["form"], filing_date=date.fromisoformat(c["filed"]),
                       accession=c["accession"], items=[], primary_doc=c["primary_doc"])]


class _Http:
    """Serves VRRM's cover as HTML, or refuses every fetch."""

    def __init__(self, *, refuse: bool = False) -> None:
        self.refuse = refuse
        self.urls: list[str] = []

    def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
        self.urls.append(url)
        if self.refuse:
            raise HttpError(f"simulated: {url}")
        assert url == COVERS["VRRM"]["url"], url
        return f"<html><body><p>{COVERS['VRRM']['cover_window']}</p></body></html>"


def _edgar() -> EdgarClient:
    return cast(EdgarClient, _Edgar(VRRM))


def test_vrrms_page_trend_ends_at_its_cover_date() -> None:
    """The committed page (reference 2026-08-14) printed "… → 151,982,804 (2026-08-31)". The count
    stays and is confirmed; it is dated 2026-08-03. The window's first count moves too: the
    2024-08-31 tag was filed 2024-08-08, before the window opens."""
    http = _Http()
    out = _share_count_trend(_edgar(), "0001682745", date(2026, 8, 14),
                             http=cast(CachedHttp, http))
    assert out.value is not None
    assert "151,982,804 (2026-08-03)" in out.value and "2026-08-31" not in out.value
    assert "164,804,157 (2024-10-25)" in out.value
    assert http.urls == [COVERS["VRRM"]["url"]]


def test_an_unreadable_cover_prints_filed_never_a_count_date() -> None:
    out = _share_count_trend(_edgar(), "0001682745", date(2026, 8, 14),
                             http=cast(CachedHttp, _Http(refuse=True)))
    assert out.value is not None and "151,982,804 (filed 2026-08-05)" in out.value


def test_vrrms_count_stays_on_the_page_at_its_cover_date() -> None:
    http = cast(CachedHttp, _Http())
    assert _edgar_shares_outstanding(_edgar(), "0001682745", as_of=date(2026, 8, 14),
                                     http=http) == 151_982_804
    flags = _share_count_flags(_edgar(), http, "0001682745", date(2026, 8, 14))
    assert any("0001193125-26-335490" in f and "2026-08-03" in f for f in flags)


def test_the_assembly_path_hands_every_share_reader_its_fetcher() -> None:
    """PIN THE CALL SITES, NOT THE HELPER. Without ``http`` a reader cannot read a cover and every
    corrected count falls to its filing-day bound — a helper test would stay green with the wiring
    deleted. Every call of a share reader inside the module passes ``http=``."""
    src = (_ROOT / "vinci" / "dossier" / "mechanical.py").read_text()
    readers = {"_share_count_trend", "_edgar_shares_outstanding", "_adjusted_facts",
               "_stock_info", "_quality", "_share_count_flags"}
    calls = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id in readers]
    assert len(calls) >= 7, [c.func.id for c in calls if isinstance(c.func, ast.Name)]
    # BY KEYWORD, every one (review round 1): a positional slot accepted `None` unseen
    unwired = [cast(ast.Name, c.func).id for c in calls
               if not any(k.arg == "http" and not (isinstance(k.value, ast.Constant)
                                                  and k.value.value is None)
                          for k in c.keywords)]
    assert not unwired, f"share readers called without their fetcher: {unwired}"


def test_a_long_hidden_xbrl_header_cannot_push_the_cover_past_the_cut() -> None:
    """Farmers National Banc's 10-K opens with a hidden inline-XBRL header that runs to raw
    character 756,469, so the first 400,000 characters held no cover at all. The header is dropped
    before the cut; without that, the same document reads nothing."""
    c = COVERS["VRRM"]
    hidden = ('<ix:header><ix:hidden><ix:nonNumeric name="dei:EntityCommonStockSharesOutstanding">'
              + "x" * (cc.COVER_HEAD_CHARS + 50_000) + "</ix:nonNumeric></ix:hidden></ix:header>")
    html = f"<html><body>{hidden}<p>{c['cover_window']}</p></body></html>"
    assert cc.cover_date(html_to_text(cc.cover_head(html)), float(c["value"])) == date(2026, 8, 3)
    assert cc.cover_date(html_to_text(html[:cc.COVER_HEAD_CHARS]), float(c["value"])) is None


def test_a_correction_is_qa_and_a_refusal_reaches_the_analyst() -> None:
    """The ruling: every corrected date is a QA flag. A refusal explains an UNKNOWN on the page, so
    it routes to the human — the module's default, kept on purpose."""
    from vinci.dossier.flags import is_qa
    counts = cc.date_counts(extract_points(VRRM, "shares"), VRRM, read=_read("VRRM"))
    corrections = [f for c in counts for f in c.flags]
    assert corrections and all(is_qa(f) for f in corrections)
    facts = json.loads(json.dumps(VRRM))
    for r in facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]:
        if r["accn"] == "0001193125-26-335490":
            r["val"] = round(r["val"] * 1.10)
    refused = next(c for c in cc.date_counts(extract_points(facts, "shares"), facts,
                                             read=_read("VRRM")) if c.refused)
    assert not is_qa(refused.flags[-1]) and refused.flags[-1].startswith("share count UNKNOWN:")


def test_a_cover_date_further_back_than_its_form_allows_is_not_the_counts() -> None:
    """Hawaiian Electric's 10-K cover is a table: its one introduced date ("as of June 30, 2025") is
    the market-value date, 242 days before the filing. The parse reads it; the lead window refuses
    it, and the count is dated at its filing day with the stated date named. (The real count is
    correctly tagged; its tag is moved past the filing here to drive the rule.)"""
    c = COVERS["HE"]
    assert cc.cover_date(c["cover_window"], float(c["value"])) == date(2025, 6, 30)
    p = ConceptPoint(concept="shares", tag="EntityCommonStockSharesOutstanding", unit="shares",
                     value=float(c["value"]), period_start=None, period_end=date(2026, 3, 31),
                     filed=date.fromisoformat(c["filed"]), fy=2025, fp="FY", form=c["form"],
                     accession=c["accession"])
    got = cc.date_counts([p], {"facts": {}}, read=lambda _: c["cover_window"])[0]
    assert got.bound and got.when == "filed 2026-02-27"
    assert "2025-06-30" in got.flags[0] and "within 90 days" in got.flags[0]
    assert cc.max_lead_days("10-K") == 90 and cc.max_lead_days("20-F/A") == 180


def test_only_the_first_occurrence_is_the_cover() -> None:
    """Whitestone's cover prints "As o f May 4, 2026", which no anchored parse reads. Its count
    recurs in the financial statements at 2026-03-31; that later occurrence used to be read as the
    cover's date. The first occurrence is the cover, and an unreadable one reads nothing."""
    c = COVERS["WSR"]
    later = (" CONSOLIDATED BALANCE SHEETS Common shares of beneficial interest outstanding at "
             f"March 31, 2026 were {c['value']:,} shares.")
    assert cc.cover_date(c["cover_window"], float(c["value"])) is None
    assert cc.cover_date(c["cover_window"] + later, float(c["value"])) is None
    assert cc.cover_date(later, float(c["value"])) == date(2026, 3, 31)  # the trap, on its own


def test_the_cover_cache_does_not_keep_a_client_alive() -> None:
    """Review round 1: the parsed-cover cache was keyed on the http client, so it held up to 32
    clients (each with its connection pool) after their run. It is keyed on the URL alone — a
    filing's document at its accession URL does not change."""
    import gc
    import weakref

    import vinci.dossier.mechanical as mech
    http = _Http()
    ref = weakref.ref(http)
    assert mech._cover_text(_edgar(), cast(CachedHttp, http), "0001682745",
                            extract_points(VRRM, "shares")[-1].model_copy(update={
                                "accession": COVERS["VRRM"]["accession"], "form": "10-Q"}))
    del http
    gc.collect()
    assert ref() is None


# ─── review round 2: each comparison carries its own measured tolerance ─────────────────────

def _vrrm_newest_scaled(k: float) -> dict[str, Any]:
    facts = json.loads(json.dumps(VRRM))
    for r in facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]:
        if r["accn"] == "0001193125-26-335490":
            r["val"] = round(r["val"] * k)
    return facts


@pytest.mark.parametrize(("k", "refused"), [(1.07, False), (1.12, True)])
def test_the_diluted_average_check_has_its_own_tolerance(k: float, refused: bool) -> None:
    """VRRM's 10-Q is checked against its quarter diluted average. Cover vs that average is wider
    than cover vs a balance-sheet count (14,279 cached pairs: p90 5.68%, 93.5% within 10%), so a
    7% gap is ordinary and a 12% one is not."""
    facts = _vrrm_newest_scaled(k)
    c = next(c for c in cc.date_counts(extract_points(facts, "shares"), facts, read=_read("VRRM"))
             if c.point.accession == "0001193125-26-335490")
    assert (c.refused is not None) is refused
    assert cc.TOLERANCES["diluted weighted average"] == 0.10


def test_a_previous_count_older_than_the_age_bound_is_no_reference() -> None:
    """With no other count in its filing, a count is held against the previous one only within the
    readers' 180-day age bound. VRRM's count before its 2026-08-05 10-Q, read with no other count
    in reach, is from 2025-10-24 — 285 days back: nothing to check against."""
    def pt(end: date, filed: date, value: float, acc: str) -> ConceptPoint:
        return ConceptPoint(concept="shares", tag="EntityCommonStockSharesOutstanding",
                            unit="shares", value=value, period_start=None, period_end=end,
                            filed=filed, fy=None, fp=None, form="10-Q", accession=acc)
    prev = pt(date(2025, 10, 24), date(2025, 10, 29), 159_564_447, "0001193125-25-256492")
    late = pt(date(2026, 8, 31), date(2026, 8, 5), 151_982_804, "0001193125-26-335490")
    got = cc.date_counts([prev, late], {"facts": {}}, read=_read("VRRM"))[1]
    assert got.refused is None
    assert any("no other count" in f for f in got.flags)
    from vinci.dossier.mechanical import _SHARES_MAX_AGE_DAYS
    assert cc.PREVIOUS_COUNT_MAX_AGE_DAYS == _SHARES_MAX_AGE_DAYS


def test_a_count_first_met_past_the_cover_block_is_not_a_cover() -> None:
    """Natural Resource Partners' count first appears on its balance sheet ("units issued and
    outstanding at March 31, 2026"), past the document's first PART I heading — no cover sentence.
    The cover block ends there: over every cached cover read that equals its own tag, the count
    sits before the first PART I heading (2,825) or the document has none (53), never after it."""
    c = COVERS["NRP"]
    text = f"{c['part_one_heading']} {c['balance_sheet_window']}"
    assert cc.cover_date(c["balance_sheet_window"], float(c["value"])) == date(2026, 3, 31)
    assert cc.cover_date(text, float(c["value"])) is None
    v = COVERS["VRRM"]  # the negative pin: a cover ahead of its PART I heading still reads
    assert cc.cover_date(f"{v['cover_window']} PART I. FINANCIAL INFORMATION", 151_982_804.0) == (
        date(2026, 8, 3))
