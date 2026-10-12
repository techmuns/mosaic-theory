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
import re
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


class Relabelling(Model):
    """The second answer labels the SAME sentence differently — observed on the real 60-page
    PDF on 2026-10-12: a re-read listed 18 sentences twice on five cards and called them "new"
    because each answer named the metric / period in its own words — and also takes the
    sentence's OTHER figure, which is evidence the first answer did not hold."""

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        first = not self.users
        x = super().extract(system=system, user=user, tool=tool, cache=cache)
        if tool["name"] != "record_article_evidence" or first:
            return x
        quote = x["claims"][0]["quote"]
        x["claims"] = [claim("c1", "b003", quote, "US transmission spending up 18%",
                             metric="US transmission capital spending", value=18,
                             value_text="18%", unit="%", period="calendar 2026"),
                       claim("c2", "b003", quote, "Transmission capex reached $42 billion",
                             metric="transmission capex", value=42e9, value_text="$42 billion",
                             unit="USD", period="2026")]
        x["hypotheses"][0]["supporting_claim_ids"] = ["c1", "c2"]
        Extraction.model_validate(x)
        return x


def test_a_reread_sentence_is_repeated_evidence_never_new_or_a_second_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = _pipe(tmp_path, Relabelling())
    with monkeypatch.context() as m:
        _unguarded(m)
        first = _ingest(pipe)
    again = _ingest(pipe, reread=True)
    assert again.article_id == first.article_id and again.version_id != first.version_id
    [t] = pipe.store.theses()
    claims = {c.claim_id: c for c in pipe.store.claims_for_article(first.article_id)}
    v2 = {lk.claim_id: lk for lk in pipe.store.links(t.thesis_id)
          if claims[lk.claim_id].article_version_id == again.version_id}
    by_value = {claims[cid].value_text: lk.change_class for cid, lk in v2.items()}
    # the same sentence and figure, labelled differently: REPEATED, not new evidence
    assert by_value["18%"] is ChangeClass.REPEATED
    # the same sentence's OTHER figure was never held: it is new (from an origin already counted)
    assert by_value["$42 billion"] is ChangeClass.NEW
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    rows = [(r.quote.lower(), r.value_text) for r in v.content.s04_key_evidence]
    assert len(rows) == len(set(rows)) == 2  # one row per figure — never the 18% twice
    assert not [lk for lk in pipe.store.links(t.thesis_id)
                if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]


