"""The research desk (PR #703, the approved design, 2026-10-13) — six screens and a thesis reading
page written beside a run's outputs, read from the registry's structured records.

End to end on registries built through the REAL engine (tests/theme_intelligence_stress.py: a
SYNTHETIC six- and twelve-week registry — every article titled "[SYNTHETIC STRESS TEST]" on a
reserved `.test` domain) and on hypothetical articles built from the real extraction types: lists
at 50-150 theses and hundreds of articles say how much they hold; findings raised in earlier weeks
stay on Review; a preview is never presented as read in full; every evidence and review link
reaches its record; the default view carries no engine id or code while the audit view keeps
them; all nine card sections stay one click away; the near-term reading of record is told apart
from the source's horizon framing (the Nomura presentation); nothing is written to the registry.

No network, no model call.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_stress import build_stress_registry
from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
    table_counts,
)
from vinci.theme_intelligence import desk
from vinci.theme_intelligence.config import load_taxonomy
from vinci.theme_intelligence.desk import (
    AREA_NAME,
    area_name,
    gates,
    near_term_reading,
    near_term_words,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import line_findings, theses_as_of_run, write_run_outputs
from vinci.theme_intelligence.schemas import (
    RetrievalState,
    RunStatus,
    ThesisStatus,
    ThesisVersion,
)

SCREENS = ("index.html", "themes.html", "articles.html", "review.html", "uploads.html",
           "sources.html")
IDS = re.compile(r"\b(?:TH-[0-9A-F]{8,}|C-[0-9a-f]{8,}|A-[0-9a-f]{10,}|R-2026\w+|D-[0-9a-f]{16}"
                 r"|VI-[0-9a-f]{8,})\b")
CODES = re.compile(r"\b[A-Z]{2,}(?:_[A-Z0-9]{2,})+\b|\bF\d{1,2}_[a-z_]+")
SECTIONS = ("s01_bottom_line", "s02_what_changed", "s03_transmission", "s04_key_evidence",
            "s05_affected", "s06_why_now", "s07_what_could_go_wrong", "s08_decision", "s09_sources")


def _soup(p: Path) -> BeautifulSoup:
    return BeautifulSoup(p.read_text(), "html.parser")


def _default_text(p: Path) -> str:
    """A page's DEFAULT view: the audit layer, scripts and the folded command blocks removed."""
    s = _soup(p)
    for x in s.select(".aud, script, style, code.cmd, title"):
        x.decompose()
    return s.get_text(" ")


def _render(pipe: Pipeline, run_id: str, out: Path) -> Path:
    return Path(write_run_outputs(pipe.store, run_id, out)["dir"])


@pytest.fixture(scope="module")
def w12(tmp_path_factory: pytest.TempPathFactory) -> tuple[Pipeline, Path, dict[str, int]]:
    root = tmp_path_factory.mktemp("stress12")
    pipe, stats = build_stress_registry(root / "reg", weeks=12)
    before = table_counts(pipe)
    calls = int(pipe.store.conn.execute("SELECT COUNT(*) FROM llm_calls").fetchone()[0])
    out = _render(pipe, stats.scans[-1], root / "out")
    after = table_counts(pipe)
    assert int(pipe.store.conn.execute("SELECT COUNT(*) FROM llm_calls").fetchone()[0]) == calls
    return pipe, out, {k: after[k] - before[k] for k in before}


@pytest.fixture(scope="module")
def w6(tmp_path_factory: pytest.TempPathFactory) -> tuple[Pipeline, Path]:
    root = tmp_path_factory.mktemp("stress6")
    pipe, stats = build_stress_registry(root / "reg", weeks=6)
    return pipe, _render(pipe, stats.scans[-1], root / "out")


# --- scale: 50-150 theses, hundreds of articles -----------------------------------------------

