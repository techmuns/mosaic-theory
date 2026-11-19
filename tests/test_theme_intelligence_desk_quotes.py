"""The research desk prints a source's own words only as SHORT quotes (operator ruling 2026-11-19,
relayed by coordinator A; CLAUDE.md, Security & secrets: the desk publishes "titles, figures and
SHORT verbatim source quotes", never an article's text).

The incident: the 2026-11-19 republish (#1139) carried a verbatim quote of 911 characters (913
with its curly quotation marks, as coordinator A counted it). It is a Goldman Sachs bond-supply
forecast table read as ONE block and stored as the quote of 5 claims. It was printed whole in the
card's claim table (`div.q`), on the thesis page's Evidence tab (`blockquote`) and in the printed
report. The live desk's longest had been 350.

Pinned here:
- a quote over `DESK_QUOTE_MAX_CHARS` is cut at a word with "…" and the note beside it;
- one of exactly the cap prints whole;
- the claim's figure and its paragraph locator still print;
- a risk sentence the source states (the risk scan) is held to the same cap on its card line
  and in every alert that quotes it (review of #1140, round 1);
- every site that prints a source's words is covered;
- the COMMITTED desk holds no source text over the cap.

HYPOTHETICAL articles and synthetic text, never the licensed report; no network, no model call.
"""

from __future__ import annotations

import html
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import publish
from vinci.theme_intelligence.cards import quote_html
from vinci.theme_intelligence.display import DESK_QUOTE_MAX_CHARS, DESK_QUOTE_NOTE, desk_quote
from vinci.theme_intelligence.schemas import RunStatus

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "frontend" / "theme-intelligence"
AS_OF = date(2026, 11, 19)


def _exactly(text: str, n: int) -> str:
    """`text` repeated to exactly `n` characters, ending on a full stop (a synthetic fixture)."""
    while len(text) < n:
        text = f"{text} {text}"
    out = text[:n - 1]
    return (out[:-1] + "s" if out.endswith(" ") else out) + "."


#: the incident's shape, a forecast table read as one block (synthetic figures, 913 characters)
LONG = _exactly("Synthetic supply forecasts, calendar year 2027, net issuance by country, "
                "billions: " + "; ".join(f"Country {i:02d} gross {100 + 7 * i} net {20 + 3 * i}"
                                         for i in range(31)), 913)
#: NEGATIVE: a quote of exactly the cap
EXACT = _exactly("Synthetic transformer lead times rose 9% in 3Q26 as utilities ordered ahead of "
                 "the grid build, and synthetic utilities kept ordering ahead of the build", 400)
#: a risk the source states as ONE 913-character sentence (no full stop inside it), the way
#: `coverage.sentences` returns a table block: the risk scan places it on a card and alerts it
LONG_RISK = _exactly("Rising synthetic input costs might put downward pressure on grid margins "
                     "this year across " + "; ".join(f"component {i:02d} up {3 + i}% in 2026"
                                                     for i in range(40)), 913)
GRID = "Synthetic grid orders rose 12% in 2026 to 40GW"
#: a 913-character span naming two sectors: one the card counts, one it refuses as the whole market
SECTORS = _exactly("Synthetic grid equipment and US equities both carry the build across "
                   + "; ".join(f"region {i:02d} up {2 + i}% in 2026" for i in range(40)), 913)
#: a business group the source names ("makers"): its excerpt is a short window by construction
MAKERS = "Synthetic transformer makers raised output 7% in 2026 for the grid build."

_SCAN_SCOPE = "(scope: ⟨the source's own words"
_ALERT = re.compile(r"a risk the source states that no model pass listed — “(.*)”[^“”]*?"
                    r"\((?:now in 07|on NO card)")


