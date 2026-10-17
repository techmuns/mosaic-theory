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

import dataclasses
import json
import re
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_stress import build_stress_registry
from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    fetched,
    hyp,
    ingest,
    make_pipeline,
    table_counts,
)
from vinci.theme_intelligence import desk
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.desk import (
    AREA_NAME,
    area_name,
    gates,
    near_term_reading,
    near_term_words,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import (
    line_findings,
    review_carry,
    theses_as_of_run,
    write_run_outputs,
)
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
            # header row first; an article's items row (data-sub) belongs to the entry above it
            rows = [r for r in box.find_next_sibling("div").select("table tr")[1:]
                    if not r.has_attr("data-sub")]
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


def test_themes_is_one_table_naming_each_theses_area_and_what_it_is_missing(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """Desk review, 2026-10-17: nine per-area tables, a header broken mid-word ("SOURCE S") and a
    related-theses count under each title. Now ONE table (the area filter reaches every row);
    under each title its area and, for a live Watch, what it is missing — the thesis page's own ✗
    list. NEGATIVE: Research Now, Skip and archived rows name nothing missing, and no row counts
    related theses (the thesis page lists them)."""
    pipe, out, _ = w12
    s = _soup(out / "themes.html")
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    asof = theses_as_of_run(pipe.store, run)
    assert len(s.select("#tt table")) == 1 and s.select("#tt details") == []
    rows = s.select("#tt tr[data-area]")
    watch = 0
    for tr in rows:
        tid = Path(str(tr.select_one("a")["href"])).stem
        t, v = asof[tid]
        sub = tr.select_one(".tsub")
        assert sub.select_one("span").get_text() == tr["data-area"] == area_name(t.key_node)
        miss = _miss_line(tr)
        if t.status is ThesisStatus.ARCHIVED or v.priority.research_action.value != "WATCH":
            assert miss is None, tid
        else:
            assert (miss or []) == _missing(_soup(out / "theses" / f"{tid}.html"))
            watch += bool(miss)
        assert not re.search(r"\d+ related thes", tr.get_text(" "))
    assert watch and watch < len(rows)
    assert "th{overflow-wrap:normal;word-break:normal}" in desk.CSS


# --- review: every active thesis, whatever week -------------------------------------------------

def test_review_lists_every_open_finding_of_every_active_thesis_including_earlier_weeks(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    pipe, out, _ = w12
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    expected = 0
    for t, v in theses_as_of_run(pipe.store, run).values():
        if t.status is not ThesisStatus.ARCHIVED:
            blocked, flagged, _c, _r = line_findings(pipe.store, t.thesis_id, v)
            carry = review_carry(pipe.store, t.thesis_id, v)
            expected += (len(blocked) + len(flagged) + near_term_reading(pipe.store, v).conflict
                         + (carry.not_run is not None) + len(carry.removed))
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
            title = tr.select_one("td.art a")
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
    # a preview-only channel's previews are never asked for (SemiAnalysis, 2026-10-13)
    preview_only = {s.id for s in load_sources() if s.paywalled_posts == "preview_only"}
    old = [a for a in pipe.store.articles()
           if (vs := pipe.store.article_versions(a.article_id))
           and vs[-1].retrieval_state is RetrievalState.PARTIAL
           and a.source_id not in preview_only
           and a.published_at and a.published_at.date() <= first]
    assert old, "the fixture must hold a preview from the first week"
    text = _soup(out / "uploads.html").get_text(" ")
    for a in old:
        assert a.title in text


def _missing(page: BeautifulSoup) -> list[str]:
    """The thesis page's own ✗ conditions, in the few words a list row uses for them."""
    return [desk._SHORT_GATE.get(b.get_text(), b.get_text().lower())
            for b in page.select("aside.decide li.unmet > div > b")]


def _miss_line(el: Any) -> list[str] | None:
    m = el.select_one(".miss")
    if m is None:
        return None
    text = m.get_text()
    assert text.startswith("Missing: "), text
    return text.removeprefix("Missing: ").split(", ")


def test_this_week_groups_its_changes_by_what_happened_and_lists_what_each_article_produced(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """Desk review, 2026-10-17: grouped by area, a Research Now sat fourth in its area beside
    retired theses. The groups are now what HAPPENED, in a fixed order — the decisions first and
    history folded — each row read here from its own chips, never from the grouping code; every
    row names its area; a live Watch names what it is missing, exactly as its page's ✗ list
    does. NEGATIVE: a Research Now or a retired / archived row names nothing missing."""
    pipe, out, _ = w12
    s = _soup(out / "index.html")
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    asof = theses_as_of_run(pipe.store, run)
    order = ["Research Now", "Moved this week", "New this week", "Updated with new evidence"]
    groups = [(g.select_one("h3").contents[0].strip(), g) for g in s.select("main.wrap div.area")]
    names = [n for n, _g in groups]
    assert names and names == [n for n in order if n in names]
    fold = [d for d in s.select("details.quiet")
            if d.select_one("summary").get_text().startswith("Retired or archived this week")]
    assert len(fold) <= 1
    shown, kinds = 0, Counter()
    for name, g in groups + [("Retired", d) for d in fold]:
        for a in g.select("a.trow"):
            t, _v = asof[Path(str(a["href"])).stem]
            gone = bool(t.retired) or t.status is ThesisStatus.ARCHIVED
            ev = [x.get_text() for x in a.select(".ev")]
            moved = any(x.startswith(("↑", "↓")) for x in ev)
            pill = a.select_one(".pill").get_text()
            want = ("Retired" if gone else "Research Now" if pill == "Research Now" else
                    "Moved this week" if moved else "New this week" if "New" in ev else
                    "Updated with new evidence")
            assert name == want, (t.thesis_id, name, want)
            assert a.select_one(".tmeta").get_text(" ").startswith(area_name(t.key_node))
            miss = _miss_line(a)
            if gone or not pill.startswith("Watch"):
                assert miss is None, t.thesis_id
            else:
                assert (miss or []) == _missing(_soup(out / "theses" / f"{t.thesis_id}.html"))
            shown += 1
            kinds[name] += 1
    n = int(re.search(r"(\d+) thes", s.select_one("main.wrap h2").get_text())[1])  # type: ignore[index]
    assert shown == n and len(kinds) >= 3  # every change, once; the fixture spans the groups
    note = s.find(string=re.compile(r"Showing \d+ of \d+ articles"))
    rows = s.select("ul.alist > li")
    if note:
        n = int(re.search(r"of (\d+)", str(note)).group(1))  # type: ignore[union-attr]
        assert len(rows) < n
    states = {r.select_one(".st").get_text() for r in rows}
    assert "Read in full" in states
    assert all(r.select_one(".atl") for r in rows)  # every listed article names itself


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
    met = [b.get_text() for b in page.select("details.met li.ok b")]
    assert desk.NEAR_GATE in met  # … met, among the conditions met (desk review, 2026-10-17) …
    assert timing.select_one(".gates") is None  # … and the timing block never states it again:
    # it gives the near-term detail and the source's own (longer-term) horizon, told apart
    text = timing.get_text(" ")
    assert "publication date" in text and "The source's own horizon:" in text
    assert "longer" in timing.select_one("b").get_text().lower()
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


# --- readability: nothing said twice, no engine detail in the default view ---------------------

def test_a_figure_label_never_repeats_the_scope_its_metric_already_names(tmp_path: Path) -> None:
    """POSITIVE + NEGATIVE pin, on the rendered reading page: a metric that already names its scope
    reads once ("HBM contract price change", never "HBM — HBM contract price change"); a scope the
    metric does not name is kept before it ("Korea — DRAM contract price change"). Decided from the
    claim's structured scope and metric; the Full record keeps the label as sealed."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=NOW)
    lines = ("HBM contract prices rose 12% in 3Q26.",
             "Korean DRAM contract prices rose 9% in 3Q26.")
    art = Hypo("figure-labels", "Test Publisher", PUB, [("paragraph", t) for t in lines])
    x = extraction(
        [claim("c1", "b001", lines[0].rstrip("."), "HBM contract prices up 12%",
               metric="HBM contract price change", value=12, value_text="12%", unit="%",
               period="3Q26", scope="HBM"),
         claim("c2", "b002", lines[1].rstrip("."), "Korean DRAM contract prices up 9%",
               metric="DRAM contract price change", value=9, value_text="9%", unit="%",
               period="3Q26", scope="Korea")],
        [hyp("h1", "Memory contract prices rise", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1", "c2"])])
    ingest(pipe, art.doc(), x, as_of=NOW, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    page = _soup(out / "theses" / f"{t.thesis_id}.html")
    labels = {x.get_text() for x in page.select(".nums .lbl")}
    assert labels == {"HBM contract price change", "Korea — DRAM contract price change"}
    evidence = page.select_one("[data-panel=ev]")
    assert evidence is not None and "HBM — HBM" not in evidence.get_text(" ")
    card = _soup(out / "cards" / f"{t.thesis_id}.html").get_text(" ")
    assert "HBM — HBM contract price change" in card  # the sealed record is unchanged


def test_a_source_id_is_an_audit_detail_on_sources_and_uploads(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """The publisher's NAME is the default view; its registry id (`citi_must_c`) belongs to the
    audit view — on Uploads it is still in each row's command, ready to copy."""
    _pipe, out, _ = w12
    sids = {x.get_text() for x in _soup(out / "sources.html").select(".aud code")}
    assert len(sids) >= 5  # the audit view keeps every source's id (the check can find them)
    for name in ("sources.html", "uploads.html"):
        text = _default_text(out / name)
        assert [s for s in sids if re.search(rf"\b{re.escape(s)}\b", text)] == [], name
    cmds = " ".join(x.get_text() for x in _soup(out / "uploads.html").select("code.cmd"))
    assert any(s in cmds for s in sids)


def test_a_flagged_lines_scope_note_is_the_audit_views_on_review_as_on_the_reading_page(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """A risk line is stored with a trailing "(scope: …)" note (engine `_risk_sentences`). The
    reading page keeps that note in the audit view; a FINDING on the line — the Review screen's
    and the reading page's "Open review findings", both drawn by `finding_item` — does the same,
    so the quoted line closes on its own words. NEGATIVE pin: a line without a note is unchanged."""
    pipe, _out, _ = w12
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    d = desk.Desk(pipe.store, run, cards={}, generated="")
    f = d.open[0]
    noted = dataclasses.replace(f, line=f.line + " (scope: US grid; author's framing)")
    item = BeautifulSoup(d.finding_item(noted), "html.parser")
    line = item.select_one(".line")
    assert line is not None
    note = line.select_one(".aud.scope")
    assert note is not None and note.get_text() == " (scope: US grid; author's framing)"
    note.decompose()
    assert line.get_text() == f"“{f.line}”"  # the default view: the line, closed on its own words
    plain = BeautifulSoup(d.finding_item(f), "html.parser")
    assert plain.select_one(".aud.scope") is None
    assert plain.select_one(".line").get_text() == f"“{f.line}”"  # type: ignore[union-attr]


# --- Sources and Uploads: plain words, the request's own links ----------------------------------

OPEN_MODELS = "https://newsletter.semianalysis.com/p/are-open-models-catching-up"
MONEY = "https://www.citigroup.com/global/insights/money-the-evolution-to-digital"
LATAM = "https://www.citigroup.com/global/insights/latam-poised-for-take-off"
MS_PDF = (Path(__file__).parent / "fixtures" / "theme_intelligence" / "synthetic_documents"
          / "ms_report_synthetic.pdf")
GS_PAGE = "https://www.goldmansachs.com/insights/goldman-sachs-research/"
GS_MARKETS = "https://www.goldmansachs.com/insights/markets"  # second place to look, 2026-10-14
MS_PAGE = "https://www.morganstanley.com/what-we-do/research"


def _desk_with_health(tmp_path: Path) -> tuple[Pipeline, Path]:
    """A run whose channels carry checks shaped as the real pilot's stored ones (2026-10-12):
    Citi DEGRADED on completeness (a teaser) asking for one article, which a supplied document
    now HOLDS; SemiAnalysis DEGRADED on completeness (a paywalled preview) asking for one — a
    request stored BEFORE the operator made it preview-only (2026-10-13); Goldman Sachs BLOCKED,
    expected, with no article it could list; TrendForce HEALTHY. Built from the real
    `SourceHealthCheck` type."""
    from vinci.theme_intelligence.documents import Declared
    from vinci.theme_intelligence.ingest import ingest_file
    from vinci.theme_intelligence.schemas import (
        HealthStatus,
        HealthTest,
        ManualAction,
        SourceHealthCheck,
    )

    pipe, _v = _measured_thesis(tmp_path)
    at = datetime(2026, 10, 12, 6, 0, tzinfo=UTC)
    ok = [HealthTest(name=n, result="PASS", detail="(test) passed") for n in
          ("access", "discovery", "extraction", "dates_authors", "freshness", "parser_integrity")]
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-test-sa", source_id="semianalysis", publisher="SemiAnalysis", checked_at=at,
        trigger="manual", status=HealthStatus.DEGRADED, reason="(test) partial", next_action="up",
        tests=(*ok, HealthTest(name="completeness", result="WARN", detail=(
            "partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is "
            "readable"))),
        manual_action=ManualAction(kind="UPLOAD_REQUIRED", issue="(test)", action="(test)",
                                   affected=(f"{OPEN_MODELS} — Are Open Models Catching Up?",))))
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-test-citi", source_id="citi_must_c", publisher="Citi", checked_at=at,
        trigger="manual", status=HealthStatus.DEGRADED, reason="(test) partial", next_action="up",
        tests=(*ok, HealthTest(name="completeness", result="WARN", detail=(
            "partial: 1 of 3 sampled article(s) partial (short body (96 words) — treated as a "
            "teaser / excerpt)"))),
        manual_action=ManualAction(kind="UPLOAD_REQUIRED", issue="(test)", action="(test)",
                                   affected=(f"{MONEY} — Money: The Evolution to Digital",
                                             f"{LATAM} — LatAm Poised for Take-Off"))))
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-test-gs", source_id="gs_research", publisher="Goldman Sachs", checked_at=at,
        trigger="manual", status=HealthStatus.BLOCKED, reason="(test) 403", next_action="up",
        expect_blocked=True, tests=(HealthTest(name="access", result="FAIL", detail=(
            f"{GS_PAGE}: access denied (HTTP 403)")),),
        manual_action=ManualAction(kind="UPLOAD_REQUIRED", issue="(test)", action="(test)",
                                   affected=("unknown — the channel cannot be read",))))
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-test-tf", source_id="trendforce", publisher="TrendForce", checked_at=at,
        trigger="manual", status=HealthStatus.HEALTHY, reason="(test) ok", next_action="none",
        tests=tuple(ok)))
    pipe.start_run("ingest", as_of=NOW)
    saved = (Path(__file__).parent / "fixtures" / "theme_intelligence" / "synthetic_documents"
             / "semianalysis_preview_saved_synthetic.pdf")
    res = ingest_file(pipe, saved, Declared(source_id="citi_must_c", url=MONEY), as_of=NOW)
    assert res.status == "HELD", res.note  # no licence statement: held, nothing analysed
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe, _render(pipe, run.run_id, tmp_path / "out")