def test_the_twelve_week_registry_is_at_the_scale_the_desk_must_hold(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    assert 50 <= len(pipe.store.theses()) <= 150
    assert len(pipe.store.articles()) >= 200
    for name in SCREENS:
        assert (out / name).exists(), name
    weeks = [r for r in pipe.store.runs() if r.mode == "scan"]
    assert len(list(out.glob("articles-*.html"))) == len(weeks) - 1  # one page per earlier week
    run = max(weeks, key=lambda r: r.started_at)
    asof = theses_as_of_run(pipe.store, run)
    assert {p.stem for p in (out / "theses").glob("TH-*.html")} == set(asof)


def test_every_long_list_says_how_much_it_holds_and_keeps_every_row(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """A capped table shows its first rows and SAYS "Showing N of M"; the other rows are in the
    page (one click away), never dropped. Themes holds every thesis of the registry."""
    pipe, out, _ = w12
    seen = 0
    for p in [out / n for n in SCREENS] + sorted(out.glob("articles-*.html")):
        s = _soup(p)
        for lab in s.select("label.morelbl"):
            m = re.fullmatch(r"Showing (\d+) of (\d+) .* — show all (\d+)", lab.get_text(" "))
            assert m and m.group(2) == m.group(3), lab.get_text(" ")
            box = s.find(id=lab["for"])
            assert box is not None and box.get("class") == ["morebox"]
            rows = box.find_next_sibling("div").select("table tr")[1:]  # header row first
            assert len(rows) == int(m.group(2))
            assert sum(1 for r in rows if "xtra" in (r.get("class") or [])) == \
                int(m.group(2)) - int(m.group(1))
            seen += 1
        for d in s.select("details.more-rows > summary"):
            m = re.fullmatch(r"Showing (\d+) of (\d+) .* — show all \d+", d.get_text(" "))
            assert m, d.get_text(" ")
            seen += 1
    assert seen, "the twelve-week registry must exercise at least one capped list"
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    rows = _soup(out / "themes.html").select("#tt tr[data-area]")
    assert len(rows) == len(theses_as_of_run(pipe.store, run))


# --- review: every active thesis, whatever week -------------------------------------------------

def test_review_lists_every_open_finding_of_every_active_thesis_including_earlier_weeks(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    expected = 0
    for t, v in theses_as_of_run(pipe.store, run).values():
        if t.status is not ThesisStatus.ARCHIVED:
            blocked, flagged, _c, _r = line_findings(pipe.store, t.thesis_id, v)
            expected += len(blocked) + len(flagged) + near_term_reading(pipe.store, v).conflict
    items = _soup(out / "review.html").select("#rv li.rvi")
    assert expected and len(items) == expected
    ages = [int(i["data-age"]) for i in items]
    assert max(ages) >= 28  # raised four weeks or more ago — still here
    # decision-affecting first, then Research Now, then the oldest
    order = [(0 if i["data-dec"] == "1" else 1, 0 if i["data-act"] == "RESEARCH NOW" else 1,
              -int(i["data-age"])) for i in items]
    assert order == sorted(order)


def test_a_review_link_opens_the_exact_flagged_line_in_the_full_record(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    _pipe, out, _ = w12
    links = list(_soup(out / "review.html").select("#rv li.rvi a[href*='cards/']"))
    assert links
    for a in links:
        u = urlparse(str(a["href"]))
        card = _soup(out / unquote(u.path))
        target = card.find(id=u.fragment)
        assert target is not None, a["href"]
        line = a.find_parent("li").select_one(".line").get_text(" ").strip("“” ")
        assert line[:40] in target.get_text(" "), (line[:40], u.fragment)


# --- reading -------------------------------------------------------------------------------------

def test_a_preview_is_never_presented_as_read_in_full(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    partial = {a.title for a in pipe.store.articles()
               if (vs := pipe.store.article_versions(a.article_id))
               and vs[-1].retrieval_state is RetrievalState.PARTIAL}
    assert partial
    shown = 0
    for p in [out / "articles.html", *out.glob("articles-*.html")]:
        for tr in _soup(p).select("#at tr[data-state]"):
            title = tr.select("td")[2].select_one("a")
            if title is not None and title.get_text() in partial:
                assert tr["data-state"] == "PARTIAL", title.get_text()
                assert "Read in full" not in tr.get_text(" ")
                shown += 1
    assert shown >= len(partial) * 0.9  # (an article read twice is listed in both weeks)


def test_every_local_link_and_anchor_on_the_desk_resolves(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    _pipe, out, _ = w12
    pages = [out / n for n in SCREENS] + sorted(out.glob("articles-*.html")) + sorted(
        (out / "theses").glob("TH-*.html"))
    ids: dict[Path, set[str]] = {}

    def anchors(p: Path) -> set[str]:
        if p not in ids:
            ids[p] = {str(x["id"]) for x in _soup(p).select("[id]")}
        return ids[p]

    broken = []
    for p in pages:
        for a in _soup(p).select("a[href]"):
            u = urlparse(str(a["href"]))
            if u.scheme:
                assert u.scheme in ("http", "https"), a["href"]  # never a urn: as a link
                continue
            target = (p.parent / unquote(u.path)).resolve() if u.path else p
            if not target.exists() or (u.fragment and unquote(u.fragment) not in anchors(target)):
                broken.append(f"{p.name} -> {a['href']}")
    assert broken == []


def test_the_default_view_carries_no_engine_id_or_code_and_the_audit_view_keeps_them(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    pages = [out / n for n in SCREENS] + sorted(out.glob("articles-*.html")) + sorted(
        (out / "theses").glob("TH-*.html"))
    found = Counter(m for p in pages for m in IDS.findall(_default_text(p))
                    + CODES.findall(_default_text(p)))
    assert found == Counter()
    tid = pipe.store.theses()[0].thesis_id
    page = _soup(out / "theses" / f"{tid}.html")
    assert any(tid in x.get_text() for x in page.select(".aud"))  # the audit view keeps the id
    assert any(CODES.search(x.get_text()) for x in page.select(".aud"))  # … and the codes
    assert page.select_one("input#audit") is not None and page.select_one("label[for=audit]")


def test_all_nine_card_sections_are_one_click_from_every_reading_page(
        w6: tuple[Pipeline, Path]) -> None:
    _pipe, out = w6
    pages = sorted((out / "theses").glob("TH-*.html"))
    assert pages
    for p in pages:
        hrefs = [str(a["href"]) for a in _soup(p).select("a[href]")]
        for sec in SECTIONS:
            link = next(h for h in hrefs if h.endswith("#sec-" + sec))
            card = _soup(p.parent / unquote(urlparse(link).path))
            assert card.find(id="sec-" + sec) is not None


def test_the_desk_writes_nothing_to_the_registry(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    _pipe, _out, delta = w12
    assert set(delta.values()) == {0}


def test_older_upload_requests_stay_listed_and_are_never_dismissed_by_age(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    first = min(r.as_of for r in pipe.store.runs() if r.mode == "scan")
    old = [a for a in pipe.store.articles()
           if (vs := pipe.store.article_versions(a.article_id))
           and vs[-1].retrieval_state is RetrievalState.PARTIAL
           and a.published_at and a.published_at.date() <= first]
    assert old, "the fixture must hold a preview from the first week"
    text = _soup(out / "uploads.html").get_text(" ")
    for a in old:
        assert a.title in text


def test_this_week_groups_its_changes_by_area_and_lists_what_each_article_produced(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    s = _soup(out / "index.html")
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    asof = theses_as_of_run(pipe.store, run)
    for area in s.select("section.main div.area"):
        name = area.select_one("h3").contents[0].strip()
        for a in area.select("a.trow"):
            tid = Path(str(a["href"])).stem
            assert area_name(asof[tid][0].key_node) == name
    note = s.find(string=re.compile(r"Showing \d+ of \d+ articles"))
    rows = s.select("table.prod tr")[1:]
    if note:
        n = int(re.search(r"of (\d+)", str(note)).group(1))  # type: ignore[union-attr]
        assert len(rows) < n
    states = {r.select_one(".st").get_text() for r in rows}
    assert "Read in full" in states


# --- areas, the near-term reading ---------------------------------------------------------------

def test_every_taxonomy_node_has_a_short_area_name_and_keys_are_untouched() -> None:
    nodes = [n.id for n in load_taxonomy().nodes]
    assert set(nodes) <= set(AREA_NAME)
    for n in nodes:
        name = area_name(n)
        assert "_" not in name and "." not in name and len(name) <= 48, (n, name)
    assert area_name("ai_infrastructure.memory") == "AI infrastructure · Memory"


NOW = date(2026, 10, 12)
PUB = date(2026, 9, 30)
LINES = ("US public debt at 100% of GDP is near historical highs.",
         "Net interest payments now exceed defense outlays.",
         "A setback could weaken the dollar over the coming years.")


def _measured_thesis(tmp_path: Path) -> tuple[Pipeline, ThesisVersion]:
    """The Nomura shape, hypothetical: MEASURED figures with no measurement date or period, in a
    source that frames the thesis as LONGER-TERM — dated, for timing, by the article's date."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=NOW)
    art = Hypo("measured-no-date", "Test Publisher", PUB, [("paragraph", t) for t in LINES])
    x = extraction(
        [claim("c1", "b001", LINES[0].rstrip("."), "US public debt at 100% of GDP",
               metric="US public debt to GDP", value=100, value_text="100%", unit="%"),
         claim("c2", "b002", LINES[1].rstrip("."), "net interest exceeds defense outlays",
               kind="event")],
        [hyp("h1", "Rising US risk premium could weaken the dollar", node="macro_market",
             mechanism="market_structure_risk", horizon="longer_term",
             supporting=["c1", "c2"], sectors=[("USD assets", "b003", "the dollar")])])
    ingest(pipe, art.doc(), x, as_of=NOW, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    return pipe, v


def test_the_near_term_reading_is_told_apart_from_the_sources_horizon_framing(
        tmp_path: Path) -> None:
    pipe, v = _measured_thesis(tmp_path)
    nt = near_term_reading(pipe.store, v)
    assert nt.stored == "yes" and not nt.conflict
    assert v.content.header.horizon.startswith("Longer")  # the framing is longer-term …
    ok, words = near_term_words(nt)
    assert ok and "publication date" in words  # … the dated evidence is current, and says why
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    page = _soup(out / "theses" / f"{v.thesis_id}.html")
    timing = page.select_one(".timing")
    assert timing is not None
    names = [b.get_text() for b in page.select(".gates b")]
    assert names.count(desk.NEAR_GATE) == 1  # the condition is stated ONCE …
    assert timing.select_one("li.ok b").get_text() == desk.NEAR_GATE  # … met, in the timing block
    assert "a description of the thesis, not a test" in timing.get_text(" ")
    assert page.select_one(".conflict") is None


def test_a_near_term_reading_its_own_claims_no_longer_support_is_review_required(
        tmp_path: Path) -> None:
    """NEGATIVE pin: the factor of record says "yes" but its cited claims, re-dated, are long
    range — Review Required, and the research action of record stands."""
    pipe, v = _measured_thesis(tmp_path)
    f5 = next(f for f in v.priority.factors if f.factor_id == "F5_near_term_relevance")
    # the record's own claims re-dated three years on: no longer current
    late = v.model_copy(update={"as_of": NOW + timedelta(days=3 * 365)})
    nt = near_term_reading(pipe.store, late)
    assert nt.stored == f5.value == "yes" and nt.recomputed != "yes" and nt.conflict
    ok, words = near_term_words(nt)
    assert not ok and words.startswith("Review required")
    g = next(x for x in gates(late, [], nt) if x.name == desk.NEAR_GATE)
    assert not g.ok
    assert late.priority.research_action is v.priority.research_action  # never re-decided here


def test_the_reading_page_never_prints_one_line_twice(w6: tuple[Pipeline, Path]) -> None:
    _pipe, out = w6
    for p in sorted((out / "theses").glob("TH-*.html")):
        s = _soup(p)
        main = [x.get_text(" ").strip() for x in s.select(
            "p.thesis, section.panel li:not(.ok):not(.unmet), section.next p")
            if not x.find_parent(attrs={"data-tabs": True})]
        lines = [re.sub(r"\s+(reported|forecast|source's view|our inference|under review)$", "",
                        m) for m in main if len(m) > 30]
        dup = [k for k, n in Counter(lines).items() if n > 1]
        assert dup == [], (p.name, dup)


def test_a_registry_with_test_domain_articles_says_so_on_every_screen(
        w6: tuple[Pipeline, Path]) -> None:
    _pipe, out = w6
    for name in SCREENS:
        banner = _soup(out / name).select_one(".testdata")
        assert banner is not None and "not research" in banner.get_text()


def test_a_registry_of_real_sources_carries_no_test_banner(tmp_path: Path) -> None:
    pipe, _v = _measured_thesis(tmp_path)
    for a in pipe.store.articles():  # the hypothetical fixture is on example.test …
        assert a.canonical_url.startswith("https://example.test/")
    assert desk._test_domain("https://example.test/x")
    assert not desk._test_domain("https://www.nomuraconnects.com/focused-thinking-posts/x/")
    assert not desk._test_domain("urn:document:sha256:abc")