class _Quotes(HTMLParser):
    """Every element the desk prints a SOURCE's words in:
    - `div.q`: the card's claim tables;
    - `span.q`: the sectors the source names and its business-group excerpts;
    - `blockquote`: a thesis page's Evidence tab.

    Each is read with tags stripped, entities decoded and the curly quote marks left out. The
    card lines (`div.s`) and list items (`li`) are kept whole for `_source_texts`, which reads the
    source's sentence out of a risk-scan line and out of an alert. A WITHHELD card line's own text,
    under its "audit text" summary, is the card's line, not a source's words, so it is not read as
    a quote."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.frames: list[tuple[str, str | None, list[str]]] = []  # (tag, kind, its text)
        self.details: list[bool] = []  # one per open <details>: is it an "audit text" one?
        self.in_summary = False
        self.quotes: list[tuple[str, str]] = []  # (kind, text)
        self.lines: list[str] = []  # div.s and li texts

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = (dict(attrs).get("class") or "").split()
        if tag == "details":
            self.details.append(False)
        self.in_summary = tag == "summary"
        kind = None
        if not any(self.details):
            kind = ("blockquote" if tag == "blockquote" else
                    f"{tag}.q" if tag in ("div", "span") and "q" in cls else None)
        if kind is None and (tag == "li" or (tag == "div" and "s" in cls)):
            kind = "line"
        self.frames.append((tag, kind, []))

    def handle_endtag(self, tag: str) -> None:
        if tag == "summary":
            self.in_summary = False
        while self.frames:
            t, kind, buf = self.frames.pop()
            text = "".join(buf).strip()
            if kind == "line":
                self.lines.append(re.sub(r"\s+", " ", text))
            elif kind:
                self.quotes.append((kind, text.strip("“”").strip()))
            if self.frames:
                self.frames[-1][2].extend(buf)
            if t == tag:
                break
        if tag == "details" and self.details:
            self.details.pop()

    def handle_data(self, data: str) -> None:
        if self.in_summary and data.strip() == "audit text" and self.details:
            self.details[-1] = True
        if self.frames:
            self.frames[-1][2].append(data)


def _parsed(page: str) -> _Quotes:
    q = _Quotes()
    q.feed(page)
    return q


def _quotes(page: str) -> list[str]:
    return [t for _k, t in _parsed(page).quotes]


def _source_texts(page: str) -> list[str]:
    """Every run of a source's own words a page prints: its quote elements, the sentence of a
    risk-scan card line (before its system scope) and the sentence an alert quotes."""
    p = _parsed(page)
    out = [t for _k, t in p.quotes]
    for line in p.lines:
        if _SCAN_SCOPE in line:
            out.append(line.split(" (scope: ⟨")[0].removeprefix("SOURCE OPINION").strip())
        out += [m.group(1) for m in _ALERT.finditer(line)]
    return out


def _published(tmp_path: Path) -> Path:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("desk-quote-cap", "Test Publisher", date(2026, 11, 12),
               [("paragraph", LONG), ("paragraph", EXACT), ("paragraph", f"{GRID}. {LONG_RISK}"),
                ("paragraph", MAKERS), ("paragraph", SECTORS)])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", LONG, "Country 00 net supply", metric="net issuance", value=20,
               value_text="20", unit="bn", period="2027", scope="Country 00"),
         claim("c2", "b002", EXACT, "lead times up", metric="lead time change", value=9,
               value_text="9%", unit="%", period="3Q26"),
         claim("c3", "b003", GRID, "grid orders up", metric="order growth", value=12,
               value_text="12%", unit="%", period="2026"),
         claim("c4", "b004", MAKERS.rstrip("."), "makers' output up", metric="output growth",
               value=7, value_text="7%", unit="%", period="2026")],
        [hyp("h1", "Synthetic grid build lengthens lead times", node="ai_infrastructure.power",
             mechanism="supply_constraint", supporting=["c1", "c2", "c3", "c4"],
             sectors=[("Synthetic grid equipment", "b005", SECTORS),
                      ("US equities", "b005", SECTORS)])]),
        as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    run_id = max(pipe.store.runs(), key=lambda r: r.started_at).run_id
    out = tmp_path / "desk"
    publish.publish(pipe.store, run_id, out, allow_test_data=True)
    return out


def _pages(out: Path) -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8") for p in out.rglob("*.html")}


def _card(pages: dict[Path, str]) -> str:
    return next(t for p, t in pages.items() if p.parent.name == "cards"
                and not p.name.endswith(".print.html"))


def test_the_cap_cuts_at_a_word_and_says_it_cut() -> None:
    assert len(LONG) == len(LONG_RISK) == len(SECTORS) == 913
    assert len(EXACT) == DESK_QUOTE_MAX_CHARS == 400
    assert desk_quote(EXACT) == (EXACT, False)  # NEGATIVE: exactly the cap prints whole
    for text in (LONG, EXACT + "x", EXACT + " more"):  # 401 kills a `<= cap + 1` mutant
        shown, cut = desk_quote(text)
        assert cut and shown.endswith("…") and len(shown) <= DESK_QUOTE_MAX_CHARS
        head = shown[:-1]
        assert text.startswith(head) and text[len(head)].isspace()  # cut at a word, never in one
    # one unbroken token longer than the cap is cut where the cap falls
    assert desk_quote("x" * 500) == ("x" * (DESK_QUOTE_MAX_CHARS - 1) + "…", True)


def test_a_quote_is_decoded_once_never_twice() -> None:
    """A source that printed "&lt;" literally (stored entity-encoded as "&amp;lt;") still prints
    "&lt;" — decoding twice turned it into "<" (review of #1140, round 1)."""
    assert quote_html("a &amp;lt; b") == '<div class="q">“a &amp;lt; b”</div>'
    assert quote_html("it&#039;s") == '<div class="q">“it&#x27;s”</div>'


def test_a_long_source_quote_is_shortened_on_every_published_page(tmp_path: Path) -> None:
    pages = _pages(_published(tmp_path))
    texts = [t for page in pages.values() for t in _source_texts(page)]
    assert texts and max(map(len, texts)) <= DESK_QUOTE_MAX_CHARS  # main: 913, printed whole
    shown, _cut = desk_quote(LONG)
    card = _card(pages)
    thesis = next(t for p, t in pages.items() if p.parent.name == "theses")
    for page in (card, thesis):  # the card's claim table and the thesis page's Evidence tab
        assert shown in _quotes(page) and DESK_QUOTE_NOTE in html.unescape(page)
        assert EXACT in _quotes(page)  # NEGATIVE: the quote of exactly the cap prints whole
    # the figure and where it was read still print beside the shortened quote
    row = card[card.index(shown[:60]):]
    row = row[:row.index("</tr>")]
    assert "<b>20</b>" in row and "paragraph " in row


def test_a_risk_sentence_the_source_states_is_capped_on_its_card_and_in_every_alert(
        tmp_path: Path) -> None:
    """The risk scan puts the source's sentence on the card as SOURCE OPINION and quotes it in
    the background alerts (dashboard, printed report, articles). A table block came out as ONE
    913-character "sentence" and printed whole on all of them (review of #1140, round 1)."""
    pages = _pages(_published(tmp_path))
    shown, cut = desk_quote(LONG_RISK)
    assert cut
    for p, page in pages.items():
        assert LONG_RISK not in html.unescape(page), p.name  # main: whole on every one
        assert max(map(len, _source_texts(page)), default=0) <= DESK_QUOTE_MAX_CHARS, p.name
    card = _parsed(_card(pages))
    lines = [x for x in card.lines if _SCAN_SCOPE in x and "downward pressure" in x]
    assert lines and all(x.startswith("SOURCE OPINION " + shown) and "shortened" in x
                         for x in lines)  # its 07 line, wherever the card repeats it
    alerted = [p.name for p, page in pages.items()
               if any(m.group(1) == shown for x in _parsed(page).lines for m in _ALERT.finditer(x))]
    assert {"dashboard.html", "report_print.html"} <= set(alerted)


def test_every_site_that_prints_a_sources_words_holds_the_cap(tmp_path: Path) -> None:
    """The four wired sites the other pins do not reach (review of #1140, round 1): a cited
    claim outside the key-evidence rows (`_other_row`), a sector the source names, one it names
    that is no sector, and a business-group excerpt."""
    card = _parsed(_card(_pages(_published(tmp_path))))
    sector_shown, risk_shown = desk_quote(SECTORS)[0], desk_quote(LONG_RISK)[0]
    # the risk scan's own claim is cited by its 07 line, never a key-evidence row: `_other_row`
    assert ("div.q", risk_shown) in card.quotes
    # the kept sector and the one refused as the whole market, each a `span.q`
    assert card.quotes.count(("span.q", sector_shown)) == 2
    # NEGATIVE: the business-group excerpt is a short window (`named_groups`), never shortened
    groups = [t for k, t in card.quotes if k == "span.q" and "transformer makers" in t]
    assert groups and all(len(t) < DESK_QUOTE_MAX_CHARS for t in groups)


def test_the_committed_desk_prints_no_source_quote_over_the_cap() -> None:
    pages = sorted((DESK / "site").rglob("*.html"))
    texts = [(len(t), p.name) for p in pages for t in _source_texts(p.read_text(encoding="utf-8"))]
    assert pages and texts  # a check that reads nothing proves nothing
    over = sorted((x for x in texts if x[0] > DESK_QUOTE_MAX_CHARS), reverse=True)
    assert not over, (f"{len(over)} source text(s) over {DESK_QUOTE_MAX_CHARS} chars "
                      f"(showing {min(10, len(over))} of {len(over)}): {over[:10]}")


def test_the_guard_reads_every_quote_element_and_no_audit_line() -> None:
    assert _quotes(f'<td><div class="q">“{"x" * 401}”</div></td>') == ["x" * 401]  # caught
    assert _quotes(f'<div class="q">“{"x" * 400}”</div>') == ["x" * 400]
    assert _quotes(f"<blockquote>“{'y' * 9}”</blockquote>") == ["y" * 9]
    assert _quotes('<span class="q">a <b>bold</b> word</span>') == ["a bold word"]
    # NEGATIVE: a withheld card line's own text is the card's, not a source's
    assert _quotes('<details><summary class="note">audit text</summary><span class="q">'
                   f'{"z" * 900}</span></details>') == []
    # a risk-scan card line and an alert quoting its sentence
    line = (f'<div class="s"><span class="lab op">SOURCE OPINION</span> {"r" * 401} (scope: '
            '<span class="sys">⟨the source&#x27;s own words, page 1 — a risk no model pass '
            'listed (risk scan)⟩</span>)</div>')
    alert = (f'<ul><li>page 1: a risk the source states that no model pass listed — '
             f'“{"a" * 402}” (on NO card — no thesis&#x27;s evidence is in its '
             'paragraph)</li></ul>')
    assert sorted(map(len, _source_texts(line + alert))) == [401, 402]
    # NEGATIVE: a model-written card line is not a source's words
    assert _source_texts(f'<div class="s"><span class="lab inf">INFERENCE</span> {"m" * 600}'
                         '</div>') == []
