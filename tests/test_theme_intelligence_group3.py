"""Group 3 of the review leads — THE PUBLISHED DESK (U36, U52, U54, U47, U13, U32; U31b folded in
at U36's sites). Verified on main d304ea16 (`docs/records/2026-10-14-theme-intelligence-unverified-
leads-verified.md`); the real runs are in the build record.

End to end through the REAL engine on HYPOTHETICAL articles (invented text on the reserved `.test`
domain), rendered and read back; the unit helper's pins are the pilot's own value/unit pairs. No
network, no model call.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import cards, desk, health
from vinci.theme_intelligence.display import clip, first_of
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.priority import ThesisState, compute_priority
from vinci.theme_intelligence.report import scoped_ids, theses_as_of_run, write_run_outputs
from vinci.theme_intelligence.schemas import (
    Claim,
    ClaimKind,
    Confidence,
    Epistemic,
    EvidenceDirection,
    Horizon,
    Provenance,
    RelationType,
    RetrievalState,
    RunStatus,
    StanceInSource,
    ThemeRelation,
    ThesisStatus,
    TransmissionStep,
)

AS_OF = date(2026, 10, 14)


def _soup(p: Path) -> BeautifulSoup:
    return BeautifulSoup(p.read_text(), "html.parser")


def _text(p: Path) -> str:
    s = _soup(p)
    for x in s.select("script, style"):
        x.decompose()
    return re.sub(r"\s+", " ", s.get_text(" "))


def _render(pipe: Pipeline, run_id: str, out: Path) -> Path:
    return Path(write_run_outputs(pipe.store, run_id, out)["dir"])


# --- U52: ONE unit helper ----------------------------------------------------------------------

#: (value as written, stored unit, what prints after it) — the pilot's own pairs (2026-10-15):
#: the card printed "$10 billion bn", "8.5 month months", "more than four times x", "roughly
#: half %"; the desk's helper dropped every unit beside a word ("more than 60" countries)
CARRIED = [("$10 billion", "$bn"), ("$0.5 trillion", "$tn"), ("US$5.5 trillion", "$tn"),
           ("$26B", "$bn"), ("$2T", "$tn"),
           ("8.5 month", "months"), ("more than four times", "x"), ("roughly half", "%"),
           ("four-fifths", "%"), ("around 1.3ppt", "percentage points"), ("~43%", "%")]
KEPT = [("more than 60", "countries", "countries"), ("five", "years", "years"),
        ("21 million", "coins", "coins"), ("eight", "quarters", "quarters"),
        ("seven", "central banks", "central banks"), ("15–20%", "% QoQ", "QoQ"),
        ("413", "$/year", "$/year"), ("$413", "$/year", "per year"), ("5", "t", "t")]


@pytest.mark.parametrize(("value", "unit"), CARRIED)
def test_a_unit_the_value_already_writes_is_never_printed_twice(value: str, unit: str) -> None:
    assert cards.unit_shown(value, unit) == ""


@pytest.mark.parametrize(("value", "unit", "shown"), KEPT)
def test_a_unit_the_value_does_not_write_is_kept_even_beside_words(value: str, unit: str,
                                                                   shown: str) -> None:
    """NEGATIVE pin: a value written in words keeps a unit it does not carry (the desk's helper
    printed "more than 60" for 60 countries), and a share word never swallows a time unit
    ("eight" quarters)."""
    assert cards.unit_shown(value, unit) == shown


def test_the_desk_and_the_card_read_units_through_one_helper() -> None:
    assert desk.unit_shown is cards.unit_shown and not hasattr(desk, "unit_of")


def _figures_thesis(tmp_path: Path) -> tuple[Pipeline, str, str]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    lines = ("Cash-pay drug sales could reach $26 billion at peak.",
             "The service now operates in more than 60 countries.")
    art = Hypo("units", "Test Publisher", date(2026, 10, 1), [("paragraph", x) for x in lines])
    x = extraction([claim("c1", "b001", lines[0].rstrip("."), "Cash-pay sales could reach $26bn",
                          metric="cash-pay market size", value=26, value_text="$26 billion",
                          unit="$bn", period="at peak"),
                    claim("c2", "b002", lines[1].rstrip("."), "The service operates in 60+ "
                          "countries", metric="countries served", value=60,
                          value_text="more than 60", unit="countries", period="2026")],
                   [hyp("h1", "Cash-pay access widens drug demand", node="healthcare",
                        mechanism="demand_volume_shift", supporting=["c1", "c2"])])
    r = ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    assert r.article_id is not None
    return pipe, t.thesis_id, pipe.store.runs()[-1].run_id


def test_a_published_figure_never_repeats_its_unit_and_keeps_one_it_lacks(
        tmp_path: Path) -> None:
    """End to end: the reading page and the card print "$26 billion" (never "$26 billion bn") and
    "more than 60 countries" (never a bare "more than 60")."""
    pipe, tid, rid = _figures_thesis(tmp_path)
    out = _render(pipe, rid, tmp_path / "out")
    for page in (out / "theses" / f"{tid}.html", out / "cards" / f"{tid}.html"):
        text = _text(page)
        assert "$26 billion" in text and not re.search(r"\$26 billion \$?bn", text), page.name
        assert "more than 60 countries" in text, page.name


# --- U36: a truncated output prints its own truncation -------------------------------------------

def test_a_cut_line_and_a_cut_list_say_so_and_a_whole_one_says_nothing() -> None:
    assert clip("a" * 10, 10) == "a" * 10  # NEGATIVE: whole
    cut = clip("word " * 30, 20, "the Full record")
    assert cut.startswith("word word") and "[+130 chars — full text in the Full record]" in cut
    assert first_of(["a", "b", "c"], 3) == "a; b; c"  # NEGATIVE: whole
    assert first_of(list("abcde"), 3, ", ") == "a, b, c (showing 3 of 5)"


def _c(cid: str, quote: str, *, kind: ClaimKind = ClaimKind.FORECAST) -> Claim:
    return Claim(claim_id=cid, article_id="A-1", article_version_id="AV-1", block_id="b001",
                 char_start=0, char_end=len(quote), quote=quote, statement=quote, kind=kind,
                 epistemic=Epistemic.FORECAST, period="next quarter", value=5.0, value_text="5",
                 confidence=Confidence.HIGH, span_verified=True, number_verified=True,
                 measure_key=f"k|{cid}", fingerprint=f"f|{cid}", extraction_id="X-1")


def _now_rule(n_supporting: int) -> str:
    step = TransmissionStep(step="costs", text="labour costs rise",
                            provenance=Provenance.SOURCE_OPINION, claim_ids=())
    st = ThesisState(
        reliability="high", counter=(), dislocation=(), listed_exposures=(),
        supporting=tuple(_c(f"c{i}", f"Orders are forecast to rise {i}% next quarter")
                         for i in range(n_supporting)),
        catalyst=(_c("e1", "The plant opens next quarter", kind=ClaimKind.EVENT),),
        instrument_exposures=(), transmission=(step,), horizon=Horizon.LONGER_TERM,
        stance=StanceInSource.ASSERTED, verification_hold=False, hold_reasons=(),
        retrieval=RetrievalState.FULL, sector_exposures=("Construction",), as_of=date(2026, 10, 11))
    pr = compute_priority(st, previous=None, evidence_direction=EvidenceDirection.NEW)
    assert pr.rules_fired[0].startswith("NOW all conditions met")
    return pr.rules_fired[0]


def test_the_research_now_rule_counts_the_windows_it_lists() -> None:
    """TH-BF20FBC464 (pilot): its RESEARCH NOW rule listed 4 of its 10 near-term windows and never
    said so. NEGATIVE pin: four windows, all listed, say nothing."""
    assert "(showing 4 of 5)" in _now_rule(4)  # four supporting + the catalyst
    assert "showing" not in _now_rule(3)


def test_an_affected_list_states_its_true_total_never_the_cut_lists_length() -> None:
    """U31b, the same lines: the stored list is cut at AFFECTED_SHOWN with a closing "… and N more"
    line, and a reader that counted it said "showing 3 of 11" of 25."""
    many = tuple(f"https://example.test/a{i} — title {i}" for i in range(25))
    ma = health._manual("UPLOAD_REQUIRED", "access refused", many, "upload").model_dump()  # noqa: SLF001
    assert ma["affected_total"] == 25 and len(ma["affected"]) == health.AFFECTED_SHOWN + 1
    assert health.affected_shown(ma, 3).endswith("(showing 3 of 25)")
    old = {"affected": [*many[:10], "… and 15 more (showing 10 of 25)"]}  # stored before the field
    assert health.affected_shown(old, 3).endswith("(showing 3 of more than 10)")
    few = health._manual("MANUAL_REVIEW", "x", many[:2], "y").model_dump()  # noqa: SLF001
    assert "showing" not in health.affected_shown(few, 3)  # NEGATIVE: whole


def test_what_changed_shows_three_and_folds_the_rest_never_drops_them(tmp_path: Path) -> None:
    """A reading page printed 3 of a thesis's 11 "What changed" lines and said nothing of the other
    eight. NEGATIVE pin: two lines, no fold."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    lines = [f"Contract prices rose {10 + i}% in segment {i} during 3Q26." for i in range(5)]
    art = Hypo("five", "Test Publisher", date(2026, 10, 1), [("paragraph", x) for x in lines])
    x = extraction([claim(f"c{i}", "b00" + str(i + 1), x.rstrip("."), f"Segment {i} prices up",
                          metric=f"segment {i} price", value=10 + i, value_text=f"{10 + i}%",
                          unit="%", period="3Q26") for i, x in enumerate(lines)],
                   [hyp("h1", "Contract prices rise across segments", node="healthcare",
                        mechanism="pricing_cycle", supporting=[f"c{i}" for i in range(5)]),
                    hyp("h2", "Segment one leads", node="healthcare.pharma_biotech",
                        mechanism="pricing_cycle", supporting=["c0", "c1"])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    by = {t.key_node: t.thesis_id for t in pipe.store.theses()}
    page = _soup(out / "theses" / f"{by['healthcare']}.html")
    items = page.select_one("ul.changed")
    assert items is not None
    shown = [li for li in items.find_all("li", recursive=False) if "morewrap" not in
             (li.get("class") or [])]
    fold = items.select_one("details summary")
    assert len(shown) == 3 and fold is not None and fold.get_text(strip=True) == "2 more changes"
    assert all(f"Segment {i} prices up" in items.get_text(" ") for i in range(5))  # all kept
    two = _soup(out / "theses" / f"{by['healthcare.pharma_biotech']}.html").select_one(
        "ul.changed")
    assert two is not None and two.select_one("details") is None


# --- U54 + U13: one week, the retired marked ------------------------------------------------------

REANALYSE_AS_OF = AS_OF
ALZ = "Alzheimer's drug sales could grow 26% in 2026."
CASH = "Direct-to-consumer cash-pay drug sales rose 26% in 2026."


def _x(line: str, title: str, node: str, metric: str) -> dict[str, Any]:
    return extraction([claim("c1", "b001", line.rstrip("."), title, metric=metric, value=26,
                             value_text="26%", unit="%", period="2026")],
                      [hyp("h1", title, node=node, mechanism="demand_volume_shift",
                           supporting=["c1"])])


def _retired_week(tmp_path: Path) -> tuple[Pipeline, dict[str, str], str, str, str]:
    """The pilot's week in small: an ingest run merges two articles into one `healthcare` thesis;
    a re-analysis the same week analyses BOTH again and retires it."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    ids: dict[str, str] = {}
    for slug, line, title, metric in (
            ("alz", ALZ, "Alzheimer's drug innovation opens a large market", "Alzheimer sales"),
            ("cash", CASH, "Healthcare demand rises", "cash-pay sales")):
        art = Hypo(slug, "Test Publisher", date(2026, 9, 14 if slug == "alz" else 29),
                   [("paragraph", line)])
        r = ingest(pipe, art.doc(), _x(line, title, "healthcare", metric), as_of=AS_OF,
                   publisher=art.publisher)
        assert r.article_id is not None
        ids[slug] = r.article_id
    first = pipe.finish_run(RunStatus.SUCCEEDED).run_id
    (old,) = [t.thesis_id for t in pipe.store.theses()]
    run, _res = pipe.run_reanalyse(
        article_ids=[ids["cash"], ids["alz"]], retire=[old], reason="healthcare sub-categories",
        as_of=REANALYSE_AS_OF, fixtures={
            ids["alz"]: _x(ALZ, "Alzheimer's drug innovation opens a large market",
                           "healthcare.pharma_biotech", "Alzheimer sales"),
            ids["cash"]: _x(CASH, "Direct-to-consumer cash-pay access widens drug sales",
                            "healthcare.pharma_biotech", "cash-pay sales")})
    assert run.status is RunStatus.SUCCEEDED
    return pipe, ids, old, first, run.run_id


def _tile(page: Path, label: str) -> tuple[int, str]:
    for t in _soup(page).select(".tiles > a, .tiles > div, .strip > a, .strip > div"):
        if t.select_one("span") and t.select_one("span").get_text(strip=True) == label:
            return int(t.select_one("b").get_text(strip=True)), t.get_text(" ", strip=True)
    raise AssertionError(f"no {label!r} tile on {page.name}")


def test_the_full_weekly_report_counts_the_week_this_week_counts(tmp_path: Path) -> None:
    """The published pair read "6 theses · 3 articles · 14 Oct" (the last run's report) beside
    This week's "18 · 13 · 12–14 Oct". ONE week now feeds both: the same span, each article ONCE
    (both articles were analysed in two runs — the old sum of the runs' counters read 4), and the
    thesis counts reconcile (the retired named on both)."""
    pipe, _ids, _old, _first, rid = _retired_week(tmp_path)
    runs = {r.run_id: r for r in pipe.store.runs()}
    assert sum(r.counts.get("articles_processed", 0) for r in runs.values()) == 4  # the trap
    out = _render(pipe, rid, tmp_path / "out")
    dash, week = _text(out / "dashboard.html"), out / "index.html"
    n_art, _ = _tile(week, "Articles read")
    assert n_art == 2 and re.search(r"\b2 Articles read · 0 in part\b", dash)
    m = re.search(r"What to research this week (\S+) – (\S+)", dash)
    assert m and m.groups() == (AS_OF.isoformat(), AS_OF.isoformat())
    n_th, tile = _tile(week, "New or changed theses")
    live = re.search(r"Theses this week \((\d+) · (\d+) retired on re-analysis", dash)
    assert live and int(live[1]) + int(live[2]) == n_th and f"· {live[2]} retired" in tile


def test_the_full_weekly_report_spans_every_run_of_the_week(tmp_path: Path) -> None:
    """Two manual runs, two days, different articles: the report of the LAST run covered only it
    ("14 Oct", one article) while This week covered both. NEGATIVE pin: This week itself is
    unchanged — 12–14 Oct, two articles."""
    pipe = make_pipeline(tmp_path)
    for day, slug, node, line in ((12, "first", "healthcare.pharma_biotech",
                                   "Biopharma volumes rose 9% in 2026."),
                                  (14, "second", "healthcare.medtech",
                                   "Device orders rose 4% in 2026.")):
        pipe.start_run("ingest", as_of=date(2026, 10, day))
        art = Hypo(slug, "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
        ingest(pipe, art.doc(), _x(line, f"{slug} thesis", node, f"{slug} metric"),
               as_of=date(2026, 10, day), publisher=art.publisher)
        pipe.finish_run(RunStatus.SUCCEEDED)
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    dash = _text(out / "dashboard.html")
    assert "What to research this week 2026-10-12 – 2026-10-14" in dash
    assert re.search(r"\b2 Articles read\b", dash)
    assert _tile(out / "index.html", "Articles read")[0] == 2
    assert "12–14 Oct 2026" in _text(out / "index.html")
    # the figure line counts the week's articles too, never the last run's counter beside them
    md = (out / "dashboard.md").read_text()
    last = pipe.store.runs()[-1].counts.get("figures_in_articles", 0)
    m = re.search(r"Reported figures not yet captured: (\d+) of (\d+)", md)
    assert m and int(m[2]) == 2 and last == 1


def _article_cells(page: Path, tid: str) -> list[str]:
    """What an article list says beside each link to `tid` (a thesis card's own link — `a.trow`,
    which carries the thesis's chips — is not an article list)."""
    return [(a.find_next_sibling("span") or a).get_text(" ", strip=True)
            for a in _soup(page).select("a") if (a.get("href") or "").endswith(f"{tid}.html")
            and "trow" not in (a.get("class") or [])]


def test_a_retired_thesis_is_marked_where_an_article_lists_it_and_only_from_its_retirement(
        tmp_path: Path) -> None:
    """The 4 retired pilot theses showed only "· new evidence" in the article lists. NEGATIVE pin:
    the run BEFORE the retirement shows the thesis as it was then — live, unmarked (the view read
    today's `retired` flag)."""
    pipe, _ids, old, first, rid = _retired_week(tmp_path)
    out = _render(pipe, rid, tmp_path / "out")
    for page in ("articles.html", "index.html"):
        cells = _article_cells(out / page, old)
        assert cells and all("retired — replaced on re-analysis" in c for c in cells), page
    then = theses_as_of_run(pipe.store, pipe.store.run(first))  # type: ignore[arg-type]
    assert then[old][0].retired == "" and then[old][0].status is ThesisStatus.ACTIVE
    early = _render(pipe, first, tmp_path / "early")
    cells = _article_cells(early / "articles.html", old)
    assert cells and not any("retired" in c for c in cells)


# --- U47 + U32c: one reading of the registry's links ----------------------------------------------

def test_an_area_root_link_is_filed_as_the_same_area_and_counted_nowhere_as_related(
        tmp_path: Path) -> None:
    """The engine filed a root-to-child link as PARENT_CHILD adjacent support (card TH-A097D4722F:
    "ADJACENT SUPPORT (parent / child)"), and Themes counted it as related while the page folded
    it (TH-DEE87FCF51: "2 related theses", both area-root links). Now the engine files it as the
    same broader area; a link STORED the old way is read the same; and Themes counts exactly what
    the page lists. NEGATIVE pin: a direct link (a shared source) is still counted and listed."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    for slug, node, title, line in (
            ("root", "healthcare", "Healthcare demand broadens",
             "Healthcare spending rose 6% in 2026."),
            ("child", "healthcare.pharma_biotech", "Biopharma volumes climb",
             "Biopharma volumes rose 9% in 2026."),
            ("other", "healthcare.medtech", "Device orders recover",
             "Device orders rose 4% in 2026.")):
        art = Hypo(slug, "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
        ingest(pipe, art.doc(), _x(line, title, node, f"{slug} metric"), as_of=AS_OF,
               publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    by = {t.key_node: t.thesis_id for t in pipe.store.theses()}
    root = by["healthcare"]
    assert pipe.store.relations(root) == []  # the area is read from the keys (U43)
    # a link stored before the fix: PARENT_CHILD adjacent support between the root and a child
    pipe.store.add_relation(ThemeRelation(
        relation_id="TR-legacy0000000", from_thesis=root, to_thesis=by["healthcare.medtech"],
        relation=RelationType.PARENT_CHILD, reason="legacy area-root link",
        run_id=pipe.store.runs()[-1].run_id, created_at=datetime.now(tz=UTC),
        evidence_role="ADJACENT_SUPPORT"))
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    page = _soup(out / "theses" / f"{root}.html")
    direct = {a["href"] for ul in page.select("ul.rel") if ul.find_parent("details") is None
              for a in ul.select("a")}
    folded = {a["href"] for d in page.select("details.more-rows") for a in d.select("ul.rel a")}
    assert f"{by['healthcare.medtech']}.html" in folded - direct
    themes = _soup(out / "themes.html")
    for tr in themes.select("tr[data-area]"):
        tid = re.search(r"TH-[0-9A-F]+", tr.get_text())[0]  # type: ignore[index]
        m = re.search(r"(\d+) related thes[ei]s", tr.get_text())
        listed = {a["href"] for ul in _soup(out / "theses" / f"{tid}.html").select("ul.rel")
                  if ul.find_parent("details") is None for a in ul.select("a")}
        assert (int(m[1]) if m else 0) == len(listed), tid


def test_a_shared_source_is_still_a_related_thesis_on_themes_and_the_page(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    lines = ("Biopharma volumes rose 9% in 2026.", "Device orders rose 4% in 2026.")
    art = Hypo("shared", "Test Publisher", date(2026, 10, 1), [("paragraph", x) for x in lines])
    x = extraction([claim("c1", "b001", lines[0].rstrip("."), "Biopharma volumes up",
                          metric="volumes", value=9, value_text="9%", unit="%", period="2026"),
                    claim("c2", "b002", lines[1].rstrip("."), "Device orders up",
                          metric="orders", value=4, value_text="4%", unit="%", period="2026")],
                   [hyp("h1", "Biopharma volumes climb", node="healthcare.pharma_biotech",
                        mechanism="demand_volume_shift", supporting=["c1"]),
                    hyp("h2", "Device orders recover", node="healthcare.medtech",
                        mechanism="demand_volume_shift", supporting=["c2"])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    text = _text(out / "themes.html")
    assert text.count("1 related thesis") == 2


# --- U32: the desk's lists, print, printed report and publish ------------------------------------

def test_the_printed_report_carries_every_card_with_ids_of_its_own(tmp_path: Path) -> None:
    """report_print.html repeated 42 ids (each card's "L-s01-0" once per card). A card's own links
    follow its ids; a link to an id outside the card is kept. NEGATIVE pin: unscoped, two cards
    collide."""
    pipe, _ids, _old, _first, rid = _retired_week(tmp_path)
    out = _render(pipe, rid, tmp_path / "out")
    html = (out / "report_print.html").read_text()
    ids = re.findall(r'\sid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    for href in set(re.findall(r'href="#([^"]+)"', html)):
        assert href in ids or href in ("top", "audit"), href
    card = '<article><p id="L-s01-0">x</p><a href="#L-s01-0">x</a><a href="#top">t</a></article>'
    assert scoped_ids(card, "TH-1") == ('<article><p id="TH-1-L-s01-0">x</p><a href="#TH-1-L-s01-'
                                        '0">x</a><a href="#top">t</a></article>')
    assert re.findall(r'id="([^"]+)"', card * 2).count("L-s01-0") == 2
    # only the id attribute moves: a data-id / aria-*-id naming the same value is left alone
    other = '<article><p id="L-1" data-id="L-1" aria-describedby="L-1">x</p></article>'
    assert scoped_ids(other, "TH-1") == ('<article><p id="TH-1-L-1" data-id="L-1" '
                                         'aria-describedby="L-1">x</p></article>')


def test_the_desk_script_re_caps_what_a_filter_or_sort_leaves_and_opens_every_fold_to_print(
        ) -> None:
    """The Themes status filter said "showing 111 of 257" with 84 on screen, a sort left the top
    rows hidden, search never read the area name and "Latest evidence" was named but not applied.
    The behaviour is exercised in a browser in the build record; these pin the script's parts."""
    js = desk.JS
    assert "function recap(" in js and js.count("recap('#tt')") == 2 and "recap('#at')" in js
    assert "r.dataset.area).toLowerCase().indexOf(q)" in js
    assert "' match'" in js and "'showing '+n" not in js
    assert "beforeprint" in js and "d.open=true" in js
    assert "+r.dataset.ord" in js and "srt();flt()" in js


def test_a_capped_themes_table_carries_its_cap_and_the_default_sort_is_the_pages_order(
        tmp_path: Path) -> None:
    pipe, _ids, _old, _first, rid = _retired_week(tmp_path)
    out = _render(pipe, rid, tmp_path / "out")
    s = _soup(out / "themes.html")
    so = s.select_one("select#so")
    assert so is not None and so.select("option")[0].get("value") == ""
    ords = [int(tr["data-ord"]) for tr in s.select("tr[data-area]")]
    assert sorted(ords) == list(range(len(ords)))
    d = desk.Desk.__new__(desk.Desk)
    d._uid = 0  # noqa: SLF001 — the table helper alone
    big = d.table("themes", "<tr><th>h</th></tr>", [f'<tr data-area="a"><td>{i}</td></tr>'
                                                     for i in range(30)], "theses")
    assert 'data-cap="25"' in big and 'data-what="theses"' in big and big.count('class="xtra"') == 5
    small = d.table("themes", "<tr><th>h</th></tr>", ['<tr data-area="a"><td>1</td></tr>'],
                    "theses")
    assert "data-cap" not in small  # NEGATIVE: an uncapped table carries no cap


def test_a_republish_never_deletes_a_file_it_did_not_write(tmp_path: Path) -> None:
    from vinci.theme_intelligence import publish

    pipe, _tid, rid = _figures_thesis(tmp_path)
    out = tmp_path / "pub"
    publish.publish(pipe.store, rid, out, allow_test_data=True)
    (out / ".DS_Store").write_bytes(b"Finder metadata")  # OS metadata never blocks a publish
    publish.publish(pipe.store, rid, out, allow_test_data=True)
    (out / "README.md").write_text("an operator's note")
    with pytest.raises(publish.PublishError, match="1 file.*README.md"):
        publish.publish(pipe.store, rid, out, allow_test_data=True)
    assert (out / "README.md").read_text() == "an operator's note"


def test_a_fold_of_one_says_one_more_in_the_singular(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    lines = [f"Contract prices rose {10 + i}% in segment {i} during 3Q26." for i in range(4)]
    art = Hypo("four", "Test Publisher", date(2026, 10, 1), [("paragraph", x) for x in lines])
    x = extraction([claim(f"c{i}", "b00" + str(i + 1), x.rstrip("."), f"Segment {i} prices up",
                          metric=f"segment {i} price", value=10 + i, value_text=f"{10 + i}%",
                          unit="%", period="3Q26") for i, x in enumerate(lines)],
                   [hyp("h1", "Contract prices rise across segments", node="healthcare",
                        mechanism="pricing_cycle", supporting=[f"c{i}" for i in range(4)])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    out = _render(pipe, pipe.store.runs()[-1].run_id, tmp_path / "out")
    (t,) = pipe.store.theses()
    fold = _soup(out / "theses" / f"{t.thesis_id}.html").select_one("ul.changed details summary")
    assert fold is not None and fold.get_text(strip=True) == "1 more change"


# --- the desk script in a real browser ------------------------------------------------------------

BRAVE = Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")


def _in_browser(page: Path, script: str) -> BeautifulSoup:
    """`page` as a browser leaves it after its own script and then `script` ran (headless Brave,
    --dump-dom): the desk's behaviour on the RENDERED page, not on a substring of its source."""
    import subprocess

    probe = page.with_name(page.stem + ".probe.html")
    probe.write_text(page.read_text().replace("</body>", f"<script>{script}</script></body>"))
    res = subprocess.run([str(BRAVE), "--headless=new", "--disable-gpu",
                          "--virtual-time-budget=3000", "--dump-dom", f"file://{probe}"],
                         capture_output=True, text=True, timeout=120, check=True)
    return BeautifulSoup(res.stdout, "html.parser")


@pytest.fixture(scope="module")
def stress12(tmp_path_factory: pytest.TempPathFactory) -> Path:
    from tests.theme_intelligence_stress import build_stress_registry

    root = tmp_path_factory.mktemp("g3stress")
    pipe, _stats = build_stress_registry(root / "reg", weeks=12)
    run = max(pipe.store.runs(), key=lambda r: r.started_at)
    return _render(pipe, run.run_id, root / "out")


@pytest.mark.skipif(not BRAVE.exists(), reason="needs a headless Chromium (Brave) on this machine")
def test_in_a_browser_a_filter_re_caps_the_articles_table_that_carries_the_id_itself(
        stress12: Path) -> None:
    """The SYNTHETIC 12-week stress registry's Articles table (`<table id="at">`, over its cap):
    after a publisher filter, the cap is re-applied to the rows the filter left — the first 25
    matching rows shown, the rest marked, the label naming the matching total. NEGATIVE pin: a
    filter leaving fewer rows than the cap marks none and hides the label. (`recap('#at')` once
    selected `#at table[data-cap]` — nothing, since `#at` IS the table.)"""
    page = stress12 / "articles.html"
    s = _soup(page)
    table = s.select_one("table#at[data-cap]")
    assert table is not None
    cap = int(table["data-cap"])
    pubs = {tr["data-pub"] for tr in table.select("tr[data-state]")}
    by_pub = {p: sum(1 for tr in table.select("tr[data-state]") if tr["data-pub"] == p)
              for p in pubs}
    for pub, n in sorted(by_pub.items(), key=lambda kv: -kv[1])[:1] + sorted(
            by_pub.items(), key=lambda kv: kv[1])[:1]:
        dom = _in_browser(page, "document.getElementById('fp').value="
                                f"{pub!r};document.querySelectorAll('input.morebox').forEach("
                                "function(b){b.checked=false});fa();recap('#at');")
        rows = [tr for tr in dom.select("table#at tr[data-state]")
                if "display: none" not in (tr.get("style") or "")]
        assert len(rows) == n, pub
        marked = [tr for tr in rows if "xtra" in (tr.get("class") or [])]
        assert len(marked) == max(0, n - cap), pub
        assert all("xtra" not in (tr.get("class") or []) for tr in rows[:cap]), pub
        total = len(table.select("tr[data-state]"))
        assert dom.select_one("#cnt2").get_text() == f"{n} of {total} match"


@pytest.mark.skipif(not BRAVE.exists(), reason="needs a headless Chromium (Brave) on this machine")
def test_in_a_browser_themes_search_reads_the_area_and_the_count_says_what_matches(
        stress12: Path) -> None:
    """Search found nothing for an area's own name (0 of 23 for "AI infrastructure" on the pilot).
    NEGATIVE pin: a word in no title and no area matches nothing."""
    page = stress12 / "themes.html"
    total = len(_soup(page).select("tr[data-area]"))
    dom = _in_browser(page, "document.getElementById('fs').value='';"
                            "document.getElementById('q').value='ai infrastructure';flt();")
    shown = [tr for tr in dom.select("tr[data-area]")
             if "display: none" not in (tr.get("style") or "")]
    assert shown and all("ai infrastructure" in tr["data-area"].lower() for tr in shown)
    assert dom.select_one("#cnt").get_text() == f"{len(shown)} of {total} match"
    none = _in_browser(page, "document.getElementById('fs').value='';"
                             "document.getElementById('q').value='zzqx';flt();")
    assert none.select_one("#cnt").get_text() == f"0 of {total} match"
