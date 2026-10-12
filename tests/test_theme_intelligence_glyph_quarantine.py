"""Undecodable PDF glyph output is quarantined before anything reads it — and never hidden.

Observed 2026-10-11 on a real 60-page Citi research PDF: its last seven pages (a disclosure
appendix) are set in a font with no character map, so the text layer came out as "(cid:N)"
codes — 302,376 characters, 242,000 of the 293,161 tokens resent in every model call, 446 false
"figures" for the completeness review, and the body-size estimate skewed to the codes' size.

The fixture `glyph_mixed_synthetic.pdf` is a SYNTHETIC, real PDF (see make_glyph_fixture.py)
read by the real reader: a clean page; a MIXED page (readable lines, a line that merely mentions
"(cid:12)", undecodable lines, a ruled table with one undecodable cell); an unreadable page.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

import vinci.theme_intelligence.documents as documents_mod
from tests.theme_intelligence_support import (
    FIXTURES,
    JPM_DIR,
    FrozenSecHttp,
    Hypo,
    claim,
    extraction,
    fetched,
    hyp,
)
from vinci.theme_intelligence.completeness import scan_article
from vinci.theme_intelligence.config import PARSER_VERSION, load_sources, load_taxonomy
from vinci.theme_intelligence.documents import Declared, read_document
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.ingest import estimate_cost, ingest_file
from vinci.theme_intelligence.parse import unreadable_glyphs
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import ChangeClass, RetrievalState, RunStatus
from vinci.theme_intelligence.securities import SecResolver

SYN = FIXTURES / "synthetic_documents"
GLYPH = SYN / "glyph_mixed_synthetic.pdf"
CLEAN = [SYN / "ms_report_synthetic.pdf", SYN / "semianalysis_full_synthetic.pdf",
         SYN / "undated_synthetic.pdf"]
CODES = "(cid:3)(cid:7)(cid:12)(cid:9)(cid:4)(cid:22)"


def _read(path: Path) -> Any:
    return read_document(path, Declared(source_id="ms_research"))


def _unguarded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader as it was before the safeguard: every line and cell passes through."""
    monkeypatch.setattr(documents_mod, "_quarantine", lambda page, lines, tables: (
        lines, tables, None))


# --- what counts as undecodable ------------------------------------------------------------

@pytest.mark.parametrize("text", [CODES * 5, f"#{CODES * 3}‘ 1", "(cid:0)(cid:2)(cid:3)"])
def test_glyph_runs_are_unreadable(text: str) -> None:
    assert unreadable_glyphs(text)


@pytest.mark.parametrize("text", [
    "A sentence that mentions (cid:12) once is ordinary text.",  # a mention
    "e(cid:14)cient o(cid:14)ces and (cid:14)nancial margins rose in 2026, as the note expects",
    "(cid:1)(cid:2)",  # two codes are too few to call a line undecodable
    "(cid:1)(cid:2) two codes are not enough",
    "Transmission capex rose 18% in 2026 to $42 billion.",
])
def test_ordinary_text_is_never_unreadable(text: str) -> None:
    assert not unreadable_glyphs(text)


def _line(text: str, chars: list[tuple[str, str]]) -> dict[str, Any]:
    """A text line in pdfplumber's own shape: its text and its characters with their fonts."""
    return {"text": text, "top": 0.0, "bottom": 10.0,
            "chars": [{"text": t, "fontname": f, "size": 10.0} for t, f in chars]}