class Aligning(Model):
    """A NORMAL re-read — alignment hints ON (the production path; the 2026-10-12 real-PDF harness
    had to switch them off to stay at $0). The second answer reads the registry candidates in its
    prompt and REUSES the grid-capex key, but keys the transformer story a new way. `cross`: the
    new thesis cites ONE earlier sentence among three of its own — cross-citation, no sibling."""

    def __init__(self, cross: bool = False, orphan: bool = False,
                 second: dict[str, str] | None = None) -> None:
        super().__init__()
        self.cross = cross
        self.orphan = orphan  # the re-read answer proposes no transformer thesis at all
        # how the re-read keys the transformer story (default: a PRICE mechanism — another family)
        self.second = second or {"mechanism": "pricing_cycle"}

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        first = not self.users
        super().extract(system=system, user=user, tool=tool, cache=cache)
        if tool["name"] != "record_article_evidence":
            return {}
        grid = "Transmission capital expenditure rose 18% in 2026 to $42 billion"
        lead = "transformer lead times reached 30 months in 2026"
        node, mech = "ai_infrastructure.power_grid", "capex_spending_cycle"
        if not first:  # align: take node / mechanism of the candidate this story matches
            m = re.search(r"^- ([\w.]+)\|(\w+)\|positive\|US — Grid capex keeps rising$", user,
                          re.M)
            assert m is not None, "the re-read prompt must carry the registry candidates"
            node, mech = m.group(1), m.group(2)
        more = [] if not (self.cross or self.orphan) or (first and not self.orphan) else [
            claim("c3", "b007", "a 7% rise in reserve margins", "Reserve margins +7%",
                  metric="reserve margin", value=7, value_text="7%", unit="%"),
            claim("c4", "b003", "substation orders are projected to grow 12% in 2027",
                  "Substation orders +12% in 2027", kind="forecast", epistemic="forecast",
                  metric="substation orders", value=12, value_text="12%", unit="%",
                  period="2027")]
        if self.second.get("partial") and not first:  # re-states only c2 of the 3 it cited
            more = []
        if self.second.get("first_more"):  # the FIRST reading cites c2-c4; the re-read only c2
            more = [] if not first else [
                claim("c3", "b007", "a 7% rise in reserve margins", "Reserve margins +7%",
                      metric="reserve margin", value=7, value_text="7%", unit="%"),
                claim("c4", "b003", "substation orders are projected to grow 12% in 2027",
                      "Substation orders +12% in 2027", kind="forecast", epistemic="forecast",
                      metric="substation orders", value=12, value_text="12%", unit="%",
                      period="2027")]
        if self.second.get("extra") and not first:  # ONE sentence the first read did not cite
            more = [claim("c4", "b003", "substation orders are projected to grow 12% in 2027",
                          "Substation orders +12% in 2027", kind="forecast",
                          epistemic="forecast", metric="substation orders", value=12,
                          value_text="12%", unit="%", period="2027")]
        x = extraction(
            [claim("c1", "b003", grid, "Transmission capex +18% in 2026",
                   metric="transmission capex" if first else "US transmission spending",
                   value=18, value_text="18%", unit="%", period="2026" if first else "CY2026"),
             claim("c2", "b004", lead, "Transformer lead times 30 months", metric="lead time",
                   value=30, value_text="30 months", period="2026"), *more],
            [hyp("h1", "Grid capex keeps rising", node=node, mechanism=mech, supporting=["c1"]),
             *([] if self.orphan and not first else [
                 hyp("h2", "Transformer shortage" if first else "Transformer prices re-rate",
                     node="ai_infrastructure.power_grid" if first else self.second.get(
                         "node", "ai_infrastructure.power_grid"),
                     mechanism="supply_constraint" if first else self.second["mechanism"],
                     direction="positive" if first else self.second.get("direction",
                                                                         "positive"),
                     supporting=["c2", *(c["local_id"] for c in more)])])])
        Extraction.model_validate(x)
        return x