def _outside_folds(page: BeautifulSoup) -> str:
    for x in page.select("details, .aud, script, style"):
        x.decompose()
    return page.get_text(" ")


def test_sources_say_each_channels_state_in_plain_words_and_fold_the_checks_own(
        tmp_path: Path) -> None:
    """POSITIVE: a degraded channel's line comes from its structured test results ("previews or
    summaries of a fuller report"), the check's own sentence sits in a fold; an expected block
    says so and links the publisher's research page. NEGATIVE: a healthy channel has no fold, and
    one stored check draws no history strip ("1 of 1" said nothing)."""
    _pipe, out = _desk_with_health(tmp_path)
    page = _soup(out / "sources.html")
    rows = {tr.select_one("td b").get_text(): tr for tr in page.select("table.srct tr")[1:]
            if tr.select_one("td b")}
    sa, gs, tf = rows["SemiAnalysis"], rows["Goldman Sachs"], rows["TrendForce"]
    assert "previews or summaries of a fuller report" in sa.get_text(" ")
    fold = sa.select_one("details")
    assert fold is not None and "paywalled previews" in fold.get_text(" ")
    assert "paywalled previews" not in _outside_folds(BeautifulSoup(str(sa), "html.parser"))
    assert "known restriction" in gs.get_text(" ")
    assert [a["href"] for a in gs.select("td a")] == [GS_PAGE, GS_MARKETS]  # both, in order
    assert [a["href"] for a in rows["Morgan Stanley"].select("td a")] == [MS_PAGE]  # one page
    assert "full text, dates and bylines read" in tf.get_text(" ")
    assert tf.select_one("details") is None
    assert not page.select(".hs")  # one check each: no strip