def test_a_font_without_a_character_map_takes_its_letters_with_it() -> None:
    """The real shape (2026-10-12, page 54): an unnamed font, 95% of whose 34,761 characters on
    the page were codes, also renders some glyphs as WRONG letters — "XQ10.(cid:3)GI(cid:3)…":
    only 3 codes in 24 characters of text, so the text test alone keeps it."""
    junk = [(f"(cid:{i})", "unknown") for i in range(40)]
    pieces = ["XQ10.", "GI", ":1G1", "<.B.CAD@", ">Q/0CH./GCE", "<.B.CAD@", "=/V.BGH./G",
              "<CG1/NBW"]  # the line as the real page gave it, between its 7 codes
    scrambled_text = "(cid:3)".join(pieces)
    scrambled = []
    for i, piece in enumerate(pieces):
        scrambled += [("(cid:3)", "unknown")] if i else []
        scrambled += [(c, "unknown") for c in piece]
    assert not unreadable_glyphs(scrambled_text)  # the text test alone would keep it
    readable_text = "e(cid:14)cient grid spending rose 18% in 2026"
    readable = [(c, "Helvetica") for c in "e"] + [("(cid:14)", "Helvetica")] + \
        [(c, "Helvetica") for c in "cient grid spending rose 18% in 2026"]
    # the page: ten lines of codes in that font (as on the real page, most of its output)
    lines = [_line("".join(t for t, _f in junk), junk) for _ in range(10)]
    lines += [_line(scrambled_text, scrambled), _line(readable_text, readable)]
    kept, _tables, q = documents_mod._quarantine(54, lines, [])
    assert [ln["text"] for ln in kept] == [readable_text]  # a stray code in a good font stays
    assert q is not None and q.lines == 11