def test_a_normal_reread_matches_the_mechanism_it_should_and_flags_the_one_it_keyed_anew(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # the re-keyed transformer story brings a sentence of its OWN (c4): a second claim to judge
    model = Aligning(second={"mechanism": "pricing_cycle", "extra": "1"})
    pipe = _pipe(tmp_path, model)
    with monkeypatch.context() as m:
        _unguarded(m)
        first = _ingest(pipe)
    v1_theses = {t.thesis_id: t.title for t in pipe.store.theses()}
    assert sorted(v1_theses.values()) == ["Grid capex keeps rising", "Transformer shortage"]
    sent = len(model.users)
    again = _ingest(pipe, reread=True)
    assert any("<registry_theses>" in u for u in model.users[sent:])  # alignment hints sent
    # identity: one article, one document, two versions; the first version's records kept
    assert len(pipe.store.articles()) == 1 and again.article_id == first.article_id
    assert len(pipe.store.article_versions(first.article_id)) == 2
    by_title = {t.title: t for t in pipe.store.theses()}
    grid = by_title["Grid capex keeps rising"]
    assert grid.thesis_id in v1_theses  # MATCHED: the aligned key updated the same thesis
    claims = {c.claim_id: c for c in pipe.store.claims_for_article(first.article_id)}
    v2_links = [lk for lk in pipe.store.links(grid.thesis_id)
                if claims[lk.claim_id].article_version_id == again.version_id]
    assert v2_links and all(lk.change_class is ChangeClass.REPEATED for lk in v2_links)
    # the transformer story keyed anew: a SIBLING — created, never merged, and flagged
    new = by_title["Transformer prices re-rate"]
    assert new.thesis_id not in v1_theses and len(pipe.store.theses()) == 3
    sib = [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"]
    assert len(sib) == 1 and sib[0].ref_id == new.thesis_id
    old = next(t for t, title in v1_theses.items() if title == "Transformer shortage")
    assert sib[0].detail.startswith(f"{old} / {new.thesis_id}")
    assert "SIBLING of “Transformer shortage”" in sib[0].detail
    [rep] = pipe.store.completeness_for_run(pipe.store.runs()[-1].run_id)
    assert rep.coverage is not None and any(a.startswith("sibling thesis: “Transformer prices")
                                            for a in rep.coverage.alerts)
    for t in pipe.store.theses():  # never a false independent confirmation
        assert not [lk for lk in pipe.store.links(t.thesis_id)
                    if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]


@pytest.mark.parametrize("second,label", [
    ({"mechanism": "demand_volume_shift"}, None),  # another label of the same (volume) family
    ({"mechanism": "supply_constraint", "node": "ai_infrastructure.datacenter_physical"},
     "different value-chain nodes (ai_infrastructure.datacenter_physical vs "
     "ai_infrastructure.power_grid; the thesis keeps ai_infrastructure.power_grid)"),
])
def test_a_reread_that_relabels_the_same_economic_claim_updates_the_same_thesis(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, second: dict[str, str],
        label: str | None) -> None:
    """2026-10-12, the real Gridlock re-read: the transformer story's 61 of 68 sentences came back
    under another key, and 5 more propositions under another value-chain NODE label — each had
    created a second thesis. The same sentences + the same direction, geography, mechanism
    family, segment, product and horizon are ONE thesis: updated, its id kept."""
    pipe = _pipe(tmp_path, Aligning(second=second))
    with monkeypatch.context() as m:
        _unguarded(m)
        first = _ingest(pipe)
    old = next(t.thesis_id for t in pipe.store.theses() if t.title == "Transformer shortage")
    again = _ingest(pipe, reread=True)
    assert len(pipe.store.theses()) == 2  # no second thesis from one article
    rid = pipe.store.runs()[-1].run_id
    assert [c.run_id for c in pipe.store.contributions(old)].count(rid) == 1  # attributed to it
    match = [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_MATCH"]
    assert [i.ref_id for i in match] == [old]
    assert (label in match[0].detail) if label else ("value-chain node" not in match[0].detail)
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"]
    claims = {c.claim_id: c for c in pipe.store.claims_for_article(first.article_id)}
    v2 = [lk for lk in pipe.store.links(old)
          if claims[lk.claim_id].article_version_id == again.version_id]
    assert v2 and all(lk.change_class is ChangeClass.REPEATED for lk in v2)
    for th in pipe.store.theses():  # a re-read never confirms anything
        assert not [lk for lk in pipe.store.links(th.thesis_id)
                    if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]


def test_a_matched_reread_counts_a_sentence_read_twice_once(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One sentence read again from another version is ONE piece of material evidence: the
    re-read's one NEW sentence moves the count by one, never by two (the real re-read took the
    low-cost US gas thesis's count 4 -> 8 with nothing new before this was pinned)."""
    pipe = _pipe(tmp_path, Aligning(second={"mechanism": "demand_volume_shift", "extra": "1"}))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    old = next(t.thesis_id for t in pipe.store.theses() if t.title == "Transformer shortage")
    _ingest(pipe, reread=True)
    assert [i.ref_id for i in pipe.store.issues() if i.code == "SAME_ARTICLE_MATCH"] == [old]
    f2 = {v.version: int(next(f.value for f in v.priority.factors
                              if f.factor_id == "F2_material_evidence"))
          for v in pipe.store.thesis_versions(old)}
    assert f2 == {1: 1, 2: 2}


@pytest.mark.parametrize("second,dim", [
    ({"mechanism": "supply_constraint", "direction": "negative"}, "direction (negative vs "
                                                                   "positive)"),
    # another FAMILY with evidence of its own (c4): maybe a second, separately falsifiable
    # mechanism — said with what each would mean for earnings
    ({"mechanism": "pricing_cycle", "extra": "1"},
     "economic mechanism (pricing_cycle, price_cost: earnings move with prices or input costs "
     "— vs supply_constraint, volume: earnings move with units or capacity sold); each reading "
     "cites evidence of its own (1 of 2 vs 0 of 1 sentences), so the source may hold two "
     "separately falsifiable mechanisms"),
])
def test_the_same_sentences_read_as_another_claim_are_held_for_review_never_merged(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, second: dict[str, str],
        dim: str) -> None:
    from vinci.theme_intelligence.schemas import ResearchAction, ThesisStatus

    pipe = _pipe(tmp_path, Aligning(second=second))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    _ingest(pipe, reread=True)
    new = next(t for t in pipe.store.theses() if t.title == "Transformer prices re-rate")
    assert new.status is ThesisStatus.REVIEW_NEEDED
    [sib] = [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"]
    assert sib.ref_id == new.thesis_id and dim in sib.detail
    v = pipe.store.thesis_version(new.thesis_id, new.current_version)
    assert v is not None and v.priority.research_action is not ResearchAction.RESEARCH_NOW
    hold = next(f for f in v.priority.factors if f.factor_id == "F10_verification_hold")
    assert hold.value == "HOLD" and "identity under review" in hold.note


@pytest.mark.parametrize("mechanism,family", [
    ("pricing_cycle", "price_cost"),            # a shortage read as its price step
    ("competitive_share_shift", "competition"),  # Citi's fuel cells: share gain vs volume
])
def test_the_same_evidence_read_as_another_step_of_the_chain_is_one_thesis(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mechanism: str, family: str) -> None:
    """Editorial decision (2026-10-12, the two fuel-cell readings, 14 of 17 sentences shared):
    two readings of ONE article that rest on the same evidence are one thesis — the earlier id
    kept, its mechanism kept, the other label stated as a step of the same causal chain — unless
    the evidence itself shows a second, separately falsifiable mechanism (the case above)."""
    pipe = _pipe(tmp_path, Aligning(second={"mechanism": mechanism}))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    old = next(t for t in pipe.store.theses() if t.title == "Transformer shortage")
    _ingest(pipe, reread=True)
    assert len(pipe.store.theses()) == 2  # no second thesis, no duplicate opportunity
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"]
    [match] = [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_MATCH"]
    assert match.ref_id == old.thesis_id
    assert "one causal chain read at two steps" in match.detail
    assert f"{mechanism} (" in match.detail and "no second, separately falsifiable" in match.detail
    kept = pipe.store.thesis(old.thesis_id)
    assert kept is not None and kept.key_mechanism == old.key_mechanism == "supply_constraint"
    for th in pipe.store.theses():
        assert not [lk for lk in pipe.store.links(th.thesis_id)
                    if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]


@pytest.mark.parametrize("second,code", [
    # the same key but its segment: an earlier VERSION's thesis (one sentence shared suffices)
    ({"mechanism": "supply_constraint"}, "SAME_ARTICLE_VERSION"),
    ({"mechanism": "supply_constraint", "cross": "1"}, "SAME_ARTICLE_VERSION"),  # 1 of 3 only
    # another label of the same family: matched on its sentences
    ({"mechanism": "demand_volume_shift"}, "SAME_ARTICLE_MATCH"),
])
def test_a_key_read_off_an_incidental_mention_is_corrected_once_a_reread_reaches_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, second: dict[str, str],
        code: str) -> None:
    """The real transformer thesis was keyed `onsite_generation` by the earlier rule (one CCGT
    comparison among 67 claims). Its re-read reaches it by another key: the SAME thesis is
    updated, its key corrected to its own subject — same id, versions and evidence, the old key
    recorded, and the old key still finds it (never a duplicate that would overwrite it). Both
    routes compare its segment AS IT IS TODAY, never only the stale one in its key."""
    from vinci.theme_intelligence import engine as engine_mod

    pipe = _pipe(tmp_path, Aligning(cross=bool(second.pop("cross", "")), second=second))
    real = engine_mod.segment_of
    with monkeypatch.context() as m:
        _unguarded(m)
        m.setattr(engine_mod, "segment_of",  # the EARLIER rule's reading, for this test
                  lambda h, *a, **k: "onsite_generation" if "Transformer" in h.raw.title
                  else real(h, *a, **k))
        _ingest(pipe)
    old = next(t for t in pipe.store.theses() if t.title == "Transformer shortage")
    assert old.key_segment == "onsite_generation"
    v1 = pipe.store.thesis_version(old.thesis_id, 1)
    _ingest(pipe, reread=True)
    assert len(pipe.store.theses()) == 2
    t = pipe.store.thesis(old.thesis_id)
    assert t is not None and t.key_segment == "grid_equipment"
    assert t.identity.endswith("|seg:grid_equipment")
    assert pipe.store.thesis_by_key(t.identity).thesis_id == old.thesis_id  # type: ignore[union-attr]
    assert pipe.store.thesis_by_key(old.identity) is None
    assert pipe.engine._by_key(old.identity).thesis_id == old.thesis_id  # type: ignore[union-attr]
    assert pipe.store.thesis_version(old.thesis_id, 1) == v1  # history untouched
    [ev] = [e for e in pipe.store.events(old.thesis_id) if e.event_type == "KEY_CORRECTED"]
    assert old.identity in ev.detail and t.identity in ev.detail
    assert [i.ref_id for i in pipe.store.issues() if i.code == "KEY_CORRECTED"] == [old.thesis_id]
    assert [i.ref_id for i in pipe.store.issues()
            if i.code in ("SAME_ARTICLE_VERSION", "SAME_ARTICLE_MATCH")] == [old.thesis_id]
    assert [i.code for i in pipe.store.issues()
            if i.code in ("SAME_ARTICLE_VERSION", "SAME_ARTICLE_MATCH")] == [code]


def test_an_unassigned_segment_today_is_no_evidence_of_a_shared_subject(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The grid-capex thesis was keyed `grid_utilities` by an earlier reading; by today's rule
    it names no segment. A re-read story naming ANOTHER segment on the same sentence is not
    shown to be the same subject by that blank — held for review, never folded in."""
    from vinci.theme_intelligence import engine as engine_mod

    pipe = _pipe(tmp_path, Aligning())
    real = engine_mod.segment_of

    def read(stale: str):  # type: ignore[no-untyped-def]
        return lambda h, *a, **k: stale if "Grid capex" in h.raw.title else real(h, *a, **k)

    with monkeypatch.context() as m:
        _unguarded(m)
        m.setattr(engine_mod, "segment_of", read("grid_utilities"))
        _ingest(pipe)
    grid = next(t for t in pipe.store.theses() if t.title == "Grid capex keeps rising")
    assert grid.key_segment == "grid_utilities" and pipe.engine.thesis_segment(grid) == ""
    with monkeypatch.context() as m:
        m.setattr(engine_mod, "segment_of", read("grid_equipment"))
        _ingest(pipe, reread=True)
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_VERSION"
                and i.ref_id == grid.thesis_id]
    sib = [i.detail for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"
           and "Grid capex" in i.detail]
    assert sib and "segment (grid_equipment vs grid_utilities)" in sib[0]


def test_a_thesis_with_no_segment_never_absorbs_another_story_of_the_article(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A thesis with NO segment nests with every segment. The re-read transformer story, keyed
    on the grid-capex thesis's node, mechanism and place, shares none of its sentences — it
    is the transformer thesis's (whose sentence it re-states), never folded into grid capex."""
    pipe = _pipe(tmp_path, Aligning(second={"mechanism": "capex_spending_cycle"}))
    with monkeypatch.context() as m:
        _unguarded(m)
        first = _ingest(pipe)
    by = {t.title: t for t in pipe.store.theses()}
    grid, old = by["Grid capex keeps rising"], by["Transformer shortage"]
    assert grid.key_segment == "" and grid.key_mechanism == "capex_spending_cycle"
    again = _ingest(pipe, reread=True)
    assert len(pipe.store.theses()) == 2
    assert [i.ref_id for i in pipe.store.issues() if i.code == "SAME_ARTICLE_MATCH"] == [
        old.thesis_id]
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_VERSION"]
    claims = {c.claim_id: c for c in pipe.store.claims_for_article(first.article_id)}
    on_grid = [claims[lk.claim_id].quote for lk in pipe.store.links(grid.thesis_id)
               if claims[lk.claim_id].article_version_id == again.version_id]
    assert not [q for q in on_grid if "transformer" in q]


def test_another_family_on_part_of_the_earlier_theses_evidence_goes_to_review(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SAME evidence means BOTH sides: the re-read cites one sentence, all of it on the earlier
    thesis — but that thesis rests on two more the re-read leaves out. Read as another kind of
    economics, it may be a second mechanism: held for review, never merged on one side's count."""
    pipe = _pipe(tmp_path, Aligning(second={"mechanism": "pricing_cycle", "first_more": "1"}))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    _ingest(pipe, reread=True)
    [sib] = [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"]
    assert "evidence of its own (0 of 1 vs 2 of 3 sentences)" in sib.detail
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_MATCH"]


def test_a_key_correction_never_takes_a_key_another_thesis_holds(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import date

    from vinci.theme_intelligence import engine as engine_mod

    pipe = _pipe(tmp_path, Aligning())
    real = engine_mod.segment_of
    with monkeypatch.context() as m:
        _unguarded(m)
        m.setattr(engine_mod, "segment_of",
                  lambda h, *a, **k: "onsite_generation" if "Transformer" in h.raw.title
                  else real(h, *a, **k))
        first = _ingest(pipe)
    old = next(t for t in pipe.store.theses() if t.title == "Transformer shortage")
    holder = old.model_copy(update={"thesis_id": "TH-HOLDER0000", "key_segment": "grid_equipment"})
    with pipe.store.tx():
        pipe.store.upsert_thesis(holder)
    art = pipe.store.article(first.article_id)
    assert art is not None
    pipe.start_run("ingest", as_of=date(2026, 10, 12))
    assert pipe.run is not None
    ctx = engine_mod.ArticleContext(article=art, version=pipe.store.article_versions(
        first.article_id)[-1], reliability="medium", run_id=pipe.run.run_id,
        as_of=date(2026, 10, 12))
    pipe.engine._correct_segment(ctx, old.thesis_id)
    pipe.finish_run(RunStatus.SUCCEEDED)
    kept = pipe.store.thesis(old.thesis_id)
    assert kept is not None and kept.key_segment == "onsite_generation"  # left, never doubled
    assert [i.code for i in pipe.store.issues() if i.ref_id == old.thesis_id
            and i.code.startswith("KEY_")] == ["KEY_NOT_CORRECTED"]


def test_one_shared_sentence_among_many_is_cross_citation_never_a_sibling(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = _pipe(tmp_path, Aligning(cross=True))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    _ingest(pipe, reread=True)
    assert len(pipe.store.theses()) == 3  # created, not merged …
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_SIBLING"]  # … no flag


def test_a_reread_fact_an_earlier_version_already_carries_is_no_coverage_alert(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The re-read proposes no transformer thesis; the earlier version's card still carries those
    sentences — carried, so no 'facts no thesis carries' alert (2026-10-12: Citi's p37 gas
    sentences on the first version's card)."""
    pipe = _pipe(tmp_path, Aligning(orphan=True))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    _ingest(pipe, reread=True)
    [rep] = pipe.store.completeness_for_run(pipe.store.runs()[-1].run_id)
    assert rep.coverage is not None
    assert not [g for g in rep.coverage.uncarried if g.status == "unexplained"
                and len(g.claim_ids) >= 2]
    assert not [a for a in rep.coverage.alerts if "no thesis carries" in a]
    # … and the earlier thesis those sentences sit on is RE-VERIFIED and re-assessed (the real
    # case: Citi's low-cost US gas thesis, WATCH -> SKIP-3 under the current timing rule)
    old = next(t for t in pipe.store.theses() if t.title == "Transformer shortage")
    assert rep.coverage.reverified == (old.thesis_id,)
    ev = [e for e in pipe.store.events(old.thesis_id) if e.event_type in ("REASSESSED",
                                                                          "ATTRIBUTION")]
    assert ev
    assert not [lk for lk in pipe.store.links(old.thesis_id)
                if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]


def test_a_reread_restating_under_half_of_a_thesis_is_carried_not_reverified(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The re-read re-states ONE of the three sentences the earlier transformer thesis cites and
    proposes nothing for it: too little to re-assess that thesis (under SIBLING_SHARE), yet the
    sentence is still on the earlier card — carried, never an uncarried fact."""
    pipe = _pipe(tmp_path, Aligning(orphan=True, second={"mechanism": "pricing_cycle",
                                                         "partial": "1"}))
    with monkeypatch.context() as m:
        _unguarded(m)
        _ingest(pipe)
    again = _ingest(pipe, reread=True)
    [rep] = pipe.store.completeness_for_run(pipe.store.runs()[-1].run_id)
    assert rep.coverage is not None and rep.coverage.reverified == ()
    restated = [c.claim_id for c in pipe.store.claims_for_article(again.article_id)
                if c.article_version_id == again.version_id and c.value_text == "30 months"]
    assert restated
    assert not [g for g in rep.coverage.uncarried if set(restated) & set(g.claim_ids)]


def _c(cid: str, version: str, quote: str, value: float | None, value_text: str | None, *,
       article: str = "A-1", metric: str = "m") -> Any:
    from vinci.theme_intelligence.schemas import Claim, ClaimKind, Confidence, Epistemic

    return Claim(claim_id=cid, article_id=article, article_version_id=version, block_id="b003",
                 char_start=0, char_end=len(quote), quote=quote, statement=quote,
                 kind=ClaimKind.METRIC, epistemic=Epistemic.ACTUAL, metric=metric, value=value,
                 value_text=value_text, confidence=Confidence.HIGH, span_verified=True,
                 number_verified=True, measure_key=f"k|{metric}", fingerprint=f"f|{cid}",
                 extraction_id="X-1")


S = "the gas cost makes up 31%, 32%, and 25%, respectively, for CCGT, recips, and fuel cells"


@pytest.mark.parametrize("new", [
    _c("n1", "AV-2", S.upper(), 31, "31%", metric="gas share of CCGT LCOE"),   # labelled anew
    _c("n2", "AV-2", "the gas cost makes up 31%, 32%, and 25%", 31, "31%"),    # a shorter quote
    _c("n3", "AV-2", S.replace(" ", " "), None, "31%"),                  # typography only
])
def test_the_same_sentence_from_another_version_is_the_same_evidence(new: Any) -> None:
    from vinci.theme_intelligence.verify import same_sentence_reread

    assert same_sentence_reread(_c("h", "AV-1", S, 31, "31%"), new)


@pytest.mark.parametrize("new", [
    _c("n1", "AV-1", S, 31, "31%"),                      # the SAME version: not a re-read
    _c("n2", "AV-2", S, 31, "31%", article="A-2"),       # another article quoting it
    _c("n3", "AV-2", S, 32, "32%"),                      # the same sentence's other figure
    _c("n6", "AV-2", S, None, "32%"),                    # ... with no parsed value either
    _c("n4", "AV-2", "fuel cells", 31, "31%"),           # a fragment, not the sentence
    _c("n5", "AV-2", "stack replacement cost is 30% of the total", 31, "31%"),  # another sentence
])
def test_another_sentence_figure_or_article_is_never_folded_in(new: Any) -> None:
    from vinci.theme_intelligence.verify import same_sentence_reread

    assert not same_sentence_reread(_c("h", "AV-1", S, 31, "31%"), new)


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
    # the rendered section says what kind of check it is (seen on the real report 2026-10-12:
    # a visual review filed under "a metadata or licence check")
    from vinci.theme_intelligence.report import _intake_html

    assert "1 needing a metadata, licence or visual check" in intake["line"]
    assert "Requiring a metadata, licence or visual check" in _intake_html(intake, False)
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