def test_uploads_link_each_requested_article_say_what_is_held_and_where_to_look(
        tmp_path: Path) -> None:
    """The source's request lists its article as a TITLE linked to its address (never the raw
    "url — title" line), says a supplied copy is held for a licence decision, and a channel that
    could list no article points to its research page instead of "unknown — the channel cannot
    be read"."""
    _pipe, out = _desk_with_health(tmp_path)
    page = _soup(out / "uploads.html")
    item = next(li for li in page.select("li.ui") if "New research from Citi" in
                li.get_text(" "))
    (a,) = [x for x in item.select("a") if x.get("href") == MONEY]
    assert a.get_text() == "Money: The Evolution to Digital"
    assert "held until you confirm its licence" in item.get_text(" ")
    assert f"{MONEY} —" not in page.get_text(" ")
    gs = next(li for li in page.select("li.ui") if "New research from Goldman Sachs" in
              li.get_text(" "))
    assert "Where to look" in gs.get_text(" ")
    hrefs = [x.get("href") for x in gs.select("a")]
    assert GS_PAGE in hrefs and GS_MARKETS in hrefs
    assert "the channel cannot be read" not in page.get_text(" ")


def test_split_affected_reads_the_one_format_the_health_check_writes() -> None:
    """The ONE reader of `ManualAction.affected` lines — shapes as stored by the real check."""
    from vinci.theme_intelligence.health import split_affected

    assert split_affected(f"{OPEN_MODELS} — Are Open Models Catching Up?") == (
        OPEN_MODELS, "Are Open Models Catching Up?")
    assert split_affected("https://x.test/a — title not known") == ("https://x.test/a",
                                                                    "title not known")
    for line in ("unknown — the channel cannot be read", "… and 3 more (showing 10 of 13)"):
        assert split_affected(line) == (None, line)  # NEGATIVE: no address, the line as written