def test_a_readable_font_with_stray_codes_is_never_condemned_whole() -> None:
    """A font that is mostly READABLE on the page, with ligature codes here and there, stays
    decodable — only a line that is itself mostly codes goes (the text test)."""
    def good(text: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for piece in text.split("(cid:14)"):
            out += [(c, "Helvetica") for c in piece] + [("(cid:14)", "Helvetica")]
        return out[:-1]

    texts = ["e(cid:14)cient grid spending rose 18% in 2026",
             "o(cid:14)ces and (cid:14)nancial terms were unchanged this year",
             "substation orders are projected to grow 12% in 2027"]
    coded = "".join(f"(cid:{i})" for i in range(12))
    lines = [_line(t, good(t)) for t in texts]
    lines.append(_line(coded, [(f"(cid:{i})", "Helvetica") for i in range(12)]))
    kept, _tables, q = documents_mod._quarantine(7, lines, [])
    assert [ln["text"] for ln in kept] == texts
    assert q is not None and q.lines == 1


# --- the reader: real PDF, mixed pages -------------------------------------------------------

def test_the_fixture_reproduces_the_defect_without_the_safeguard(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _unguarded(monkeypatch)
    r = _read(GLYPH)
    assert sum(b.text.count("(cid:") for b in r.doc.blocks) > 100  # the codes reach the text
    assert not r.quarantined
    # … and the old reader misdiagnosed the unreadable page holding an image as a scan
    assert any(i.startswith("page 3: no usable text layer") for i in r.issues)


def test_unreadable_lines_and_cells_are_quarantined_and_readable_ones_kept() -> None:
    r = _read(GLYPH)
    by_page = {q.page: q for q in r.quarantined}
    assert sorted(by_page) == [2, 3]
    assert (by_page[2].lines, by_page[2].cells, by_page[3].lines, by_page[3].cells) == (3, 1, 12, 0)
    texts = [(b.page, b.kind, b.text) for b in r.doc.blocks]
    # nothing undecodable reaches a block; the readable text survives with its page
    assert not any(unreadable_glyphs(t) for _p, _k, t in texts)
    assert (2, "paragraph", "A sentence that mentions (cid:12) once is ordinary text and "
                            "stays.") in texts  # a MENTION stays verbatim
    assert any(p == 2 and "lead times reached 30 months" in t for p, _k, t in texts)
    assert any(p == 2 and "7% rise in reserve margins" in t for p, _k, t in texts)
    assert (2, "table", "Metric | Value ; Capex growth | 18% ; Note |") in texts  # cell blanked
    assert any(p == 1 and k == "heading" for p, k, _t in texts)
    assert not any(p == 3 for p, _k, _t in texts)
    # said, never hidden: PARTIAL, each page named, what was left out counted and hashed
    assert r.doc.retrieval_state is RetrievalState.PARTIAL
    issues = " ".join(r.issues)
    assert "page 2: undecodable font glyphs" in issues and "page 3: undecodable" in issues
    assert "visual / OCR review" in issues and "1 table cell(s)" in issues
    assert "no usable text layer" not in issues  # page 3 holds an image: still not "a scan"
    assert all(len(q.sha256) == 64 and q.chars > 0 for q in r.quarantined)


def test_the_file_identity_is_unchanged() -> None:
    r = _read(GLYPH)
    assert r.sha256 == hashlib.sha256(GLYPH.read_bytes()).hexdigest()


def test_glyph_codes_are_never_figures_arguments_or_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    clean = _read(GLYPH)
    led = scan_article(clean.doc)
    figures = sorted((f.block_id, f.core) for f in led.figures)
    # exactly the readable figures — the mention's "(cid:12)" and every code's number excluded
    assert figures == [("b003", "12%"), ("b003", "18%"), ("b003", "42"), ("b004", "30"),
                       ("b006", "18%"), ("b007", "7%")]
    est = estimate_cost(clean)
    _unguarded(monkeypatch)
    raw = _read(GLYPH)
    led_raw = scan_article(raw.doc)
    # even text that still CONTAINS codes yields no figure from them, and no argument words
    assert sorted(f.core for f in led_raw.figures) == sorted(c for _b, c in figures)
    assert len(led_raw.argument_blocks) == len(led.argument_blocks)
    assert estimate_cost(raw).figures == est.figures


@pytest.mark.parametrize("path", CLEAN, ids=lambda p: p.name)
def test_a_clean_pdf_reads_exactly_as_before(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The safeguard never touches a PDF without undecodable glyphs: identical blocks."""
    guarded = _read(path)
    _unguarded(monkeypatch)
    plain = _read(path)
    assert not guarded.quarantined
    assert guarded.doc.content_sha256 == plain.doc.content_sha256
    assert [(b.page, b.kind) for b in guarded.doc.blocks] == \
        [(b.page, b.kind) for b in plain.doc.blocks]
    assert guarded.doc.retrieval_state is plain.doc.retrieval_state


# --- identity: the same file, read again by the new reader -----------------------------------

class Model:
    """Answers like the model; records every prompt it is SENT (a cache hit never arrives)."""

    model = "claude-opus-4-8"

    def __init__(self) -> None:
        self.users: list[str] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.users.append(user)
        self.last_usage = {"input_tokens": 100, "output_tokens": 40}
        if tool["name"] != "record_article_evidence":
            return {}
        quote = "Transmission capital expenditure rose 18% in 2026 to $42 billion"
        x = extraction([claim("c1", "b003", quote, "Transmission capex +18% in 2026",
                              metric="transmission capex growth", value=18, value_text="18%",
                              unit="%", period="2026")],
                       [hyp("h1", "Grid capex keeps rising", node="ai_infrastructure.power_grid",
                            mechanism="capex_spending_cycle", supporting=["c1"])])
        Extraction.model_validate(x)
        return x


def _pipe(tmp: Path, model: Model) -> Pipeline:
    resolver = SecResolver(tmp / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    return Pipeline(tmp / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=model, resolver=resolver, review=False)  # type: ignore[arg-type]


def _ingest(pipe: Pipeline, **kw: Any) -> Any:
    pipe.start_run("ingest", as_of=__import__("datetime").date(2026, 10, 12))
    res = ingest_file(pipe, GLYPH, Declared(source_id="ms_research", llm_permitted=True),
                      as_of=__import__("datetime").date(2026, 10, 12), **kw)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return res


def test_a_reread_is_a_new_version_of_the_same_article_with_history_kept(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    model = Model()
    pipe = _pipe(tmp_path, model)
    with monkeypatch.context() as m:  # the registry as the OLD reader left it
        _unguarded(m)
        first = _ingest(pipe)
    assert first.status == "INGESTED"
    v1 = pipe.store.article_version(first.version_id)
    assert v1 is not None and "(cid:" in "".join(b.text for b in v1.blocks)
    rec1 = pipe.store.document(first.doc_id)
    assert rec1 is not None
    reports1 = pipe.store.completeness(v1.version_id)
    sent_before = len(model.users)
    # the same file again: a DUPLICATE, and the note says a re-read would differ
    dup = _ingest(pipe)
    assert dup.status == "DUPLICATE" and "--reread" in dup.note
    assert len(model.users) == sent_before  # nothing sent
    # re-read: a NEW VERSION of the SAME article; the document's standing and arrival kept
    again = _ingest(pipe, reread=True)
    assert again.status == "INGESTED" and again.article_id == first.article_id
    assert again.version_id != first.version_id
    versions = pipe.store.article_versions(first.article_id)
    assert [v.version_id for v in versions] == [first.version_id, again.version_id]
    v2 = versions[-1]
    assert v2.parser_version == PARSER_VERSION and v2.retrieval_state is RetrievalState.PARTIAL
    assert "(cid:" not in "".join(b.text for b in v2.blocks if "mentions" not in b.text)
    assert len(pipe.store.articles()) == 1  # never a new, unrelated article
    rec = pipe.store.document(first.doc_id)
    assert rec is not None and rec.doc_id == rec1.doc_id and rec.sha256 == rec1.sha256
    assert rec.received_at == rec1.received_at and rec.filename == rec1.filename
    assert rec.version_id == again.version_id and [q.page for q in rec.quarantined] == [2, 3]
    assert len(rec.history) == len(rec1.history) + 1
    # the old version's verification is untouched; the model was ASKED again (new text)
    assert pipe.store.completeness(v1.version_id) == reports1
    new_prompts = model.users[sent_before:]
    assert new_prompts and not any("(cid:7)" in u for u in new_prompts)
    # one source, counted once: no independent confirmation from the same document
    for t in pipe.store.theses():
        links = pipe.store.links(t.thesis_id)
        assert len({lk.independence_group for lk in links}) == 1
        assert not [lk for lk in links if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]


def test_a_reread_of_unchanged_text_adds_nothing(tmp_path: Path) -> None:
    model = Model()
    pipe = _pipe(tmp_path, model)
    first = _ingest(pipe)
    sent = len(model.users)
    again = _ingest(pipe, reread=True)
    assert again.status == "DUPLICATE" and "unchanged" in again.note
    assert len(model.users) == sent and len(pipe.store.article_versions(first.article_id)) == 1


def test_the_weekly_report_asks_for_a_visual_review_never_for_a_missing_document(
        tmp_path: Path) -> None:
    from vinci.theme_intelligence.report import research_intake, research_verification

    pipe = _pipe(tmp_path, Model())
    _ingest(pipe)
    run = pipe.store.runs()[-1]
    intake = research_intake(pipe.store, run, [run], {"rows": [], "attention": []})
    review = [x for x in intake["needs_metadata"]["items"] if x.startswith("VISUAL / OCR REVIEW")]
    assert len(review) == 1 and "pages 2–3" in review[0] and "NOT read" in review[0]
    [awaiting] = intake["awaiting_documents"]["items"]
    assert "not a missing document: pages 2–3 could not be read" in awaiting
    v = research_verification(pipe.store, run)
    assert "read only in part (a preview, or pages that could not be read)" in v["summary"]


def test_a_reread_keeps_an_upgraded_documents_standing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A document that UPGRADED an article is still the upgrade after a re-read."""
    import datetime as dt

    pipe = _pipe(tmp_path, Model())
    pipe.start_run("article", as_of=dt.date(2026, 10, 12))
    preview = Hypo(slug="glyph-preview", publisher="Morgan Stanley", published=dt.date(2026, 10, 1),
                   blocks=[("paragraph", "Transmission capital expenditure rose 18% in 2026.")])
    doc = preview.doc()
    pre = pipe.process_document(doc, fetched(doc, state=RetrievalState.PARTIAL), url=preview.url,
                                source_id="ms_research", as_of=dt.date(2026, 10, 12))
    pipe.finish_run(RunStatus.SUCCEEDED)
    with monkeypatch.context() as m:
        _unguarded(m)
        up = _ingest(pipe, same_as=pre.article_id)
    assert up.status == "UPGRADED"
    again = _ingest(pipe, reread=True)
    assert again.status == "UPGRADED" and again.article_id == pre.article_id
    rec = pipe.store.document(up.doc_id)
    assert rec is not None and rec.status == "UPGRADED" and rec.version_id == again.version_id
