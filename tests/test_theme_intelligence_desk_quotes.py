"""The research desk prints a source's own words only as SHORT quotes (operator ruling 2026-11-19,
relayed by coordinator A; CLAUDE.md, Security & secrets: the desk publishes "titles, figures and
SHORT verbatim source quotes", never an article's text).

The incident: the 2026-11-19 republish (#1139) carried a 911-character verbatim quote, a Goldman
Sachs bond-supply forecast table read as ONE block and stored as the quote of 5 claims. It was
printed whole in the card's claim table (`div.q`), on the thesis page's Evidence tab
(`blockquote`) and in the printed report. The live desk's longest had been 350. Pinned here:
- a quote over `DESK_QUOTE_MAX_CHARS` is cut at a word with "…" and the note beside it;
- one of exactly the cap prints whole;
- the claim's figure and its paragraph locator still print;
- the COMMITTED desk holds no quote over the cap.

HYPOTHETICAL articles and synthetic text, never the licensed report; no network, no model call.
"""

from __future__ import annotations

import html
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import publish
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


#: the incident's shape: a forecast table read as one 913-character block (synthetic figures)
LONG = _exactly("Synthetic supply forecasts, calendar year 2027, net issuance by country, "
                "billions: " + "; ".join(f"Country {i:02d} gross {100 + 7 * i} net {20 + 3 * i}"
                                         for i in range(31)), 913)
#: NEGATIVE: a quote of exactly the cap
EXACT = _exactly("Synthetic transformer lead times rose 9% in 3Q26 as utilities ordered ahead of "
                 "the grid build, and synthetic utilities kept ordering ahead of the build", 400)


class _Quotes(HTMLParser):
    """Every element the desk prints a SOURCE's words in:
    - `div.q`: the card's claim tables;
    - `span.q`: the sectors the source names and its business-group excerpts;
    - `blockquote`: a thesis page's Evidence tab.

    Each is read with tags stripped, entities decoded and the curly quote marks left out. A
    WITHHELD card line's own text, under its "audit text" summary, is the card's line, not a
    source's words, so it is not read as a quote."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.frames: list[tuple[str, bool, list[str]]] = []  # (tag, a quote?, its text)
        self.details: list[bool] = []  # one per open <details>: is it an "audit text" one?
        self.in_summary = False
        self.quotes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = (dict(attrs).get("class") or "").split()
        if tag == "details":
            self.details.append(False)
        self.in_summary = tag == "summary"
        quote = (tag == "blockquote" or (tag in ("div", "span") and "q" in cls)) \
            and not any(self.details)
        self.frames.append((tag, quote, []))

    def handle_endtag(self, tag: str) -> None:
        if tag == "summary":
            self.in_summary = False
        while self.frames:
            t, quote, buf = self.frames.pop()
            if quote:
                self.quotes.append("".join(buf).strip().strip("“”").strip())
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


def _quotes(html_text: str) -> list[str]:
    q = _Quotes()
    q.feed(html_text)
    return q.quotes


def _published(tmp_path: Path) -> Path:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("desk-quote-cap", "Test Publisher", date(2026, 11, 12),
               [("paragraph", LONG), ("paragraph", EXACT)])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", LONG, "Country 00 net supply", metric="net issuance", value=20,
               value_text="20", unit="bn", period="2027", scope="Country 00"),
         claim("c2", "b002", EXACT, "lead times up", metric="lead time change", value=9,
               value_text="9%", unit="%", period="3Q26")],
        [hyp("h1", "Synthetic grid build lengthens lead times", node="ai_infrastructure.power",
             mechanism="supply_constraint", supporting=["c1", "c2"])]),
        as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    run_id = max(pipe.store.runs(), key=lambda r: r.started_at).run_id
    out = tmp_path / "desk"
    publish.publish(pipe.store, run_id, out, allow_test_data=True)
    return out


def test_the_cap_cuts_at_a_word_and_says_it_cut() -> None:
    assert len(LONG) == 913 and len(EXACT) == DESK_QUOTE_MAX_CHARS == 400  # the fixtures' shape
    assert desk_quote(EXACT) == (EXACT, False)  # NEGATIVE: exactly the cap prints whole
    for text in (LONG, EXACT + " more"):
        shown, cut = desk_quote(text)
        assert cut and shown.endswith("…") and len(shown) <= DESK_QUOTE_MAX_CHARS
        head = shown[:-1]
        assert text.startswith(head) and text[len(head)].isspace()  # cut at a word, never in one


def test_a_long_source_quote_is_shortened_on_every_published_page(tmp_path: Path) -> None:
    out = _published(tmp_path)
    pages = {p: p.read_text(encoding="utf-8") for p in out.rglob("*.html")}
    quotes = [q for t in pages.values() for q in _quotes(t)]
    assert quotes and max(map(len, quotes)) <= DESK_QUOTE_MAX_CHARS  # main: 913, printed whole
    shown, _cut = desk_quote(LONG)
    card = next(t for p, t in pages.items() if p.parent.name == "cards"
                and not p.name.endswith(".print.html"))
    thesis = next(t for p, t in pages.items() if p.parent.name == "theses")
    for page in (card, thesis):  # the card's claim table and the thesis page's Evidence tab
        assert shown in _quotes(page) and DESK_QUOTE_NOTE in html.unescape(page)
        assert EXACT in _quotes(page)  # NEGATIVE: the quote of exactly the cap prints whole
    # the figure and where it was read still print beside the shortened quote
    row = card[card.index(shown[:60]):]
    row = row[:row.index("</tr>")]
    assert "<b>20</b>" in row and "paragraph " in row


def test_the_committed_desk_prints_no_source_quote_over_the_cap() -> None:
    pages = sorted((DESK / "site").rglob("*.html"))
    quotes = [(len(q), p.name) for p in pages for q in _quotes(p.read_text(encoding="utf-8"))]
    assert pages and quotes  # a check that reads nothing proves nothing
    over = sorted(x for x in quotes if x[0] > DESK_QUOTE_MAX_CHARS)
    assert not over, f"{len(over)} quote(s) over {DESK_QUOTE_MAX_CHARS} chars: {over[:10]}"


def test_the_guard_reads_every_quote_element_and_no_audit_line() -> None:
    assert _quotes(f'<td><div class="q">“{"x" * 401}”</div></td>') == ["x" * 401]  # caught
    assert _quotes(f'<div class="q">“{"x" * 400}”</div>') == ["x" * 400]
    assert _quotes(f"<blockquote>“{'y' * 9}”</blockquote>") == ["y" * 9]
    assert _quotes('<span class="q">a <b>bold</b> word</span>') == ["a bold word"]
    # NEGATIVE: a withheld card line's own text is the card's, not a source's
    assert _quotes('<details><summary class="note">audit text</summary><span class="q">'
                   f'{"z" * 900}</span></details>') == []