def test_an_articles_follow_up_is_one_action_and_its_open_items_fold(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """A preview's follow-up LINKS to Uploads; the figure count lives inside the open-items fold,
    never as a third line in a narrow column."""
    _pipe, out, _ = w12
    page = _soup(out / "articles.html")
    partial = page.select('#at tr[data-state="PARTIAL"]')
    assert partial
    for tr in partial:
        cell = tr.select("td")[-1]
        assert [a.get_text() for a in cell.select("a[href='uploads.html']")] == [
            "Supply the full report"]
    assert "figures captured" in page.get_text(" ")  # kept, one fold away …
    assert "figures captured" not in _outside_folds(page)  # … never a line of its own



# --- SemiAnalysis preview-only (operator decision 2026-10-13: no subscription) --------------------

def test_a_preview_only_channels_paid_posts_are_never_asked_for(tmp_path: Path) -> None:
    """`paywalled_posts = "preview_only"` (SemiAnalysis): its paid-post previews are analysed and
    labelled previews, never requested — not on Uploads (neither the article nor the channel's
    request stored BEFORE the decision), not on the weekly report's intake, and Articles says so.
    NEGATIVE pins: a "request" channel's preview is still asked for, and so is a preview-only
    channel's page that LINKS a fuller report (that is `linked_reports`, not this decision)."""
    from vinci.theme_intelligence.desk import _Registry, upload_items
    from vinci.theme_intelligence.report import build_dashboard
    from vinci.theme_intelligence.schemas import IssueSeverity

    pipe, out = _desk_with_health(tmp_path)  # carries SemiAnalysis's pre-decision request
    made: dict[str, str] = {}
    for slug, sid, pub in (("sa-paid-post", "semianalysis", "SemiAnalysis"),
                           ("sa-linking-page", "semianalysis", "SemiAnalysis"),
                           ("jpm-teaser", "jpm_tmt", "J.P. Morgan Private Bank")):
        text = (f"The {slug} page: memory contract prices rose 9% in 3Q26 as AI servers absorbed "
                f"most new supply, and the tightness is expected to persist into next year.")
        art = Hypo(slug, pub, PUB, [("paragraph", text)])
        ext = extraction([claim("c1", "b001", "memory contract prices rose 9% in 3Q26",
                                "Memory contract prices +9% in 3Q26", metric="contract price "
                                "change", value=9, value_text="9%", unit="%", period="3Q26")],
                         [hyp("h1", "Memory contract prices rise", node="ai_infrastructure.memory",
                              mechanism="pricing_cycle", supporting=["c1"])])
        doc = dataclasses.replace(art.doc(), retrieval_state=RetrievalState.PARTIAL)
        pipe.start_run("article", as_of=NOW)
        res = pipe.process_document(doc, fetched(doc, state=RetrievalState.PARTIAL),
                                    url=doc.canonical_url, source_id=sid, as_of=NOW,
                                    fixture=ext, publisher_override=pub)
        pipe.finish_run(RunStatus.SUCCEEDED)
        made[slug] = res.article_id or ""
    pipe._issue("article", made["sa-linking-page"], IssueSeverity.WARN,  # noqa: SLF001
                "LINKED_REPORT_UPLOAD", "the page links a fuller report (test)")
    asked = {u.url.rsplit("/", 1)[-1]: u for u in upload_items(_Registry(pipe.store), {}, [])
             if u.kind == "full_report"}
    assert sorted(asked) == ["jpm-teaser", "sa-linking-page"]
    last = max(pipe.store.runs(), key=lambda r: r.started_at)
    out = _render(pipe, last.run_id, tmp_path / "out2")
    page = _soup(out / "uploads.html")
    assert "New research from SemiAnalysis" not in page.get_text(" ")  # the pre-decision request
    assert "New research from Citi" in page.get_text(" ")  # a request channel still asks
    awaiting = " ".join(build_dashboard(pipe.store, last.run_id, cards={},
                                        generated="t").intake["awaiting_documents"]["items"])
    assert made["jpm-teaser"] in awaiting and made["sa-linking-page"] in awaiting
    assert made["sa-paid-post"] not in awaiting
    rows = {tr.select_one("td.art a").get("href", "").rsplit("/", 1)[-1]: tr
            for tr in _soup(out / "articles.html").select("#at tr[data-state='PARTIAL']")
            if tr.select_one("td.art a")}
    assert "Preview only — by decision" in rows["sa-paid-post"].get_text(" ")
    assert not rows["sa-paid-post"].select("a[href='uploads.html']")
    assert rows["jpm-teaser"].select("a[href='uploads.html']")



def test_a_sources_request_leaves_uploads_once_every_article_it_lists_is_supplied(
        tmp_path: Path) -> None:
    """Asked 2026-10-14: "why is New research from Citi still pending if the article PDF is
    already supplied?" A channel's request (from its health check) lists the articles it found;
    once EVERY one is supplied, held or read, the request has nothing left to ask and leaves
    Uploads — the held copy stays under Held documents. NEGATIVE pin: while one listed article is
    still missing, the request stays (the test above, LatAm not supplied)."""
    from vinci.theme_intelligence.documents import Declared
    from vinci.theme_intelligence.ingest import ingest_file

    pipe, _out = _desk_with_health(tmp_path)  # Money held; LatAm not supplied
    pipe.start_run("ingest", as_of=NOW)
    res = ingest_file(pipe, MS_PDF, Declared(source_id="citi_must_c", url=LATAM), as_of=NOW)
    assert res.status == "HELD", res.note
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    page = _soup(_render(pipe, run.run_id, tmp_path / "out2") / "uploads.html")
    text = page.get_text(" ")
    assert "New research from Citi" not in text
    held = [li for li in page.select("li.ui") if "Release command" in li.get_text(" ")]
    assert len(held) == 2  # both supplied copies still wait for their licence decision
    assert "New research from Goldman Sachs" in text  # a manual-first channel's standing request


def test_this_week_and_uploads_give_the_content_the_full_width(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """Asked 2026-10-14: the "Needs your attention" panel repeated the tiles beside it and squeezed
    the week's content. NEGATIVE: neither screen has a side panel. POSITIVE: what the tiles do not
    already say (failed or blocked articles, theses close to archiving, sources needing attention)
    is one line of links under them; Uploads' weekly routine is one closed fold holding its four
    steps, above the list."""
    _pipe, out, _ = w12
    week = _soup(out / "index.html")
    assert not week.select("main.wrap aside") and "Needs your attention" not in week.get_text()
    line = week.select_one(".hero .headsup")
    assert line is not None
    assert {a["href"] for a in line.select("a")} >= {"articles.html", "sources.html"}
    tiles = {a["href"] for a in week.select(".hero .strip a")}
    assert {"review.html", "uploads.html"} <= tiles  # findings and uploads stay as tiles
    up = _soup(out / "uploads.html")
    assert not up.select("main.wrap aside")
    howto = up.select_one("details.howto")
    assert howto is not None and not howto.has_attr("open")
    assert len(howto.select("ol.steps4 > li")) == 4
    first = up.select_one("main.wrap details.howto ~ details.ubk")
    assert first is not None  # the list follows the fold, at full width


# --- the reading page's tabs, and the folds of the other screens (audit 2026-10-14) -------------

def test_the_reading_pages_tabs_read_as_lists_against_first_and_name_each_thesis_once(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """Asked 2026-10-14: the Evidence / History / Sources / Full record block "looks completely
    unreadable". Evidence is no five-column table: a summary line, then what speaks AGAINST the
    thesis first, then the supporting items by source — one line each, the source's words one
    click away (provenance, on demand), no placeholder dash for a statement with no number.
    Related theses name a thesis once, with every reason; the Full record list numbers its
    sections once ("1. Bottom line", never "1. 01 Bottom Line")."""
    _pipe, out, _ = w12
    pages = sorted((out / "theses").glob("TH-*.html"))
    for p in pages:
        s = _soup(p)
        ev = s.select_one("[data-panel=ev]")
        assert ev is not None and not ev.select("table"), p.name
        for li in ev.select("ul.evl > li:not(.morewrap)"):
            summary = li.select_one("details > summary")
            quote = li.select_one("details > blockquote")
            assert summary is not None and quote is not None, p.name
            assert "“" not in summary.get_text() and quote.get_text().startswith("“")
            v = summary.select_one(".v")
            assert v is None or v.get_text().strip() not in ("", "—")
        assert ev.select_one("p.evsum") is not None
        names = [a["href"] for a in s.select("ul.rel > li > a")]
        assert len(names) == len(set(names)), (p.name, names)  # a thesis once
        for li in s.select("ol.nine li"):
            assert not li.get_text().strip()[:1].isdigit(), li.get_text()
    assert pages


def test_evidence_against_the_thesis_is_listed_first(tmp_path: Path) -> None:
    """A thesis with a supporting figure and a counter-claim (hypothetical): the Evidence tab says
    how many are against, and lists them FIRST, before the supporting ones."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=NOW)
    lines = ("HBM contract prices rose 12% in 3Q26.",
             "Some buyers expect HBM prices to fall 5% in 2027 as capacity arrives.")
    art = Hypo("against-first", "Test Publisher", PUB, [("paragraph", t) for t in lines])
    x = extraction(
        [claim("c1", "b001", lines[0].rstrip("."), "HBM contract prices up 12%",
               metric="HBM contract price change", value=12, value_text="12%", unit="%",
               period="3Q26"),
         claim("c2", "b002", lines[1].rstrip("."), "HBM prices expected to fall 5% in 2027",
               kind="forecast", epistemic="forecast", metric="expected HBM price decline",
               value=5, value_text="5%", unit="%", period="2027")],
        [hyp("h1", "HBM contract prices rise", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"], counter=["c2"])])
    ingest(pipe, art.doc(), x, as_of=NOW, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    ev = _soup(out / "theses" / f"{t.thesis_id}.html").select_one("[data-panel=ev]")
    assert ev is not None
    heads = [h.get_text(" ") for h in ev.select("h3.evh")]
    assert heads and heads[0].startswith("Against"), heads
    assert any(h.startswith("Supporting") for h in heads[1:]), heads
    assert "1 against" in ev.select_one("p.evsum").get_text(" ")  # type: ignore[union-attr]


def test_an_articles_open_items_sit_under_it_at_full_width_and_review_groups_them(
        w12: tuple[Pipeline, Path, dict[str, int]]) -> None:
    """An article's open items are one fold in a full-width row under the article — never inside
    the narrow Follow-up column — and the row travels with its article (capped or filtered).
    Review's completeness list names each article once, its items under it."""
    _pipe, out, _ = w12
    rows_seen = 0
    for p in [out / "articles.html", *sorted(out.glob("articles-*.html"))]:
        s = _soup(p)
        for sub in s.select("#at tr[data-sub]"):
            rows_seen += 1
            prev = sub.find_previous_sibling("tr")
            assert prev is not None and prev.has_attr("data-state") and prev.has_attr("data-hassub")
            assert sub.select_one("td[colspan='5'] details.fold") is not None
            assert ("xtra" in (sub.get("class") or [])) == ("xtra" in (prev.get("class") or []))
        for tr in s.select("#at tr[data-state]"):
            assert not tr.select("td")[-1].select("details")  # the follow-up is one action
    assert rows_seen, "the fixture must hold an article with open items"
    review = _soup(out / "review.html")
    comp = review.select("ul.compl > li > a")
    assert comp and len({a.get_text() + a["href"] for a in comp}) == len(comp)
    for li in review.select("ul.compl > li:not(.morewrap)"):
        assert li.select_one("ul > li") is not None  # the article's items, under it
    assert "not accounted for — not accounted for" not in review.get_text(" ")


# --- who is exposed, the reading page's order, the Evidence tab's repeats (2026-10-14) ----------

def _exposure_thesis(tmp_path: Path) -> tuple[Pipeline, Path, str]:
    """Hypothetical article, AUTHENTIC frozen SEC subset (the J.P. Morgan fixture's): Micron named
    as a beneficiary, Microsoft as harmed, and FactSet — a data source — carried in the thesis's
    own list of affected names, the shape the extraction gave the Alzheimer thesis on 2026-10-14
    (Morgan Stanley, the publisher, as its one listed exposure). Two figures the article states
    twice ("36%" for 2026) and once for another year (2025), and one the thesis statement
    cites."""
    from tests.theme_intelligence_support import JPM_AS_OF, mention

    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    lines = ("Micron's HBM revenue rose 40% in the quarter as AI servers ramped.",
             "Microsoft could see cloud margins squeezed as memory costs climb.",
             "FactSet data show 36% of buyers plan to add memory this year.",
             "Survey: 36% of buyers will add memory in 2026, per FactSet.",
             "Memory makers plan 10% more capacity by 2027.",
             "In 2025, 36% of buyers added memory, per FactSet.",
             "Buyers spend $413 a year on memory upgrades.")
    art = Hypo("who-is-exposed", "Test Publisher", date(2026, 2, 2),
               [("paragraph", t) for t in lines])
    x = extraction(
        [claim("c1", "b001", lines[0].rstrip("."), "Micron HBM revenue up 40%",
               metric="HBM revenue growth", value=40, value_text="40%", unit="%",
               period="the quarter"),
         claim("c2", "b003", "36% of buyers plan to add memory this year",
               "36% of buyers plan to add memory", metric="buyers planning to add memory",
               value=36, value_text="36%", unit="%", source="FactSet"),
         claim("c3", "b004", "36% of buyers will add memory in 2026",
               "36% of buyers will add memory in 2026", metric="buyers adding memory",
               value=36, value_text="36%", unit="%", period="2026", source="FactSet"),
         claim("c4", "b005", lines[4].rstrip("."), "capacity up 10% by 2027",
               kind="forecast", epistemic="forecast", metric="memory capacity growth",
               value=10, value_text="10%", unit="%", period="by 2027"),
         claim("c5", "b006", "In 2025, 36% of buyers added memory",
               "36% of buyers added memory in 2025", metric="buyers adding memory",
               value=36, value_text="36%", unit="%", period="2025", source="FactSet"),
         claim("c6", "b007", lines[6].rstrip("."), "buyers spend $413 a year",
               metric="annual memory-upgrade spend", value=413, value_text="$413",
               unit="$/year", period="per year")],
        [hyp("h1", "HBM demand lifts memory makers", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c4", "c1", "c2", "c3", "c5", "c6"],
             affected=[("Micron", "potential_beneficiary"),
                       ("Microsoft", "potentially_harmed"), ("FactSet", "data_source")])],
        mentions=[mention("Micron", "b001", "Micron's HBM revenue rose 40%", ticker="MU"),
                  mention("Microsoft", "b002", "Microsoft could see cloud margins squeezed",
                          role="potentially_harmed", direction="negative", ticker="MSFT"),
                  mention("FactSet", "b003", "FactSet data show", entity_type="data_provider",
                          role="data_source", direction="neutral", ticker="FDS")])
    # a page saved as PDF keeps its browser-tab title: "… | <publisher>" (Morgan Stanley's, 2026)
    doc = dataclasses.replace(art.doc(), title="Memory Note: HBM Demand | Test Publisher")
    ingest(pipe, doc, x, as_of=JPM_AS_OF, publisher=art.publisher)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    return pipe, _render(pipe, run.run_id, tmp_path / "out"), t.thesis_id


def test_who_is_exposed_says_who_could_benefit_or_be_hurt_and_never_lists_a_data_source(
        tmp_path: Path) -> None:
    """POSITIVE: Micron under "Could benefit" with its verified ticker, Microsoft under "Could be
    hurt". NEGATIVE: FactSet — named, but as the data source — sits in no bucket, on the reading
    page, the card's exposure table and the weekly report; it is counted as also named."""
    pipe, out, tid = _exposure_thesis(tmp_path)
    expo = _soup(out / "theses" / f"{tid}.html").select_one(".expo")
    assert expo is not None
    heads = [h.get_text() for h in expo.select("h3")]
    groups = {h.get_text(): h.find_next_sibling("ul").get_text(" ") for h in expo.select("h3")}
    assert "Could benefit" in heads and "Could be hurt" in heads
    assert "Micron" in groups["Could benefit"] and "MU" in groups["Could benefit"]
    assert "Microsoft" in groups["Could be hurt"] and "MSFT" in groups["Could be hurt"]
    assert not any("FactSet" in g for g in groups.values())
    assert "Also named, not exposures: FactSet (data source)" in expo.get_text(" ")
    card = _soup(out / "cards" / f"{tid}.html").select_one('[data-field="s05_affected"]')
    assert card is not None
    subs = card.select(".sub")
    stock = next(s for s in subs if s.get_text().startswith("Stock exposures"))
    table = stock.find_next_sibling()
    assert "Micron" in table.get_text(" ") and "FactSet" not in table.get_text(" ")
    also = next(s for s in subs if s.get_text().startswith("Also named"))
    assert "FactSet" in also.find_next_sibling().get_text(" ")
    from vinci.theme_intelligence.report import build_dashboard

    d = build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={}, generated="t")
    (row,) = [r for rs in d.categories.values() for r in rs]
    assert any(n.startswith("Micron") for n in row.named_companies)
    assert not any(n.startswith("FactSet") for n in row.named_companies)


def test_the_reading_page_leads_with_the_thesis_figure_and_merges_a_figure_stated_twice(
        tmp_path: Path) -> None:
    """The strongest figures lead with what the thesis statement itself cites (its fact line
    cites c4, the capacity forecast — listed first in the evidence though not first by type).
    The Evidence tab lists "36%" ONCE when the article states it twice for one measure (periods
    that do not disagree); NEGATIVE: a figure is never merged with a different one."""
    _pipe, out, tid = _exposure_thesis(tmp_path)
    page = _soup(out / "theses" / f"{tid}.html")
    first = page.select_one(".nums .num b")
    assert first is not None and first.get_text() == "10%"
    ev = page.select_one("[data-panel=ev]")
    assert ev is not None
    lines = [li.select_one("summary").get_text(" ") for li in ev.select("ul.evl > li")
             if li.select_one("summary")]
    # 2026's figure, stated twice, is one line; 2025's — the same measure, another year — is not
    assert sum(1 for x in lines if x.startswith("36%")) == 2
    twice = [li for li in ev.select("ul.evl > li") if "stated 2 times" in li.get_text(" ")]
    assert len(twice) == 1 and len(twice[0].select("blockquote")) == 2
    assert "2026" in twice[0].get_text(" ") and "2025" not in twice[0].get_text(" ")
    assert sum(1 for x in lines if x.startswith("40%")) == 1  # a different figure stays apart


def test_a_unit_and_a_title_never_repeat_what_is_already_said(tmp_path: Path) -> None:
    """"$413 $/year … · per year" read the unit three times: it reads "$413 per year". A saved
    page's title keeps its site suffix ("… | Morgan Stanley", so Review read "… | Morgan Stanley
    Morgan Stanley"): every screen drops a suffix that repeats the publisher. NEGATIVE pins: a
    unit the value does not carry is kept; a trailing part naming anything else stays."""
    from vinci.theme_intelligence.cards import unit_shown
    from vinci.theme_intelligence.parse import clean_title

    assert unit_shown("$413", "$/year") == "per year"
    assert unit_shown("413", "$/year") == "$/year" and unit_shown("~43%", "%") == ""
    assert clean_title("Caffeine Market Outlook | Morgan Stanley", "Morgan Stanley") == \
        "Caffeine Market Outlook"
    assert clean_title("How AI Masks America&#039;s Rising Risk Premium", "Nomura") == \
        "How AI Masks America's Rising Risk Premium"
    assert clean_title("Must C - Sizing the ETF Opportunity", "Citi") == \
        "Must C - Sizing the ETF Opportunity"
    assert clean_title("Outlook | Morgan Stanley", "Citi") == "Outlook | Morgan Stanley"
    _pipe, out, tid = _exposure_thesis(tmp_path)
    page = _soup(out / "theses" / f"{tid}.html")
    ev = page.select_one("[data-panel=ev]")
    assert ev is not None
    line = next(li.select_one("summary").get_text(" ") for li in ev.select("ul.evl > li")
                if li.select_one("summary") and "$413" in li.get_text(" "))
    assert line.startswith("$413 per year") and "$/year" not in line and "· per year" not in line
    for screen in (out / "articles.html", out / "theses" / f"{tid}.html",
                   out / "cards" / f"{tid}.html"):
        text = _soup(screen).get_text(" ")
        assert "Memory Note: HBM Demand" in text, screen.name
        assert "| Test Publisher" not in text, screen.name


def test_a_thesis_filed_at_an_areas_root_is_folded_with_the_area_not_listed_as_related(
        tmp_path: Path) -> None:
    """Canada's power and minerals thesis (filed at the AI-infrastructure ROOT) was listed as
    related to HBM memory pricing: a root node is "parent" of every thesis in its area, so that
    link says only "same area". It joins the broader-area fold. NEGATIVE pin: a thesis sharing
    a source is still listed directly."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=NOW)
    grid = "Grid operators sign 3 GW of new data-center contracts in 2026."
    for slug, node, title, line in (
            ("root", "ai_infrastructure", "Canada's power supplies the compute cycle",
             "Canada's grid adds 4 GW for data centers by 2027."),
            ("child", "ai_infrastructure.memory", "HBM prices rise on tight supply",
             "HBM contract prices rose 12% in 3Q26.")):
        art = Hypo(slug, "Test Publisher", PUB, [("paragraph", line), ("paragraph", grid)])
        x = extraction([claim("c1", "b001", line.rstrip("."), title, metric=f"{slug} figure",
                              value=12, value_text="12%", unit="%", period="3Q26"),
                        claim("c2", "b002", grid.rstrip("."), "3 GW of grid contracts",
                              metric="grid contracts", value=3, value_text="3 GW", unit="GW",
                              period="2026")],
                       [hyp("h1", title, node=node, mechanism="pricing_cycle",
                            supporting=["c1"])]
                       # the root's article also carries a grid thesis: the SAME source
                       + ([hyp("h2", "Grid contracts accelerate", node="ai_infrastructure"
                               ".power_grid", mechanism="demand_volume_shift",
                               supporting=["c2"])] if slug == "root" else []))
        ingest(pipe, art.doc(), x, as_of=NOW, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    by = {t.key_node: t.thesis_id for t in pipe.store.theses()}
    rels = [r.relation.value for r in pipe.store.relations(by["ai_infrastructure"])]
    # an area root and its area's theses are never linked pair by pair (U43, U47): the area is
    # read from the keys …
    assert rels == []
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    page = _soup(out / "theses" / f"{by['ai_infrastructure']}.html")
    direct = [a["href"] for ul in page.select("ul.rel") if ul.find_parent("details") is None
              for a in ul.select("a")]
    folded = [a["href"] for d in page.select("details.more-rows") for a in d.select("ul.rel a")]
    child = f"{by['ai_infrastructure.memory']}.html"
    assert child not in direct and child in folded  # … the page folds it with the area
    same_source = f"{by['ai_infrastructure.power_grid']}.html"
    assert same_source in direct and same_source not in folded  # a shared source stays listed


def test_the_weekly_reports_sources_say_each_channels_state_in_words(tmp_path: Path) -> None:
    """2026-10-14: the weekly report's Sources printed each check's raw reason ("robots.txt
    unreachable (RemoteProtocolError) — FAIL CLOSED"), state codes ("[automatic; access
    DEGRADED] … PARTIAL automated coverage") and placeholder dashes, while the desk's Sources said
    the same in words. POSITIVE: each channel needing attention reads from its structured test
    results, as on the desk. NEGATIVE pin: the raw reason is kept — in Operations & audit."""
    from vinci.theme_intelligence.report import build_dashboard, render_dashboard_html

    pipe, _out = _desk_with_health(tmp_path)
    d = build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={}, generated="t")
    page = BeautifulSoup(render_dashboard_html(d), "html.parser")
    src, ops = page.select_one("#sources"), page.select_one("#ops")
    assert src is not None and ops is not None
    text = src.get_text(" ")
    assert "previews or summaries of a fuller report" in text  # SemiAnalysis, from its tests
    assert "a known restriction — supply its research by upload" in text  # Goldman Sachs
    assert "partly working" in text and "by upload" in text
    for raw in ("(test) 403", "(test) partial", "access DEGRADED", "PARTIAL automated",
                "MANUAL-FIRST", "DEGRADED", "BLOCKED", "[automated access"):
        assert raw not in text, raw
    assert "(test) 403" in ops.get_text(" ")



# --- one sector, named twice -------------------------------------------------------------------

DIAG = ("Diagnostics and care delivery, as well as the retirement and insurance industries, could "
        "benefit from—or need to adapt to—rising demand.")
MARKETS = ("Banks hold steady while US regional banks could gain; US regional banks and lenders "
           "could fall, and insurance brokers wait.")
TWICE = [  # (name, direction, verbatim quote) — the pilot's shape (TH-8DDD7B2868, 2026-10-14)
    ("Diagnostics and care delivery, retirement and insurance industries", "unclear",
     DIAG.split(" rising")[0]),
    ("Diagnostics and care delivery, as well as the retirement and insurance industries",
     "positive", DIAG.split(" from")[0]),
    # sectors, not asset classes: "Treasurys" and "US equity and credit" are refused as sectors
    # since 2026-10-16 (`cards.not_a_sector`), so these pins use real ones of the same shape
    ("Banks", "unclear", "Banks hold steady"),
    ("US regional banks", "positive", "US regional banks could gain"),
    ("US regional banks and lenders", "negative", "US regional banks and lenders could fall"),
    ("insurance", "unclear", "insurance brokers"),
]


def test_a_sector_named_twice_in_near_words_is_shown_once_on_every_surface(
        tmp_path: Path) -> None:
    """The extraction named one sector twice from one sentence — "Diagnostics and care delivery,
    retirement and insurance industries" (no direction) and "…, as well as the retirement and
    insurance industries" (could benefit) — and the reading page listed both, under two headings.
    Shown once, the directional one kept: on the reading page, its gate, the card (HTML,
    Markdown) and the weekly dashboard. NEGATIVE pins: two different one-word sectors stay apart
    ("Banks", "insurance" — the equal-size case once merged them all); one sector inside a
    list of several ("insurance") stays apart; near names said to benefit AND be hurt both stay
    — a contradiction is never hidden. The stored version keeps every entry as extracted."""
    pipe = make_pipeline(tmp_path / "reg")
    pipe.start_run("ingest", as_of=NOW)
    art = Hypo("sector-twice", "Test Publisher", PUB, [("paragraph", DIAG), ("paragraph", MARKETS)])
    h = hyp("h1", "Rising demand lifts care delivery and insurers",
            node="healthcare.services_payers", mechanism="demand_volume_shift", supporting=["c1"])
    h["sector_exposures"] = [{"name": n, "direction": d, "block_id": "b001", "quote": q,
                              "claim_ids": []} for n, d, q in TWICE]
    x = extraction([claim("c1", "b001", DIAG.rstrip("."), "care delivery could benefit",
                          kind="event")], [h])
    ingest(pipe, art.doc(), x, as_of=NOW, publisher=art.publisher)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    assert [s.name for s in v.content.s05_affected.sector_exposures] == [n for n, _, _ in TWICE]
    out = _render(pipe, run.run_id, tmp_path / "out")
    kept = [TWICE[i] for i in (1, 2, 3, 4, 5)]

    page = _soup(out / "theses" / f"{t.thesis_id}.html")
    heads = {"Could benefit": "up", "Could be hurt": "down",
             "Named as exposed — direction not stated": "flat"}
    got = {heads[h3.get_text(strip=True)]: [b.get_text(strip=True)
                                            for b in h3.find_next_sibling("ul").select("li > b")]
           for h3 in page.select(".expo h3")}
    assert got == {"up": [TWICE[1][0], TWICE[3][0]], "down": [TWICE[4][0]],
                   "flat": [TWICE[2][0], TWICE[5][0]]}
    gate = page.find(string=re.compile(r"^sectors: "))
    lean = {"positive": " (could benefit)", "negative": " (could be hurt)"}  # each with its
    assert gate == "sectors: " + ", ".join(f"{n}{lean.get(d, '')}" for n, d, _ in kept)  # side

    cards = out / "cards"
    md = (cards / f"{t.thesis_id}.md").read_text()
    block = md.split("**Sectors / themes the source names as exposed:**")[1].split("**Business")[0]
    assert [ln for ln in block.splitlines() if ln.startswith("- ")] == [
        f"- **SOURCE OPINION:** {n} — {d} — “{q}”" for n, d, q in kept]
    html = (cards / f"{t.thesis_id}.html").read_text()
    assert html.count("<b>Diagnostics and care delivery") == 1 and "5 sector(s)" in html

    dash = json.loads((out / "dashboard.json").read_text())
    rows = [r for rs in dash["categories"].values() for r in rs if r["thesis_id"] == t.thesis_id]
    assert rows and all(r["sector_exposures"] == [f"{n} ({d})" for n, d, _ in kept]
                        for r in rows)
